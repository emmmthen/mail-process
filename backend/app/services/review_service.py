from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.email_feedback import EmailArtifact, EmailMessage, ExtractionRun, ReviewAction
from app.models.quote import Quote
from app.schemas.feedback import (
    ReviewApproveRequest,
    ReviewCorrectRequest,
    ReviewDetailResponse,
    ReviewPendingItem,
    ReviewRejectRequest,
)
from app.schemas.quote import QuoteCreate
from app.services.quote_service import QuoteService


class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.quote_service = QuoteService(db)

    async def list_pending_reviews(self, limit: int = 100) -> list[ReviewPendingItem]:
        runs = (
            self.db.query(ExtractionRun)
            .filter(ExtractionRun.run_status == "pending_review")
            .order_by(ExtractionRun.created_at.desc())
            .limit(limit)
            .all()
        )
        items: list[ReviewPendingItem] = []
        for run in runs:
            payload = run.llm_output_json or {}
            quote = (payload.get("quotes") or [{}])[0]
            items.append(
                ReviewPendingItem(
                    extraction_run_id=run.id,
                    email_message_id=run.email_message_id,
                    subject=run.email_message.subject if run.email_message else None,
                    sender=run.email_message.sender if run.email_message else None,
                    confidence_score=run.confidence_score,
                    run_status=run.run_status,
                    created_at=run.created_at,
                    quote_status=payload.get("quote_status"),
                    supplier_name=quote.get("supplier_name"),
                    part_number=quote.get("part_number"),
                )
            )
        return items

    async def get_review_detail(self, extraction_run_id: int) -> Optional[ReviewDetailResponse]:
        run = self.db.query(ExtractionRun).filter(ExtractionRun.id == extraction_run_id).first()
        if not run:
            return None
        return ReviewDetailResponse(
            email_message=run.email_message,
            email_artifact=run.email_artifact,
            extraction_run=run,
            review_actions=list(run.review_actions),
        )

    async def approve_review(self, extraction_run_id: int, request: ReviewApproveRequest):
        run = self._get_run_or_raise(extraction_run_id)
        final_values = request.final_values or run.llm_output_json or {}
        committed_quote = await self._commit_quote(run=run, final_values=final_values)
        return self._finalize_review(
            run=run,
            review_status="approved",
            review_reason=request.review_reason,
            reviewed_fields_json=None,
            final_values_json=final_values,
            can_reuse_as_pattern=request.can_reuse_as_pattern,
            reviewer=request.reviewer,
            committed_quote_id=committed_quote.id if committed_quote else None,
        )

    async def correct_review(self, extraction_run_id: int, request: ReviewCorrectRequest):
        run = self._get_run_or_raise(extraction_run_id)
        final_values = request.final_values or {}
        committed_quote = await self._commit_quote(run=run, final_values=final_values)
        return self._finalize_review(
            run=run,
            review_status="approved",
            review_reason=request.review_reason,
            reviewed_fields_json=request.reviewed_fields,
            final_values_json=final_values,
            can_reuse_as_pattern=request.can_reuse_as_pattern,
            reviewer=request.reviewer,
            committed_quote_id=committed_quote.id if committed_quote else None,
        )

    async def reject_review(self, extraction_run_id: int, request: ReviewRejectRequest):
        run = self._get_run_or_raise(extraction_run_id)
        return self._finalize_review(
            run=run,
            review_status="rejected",
            review_reason=request.review_reason,
            reviewed_fields_json=request.reviewed_fields,
            final_values_json=None,
            can_reuse_as_pattern=request.can_reuse_as_pattern,
            reviewer=request.reviewer,
            committed_quote_id=None,
        )

    async def delete_review(self, extraction_run_id: int):
        run = self._get_run_or_raise(extraction_run_id)
        for action in list(run.review_actions):
            self.db.delete(action)
        self.db.delete(run)
        self.db.commit()
        return {"deleted": True, "extraction_run_id": extraction_run_id}

    def restore_to_pending(self, extraction_run_id: int, reviewer: Optional[str] = None):
        run = self._get_run_or_raise(extraction_run_id)
        return self._finalize_review(
            run=run,
            review_status="pending_review",
            review_reason="review_not_finalized",
            reviewed_fields_json=None,
            final_values_json=None,
            can_reuse_as_pattern=False,
            reviewer=reviewer,
            committed_quote_id=None,
        )

    def _get_run_or_raise(self, extraction_run_id: int) -> ExtractionRun:
        run = self.db.query(ExtractionRun).filter(ExtractionRun.id == extraction_run_id).first()
        if not run:
            raise ValueError(f"Extraction run {extraction_run_id} not found")
        return run

    async def _commit_quote(self, *, run: ExtractionRun, final_values: dict[str, Any]):
        quote_create = QuoteCreate(
            part_number=final_values.get("part_number"),
            product_name=final_values.get("product_name"),
            supplier_name=final_values.get("supplier_name"),
            quantity=final_values.get("quantity"),
            currency=final_values.get("currency") or final_values.get("currency_symbol"),
            unit_price=final_values.get("unit_price") or final_values.get("usd_price"),
            cny_price=final_values.get("cny_price"),
            lead_time=final_values.get("lead_time"),
            moq=final_values.get("moq"),
            remarks=final_values.get("remarks"),
            exchange_rate=final_values.get("exchange_rate", 7.2),
            additional_fee=final_values.get("additional_fee", 0.0),
            service_fee_rate=final_values.get("service_fee_rate", 0.0),
            source_type=final_values.get("source_type", "email"),
            source_id=final_values.get("source_id") or str(run.email_message_id),
        )
        return await self.quote_service.create_quote(quote_create)

    def _finalize_review(
        self,
        *,
        run: ExtractionRun,
        review_status: str,
        review_reason: Optional[str],
        reviewed_fields_json: Optional[dict[str, Any]],
        final_values_json: Optional[dict[str, Any]],
        can_reuse_as_pattern: bool,
        reviewer: Optional[str],
        committed_quote_id: Optional[int],
    ):
        action = ReviewAction(
            extraction_run_id=run.id,
            review_status=review_status,
            review_reason=review_reason,
            reviewed_fields_json=reviewed_fields_json,
            final_values_json=final_values_json,
            can_reuse_as_pattern=can_reuse_as_pattern,
            reviewer=reviewer,
            reviewed_at=datetime.utcnow(),
        )
        self.db.add(action)

        run.run_status = review_status
        run.committed_quote_id = committed_quote_id
        run.updated_at = datetime.utcnow()

        if final_values_json is not None:
            run.llm_output_json = final_values_json

        self.db.commit()
        self.db.refresh(run)
        self.db.refresh(action)
        return {
            "extraction_run_id": run.id,
            "run_status": run.run_status,
            "committed_quote_id": run.committed_quote_id,
            "review_action_id": action.id,
        }

from __future__ import annotations

import email
import logging
import os
from typing import List

from sqlalchemy.orm import Session

from app.models.email_feedback import EmailArtifact, EmailMessage, ExtractionRun
from app.schemas.email import EmailImportResponse
from app.services.email_cleaner import EmailCleaner
from app.services.email_extractor import EmailExtractor
from app.services.email_rebuilder import EmailRebuilder
from app.services.email_validator import EmailValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EmailProcessor:
    """邮件数据提取处理器"""

    def __init__(self, db: Session):
        self.db = db
        self.cleaner = EmailCleaner()
        self.rebuilder = EmailRebuilder()
        self.extractor = EmailExtractor()
        self.validator = EmailValidator()

    async def process_email(self, email_path: str, process_type: str = "auto") -> EmailImportResponse:
        logger.info("开始处理邮件：%s", email_path)
        logger.info("处理类型：%s", process_type)

        try:
            raw_content = self._read_email_content(email_path)
            cleaned_text = self.cleaner.clean(raw_content)
            source_type = self._detect_source_type(email_path, cleaned_text)
            source_name = os.path.basename(email_path)
            rebuilt = self.rebuilder.rebuild(
                source_name=source_name,
                cleaned_text=cleaned_text,
                source_type=source_type,
            )

            email_message = self._create_email_message(email_path=email_path, source_type=source_type)
            email_artifact = self._create_email_artifact(
                email_message_id=email_message.id,
                cleaned_text=cleaned_text,
                rebuilt=rebuilt,
                extractable_status="pending",
            )

            extracted_quotes = await self.extractor.extract(
                content=rebuilt["rebuilt_text"],
                source_path=email_path,
                process_type=process_type,
            )
            validation = self.validator.validate(extracted_quotes, cleaned_text, rebuilt)

            extraction_run = self._create_extraction_run(
                email_message_id=email_message.id,
                email_artifact_id=email_artifact.id,
                extract_mode=process_type,
                llm_input_snapshot=rebuilt["rebuilt_text"],
                llm_output_json={
                    "quote_status": validation["quote_status"],
                    "quotes": extracted_quotes,
                },
                validation_result_json=validation,
                confidence_score=validation["confidence_score"],
                run_status="pending_review",
            )

            quotes_serialized = [self._serialize_extracted_quote(quote) for quote in extracted_quotes]
            message = self._build_result_message(validation, len(extracted_quotes))

            return EmailImportResponse(
                success=True,
                quotes_extracted=len(extracted_quotes),
                message=message,
                quotes=quotes_serialized,
            )
        except Exception as e:
            logger.exception("处理邮件时发生错误")
            return EmailImportResponse(
                success=False,
                quotes_extracted=0,
                message=f"处理失败：{str(e)}",
            )

    async def process_batch_emails(self, folder_path: str) -> EmailImportResponse:
        total_quotes = 0
        success_count = 0

        for filename in os.listdir(folder_path):
            if filename.endswith((".eml", ".msg", ".txt", ".html", ".pdf")):
                file_path = os.path.join(folder_path, filename)
                result = await self.process_email(file_path)
                if result.success:
                    success_count += 1
                    total_quotes += result.quotes_extracted

        return EmailImportResponse(
            success=True,
            quotes_extracted=total_quotes,
            message=f"成功处理 {success_count} 封邮件，提取 {total_quotes} 条报价",
        )

    def _create_email_message(self, email_path: str, source_type: str) -> EmailMessage:
        message = EmailMessage(
            subject=None,
            sender=None,
            received_at=None,
            source_file_path=email_path,
            source_file_hash=self._compute_source_hash(email_path),
            source_type=source_type,
            message_id=None,
            raw_status="received",
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def _create_email_artifact(self, *, email_message_id: int, cleaned_text: str, rebuilt: dict, extractable_status: str) -> EmailArtifact:
        artifact = EmailArtifact(
            email_message_id=email_message_id,
            cleaned_text=cleaned_text,
            rebuilt_text=rebuilt["rebuilt_text"],
            rebuilt_blocks_json=rebuilt["rebuilt_blocks_json"],
            extractable_status=extractable_status,
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def _create_extraction_run(
        self,
        *,
        email_message_id: int,
        email_artifact_id: int,
        extract_mode: str,
        llm_input_snapshot: str,
        llm_output_json: dict,
        validation_result_json: dict,
        confidence_score: float,
        run_status: str,
    ) -> ExtractionRun:
        run = ExtractionRun(
            email_message_id=email_message_id,
            email_artifact_id=email_artifact_id,
            extract_mode=extract_mode,
            llm_input_snapshot=llm_input_snapshot,
            llm_output_json=llm_output_json,
            validation_result_json=validation_result_json,
            confidence_score=confidence_score,
            run_status=run_status,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _serialize_extracted_quote(self, quote: dict):
        return {
            "part_number": quote.get("part_number"),
            "supplier_name": quote.get("supplier_name"),
            "usd_price": quote.get("usd_price"),
            "cny_price": quote.get("cny_price"),
            "currency_symbol": quote.get("currency_symbol"),
            "lead_time": quote.get("lead_time"),
            "moq": quote.get("moq"),
            "source_type": quote.get("source_type"),
            "source_location": quote.get("source_location"),
            "quote_status": quote.get("quote_status"),
            "confidence": quote.get("confidence"),
        }

    def _build_result_message(self, validation: dict, created_count: int) -> str:
        if validation["quote_status"] == "no_quote":
            return "检测到暂无报价，已记录为负样本并进入审核队列"
        return f"成功提取 {created_count} 条报价数据，已进入审核队列"

    def _detect_source_type(self, email_path: str, content: str) -> str:
        ext = os.path.splitext(email_path)[1].lower()
        if ext == ".pdf":
            return "pdf"
        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
            return "image"
        if "<html" in (content or "").lower() or "<table" in (content or "").lower():
            return "html"
        return "text"

    def _read_email_content(self, email_path: str) -> str:
        ext = os.path.splitext(email_path)[1].lower()

        if ext == ".eml":
            with open(email_path, "rb") as f:
                msg = email.message_from_bytes(f.read())

            content = []

            def process_part(part):
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    return

                if content_type in {"text/plain", "text/html"}:
                    charset = part.get_content_charset("utf-8")
                    try:
                        payload = part.get_payload(decode=True).decode(charset)
                    except Exception:
                        payload = part.get_payload()
                    content.append(payload)
                    return

                if part.is_multipart():
                    for subpart in part.get_payload():
                        process_part(subpart)

            if msg.is_multipart():
                for part in msg.get_payload():
                    process_part(part)
            else:
                process_part(msg)

            return "\n".join(content)

        with open(email_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def _compute_source_hash(self, email_path: str) -> str:
        try:
            import hashlib

            with open(email_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

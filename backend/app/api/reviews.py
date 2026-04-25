from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.feedback import (
    ReviewApproveRequest,
    ReviewCorrectRequest,
    ReviewDetailResponse,
    ReviewPendingItem,
    ReviewRejectRequest,
)
from app.services.review_service import ReviewService

router = APIRouter()


@router.get("/pending", response_model=list[ReviewPendingItem])
async def get_pending_reviews(limit: int = Query(100, le=1000), db: Session = Depends(get_db)):
    service = ReviewService(db)
    return await service.list_pending_reviews(limit=limit)


@router.get("/{extraction_run_id}", response_model=ReviewDetailResponse)
async def get_review_detail(extraction_run_id: int, db: Session = Depends(get_db)):
    service = ReviewService(db)
    detail = await service.get_review_detail(extraction_run_id)
    if not detail:
        raise HTTPException(status_code=404, detail="抽取记录不存在")
    return detail


@router.post("/{extraction_run_id}/approve")
async def approve_review(extraction_run_id: int, request: ReviewApproveRequest, db: Session = Depends(get_db)):
    service = ReviewService(db)
    try:
        return await service.approve_review(extraction_run_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{extraction_run_id}/correct")
async def correct_review(extraction_run_id: int, request: ReviewCorrectRequest, db: Session = Depends(get_db)):
    service = ReviewService(db)
    try:
        return await service.correct_review(extraction_run_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{extraction_run_id}/reject")
async def reject_review(extraction_run_id: int, request: ReviewRejectRequest, db: Session = Depends(get_db)):
    service = ReviewService(db)
    try:
        return await service.reject_review(extraction_run_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{extraction_run_id}")
async def delete_review(extraction_run_id: int, db: Session = Depends(get_db)):
    service = ReviewService(db)
    try:
        return await service.delete_review(extraction_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

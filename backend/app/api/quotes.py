from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models.quote import Quote
from app.schemas.quote import QuoteCreate, QuoteUpdate, QuoteResponse, QuoteComparison
from app.services.quote_service import QuoteService

router = APIRouter()


@router.post("/", response_model=QuoteResponse)
async def create_quote(quote: QuoteCreate, db: Session = Depends(get_db)):
    """创建报价记录"""
    service = QuoteService(db)
    return await service.create_quote(quote)


@router.get("/", response_model=list[QuoteResponse])
async def get_quotes(
    part_number: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """获取报价列表"""
    service = QuoteService(db)
    return await service.get_quotes(part_number=part_number, status=status, limit=limit)


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: int, db: Session = Depends(get_db)):
    """获取单个报价详情"""
    service = QuoteService(db)
    quote = await service.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="报价记录不存在")
    return quote


@router.put("/{quote_id}", response_model=QuoteResponse)
async def update_quote(quote_id: int, quote: QuoteUpdate, db: Session = Depends(get_db)):
    """更新报价记录"""
    service = QuoteService(db)
    return await service.update_quote(quote_id, quote)


@router.delete("/{quote_id}")
async def delete_quote(quote_id: int, db: Session = Depends(get_db)):
    """删除报价记录"""
    service = QuoteService(db)
    await service.delete_quote(quote_id)
    return {"message": "删除成功"}


@router.get("/comparison/{part_number}", response_model=QuoteComparison)
async def get_price_comparison(part_number: str, db: Session = Depends(get_db)):
    """获取比价单"""
    service = QuoteService(db)
    comparison = await service.get_price_comparison(part_number)
    if not comparison:
        raise HTTPException(status_code=404, detail="该件号没有报价记录")
    return comparison


@router.get("/comparison/all/export")
async def export_all_comparisons(db: Session = Depends(get_db)):
    """导出所有比价单（Excel）"""
    service = QuoteService(db)
    return await service.export_comparisons_to_excel()

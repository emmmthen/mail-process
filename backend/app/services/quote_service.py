from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import Optional, List
from app.models.quote import Quote, QuoteHistory
from app.schemas.quote import QuoteCreate, QuoteUpdate, QuoteComparison
import pandas as pd


class QuoteService:
    """报价管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_quote(self, quote: QuoteCreate) -> Quote:
        """创建报价记录"""
        # 计算人民币单价
        cny_price = self._calculate_cny_price(
            quote.usd_price,
            quote.exchange_rate,
            quote.additional_fee,
            quote.service_fee_rate
        )
        
        db_quote = Quote(
            part_number=quote.part_number,
            supplier_name=quote.supplier_name,
            usd_price=quote.usd_price,
            cny_price=cny_price,
            currency_symbol=quote.currency_symbol,
            exchange_rate=quote.exchange_rate or 7.2,
            additional_fee=quote.additional_fee or 0.0,
            service_fee_rate=quote.service_fee_rate or 0.0,
            lead_time=quote.lead_time,
            moq=quote.moq,
            source_type=quote.source_type,
            source_id=quote.source_id,
            status="valid"
        )
        
        self.db.add(db_quote)
        self.db.commit()
        self.db.refresh(db_quote)
        return db_quote
    
    async def get_quotes(
        self,
        part_number: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Quote]:
        """获取报价列表"""
        query = self.db.query(Quote)
        
        if part_number:
            query = query.filter(Quote.part_number.like(f"%{part_number}%"))
        if status:
            query = query.filter(Quote.status == status)
        
        return query.order_by(Quote.created_at.desc()).limit(limit).all()
    
    async def get_quote(self, quote_id: int) -> Optional[Quote]:
        """获取单个报价"""
        return self.db.query(Quote).filter(Quote.id == quote_id).first()
    
    async def update_quote(self, quote_id: int, quote: QuoteUpdate) -> Quote:
        """更新报价记录"""
        db_quote = await self.get_quote(quote_id)
        if not db_quote:
            raise ValueError(f"Quote {quote_id} not found")
        
        # 记录历史
        if quote.usd_price is not None and quote.usd_price != db_quote.usd_price:
            self._create_history(db_quote, "价格变更")
        
        # 更新字段
        update_data = quote.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_quote, field, value)
        
        # 重新计算人民币单价
        if any(k in update_data for k in ['usd_price', 'exchange_rate', 'additional_fee', 'service_fee_rate']):
            db_quote.cny_price = self._calculate_cny_price(
                db_quote.usd_price,
                db_quote.exchange_rate,
                db_quote.additional_fee,
                db_quote.service_fee_rate
            )
        
        db_quote.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_quote)
        return db_quote
    
    async def delete_quote(self, quote_id: int):
        """删除报价记录"""
        db_quote = await self.get_quote(quote_id)
        if db_quote:
            self.db.delete(db_quote)
            self.db.commit()
    
    async def get_price_comparison(self, part_number: str) -> Optional[QuoteComparison]:
        """获取比价单"""
        quotes = self.db.query(Quote).filter(
            and_(
                Quote.part_number == part_number,
                Quote.status == "valid"
            )
        ).all()
        
        if not quotes:
            return None
        
        # 找出最低价格
        valid_quotes = [q for q in quotes if q.cny_price is not None]
        min_cny_price = min(q.cny_price for q in valid_quotes) if valid_quotes else None
        
        return QuoteComparison(
            part_number=part_number,
            quotes=quotes,
            min_cny_price=min_cny_price,
            min_usd_price=min(q.usd_price for q in quotes) if any(q.usd_price for q in quotes) else None,
            supplier_count=len(quotes)
        )
    
    async def export_comparisons_to_excel(self):
        """导出所有比价单到 Excel"""
        # 获取所有件号
        part_numbers = self.db.query(Quote.part_number).distinct().all()
        
        all_data = []
        for (pn,) in part_numbers:
            comparison = await self.get_price_comparison(pn)
            if comparison:
                for quote in comparison.quotes:
                    all_data.append({
                        "件号": quote.part_number,
                        "供应商": quote.supplier_name,
                        "美金单价": quote.usd_price,
                        "人民币单价": quote.cny_price,
                        "交货期": quote.lead_time,
                        "MOQ": quote.moq,
                        "是否最低价": quote.cny_price == comparison.min_cny_price
                    })
        
        df = pd.DataFrame(all_data)
        
        # 保存到临时文件
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        df.to_excel(temp_file.name, index=False)
        
        return {"file_path": temp_file.name, "record_count": len(all_data)}
    
    def _calculate_cny_price(
        self,
        usd_price: Optional[float],
        exchange_rate: float = 7.2,
        additional_fee: float = 0.0,
        service_fee_rate: float = 0.0
    ) -> Optional[float]:
        """
        计算人民币单价
        公式：人民币单价 = 美金单价 × 汇率 + 附加费用 + (美金单价 × 服务费率)
        """
        if usd_price is None:
            return None
        
        return (usd_price * exchange_rate) + additional_fee + (usd_price * service_fee_rate)
    
    def _create_history(self, quote: Quote, reason: str):
        """创建历史记录"""
        history = QuoteHistory(
            quote_id=quote.id,
            part_number=quote.part_number,
            supplier_name=quote.supplier_name,
            usd_price=quote.usd_price,
            cny_price=quote.cny_price,
            exchange_rate=quote.exchange_rate,
            additional_fee=quote.additional_fee,
            service_fee_rate=quote.service_fee_rate,
            change_reason=reason
        )
        self.db.add(history)
        self.db.commit()

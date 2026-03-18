from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class QuoteBase(BaseModel):
    """报价基础 Schema"""
    part_number: str = Field(..., min_length=1, description="件号（必填）")
    supplier_name: Optional[str] = Field(None, max_length=200, description="供应商名称")
    
    usd_price: Optional[float] = Field(None, description="美金单价")
    currency_symbol: Optional[str] = Field(None, max_length=10, description="原始货币符号")
    
    lead_time: Optional[str] = Field(None, max_length=100, description="交货期")
    moq: Optional[int] = Field(None, description="最小起订量")
    remarks: Optional[str] = Field(None, description="备注信息")
    
    exchange_rate: Optional[float] = Field(7.2, description="汇率")
    additional_fee: Optional[float] = Field(0.0, description="附加费用")
    service_fee_rate: Optional[float] = Field(0.0, description="服务费率")


class QuoteCreate(QuoteBase):
    """创建报价 Schema"""
    source_type: Optional[str] = None
    source_id: Optional[str] = None


class QuoteUpdate(BaseModel):
    """更新报价 Schema"""
    supplier_name: Optional[str] = None
    usd_price: Optional[float] = None
    cny_price: Optional[float] = None
    currency_symbol: Optional[str] = None
    lead_time: Optional[str] = None
    moq: Optional[int] = None
    remarks: Optional[str] = None
    exchange_rate: Optional[float] = None
    additional_fee: Optional[float] = None
    service_fee_rate: Optional[float] = None
    status: Optional[str] = None


class QuoteResponse(QuoteBase):
    """报价响应 Schema"""
    id: int
    cny_price: Optional[float] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QuoteComparison(BaseModel):
    """比价单 Schema"""
    part_number: str
    quotes: list[QuoteResponse]
    min_cny_price: Optional[float] = None
    min_usd_price: Optional[float] = None
    supplier_count: int

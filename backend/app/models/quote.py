from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Quote(Base):
    """报价数据模型"""
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 核心业务字段
    part_number = Column(String(200), nullable=False, index=True, comment="件号（必填）")
    supplier_name = Column(String(200), index=True, comment="供应商名称")
    
    # 价格字段
    usd_price = Column(Float, nullable=True, comment="美金单价")
    cny_price = Column(Float, nullable=True, comment="人民币单价（计算得出）")
    currency_symbol = Column(String(10), nullable=True, comment="原始货币符号")
    
    # 汇率换算参数
    exchange_rate = Column(Float, default=7.2, comment="汇率（USD 转 CNY）")
    additional_fee = Column(Float, default=0.0, comment="附加费用")
    service_fee_rate = Column(Float, default=0.0, comment="服务费率（百分比）")
    
    # 其他业务字段
    lead_time = Column(String(100), nullable=True, comment="交货期")
    moq = Column(Integer, nullable=True, comment="最小起订量")
    remarks = Column(Text, nullable=True, comment="备注信息")
    
    # 数据来源和状态
    source_type = Column(String(50), nullable=True, comment="数据来源类型（email/html/pdf/image）")
    source_id = Column(String(200), nullable=True, comment="数据来源 ID（邮件 ID/文件路径）")
    status = Column(String(50), default="valid", comment="数据状态（valid/invalid/pending）")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关联字段（为未来多用户预留）
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="用户 ID（预留）")


class QuoteHistory(Base):
    """报价历史记录（用于追溯）"""
    __tablename__ = "quote_history"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    
    # 快照数据
    part_number = Column(String(200), nullable=False)
    supplier_name = Column(String(200))
    usd_price = Column(Float)
    cny_price = Column(Float)
    exchange_rate = Column(Float)
    additional_fee = Column(Float)
    service_fee_rate = Column(Float)
    lead_time = Column(String(100))
    moq = Column(Integer)
    remarks = Column(Text)
    
    # 变更时间
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_reason = Column(String(500), comment="变更原因")

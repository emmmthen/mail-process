from pydantic import BaseModel, Field
from typing import Optional


class SystemSettingsBase(BaseModel):
    """系统配置基础 Schema"""
    setting_key: str = Field(..., min_length=1, max_length=100)
    setting_value: str
    setting_type: Optional[str] = "string"
    description: Optional[str] = None


class SystemSettingsCreate(SystemSettingsBase):
    """创建系统配置 Schema"""
    pass


class SystemSettingsUpdate(BaseModel):
    """更新系统配置 Schema"""
    setting_value: Optional[str] = None
    description: Optional[str] = None


class SystemSettingsResponse(SystemSettingsBase):
    """系统配置响应 Schema"""
    id: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ExchangeRateSettings(BaseModel):
    """汇率换算公式配置 Schema"""
    exchange_rate: float = Field(7.2, description="美金转人民币汇率")
    additional_fee: float = Field(0.0, description="附加费用")
    service_fee_rate: float = Field(0.0, description="服务费率（百分比）")
    formula_description: Optional[str] = "人民币单价 = 美金单价 × 汇率 + 附加费用 + (美金单价 × 服务费率)"

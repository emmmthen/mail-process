from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "航空零件采购比价系统"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/quotes.db"
    
    # 邮件服务器配置
    EMAIL_USER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_IMAP_SERVER: Optional[str] = None
    EMAIL_IMAP_PORT: int = 993
    
    # 汇率换算公式配置
    EXCHANGE_RATE: float = 7.2  # 美金转人民币的汇率
    ADDITIONAL_FEE: float = 0.0  # 附加费用
    SERVICE_FEE_RATE: float = 0.0  # 服务费率（百分比）
    
    # 公式：人民币单价 = 美金单价 × 汇率 + 附加费用 + (美金单价 × 服务费率)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "航空零件采购比价系统"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/quotes.db"
    
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

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        """兼容常见环境值，避免 DEBUG=release 之类的配置导致启动失败。"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False
        return value
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

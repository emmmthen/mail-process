from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.system_settings import SystemSettings
from app.schemas.settings import ExchangeRateSettings


class SettingsService:
    """系统配置管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_exchange_rate_settings(self) -> ExchangeRateSettings:
        """获取汇率换算公式配置"""
        settings = {
            "exchange_rate": 7.2,
            "additional_fee": 0.0,
            "service_fee_rate": 0.0
        }
        
        db_settings = self.db.query(SystemSettings).filter(
            SystemSettings.setting_key.in_(["exchange_rate", "additional_fee", "service_fee_rate"])
        ).all()
        
        for setting in db_settings:
            if setting.setting_key in settings:
                settings[setting.setting_key] = float(setting.setting_value)
        
        return ExchangeRateSettings(**settings)
    
    async def update_exchange_rate_settings(self, settings: ExchangeRateSettings) -> ExchangeRateSettings:
        """更新汇率换算公式配置"""
        updates = [
            ("exchange_rate", str(settings.exchange_rate), "美金转人民币汇率"),
            ("additional_fee", str(settings.additional_fee), "附加费用"),
            ("service_fee_rate", str(settings.service_fee_rate), "服务费率（百分比）")
        ]
        
        for key, value, desc in updates:
            setting = self.db.query(SystemSettings).filter(
                SystemSettings.setting_key == key
            ).first()
            
            if setting:
                setting.setting_value = value
                setting.description = desc
            else:
                setting = SystemSettings(
                    setting_key=key,
                    setting_value=value,
                    setting_type="number",
                    description=desc
                )
                self.db.add(setting)
        
        self.db.commit()
        return settings
    
    async def get_all_settings(self) -> List[SystemSettings]:
        """获取所有系统配置"""
        return self.db.query(SystemSettings).all()
    
    async def create_setting(self, setting_data) -> SystemSettings:
        """创建系统配置"""
        setting = SystemSettings(**setting_data.model_dump())
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting
    
    async def update_setting(self, setting_key: str, setting_data) -> SystemSettings:
        """更新系统配置"""
        setting = self.db.query(SystemSettings).filter(
            SystemSettings.setting_key == setting_key
        ).first()
        
        if not setting:
            raise ValueError(f"Setting {setting_key} not found")
        
        update_data = setting_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(setting, field, value)
        
        self.db.commit()
        self.db.refresh(setting)
        return setting

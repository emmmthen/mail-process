from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.settings import (
    SystemSettingsCreate,
    SystemSettingsUpdate,
    SystemSettingsResponse,
    ExchangeRateSettings
)
from app.services.settings_service import SettingsService

router = APIRouter()


@router.get("/exchange-rate", response_model=ExchangeRateSettings)
async def get_exchange_rate_settings(db: Session = Depends(get_db)):
    """获取汇率换算公式配置"""
    service = SettingsService(db)
    return await service.get_exchange_rate_settings()


@router.put("/exchange-rate", response_model=ExchangeRateSettings)
async def update_exchange_rate_settings(
    settings: ExchangeRateSettings,
    db: Session = Depends(get_db)
):
    """更新汇率换算公式配置"""
    service = SettingsService(db)
    return await service.update_exchange_rate_settings(settings)


@router.get("/", response_model=list[SystemSettingsResponse])
async def get_all_settings(db: Session = Depends(get_db)):
    """获取所有系统配置"""
    service = SettingsService(db)
    return await service.get_all_settings()


@router.post("/", response_model=SystemSettingsResponse)
async def create_setting(
    setting: SystemSettingsCreate,
    db: Session = Depends(get_db)
):
    """创建系统配置"""
    service = SettingsService(db)
    return await service.create_setting(setting)


@router.put("/{setting_key}", response_model=SystemSettingsResponse)
async def update_setting(
    setting_key: str,
    setting: SystemSettingsUpdate,
    db: Session = Depends(get_db)
):
    """更新系统配置"""
    service = SettingsService(db)
    return await service.update_setting(setting_key, setting)

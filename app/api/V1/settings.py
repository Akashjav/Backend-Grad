from fastapi import APIRouter, Depends

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.profile import Profile

from app.models.settings import (
    UserPrivacySettings,
    UserNotificationPreferences,
    UserSecuritySettings,
    UserLanguageSettings
)

from app.schemas.settings import (
    AccountUpdate,
    SecuritySettingsUpdate,
    NotificationSettingsUpdate,
    PrivacySettingsUpdate,
    LanguageSettingsUpdate
)

from app.services import settings_service

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get('/')
async def get_settings(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await settings_service.get_settings(current_user, db)

@router.patch('/account')
async def update_account_settings(data: AccountUpdate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await settings_service.update_account_settings(data, current_user, db)

@router.patch('/security')
async def update_security_settings(data: SecuritySettingsUpdate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await settings_service.update_security_settings(data, current_user, db)

@router.patch('/notifications')
async def update_notification_settings(data: NotificationSettingsUpdate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await settings_service.update_notification_settings(data, current_user, db)

@router.patch('/privacy')
async def update_privacy_settings(data: PrivacySettingsUpdate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await settings_service.update_privacy_settings(data, current_user, db)

@router.patch('/language')
async def update_language_settings(data: LanguageSettingsUpdate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await settings_service.update_language_settings(data, current_user, db)

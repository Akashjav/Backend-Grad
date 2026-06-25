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

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("/")
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    privacy_result = await db.execute(
        select(UserPrivacySettings).where(UserPrivacySettings.user_id == current_user.id)
    )
    privacy = privacy_result.scalar_one_or_none()

    notif_result = await db.execute(
        select(UserNotificationPreferences).where(UserNotificationPreferences.user_id == current_user.id)
    )
    notifications = notif_result.scalar_one_or_none()

    security_result = await db.execute(
        select(UserSecuritySettings).where(UserSecuritySettings.user_id == current_user.id)
    )
    security = security_result.scalar_one_or_none()

    language_result = await db.execute(
        select(UserLanguageSettings).where(UserLanguageSettings.user_id == current_user.id)
    )
    language = language_result.scalar_one_or_none()

    return {
        "account": {
            "display_name": profile.display_name if profile else None,
            "headline": profile.headline if profile else None,
            "company": profile.company if profile else None,
            "location": profile.location if profile else None,
            "bio": profile.bio if profile else None
        },
        "privacy": {
            "public_profile": privacy.public_profile if privacy else True,
            "show_email": privacy.show_email if privacy else False,
            "discoverable": privacy.discoverable if privacy else True,
            "read_receipts": privacy.read_receipts if privacy else True
        },
        "notifications": {
            "messages": notifications.messages if notifications else True,
            "events": notifications.events if notifications else True,
            "mentions": notifications.mentions if notifications else True,
            "weekly_digest": notifications.weekly_digest if notifications else True,
            "product_updates": notifications.product_updates if notifications else False
        },
        "security": {
            "two_factor_enabled": security.two_factor_enabled if security else False,
            "signin_alerts": security.signin_alerts if security else True
        },
        "language": {
            "language": language.language if language else "en"
        }
    }

@router.patch("/account")
async def update_account_settings(
    data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        profile = Profile(user_id=current_user.id, display_name=current_user.email)
        db.add(profile)
        await db.flush()

    if data.display_name is not None:
        profile.display_name = data.display_name
    if data.headline is not None:
        profile.headline = data.headline
    if data.company is not None:
        profile.company = data.company
    if data.location is not None:
        profile.location = data.location
    if data.bio is not None:
        profile.bio = data.bio

    await db.commit()

    return {"message": "Account settings updated successfully"}

@router.patch("/security")
async def update_security_settings(
    data: SecuritySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserSecuritySettings).where(UserSecuritySettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserSecuritySettings(user_id=current_user.id)
        db.add(settings)
        await db.flush()

    if data.two_factor_enabled is not None:
        settings.two_factor_enabled = data.two_factor_enabled
    if data.signin_alerts is not None:
        settings.signin_alerts = data.signin_alerts

    await db.commit()
    return {"message": "Security settings updated successfully"}

@router.patch("/notifications")
async def update_notification_settings(
    data: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserNotificationPreferences).where(
            UserNotificationPreferences.user_id == current_user.id
        )
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserNotificationPreferences(user_id=current_user.id)
        db.add(settings)
        await db.flush()

    if data.messages is not None:
        settings.messages = data.messages
    if data.events is not None:
        settings.events = data.events
    if data.mentions is not None:
        settings.mentions = data.mentions
    if data.weekly_digest is not None:
        settings.weekly_digest = data.weekly_digest
    if data.product_updates is not None:
        settings.product_updates = data.product_updates

    await db.commit()
    return {"message": "Notification settings updated successfully"}

@router.patch("/privacy")
async def update_privacy_settings(
    data: PrivacySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserPrivacySettings).where(UserPrivacySettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserPrivacySettings(user_id=current_user.id)
        db.add(settings)
        await db.flush()

    if data.public_profile is not None:
        settings.public_profile = data.public_profile
    if data.show_email is not None:
        settings.show_email = data.show_email
    if data.discoverable is not None:
        settings.discoverable = data.discoverable
    if data.read_receipts is not None:
        settings.read_receipts = data.read_receipts

    await db.commit()
    return {"message": "Privacy settings updated successfully"}

@router.patch("/language")
async def update_language_settings(
    data: LanguageSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UserLanguageSettings).where(UserLanguageSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserLanguageSettings(user_id=current_user.id)
        db.add(settings)
        await db.flush()

    settings.language = data.language

    await db.commit()
    return {"message": "Language settings updated successfully"}

from pydantic import BaseModel
from typing import Optional


class AccountUpdate(BaseModel):
    display_name: Optional[str] = None
    headline: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None


class SecuritySettingsUpdate(BaseModel):
    two_factor_enabled: Optional[bool] = None
    signin_alerts: Optional[bool] = None


class NotificationSettingsUpdate(BaseModel):
    messages: Optional[bool] = None
    events: Optional[bool] = None
    mentions: Optional[bool] = None
    weekly_digest: Optional[bool] = None
    product_updates: Optional[bool] = None


class PrivacySettingsUpdate(BaseModel):
    public_profile: Optional[bool] = None
    show_email: Optional[bool] = None
    discoverable: Optional[bool] = None
    read_receipts: Optional[bool] = None


class LanguageSettingsUpdate(BaseModel):
    language: str
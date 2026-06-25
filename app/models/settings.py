from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class UserPrivacySettings(Base):
    __tablename__ = "user_privacy_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)

    public_profile: Mapped[bool] = mapped_column(Boolean, default=True)
    show_email: Mapped[bool] = mapped_column(Boolean, default=False)
    discoverable: Mapped[bool] = mapped_column(Boolean, default=True)
    read_receipts: Mapped[bool] = mapped_column(Boolean, default=True)


class UserNotificationPreferences(Base):
    __tablename__ = "user_notification_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)

    messages: Mapped[bool] = mapped_column(Boolean, default=True)
    events: Mapped[bool] = mapped_column(Boolean, default=True)
    mentions: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_digest: Mapped[bool] = mapped_column(Boolean, default=True)
    product_updates: Mapped[bool] = mapped_column(Boolean, default=False)


class UserSecuritySettings(Base):
    __tablename__ = "user_security_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)

    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    signin_alerts: Mapped[bool] = mapped_column(Boolean, default=True)


class UserLanguageSettings(Base):
    __tablename__ = "user_language_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)

    language: Mapped[str] = mapped_column(String, default="en")
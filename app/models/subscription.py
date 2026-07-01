from sqlalchemy import String, Text, ForeignKey, DateTime, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timedelta

from app.models.user import Base


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"), nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    features: Mapped[str] = mapped_column(Text, nullable=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id"), nullable=True)

    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    status: Mapped[str] = mapped_column(String, default="trial")
    payment_status: Mapped[str] = mapped_column(String, default="unpaid")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), nullable=True)

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[str] = mapped_column(String, nullable=True)
    payment_status: Mapped[str] = mapped_column(String, default="pending")
    transaction_id: Mapped[str] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
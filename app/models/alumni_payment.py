from sqlalchemy import String, ForeignKey, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.models.user import Base


class AlumniEarning(Base):
    __tablename__ = "alumni_earnings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    alumni_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    session_id: Mapped[int] = mapped_column(ForeignKey("mentorship_sessions.id"), nullable=False)

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, default="unpaid")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AlumniPayout(Base):
    __tablename__ = "alumni_payouts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    alumni_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    session_count: Mapped[int] = mapped_column(Integer, default=0)

    payout_status: Mapped[str] = mapped_column(String, default="pending")
    payment_method: Mapped[str] = mapped_column(String, nullable=True)
    transaction_id: Mapped[str] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    paid_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
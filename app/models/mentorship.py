from sqlalchemy import String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.models.user import Base


class MentorshipRequest(Base):
    __tablename__ = "mentorship_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    alumni_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    topic: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MentorshipSession(Base):
    __tablename__ = "mentorship_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    request_id: Mapped[int] = mapped_column(ForeignKey("mentorship_requests.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    alumni_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    topic: Mapped[str] = mapped_column(String, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)

    meeting_link: Mapped[str] = mapped_column(String, nullable=True)
    recording_url: Mapped[str] = mapped_column(String, nullable=True)

    status: Mapped[str] = mapped_column(String, default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
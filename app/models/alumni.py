from sqlalchemy import String, ForeignKey, Text, DateTime, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.models.user import Base


class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)

    department: Mapped[str] = mapped_column(String, nullable=True)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=True)

    current_role: Mapped[str] = mapped_column(String, nullable=True)
    company: Mapped[str] = mapped_column(String, nullable=True)
    industry: Mapped[str] = mapped_column(String, nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=True)

    linkedin_url: Mapped[str] = mapped_column(String, nullable=True)
    mentorship_areas: Mapped[str] = mapped_column(Text, nullable=True)

    focus: Mapped[str] = mapped_column(String, nullable=True)
    chapter: Mapped[str] = mapped_column(String, nullable=True)
    availability: Mapped[str] = mapped_column(String, nullable=True)
    response_time: Mapped[str] = mapped_column(String, nullable=True)

    current_project: Mapped[str] = mapped_column(Text, nullable=True)
    impact: Mapped[str] = mapped_column(Text, nullable=True)

    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0)

    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
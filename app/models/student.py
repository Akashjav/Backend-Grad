from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.models.user import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)

    roll_number: Mapped[str] = mapped_column(String, nullable=True)
    department: Mapped[str] = mapped_column(String, nullable=True)
    year_of_study: Mapped[int] = mapped_column(Integer, nullable=True)
    cgpa: Mapped[float] = mapped_column(Float, nullable=True)

    skills: Mapped[str] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[str] = mapped_column(String, nullable=True)
    github_url: Mapped[str] = mapped_column(String, nullable=True)
    career_goals: Mapped[str] = mapped_column(Text, nullable=True)

    verification_status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
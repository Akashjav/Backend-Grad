from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.models.user import Base


class StudentDocument(Base):
    __tablename__ = "student_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    document_type: Mapped[str] = mapped_column(String, nullable=False)
    file_url: Mapped[str] = mapped_column(String, nullable=False)

    verification_status: Mapped[str] = mapped_column(String, default="pending")
    verified_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
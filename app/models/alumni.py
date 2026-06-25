from sqlalchemy import String, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id"))
    focus: Mapped[str] = mapped_column(String)
    chapter: Mapped[str] = mapped_column(String)
    availability: Mapped[str] = mapped_column(String)
    response_time: Mapped[str] = mapped_column(String)
    current_project: Mapped[str] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(Text)

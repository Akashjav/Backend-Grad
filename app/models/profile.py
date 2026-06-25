from sqlalchemy import String, Integer, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id"))
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    headline: Mapped[str] = mapped_column(String, nullable=True)
    company: Mapped[str] = mapped_column(String, nullable=True)
    location: Mapped[str] = mapped_column(String, nullable=True)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)

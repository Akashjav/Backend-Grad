import uuid
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.user import Base


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    blurb: Mapped[str] = mapped_column(Text, nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    cadence: Mapped[str] = mapped_column(String, nullable=True)
    activity: Mapped[str] = mapped_column(String, nullable=True)


class CommunityMembership(Base):
    __tablename__ = "community_memberships"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    community_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("communities.id"))
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id"))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

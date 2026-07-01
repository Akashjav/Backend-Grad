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

class CommunityPost(Base):
    __tablename__ = "community_posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    community_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("communities.id"), nullable=False)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[str] = mapped_column(Text, nullable=True)

    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    replies_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CommunityPostLike(Base):
    __tablename__ = "community_post_likes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CommunityPostReply(Base):
    __tablename__ = "community_post_replies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("community_posts.id"), nullable=False)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

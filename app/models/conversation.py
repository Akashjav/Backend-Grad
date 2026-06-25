from sqlalchemy import String, Text, ForeignKey, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.user import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String)
    created_by: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id"))


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    author_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

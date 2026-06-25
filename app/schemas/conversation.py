from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class ConversationCreate(BaseModel):
    other_user_id: UUID
    title: Optional[str] = None


class MessageCreate(BaseModel):
    body: str

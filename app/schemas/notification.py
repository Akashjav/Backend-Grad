from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class NotificationCreate(BaseModel):
    user_id: UUID
    kind: str
    title: str
    body: str
    action_url: Optional[str] = None

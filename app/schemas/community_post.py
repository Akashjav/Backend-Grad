from pydantic import BaseModel
from typing import Optional


class CommunityPostCreate(BaseModel):
    title: str
    body: str
    tags: Optional[str] = None


class CommunityReplyCreate(BaseModel):
    body: str
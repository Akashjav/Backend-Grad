from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EventCreate(BaseModel):
    title: str
    starts_at: datetime
    ends_at: Optional[datetime] = None
    location: str
    event_type: str
    host: Optional[str] = None
    audience: Optional[str] = None
    description: str
    capacity: int
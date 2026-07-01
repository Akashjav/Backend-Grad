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

    domain_id: Optional[int] = None
    speaker_name: Optional[str] = None
    speaker_company: Optional[str] = None
    cover_image_url: Optional[str] = None

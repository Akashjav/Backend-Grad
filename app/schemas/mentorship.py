from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MentorshipRequestCreate(BaseModel):
    alumni_id: str
    topic: str
    message: Optional[str] = None


class MentorshipSessionCreate(BaseModel):
    request_id: int
    scheduled_at: datetime
    duration_minutes: int = 60
    meeting_link: Optional[str] = None
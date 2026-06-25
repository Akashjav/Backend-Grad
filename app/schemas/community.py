from pydantic import BaseModel
from typing import Optional


class CommunityCreate(BaseModel):
    name: str
    category: str
    blurb: str
    cadence: Optional[str] = None
    activity: Optional[str] = None
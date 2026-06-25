from pydantic import BaseModel
from typing import Optional


class AlumniCreate(BaseModel):
    focus: str
    chapter: str
    availability: str
    response_time: str
    current_project: str
    impact: str


class AlumniResponse(BaseModel):
    id: int
    display_name: str
    headline: Optional[str]
    company: Optional[str]
    location: Optional[str]
    graduation_year: Optional[int]
    bio: Optional[str]
    focus: str
    chapter: str
    availability: str
    response_time: str
    current_project: str
    impact: str
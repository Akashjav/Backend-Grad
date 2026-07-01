from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobCreate(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    job_type: str
    salary_or_stipend: Optional[str] = None
    deadline: Optional[datetime] = None
    description: str
    tags: Optional[str] = None
from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


from pydantic import BaseModel, EmailStr
from typing import Optional


class StudentSignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    roll_number: Optional[str] = None
    department: Optional[str] = None
    year_of_study: Optional[int] = None
    cgpa: Optional[float] = None
    skills: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    career_goals: Optional[str] = None


class AlumniSignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    graduation_year: Optional[int] = None
    department: Optional[str] = None
    current_company: Optional[str] = None
    current_role: Optional[str] = None
    years_of_experience: Optional[int] = None
    linkedin_url: Optional[str] = None
    mentorship_areas: Optional[str] = None
    availability: Optional[str] = None
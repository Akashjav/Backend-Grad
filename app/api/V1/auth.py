from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.api.deps import get_db

from app.models.user import User

from app.models.profile import Profile

from app.schemas.auth import SignupRequest, SigninRequest, TokenResponse

from app.core.security import hash_password, verify_password, create_access_token

from fastapi.security import OAuth2PasswordRequestForm

from app.models.student import StudentProfile

from app.models.alumni import AlumniProfile

from app.models.profile import Profile

from app.schemas.auth import StudentSignupRequest, AlumniSignupRequest

from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post('/signup', response_model=TokenResponse)
async def signup(data: SignupRequest, db: AsyncSession=Depends(get_db)):
    return await auth_service.signup(data, db)

@router.post('/signin', response_model=TokenResponse)
async def signin(form_data: OAuth2PasswordRequestForm=Depends(), db: AsyncSession=Depends(get_db)):
    return await auth_service.signin(form_data, db)

@router.post('/signup/student')
async def signup_student(data: StudentSignupRequest, db: AsyncSession=Depends(get_db)):
    return await auth_service.signup_student(data, db)

@router.post('/signup/alumni')
async def signup_alumni(data: AlumniSignupRequest, db: AsyncSession=Depends(get_db)):
    return await auth_service.signup_alumni(data, db)

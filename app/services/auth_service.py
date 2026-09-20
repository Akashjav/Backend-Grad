from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.profile import Profile
from app.schemas.auth import SignupRequest, SigninRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from app.models.student import StudentProfile
from app.models.alumni import AlumniProfile
from app.models.profile import Profile
from app.schemas.auth import StudentSignupRequest, AlumniSignupRequest
from app.core.config import settings
from app.core.workers import password_work

def legacy_registration_guard():
    if settings.APP_ENV == 'production':
        raise HTTPException(410, 'Use /api/v1/auth/signup and email verification')

async def signup(data: SignupRequest, db: AsyncSession):
    legacy_registration_guard()
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    user = User(email=data.email, password_hash=await password_work(hash_password, data.password), role='student', is_active=True, is_verified=False)
    db.add(user)
    await db.flush()
    profile = Profile(user_id=user.id, display_name=data.display_name)
    db.add(profile)
    await db.commit()
    token = create_access_token({'sub': user.id})
    return {'access_token': token, 'token_type': 'bearer'}

async def signin(form_data: OAuth2PasswordRequestForm, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail='Invalid email or password')
    if not await password_work(verify_password, form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Invalid email or password')
    from app.models.platform import DomainProfile
    if settings.APP_ENV == 'production' or await db.get(DomainProfile, user.id):
        if not user.is_verified:
            raise HTTPException(403, 'Verify your email before signing in')
        from app.services.identity_service import issue_session
        tokens = await issue_session(db, user)
        await db.commit()
        return tokens
    token = create_access_token({'sub': user.id})
    return {'access_token': token, 'token_type': 'bearer'}

async def signup_student(data: StudentSignupRequest, db: AsyncSession):
    legacy_registration_guard()
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    user = User(email=data.email, password_hash=await password_work(hash_password, data.password), role='student', is_active=True, is_verified=False)
    db.add(user)
    await db.flush()
    profile = Profile(user_id=user.id, display_name=data.full_name, headline='Student', location=None, company=None, bio=None)
    student_profile = StudentProfile(user_id=user.id, roll_number=data.roll_number, department=data.department, year_of_study=data.year_of_study, cgpa=data.cgpa, skills=data.skills, linkedin_url=data.linkedin_url, github_url=data.github_url, career_goals=data.career_goals)
    db.add(profile)
    db.add(student_profile)
    await db.commit()
    token = create_access_token({'sub': user.id})
    return {'message': 'Student registered successfully', 'access_token': token, 'token_type': 'bearer', 'user': {'id': user.id, 'email': user.email, 'role': user.role, 'display_name': data.full_name}}

async def signup_alumni(data: AlumniSignupRequest, db: AsyncSession):
    legacy_registration_guard()
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    user = User(email=data.email, password_hash=await password_work(hash_password, data.password), role='alumni', is_active=True, is_verified=False)
    db.add(user)
    await db.flush()
    profile = Profile(user_id=user.id, display_name=data.full_name, headline=data.current_role, company=data.current_company, graduation_year=data.graduation_year, bio=None)
    alumni_profile = AlumniProfile(user_id=user.id, department=data.department, graduation_year=data.graduation_year, current_role=data.current_role, company=data.current_company, experience_years=data.years_of_experience, linkedin_url=data.linkedin_url, mentorship_areas=data.mentorship_areas, availability=data.availability, focus=data.mentorship_areas, chapter=data.department, response_time='Replies in 1 day', current_project=None, impact=None)
    db.add(profile)
    db.add(alumni_profile)
    await db.commit()
    token = create_access_token({'sub': user.id})
    return {'message': 'Alumni registered successfully', 'access_token': token, 'token_type': 'bearer', 'user': {'id': user.id, 'email': user.email, 'role': user.role, 'display_name': data.full_name}}

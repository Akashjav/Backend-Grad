from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.config import settings
from app.api.deps import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.student import StudentProfile
from app.models.alumni import AlumniProfile

router = APIRouter(prefix="/api", tags=["Users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/signin")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            user_id = str(UUID(user_id))
        except (TypeError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    profile_result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    response = {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "profile": {
            "display_name": profile.display_name if profile else None,
            "headline": profile.headline if profile else None,
            "company": profile.company if profile else None,
            "location": profile.location if profile else None,
            "bio": profile.bio if profile else None,
        }
    }

    if current_user.role == "student":
        student_result = await db.execute(
            select(StudentProfile).where(StudentProfile.user_id == current_user.id)
        )
        student = student_result.scalar_one_or_none()

        response["student_profile"] = {
            "roll_number": student.roll_number if student else None,
            "department": student.department if student else None,
            "year_of_study": student.year_of_study if student else None,
            "cgpa": student.cgpa if student else None,
            "skills": student.skills if student else None,
            "linkedin_url": student.linkedin_url if student else None,
            "github_url": student.github_url if student else None,
            "career_goals": student.career_goals if student else None,
            "verification_status": student.verification_status if student else None
        }

    if current_user.role == "alumni":
        alumni_result = await db.execute(
            select(AlumniProfile).where(AlumniProfile.user_id == current_user.id)
        )
        alumni = alumni_result.scalar_one_or_none()

        response["alumni_profile"] = {
            "department": alumni.department if alumni else None,
            "graduation_year": alumni.graduation_year if alumni else None,
            "current_role": alumni.current_role if alumni else None,
            "company": alumni.company if alumni else None,
            "industry": alumni.industry if alumni else None,
            "experience_years": alumni.experience_years if alumni else None,
            "linkedin_url": alumni.linkedin_url if alumni else None,
            "mentorship_areas": alumni.mentorship_areas if alumni else None,
            "availability": alumni.availability if alumni else None,
            "is_starred": alumni.is_starred if alumni else False,
            "rating": alumni.rating if alumni else 0,
            "verified": alumni.verified_at is not None if alumni else False
        }

    return response
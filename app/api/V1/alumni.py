from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.models.profile import Profile
from app.models.alumni import AlumniProfile

from app.schemas.alumni import AlumniCreate
from app.models.user import User
from app.api.V1.users import get_current_user
from app.models.user import User
from app.schemas.alumni import AlumniCreate
from app.models.subscription import Subscription
from app.models.notification import Notification

router = APIRouter(prefix="/api/alumni", tags=["Alumni"])


@router.get("/")
async def get_alumni(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AlumniProfile, Profile)
        .join(Profile, AlumniProfile.user_id == Profile.user_id)
    )

    rows = result.all()

    alumni_list = []

    for alumni, profile in rows:
        alumni_list.append({
            "id": alumni.id,
            "display_name": profile.display_name,
            "headline": profile.headline,
            "company": profile.company,
            "location": profile.location,
            "graduation_year": profile.graduation_year,
            "bio": profile.bio,
            "focus": alumni.focus,
            "chapter": alumni.chapter,
            "availability": alumni.availability,
            "response_time": alumni.response_time,
            "current_project": alumni.current_project,
            "impact": alumni.impact
        })

    return alumni_list

@router.post("/")
async def create_alumni(
    data: AlumniCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(
        select(AlumniProfile).where(AlumniProfile.user_id == current_user.id)
    )
    existing_alumni = existing.scalar_one_or_none()

    if existing_alumni:
        raise HTTPException(status_code=400, detail="Alumni profile already exists")

    alumni = AlumniProfile(
        user_id=current_user.id,
        focus=data.focus,
        chapter=data.chapter,
        availability=data.availability,
        response_time=data.response_time,
        current_project=data.current_project,
        impact=data.impact
    )

    db.add(alumni)
    await db.commit()
    await db.refresh(alumni)

    return {
        "message": "Alumni profile created successfully",
        "alumni_id": alumni.id
    }


@router.get("/{alumni_id}")
async def get_alumni_detail(
    alumni_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AlumniProfile, Profile)
        .join(Profile, AlumniProfile.user_id == Profile.user_id)
        .where(AlumniProfile.id == alumni_id)
    )

    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Alumni not found")

    alumni, profile = row

    return {
        "id": alumni.id,
        "display_name": profile.display_name,
        "headline": profile.headline,
        "company": profile.company,
        "location": profile.location,
        "graduation_year": profile.graduation_year,
        "bio": profile.bio,
        "focus": alumni.focus,
        "chapter": alumni.chapter,
        "availability": alumni.availability,
        "response_time": alumni.response_time,
        "current_project": alumni.current_project,
        "impact": alumni.impact
    }
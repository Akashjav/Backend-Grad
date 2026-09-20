from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.profile import Profile
from app.models.alumni import AlumniProfile
from app.schemas.alumni import AlumniCreate
from app.models.user import User
from app.models.user import User
from app.schemas.alumni import AlumniCreate
from app.models.subscription import Subscription
from app.models.notification import Notification
from app.models.platform import DomainProfile
from app.models.settings import UserPrivacySettings
from sqlalchemy import or_

def public_alumni():
    return (select(AlumniProfile, Profile).join(Profile, AlumniProfile.user_id == Profile.user_id)
        .join(User, User.id == AlumniProfile.user_id)
        .outerjoin(DomainProfile, DomainProfile.user_id == User.id)
        .outerjoin(UserPrivacySettings, UserPrivacySettings.user_id == User.id)
        .where(User.is_active.is_(True), or_(DomainProfile.user_id.is_(None), DomainProfile.discoverable.is_(True)),
               or_(UserPrivacySettings.user_id.is_(None), UserPrivacySettings.public_profile.is_(True)),
               or_(UserPrivacySettings.user_id.is_(None), UserPrivacySettings.discoverable.is_(True))))

async def get_alumni(db: AsyncSession):
    result = await db.execute(public_alumni())
    rows = result.all()
    alumni_list = []
    for alumni, profile in rows:
        alumni_list.append({'id': alumni.id, 'display_name': profile.display_name, 'headline': profile.headline, 'company': profile.company, 'location': profile.location, 'graduation_year': profile.graduation_year, 'bio': profile.bio, 'focus': alumni.focus, 'chapter': alumni.chapter, 'availability': alumni.availability, 'response_time': alumni.response_time, 'current_project': alumni.current_project, 'impact': alumni.impact})
    return alumni_list

async def create_alumni(data: AlumniCreate, current_user: User, db: AsyncSession):
    if current_user.role != 'alumni':
        raise HTTPException(403, 'Only alumni can create alumni profiles')
    existing = await db.execute(select(AlumniProfile).where(AlumniProfile.user_id == current_user.id))
    existing_alumni = existing.scalar_one_or_none()
    if existing_alumni:
        raise HTTPException(status_code=400, detail='Alumni profile already exists')
    alumni = AlumniProfile(user_id=current_user.id, focus=data.focus, chapter=data.chapter, availability=data.availability, response_time=data.response_time, current_project=data.current_project, impact=data.impact)
    db.add(alumni)
    await db.commit()
    await db.refresh(alumni)
    return {'message': 'Alumni profile created successfully', 'alumni_id': alumni.id}

async def get_alumni_detail(alumni_id: int, db: AsyncSession):
    result = await db.execute(public_alumni().where(AlumniProfile.id == alumni_id))
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail='Alumni not found')
    alumni, profile = row
    return {'id': alumni.id, 'display_name': profile.display_name, 'headline': profile.headline, 'company': profile.company, 'location': profile.location, 'graduation_year': profile.graduation_year, 'bio': profile.bio, 'focus': alumni.focus, 'chapter': alumni.chapter, 'availability': alumni.availability, 'response_time': alumni.response_time, 'current_project': alumni.current_project, 'impact': alumni.impact}

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

from app.services import alumni_service

router = APIRouter(prefix="/api/alumni", tags=["Alumni"])

@router.get('/')
async def get_alumni(db: AsyncSession=Depends(get_db)):
    return await alumni_service.get_alumni(db)

@router.post('/')
async def create_alumni(data: AlumniCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await alumni_service.create_alumni(data, current_user, db)

@router.get('/{alumni_id}')
async def get_alumni_detail(alumni_id: int, db: AsyncSession=Depends(get_db)):
    return await alumni_service.get_alumni_detail(alumni_id, db)

from fastapi import APIRouter, Depends

from sqlalchemy import select, func

from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.alumni import AlumniProfile

from app.models.profile import Profile

from app.models.community import Community

from app.models.events import Event

from app.models.notification import Notification

from app.models.mentorship import MentorshipRequest, MentorshipSession

from app.models.job import JobApplication, SavedJob

from app.models.subscription import Subscription, Domain

from app.models.alumni_payment import AlumniEarning

from app.models.student_document import StudentDocument

from fastapi import HTTPException

from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get('/')
async def get_dashboard(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await dashboard_service.get_dashboard(current_user, db)

@router.get('/student')
async def student_dashboard(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await dashboard_service.student_dashboard(current_user, db)

@router.get('/alumni')
async def alumni_dashboard(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await dashboard_service.alumni_dashboard(current_user, db)

@router.get('/admin')
async def admin_dashboard(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await dashboard_service.admin_dashboard(current_user, db)

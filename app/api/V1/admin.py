from datetime import datetime

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.alumni import AlumniProfile

from app.models.events import Event

from app.models.notification import Notification

from app.models.student_document import StudentDocument

from app.models.student import StudentProfile

from app.models.subscription import Subscription

from sqlalchemy import func

from app.models.alumni_payment import AlumniEarning, AlumniPayout

from app.schemas.alumni_payment import AlumniPayoutCreate

from app.services import admin_service

router = APIRouter(prefix="/api/admin", tags=["Admin"])

def check_admin(current_user: User):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

@router.get('/users')
async def get_all_users(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await admin_service.get_all_users(current_user, db)

@router.patch('/users/{user_id}/role')
async def update_user_role(user_id: str, role: str, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await admin_service.update_user_role(user_id, role, current_user, db)

@router.post('/alumni/{alumni_id}/verify')
async def verify_alumni(alumni_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await admin_service.verify_alumni(alumni_id, current_user, db)

@router.post('/events/{event_id}/publish')
async def publish_event(event_id: str, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await admin_service.publish_event(event_id, current_user, db)

@router.patch('/student-documents/{document_id}/verify')
async def verify_student_document(document_id: int, status: str, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await admin_service.verify_student_document(document_id, status, current_user, db)

@router.get('/alumni-earnings')
async def get_all_alumni_earnings(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await admin_service.get_all_alumni_earnings(current_user, db)

@router.get('/alumni-earnings/{alumni_id}')
async def get_alumni_earnings(alumni_id: str, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await admin_service.get_alumni_earnings(alumni_id, current_user, db)

@router.post('/alumni-payouts')
async def create_alumni_payout(data: AlumniPayoutCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await admin_service.create_alumni_payout(data, current_user, db)

@router.patch('/alumni-payouts/{payout_id}/mark-paid')
async def mark_payout_paid(payout_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await admin_service.mark_payout_paid(payout_id, current_user, db)

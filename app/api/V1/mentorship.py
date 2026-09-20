from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.mentorship import MentorshipRequest, MentorshipSession

from app.schemas.mentorship import MentorshipRequestCreate, MentorshipSessionCreate

from app.models.alumni_payment import AlumniEarning

from app.services import mentorship_service

router = APIRouter(prefix="/api/mentorship", tags=["Mentorship"])

@router.post('/requests')
async def create_mentorship_request(data: MentorshipRequestCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await mentorship_service.create_mentorship_request(data, current_user, db)

@router.get('/requests/my')
async def get_my_mentorship_requests(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await mentorship_service.get_my_mentorship_requests(current_user, db)

@router.get('/requests/incoming')
async def get_incoming_mentorship_requests(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await mentorship_service.get_incoming_mentorship_requests(current_user, db)

@router.patch('/requests/{request_id}/accept')
async def accept_mentorship_request(request_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await mentorship_service.accept_mentorship_request(request_id, current_user, db)

@router.patch('/requests/{request_id}/reject')
async def reject_mentorship_request(request_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await mentorship_service.reject_mentorship_request(request_id, current_user, db)

@router.post('/sessions')
async def create_mentorship_session(data: MentorshipSessionCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await mentorship_service.create_mentorship_session(data, current_user, db)

@router.get('/sessions/my')
async def get_my_mentorship_sessions(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await mentorship_service.get_my_mentorship_sessions(current_user, db)

@router.patch('/sessions/{session_id}/complete')
async def complete_mentorship_session(session_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await mentorship_service.complete_mentorship_session(session_id, current_user, db)

@router.patch('/sessions/{session_id}/cancel')
async def cancel_mentorship_session(session_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await mentorship_service.cancel_mentorship_session(session_id, current_user, db)

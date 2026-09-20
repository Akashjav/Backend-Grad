from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from uuid import UUID

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.events import Event, EventRSVP

from app.models.subscription import Domain

from app.schemas.event import EventCreate

from app.services import events_service

router = APIRouter(prefix="/api/events", tags=["Events"])

@router.post('/')
async def create_event(data: EventCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await events_service.create_event(data, current_user, db)

@router.get('/')
async def get_events(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await events_service.get_events(current_user, db)

@router.get('/{event_id}')
async def get_event_detail(event_id: UUID, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await events_service.get_event_detail(event_id, current_user, db)

@router.post('/{event_id}/rsvp')
async def rsvp_event(event_id: UUID, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await events_service.rsvp_event(event_id, current_user, db)

@router.delete('/{event_id}/rsvp')
async def cancel_rsvp(event_id: UUID, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await events_service.cancel_rsvp(event_id, current_user, db)

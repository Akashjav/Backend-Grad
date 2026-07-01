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


router = APIRouter(prefix="/api/events", tags=["Events"])


@router.post("/")
async def create_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if data.domain_id is not None:
        domain_result = await db.execute(
            select(Domain).where(Domain.id == data.domain_id)
        )
        if not domain_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Domain not found")

    event = Event(
        title=data.title,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        location=data.location,
        event_type=data.event_type,
        host=data.host,
        audience=data.audience,
        description=data.description,
        capacity=data.capacity,
        attendees=0,
        domain_id=data.domain_id,
        speaker_name=data.speaker_name,
        speaker_company=data.speaker_company,
        cover_image_url=data.cover_image_url,
        status="draft"
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    return {
        "message": "Event created successfully",
        "event_id": event.id
    }


@router.get("/")
async def get_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Event).order_by(Event.starts_at))
    events = result.scalars().all()

    output = []

    for event in events:
        rsvp_result = await db.execute(
            select(EventRSVP).where(
                EventRSVP.event_id == event.id,
                EventRSVP.user_id == current_user.id
            )
        )

        is_rsvped = rsvp_result.scalar_one_or_none() is not None

        output.append({

            "id": event.id,
            "title": event.title,
            "starts_at": event.starts_at,
            "ends_at": event.ends_at,
            "location": event.location,
            "event_type": event.event_type,
            "host": event.host,
            "audience": event.audience,
            "description": event.description,
            "capacity": event.capacity,
            "attendees": event.attendees,
            "is_rsvped": is_rsvped,
            "domain_id": event.domain_id,
            "speaker_name": event.speaker_name,
            "speaker_company": event.speaker_company,
            "cover_image_url": event.cover_image_url,
            "status": event.status
        })

    return output


@router.get("/{event_id}")
async def get_event_detail(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    event_id = str(event_id)

    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    rsvp_result = await db.execute(
        select(EventRSVP).where(
            EventRSVP.event_id == event.id,
            EventRSVP.user_id == current_user.id
        )
    )

    is_rsvped = rsvp_result.scalar_one_or_none() is not None

    return {
        "id": event.id,
        "title": event.title,
        "starts_at": event.starts_at,
        "ends_at": event.ends_at,
        "location": event.location,
        "event_type": event.event_type,
        "host": event.host,
        "audience": event.audience,
        "description": event.description,
        "capacity": event.capacity,
        "attendees": event.attendees,
        "is_rsvped": is_rsvped,
        "domain_id": event.domain_id,
        "speaker_name": event.speaker_name,
        "speaker_company": event.speaker_company,
        "cover_image_url": event.cover_image_url,
        "status": event.status
    }


@router.post("/{event_id}/rsvp")
async def rsvp_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    event_id = str(event_id)

    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    existing = await db.execute(
        select(EventRSVP).where(
            EventRSVP.event_id == event_id,
            EventRSVP.user_id == current_user.id
        )
    )

    if existing.scalar_one_or_none():
        return {"message": "Already RSVPed"}

    if event.attendees >= event.capacity:
        raise HTTPException(status_code=400, detail="Event is full")

    rsvp = EventRSVP(
        event_id=event_id,
        user_id=current_user.id,
        status="going"
    )

    event.attendees += 1

    db.add(rsvp)
    await db.commit()

    return {"message": "RSVP successful"}


@router.delete("/{event_id}/rsvp")
async def cancel_rsvp(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    event_id = str(event_id)

    result = await db.execute(
        select(EventRSVP).where(
            EventRSVP.event_id == event_id,
            EventRSVP.user_id == current_user.id
        )
    )

    rsvp = result.scalar_one_or_none()

    if not rsvp:
        raise HTTPException(status_code=404, detail="RSVP not found")

    event_result = await db.execute(select(Event).where(Event.id == event_id))
    event = event_result.scalar_one_or_none()

    if event and event.attendees > 0:
        event.attendees -= 1

    await db.delete(rsvp)
    await db.commit()

    return {"message": "RSVP cancelled successfully"}

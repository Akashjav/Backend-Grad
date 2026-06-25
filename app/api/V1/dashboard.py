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

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    users_count = await db.execute(
        select(func.count(User.id))
        .outerjoin(AlumniProfile, User.id == AlumniProfile.user_id)
        .where(AlumniProfile.id == None)
    )
    alumni_count = await db.execute(select(func.count(AlumniProfile.id)))
    community_count = await db.execute(select(func.count(Community.id)))
    event_count = await db.execute(select(func.count(Event.id)))

    upcoming_events_result = await db.execute(
        select(Event)
        .where(Event.starts_at > datetime.utcnow())
        .order_by(Event.starts_at)
        .limit(3)
    )
    upcoming_events = upcoming_events_result.scalars().all()

    alumni_result = await db.execute(
        select(AlumniProfile, Profile)
        .join(Profile, AlumniProfile.user_id == Profile.user_id)
        .where(Profile.headline != None)
        .limit(3)
    )
    alumni_rows = alumni_result.all()

    communities_result = await db.execute(
        select(Community)
        .where(Community.member_count > 0)
        .limit(3)
    )
    communities = communities_result.scalars().all()

    unread_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.read_at == None
        )
    )

    return {
        "stats": {
            "total_users": users_count.scalar(),
            "total_alumni": alumni_count.scalar(),
            "total_communities": community_count.scalar(),
            "total_events": event_count.scalar()
        },
        "upcoming_events": [
            {
                "id": event.id,
                "title": event.title,
                "starts_at": event.starts_at,
                "location": event.location,
                "event_type": event.event_type,
                "capacity": event.capacity,
                "attendees": event.attendees
            }
            for event in upcoming_events
        ],
        "featured_alumni": [
            {
                "id": alumni.id,
                "display_name": profile.display_name,
                "headline": profile.headline,
                "company": profile.company,
                "location": profile.location,
                "focus": alumni.focus,
                "availability": alumni.availability
            }
            for alumni, profile in alumni_rows
        ],
        "active_communities": [
            {
                "id": community.id,
                "name": community.name,
                "category": community.category,
                "member_count": community.member_count,
                "activity": community.activity
            }
            for community in communities
        ],
        "notifications_count": unread_result.scalar()
    }

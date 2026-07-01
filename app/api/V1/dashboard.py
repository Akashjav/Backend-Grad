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

@router.get("/student")
async def student_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this dashboard")

    subscription_result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )
    subscription = subscription_result.scalars().first()

    mentorship_result = await db.execute(
        select(MentorshipRequest)
        .where(MentorshipRequest.student_id == current_user.id)
        .order_by(MentorshipRequest.created_at.desc())
        .limit(5)
    )

    sessions_result = await db.execute(
        select(MentorshipSession)
        .where(MentorshipSession.student_id == current_user.id)
        .order_by(MentorshipSession.scheduled_at)
        .limit(5)
    )

    notifications_result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(5)
    )

    saved_jobs_count = await db.execute(
        select(func.count(SavedJob.id)).where(SavedJob.user_id == current_user.id)
    )

    applied_jobs_count = await db.execute(
        select(func.count(JobApplication.id)).where(JobApplication.user_id == current_user.id)
    )

    return {
        "role": "student",
        "subscription": {
            "status": subscription.status if subscription else None,
            "end_date": subscription.end_date if subscription else None,
            "domain_id": subscription.domain_id if subscription else None
        },
        "recent_mentorship_requests": [
            {
                "id": req.id,
                "alumni_id": req.alumni_id,
                "topic": req.topic,
                "status": req.status,
                "created_at": req.created_at
            }
            for req in mentorship_result.scalars().all()
        ],
        "upcoming_sessions": [
            {
                "id": session.id,
                "alumni_id": session.alumni_id,
                "topic": session.topic,
                "scheduled_at": session.scheduled_at,
                "status": session.status
            }
            for session in sessions_result.scalars().all()
        ],
        "notifications": [
            {
                "id": note.id,
                "title": note.title,
                "body": note.body,
                "read": note.read_at is not None,
                "created_at": note.created_at
            }
            for note in notifications_result.scalars().all()
        ],
        "jobs": {
            "saved_count": saved_jobs_count.scalar(),
            "applied_count": applied_jobs_count.scalar()
        }
    }

@router.get("/alumni")
async def alumni_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "alumni":
        raise HTTPException(status_code=403, detail="Only alumni can access this dashboard")

    incoming_requests = await db.execute(
        select(MentorshipRequest)
        .where(MentorshipRequest.alumni_id == current_user.id)
        .order_by(MentorshipRequest.created_at.desc())
        .limit(5)
    )

    upcoming_sessions = await db.execute(
        select(MentorshipSession)
        .where(MentorshipSession.alumni_id == current_user.id)
        .order_by(MentorshipSession.scheduled_at)
        .limit(5)
    )

    unpaid_earnings = await db.execute(
        select(func.sum(AlumniEarning.amount))
        .where(
            AlumniEarning.alumni_id == current_user.id,
            AlumniEarning.status != "paid"
        )
    )

    completed_sessions_count = await db.execute(
        select(func.count(MentorshipSession.id))
        .where(
            MentorshipSession.alumni_id == current_user.id,
            MentorshipSession.status == "completed"
        )
    )

    return {
        "role": "alumni",
        "incoming_requests": [
            {
                "id": req.id,
                "student_id": req.student_id,
                "topic": req.topic,
                "message": req.message,
                "status": req.status,
                "created_at": req.created_at
            }
            for req in incoming_requests.scalars().all()
        ],
        "upcoming_sessions": [
            {
                "id": session.id,
                "student_id": session.student_id,
                "topic": session.topic,
                "scheduled_at": session.scheduled_at,
                "meeting_link": session.meeting_link,
                "status": session.status
            }
            for session in upcoming_sessions.scalars().all()
        ],
        "earnings": {
            "unpaid_amount": unpaid_earnings.scalar() or 0,
            "completed_sessions": completed_sessions_count.scalar()
        }
    }

@router.get("/admin")
async def admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can access this dashboard")

    users_count = await db.execute(select(func.count(User.id)))
    alumni_count = await db.execute(select(func.count(AlumniProfile.id)))
    communities_count = await db.execute(select(func.count(Community.id)))
    events_count = await db.execute(select(func.count(Event.id)))

    pending_docs = await db.execute(
        select(func.count(StudentDocument.id))
        .where(StudentDocument.verification_status == "pending")
    )

    pending_alumni = await db.execute(
        select(func.count(AlumniProfile.id))
        .where(AlumniProfile.verified_at == None)
    )

    active_subscriptions = await db.execute(
        select(func.count(Subscription.id))
        .where(Subscription.status.in_(["trial", "active"]))
    )

    return {
        "role": "admin",
        "stats": {
            "total_users": users_count.scalar(),
            "total_alumni": alumni_count.scalar(),
            "total_communities": communities_count.scalar(),
            "total_events": events_count.scalar(),
            "pending_student_documents": pending_docs.scalar(),
            "pending_alumni_verifications": pending_alumni.scalar(),
            "active_subscriptions": active_subscriptions.scalar()
        }
    }
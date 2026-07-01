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

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def check_admin(current_user: User):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/users")
async def get_all_users(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_admin(current_user)

    result = await db.execute(select(User))
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }
        for user in users
    ]


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_admin(current_user)

    if role not in ["student", "alumni", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role
    await db.commit()

    return {"message": "User role updated successfully"}


@router.post("/alumni/{alumni_id}/verify")
async def verify_alumni(
    alumni_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_admin(current_user)

    result = await db.execute(
        select(AlumniProfile).where(AlumniProfile.id == alumni_id)
    )
    alumni = result.scalar_one_or_none()

    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni not found")

    alumni.verified_at = datetime.utcnow()
    await db.commit()

    return {"message": "Alumni verified successfully"}


@router.post("/events/{event_id}/publish")
async def publish_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_admin(current_user)

    if event_id.isdigit():
        result = await db.execute(
            select(Event)
            .order_by(Event.starts_at.desc(), Event.id.desc())
            .offset(int(event_id) - 1)
            .limit(1)
        )
        action_event_id = event_id
    else:
        try:
            event_uuid = str(UUID(event_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid event id")

        result = await db.execute(select(Event).where(Event.id == event_uuid))
        action_event_id = event_uuid

    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.status = "published"

    if event.domain_id is not None:
        subscriptions_result = await db.execute(
            select(Subscription).where(
                Subscription.domain_id == event.domain_id,
                Subscription.status.in_(["trial", "active"])
            )
        )

        subscriptions = subscriptions_result.scalars().all()

        for subscription in subscriptions:
            notification = Notification(
                user_id=subscription.user_id,
                kind="event",
                title=f"New event: {event.title}",
                body="A new event has been published for your subscribed domain.",
                action_url=f"/events/{action_event_id}"
            )
            db.add(notification)

    await db.commit()

    return {
        "message": "Event published successfully and notifications sent",
        "event_id": event.id,
        "status": event.status
    }

@router.patch("/student-documents/{document_id}/verify")
async def verify_student_document(
    document_id: int,
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_admin(current_user)

    if status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be approved or rejected")

    result = await db.execute(
        select(StudentDocument).where(StudentDocument.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.verification_status = status
    document.verified_by = current_user.id
    document.verified_at = datetime.utcnow()

    student_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == document.user_id)
    )
    student_profile = student_result.scalar_one_or_none()

    if student_profile:
        student_profile.verification_status = status

    await db.commit()

    return {
        "message": f"Student document {status} successfully",
        "document_id": document.id,
        "status": document.verification_status
    }

@router.get("/alumni-earnings")
async def get_all_alumni_earnings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_admin(current_user)

    result = await db.execute(select(AlumniEarning).order_by(AlumniEarning.created_at.desc()))
    earnings = result.scalars().all()

    return [
        {
            "id": earning.id,
            "alumni_id": earning.alumni_id,
            "student_id": earning.student_id,
            "session_id": earning.session_id,
            "amount": earning.amount,
            "status": earning.status,
            "created_at": earning.created_at
        }
        for earning in earnings
    ]


@router.get("/alumni-earnings/{alumni_id}")
async def get_alumni_earnings(
    alumni_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_admin(current_user)

    result = await db.execute(
        select(AlumniEarning).where(AlumniEarning.alumni_id == alumni_id)
    )
    earnings = result.scalars().all()

    total_unpaid = sum(e.amount for e in earnings if e.status == "unpaid")

    return {
        "alumni_id": alumni_id,
        "total_unpaid": total_unpaid,
        "earnings": [
            {
                "id": earning.id,
                "student_id": earning.student_id,
                "session_id": earning.session_id,
                "amount": earning.amount,
                "status": earning.status,
                "created_at": earning.created_at
            }
            for earning in earnings
        ]
    }


@router.post("/alumni-payouts")
async def create_alumni_payout(
    data: AlumniPayoutCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_admin(current_user)

    result = await db.execute(
        select(AlumniEarning).where(
            AlumniEarning.alumni_id == data.alumni_id,
            AlumniEarning.status == "unpaid"
        )
    )
    unpaid_earnings = result.scalars().all()

    if not unpaid_earnings:
        raise HTTPException(status_code=400, detail="No unpaid earnings found")

    total_amount = sum(e.amount for e in unpaid_earnings)
    session_count = len(unpaid_earnings)

    payout = AlumniPayout(
        alumni_id=data.alumni_id,
        total_amount=total_amount,
        session_count=session_count,
        payout_status="pending",
        payment_method=data.payment_method,
        transaction_id=data.transaction_id
    )

    db.add(payout)
    await db.flush()

    for earning in unpaid_earnings:
        earning.status = "payout_created"

    await db.commit()
    await db.refresh(payout)

    return {
        "message": "Payout report created successfully",
        "payout_id": payout.id,
        "alumni_id": payout.alumni_id,
        "total_amount": payout.total_amount,
        "session_count": payout.session_count,
        "status": payout.payout_status
    }


@router.patch("/alumni-payouts/{payout_id}/mark-paid")
async def mark_payout_paid(
    payout_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    check_admin(current_user)

    result = await db.execute(
        select(AlumniPayout).where(AlumniPayout.id == payout_id)
    )
    payout = result.scalar_one_or_none()

    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")

    payout.payout_status = "paid"
    payout.paid_at = datetime.utcnow()

    earnings_result = await db.execute(
        select(AlumniEarning).where(
            AlumniEarning.alumni_id == payout.alumni_id,
            AlumniEarning.status == "payout_created"
        )
    )
    earnings = earnings_result.scalars().all()

    for earning in earnings:
        earning.status = "paid"

    await db.commit()

    return {
        "message": "Payout marked as paid",
        "payout_id": payout.id,
        "status": payout.payout_status
    }
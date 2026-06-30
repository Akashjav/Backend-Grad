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
from app.models.student_document import StudentDocument
from app.models.student import StudentProfile

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
            .order_by(Event.starts_at, Event.id)
            .offset(int(event_id) - 1)
            .limit(1)
        )
    else:
        try:
            event_uuid = str(UUID(event_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid event id")

        result = await db.execute(select(Event).where(Event.id == event_uuid))

    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.status = "published"
    await db.commit()

    return {"message": "Event published successfully"}

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
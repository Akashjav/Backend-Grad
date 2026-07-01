from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.V1.users import get_current_user
from app.models.user import User
from app.models.mentorship import MentorshipRequest, MentorshipSession
from app.schemas.mentorship import MentorshipRequestCreate, MentorshipSessionCreate

router = APIRouter(prefix="/api/mentorship", tags=["Mentorship"])

@router.post("/requests")
async def create_mentorship_request(
    data: MentorshipRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can send mentorship requests")

    alumni_result = await db.execute(
        select(User).where(
            User.id == data.alumni_id,
            User.role == "alumni"
        )
    )
    alumni = alumni_result.scalar_one_or_none()

    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni not found")

    mentorship_request = MentorshipRequest(
        student_id=current_user.id,
        alumni_id=data.alumni_id,
        topic=data.topic,
        message=data.message,
        status="pending"
    )

    db.add(mentorship_request)
    await db.commit()
    await db.refresh(mentorship_request)

    return {
        "message": "Mentorship request sent successfully",
        "request_id": mentorship_request.id,
        "status": mentorship_request.status
    }

@router.get("/requests/my")
async def get_my_mentorship_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MentorshipRequest)
        .where(MentorshipRequest.student_id == current_user.id)
        .order_by(MentorshipRequest.created_at.desc())
    )

    requests = result.scalars().all()

    return [
        {
            "id": req.id,
            "student_id": req.student_id,
            "alumni_id": req.alumni_id,
            "topic": req.topic,
            "message": req.message,
            "status": req.status,
            "created_at": req.created_at
        }
        for req in requests
    ]

@router.get("/requests/incoming")
async def get_incoming_mentorship_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "alumni":
        raise HTTPException(status_code=403, detail="Only alumni can view incoming requests")

    result = await db.execute(
        select(MentorshipRequest)
        .where(MentorshipRequest.alumni_id == current_user.id)
        .order_by(MentorshipRequest.created_at.desc())
    )

    requests = result.scalars().all()

    return [
        {
            "id": req.id,
            "student_id": req.student_id,
            "alumni_id": req.alumni_id,
            "topic": req.topic,
            "message": req.message,
            "status": req.status,
            "created_at": req.created_at
        }
        for req in requests
    ]

@router.patch("/requests/{request_id}/accept")
async def accept_mentorship_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "alumni":
        raise HTTPException(status_code=403, detail="Only alumni can accept requests")

    result = await db.execute(
        select(MentorshipRequest).where(
            MentorshipRequest.id == request_id,
            MentorshipRequest.alumni_id == current_user.id
        )
    )

    mentorship_request = result.scalar_one_or_none()

    if not mentorship_request:
        raise HTTPException(status_code=404, detail="Request not found")

    mentorship_request.status = "accepted"
    await db.commit()

    return {
        "message": "Mentorship request accepted",
        "request_id": mentorship_request.id,
        "status": mentorship_request.status
    }

@router.patch("/requests/{request_id}/reject")
async def reject_mentorship_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "alumni":
        raise HTTPException(status_code=403, detail="Only alumni can reject requests")

    result = await db.execute(
        select(MentorshipRequest).where(
            MentorshipRequest.id == request_id,
            MentorshipRequest.alumni_id == current_user.id
        )
    )

    mentorship_request = result.scalar_one_or_none()

    if not mentorship_request:
        raise HTTPException(status_code=404, detail="Request not found")

    mentorship_request.status = "rejected"
    await db.commit()

    return {
        "message": "Mentorship request rejected",
        "request_id": mentorship_request.id,
        "status": mentorship_request.status
    }

@router.post("/sessions")
async def create_mentorship_session(
    data: MentorshipSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "alumni":
        raise HTTPException(status_code=403, detail="Only alumni can schedule sessions")

    request_result = await db.execute(
        select(MentorshipRequest).where(
            MentorshipRequest.id == data.request_id,
            MentorshipRequest.alumni_id == current_user.id
        )
    )

    mentorship_request = request_result.scalar_one_or_none()

    if not mentorship_request:
        raise HTTPException(status_code=404, detail="Mentorship request not found")

    if mentorship_request.status != "accepted":
        raise HTTPException(
            status_code=400,
            detail="Only accepted requests can be scheduled"
        )

    session = MentorshipSession(
        request_id=mentorship_request.id,
        student_id=mentorship_request.student_id,
        alumni_id=mentorship_request.alumni_id,
        topic=mentorship_request.topic,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
        meeting_link=data.meeting_link,
        status="scheduled"
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return {
        "message": "Mentorship session scheduled successfully",
        "session_id": session.id,
        "status": session.status
    }

@router.get("/sessions/my")
async def get_my_mentorship_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == "student":
        result = await db.execute(
            select(MentorshipSession)
            .where(MentorshipSession.student_id == current_user.id)
            .order_by(MentorshipSession.scheduled_at.desc())
        )
    elif current_user.role == "alumni":
        result = await db.execute(
            select(MentorshipSession)
            .where(MentorshipSession.alumni_id == current_user.id)
            .order_by(MentorshipSession.scheduled_at.desc())
        )
    else:
        raise HTTPException(status_code=403, detail="Only students and alumni can view sessions")

    sessions = result.scalars().all()

    return [
        {
            "id": session.id,
            "request_id": session.request_id,
            "student_id": session.student_id,
            "alumni_id": session.alumni_id,
            "topic": session.topic,
            "scheduled_at": session.scheduled_at,
            "duration_minutes": session.duration_minutes,
            "meeting_link": session.meeting_link,
            "recording_url": session.recording_url,
            "status": session.status
        }
        for session in sessions
    ]

@router.patch("/sessions/{session_id}/complete")
async def complete_mentorship_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "alumni":
        raise HTTPException(status_code=403, detail="Only alumni can complete sessions")

    result = await db.execute(
        select(MentorshipSession).where(
            MentorshipSession.id == session_id,
            MentorshipSession.alumni_id == current_user.id
        )
    )

    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "completed"
    await db.commit()

    return {
        "message": "Mentorship session marked as completed",
        "session_id": session.id,
        "status": session.status
    }

@router.patch("/sessions/{session_id}/cancel")
async def cancel_mentorship_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MentorshipSession).where(MentorshipSession.id == session_id)
    )

    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_user.id not in [session.student_id, session.alumni_id]:
        raise HTTPException(status_code=403, detail="Not allowed to cancel this session")

    session.status = "cancelled"
    await db.commit()

    return {
        "message": "Mentorship session cancelled",
        "session_id": session.id,
        "status": session.status
    }

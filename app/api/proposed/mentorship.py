from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import Field
from app.api.proposed.deps import DB, Actor
from app.models.platform import DomainProfile, StudentSkill, SkillGap, AuditLog
from app.models.mentorship import MentorshipSession
from app.repositories.platform import get, rows, audit
from app.schemas.platform import Input
from app.services import mentorship_service as service
from app.api.proposed.organizations import directory

router = APIRouter(tags=["2.0 Mentor discovery and feedback"])


class Decision(Input):
    status: Literal["accepted", "rejected"]


class Review(Input):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1, max_length=2000)


@router.get("/mentors")
async def mentors(db: DB, user: Actor):
    result = []
    for role in ["alumni", "academician", "industry"]:
        result.extend(await directory(db, role))
    return result


@router.get("/mentors/recommended")
@router.get("/recommendations/mentors")
async def recommended(db: DB, user: Actor):
    profile = await get(db, DomainProfile, user.id)
    gaps = await rows(
        db, SkillGap, SkillGap.student_id == user.id, SkillGap.gap_score > 0
    )
    gap_ids = {g.skill_id for g in gaps}
    result = []
    for mentor in await mentors(db, user):
        if mentor["id"] == user.id:
            continue
        expertise = await rows(
            db,
            StudentSkill,
            StudentSkill.user_id == mentor["id"],
            StudentSkill.evidence_type != "self_declared",
        )
        matching_skills = [
            s.skill_id for s in expertise if s.skill_id in gap_ids and s.score >= 60
        ]
        interest_overlap = set(profile.interests) & set(mentor["profile"]["interests"])
        same_domain = profile.domain_id == mentor["profile"]["domain_id"]
        result.append(
            {
                **mentor,
                "score": min(
                    100,
                    60 * len(matching_skills) / max(1, len(gap_ids))
                    + 20 * bool(interest_overlap)
                    + 20 * same_domain,
                ),
                "explanation": {
                    "gap_skills_covered": matching_skills,
                    "shared_interests": sorted(interest_overlap),
                    "same_domain": same_domain,
                },
            }
        )
    return sorted(result, key=lambda x: -x["score"])[:20]


@router.get("/mentorship/requests")
async def requests(db: DB, user: Actor):
    if user.role == "student":
        return await service.get_my_mentorship_requests(user, db)
    return await service.get_incoming_mentorship_requests(user, db)


@router.patch("/mentorship/requests/{request_id}")
async def decide(request_id: int, data: Decision, db: DB, user: Actor):
    if data.status == "accepted":
        return await service.accept_mentorship_request(request_id, user, db)
    return await service.reject_mentorship_request(request_id, user, db)


@router.get("/mentorship/sessions")
async def sessions(db: DB, user: Actor):
    return await service.get_my_mentorship_sessions(user, db)


@router.post("/mentorship/sessions/{session_id}/feedback")
async def feedback(session_id: int, data: Review, db: DB, user: Actor):
    session = await get(db, MentorshipSession, session_id, lock=True)
    if session.student_id != user.id:
        raise HTTPException(403, "Only this session student may submit a review")
    if session.status != "completed":
        raise HTTPException(409, "Complete the session before reviewing")
    previous = await rows(
        db,
        AuditLog,
        AuditLog.actor_id == user.id,
        AuditLog.action == "mentorship.feedback",
        AuditLog.target == str(session_id),
    )
    if previous:
        raise HTTPException(409, "Review already submitted")
    audit(db, user, "mentorship.feedback", session_id, **data.model_dump())
    return {"session_id": session_id, **data.model_dump()}

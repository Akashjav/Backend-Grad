from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, or_
from app.api.proposed.deps import DB, Actor, roles
from app.models.platform import DomainProfile, Skill
from app.models.development import PracticalAssessment, PracticalSubmission
from app.repositories.platform import get, rows, add, public, audit
from app.schemas.development import PracticalInput, PracticalEvidence, PracticalReview
from app.services.competency_service import set_skill, readiness

router = APIRouter(tags=["2.0 Practical assessments"])


async def reviewer(db, user, domain_id):
    roles(user, "academician", "industry", "alumni", "admin", "super_admin")
    if user.role not in {"admin", "super_admin"}:
        profile = await get(db, DomainProfile, user.id)
        if not profile.verified or profile.domain_id != domain_id:
            raise HTTPException(403, "A verified reviewer in this domain is required")


@router.get("/practical-assessments")
async def listing(db: DB, user: Actor, domain_id: int | None = None):
    conditions = [PracticalAssessment.active.is_(True)]
    if domain_id:
        conditions.append(PracticalAssessment.domain_id == domain_id)
    return [public(a) for a in await rows(db, PracticalAssessment, *conditions)]


@router.post("/practical-assessments", status_code=201)
async def create(data: PracticalInput, db: DB, user: Actor):
    await reviewer(db, user, data.domain_id)
    for sid in data.rubric:
        skill = await get(db, Skill, sid)
        if skill.domain_id != data.domain_id:
            raise HTTPException(422, "Rubric skills must belong to the assessment domain")
    row = await add(db, PracticalAssessment, reviewer_id=user.id, **data.model_dump(mode="json"))
    audit(db, user, "practical.create", row.id)
    return public(row)


@router.delete("/practical-assessments/{practical_id}")
async def archive(practical_id: int, db: DB, user: Actor):
    row = await get(db, PracticalAssessment, practical_id)
    if user.id != row.reviewer_id and user.role not in {"admin", "super_admin"}:
        raise HTTPException(403, "Assessment owner required")
    row.active = False
    audit(db, user, "practical.archive", row.id)
    return public(row)


@router.post("/practical-assessments/{practical_id}/submit", status_code=201)
async def submit(practical_id: int, data: PracticalEvidence, db: DB, user: Actor):
    roles(user, "student")
    row = await get(db, PracticalAssessment, practical_id, lock=True)
    profile = await get(db, DomainProfile, user.id)
    if profile.domain_id != row.domain_id:
        raise HTTPException(403, "Assessment domain eligibility required")
    if not row.active:
        raise HTTPException(409, "Assessment is closed")
    pending = await rows(db, PracticalSubmission, PracticalSubmission.assessment_id == row.id,
        PracticalSubmission.student_id == user.id, PracticalSubmission.status == "submitted")
    if pending:
        raise HTTPException(409, "Wait for review before submitting another attempt")
    result = await add(db, PracticalSubmission, assessment_id=row.id, student_id=user.id,
                       **data.model_dump(mode="json"))
    audit(db, user, "practical.submit", result.id)
    return public(result)


@router.get("/practical-submissions")
async def submissions(db: DB, user: Actor):
    owned = select(PracticalAssessment.id).where(PracticalAssessment.reviewer_id == user.id)
    return [public(s) for s in await rows(db, PracticalSubmission,
        or_(PracticalSubmission.student_id == user.id, PracticalSubmission.assessment_id.in_(owned)))]


@router.post("/practical-submissions/{submission_id}/review")
async def review(submission_id: int, data: PracticalReview, db: DB, user: Actor):
    submission = await get(db, PracticalSubmission, submission_id, lock=True)
    assessment = await get(db, PracticalAssessment, submission.assessment_id)
    await reviewer(db, user, assessment.domain_id)
    if user.id != assessment.reviewer_id or user.id == submission.student_id:
        raise HTTPException(403, "Only the assigned independent reviewer can evaluate")
    if submission.status != "submitted":
        raise HTTPException(409, "Submission has already been reviewed")
    if {str(k) for k in data.scores} != set(assessment.rubric):
        raise HTTPException(422, "Evaluate every rubric skill and no additional skills")
    submission.scores = {str(k): v for k, v in data.scores.items()}
    submission.feedback, submission.status, submission.reviewed_at = data.feedback, "reviewed", datetime.utcnow()
    for sid, score in data.scores.items():
        await set_skill(db, submission.student_id, sid, score, "assessment_verified",
                        {"practical_submission_id": submission.id, "reviewer_id": user.id})
    await readiness(db, submission.student_id, persist=True)
    audit(db, user, "practical.review", submission.id)
    return public(submission)

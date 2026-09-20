from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.api.proposed.deps import DB, Actor, roles, administrator
from app.models.platform import Assessment, AssessmentAttempt, Skill
from app.models.subscription import Domain
from app.repositories.platform import get, add, public, rows, audit
from app.schemas.platform import AssessmentInput, Submission
from app.services.competency_service import set_skill, readiness

router = APIRouter(tags=["2.0 Assessments"])


def questions_public(questions):
    return [{k: v for k, v in q.items() if k != "answer"} for q in questions]


@router.post("/assessments", status_code=201)
async def create(data: AssessmentInput, db: DB, user: Actor):
    administrator(user)
    await get(db, Domain, data.domain_id)
    for q in data.questions:
        skill = await get(db, Skill, q.skill_id)
        if skill.domain_id != data.domain_id:
            raise HTTPException(
                422, "Question skill must belong to the assessment domain"
            )
    assessment = await add(db, Assessment, **data.model_dump())
    audit(db, user, "assessment.create", assessment.id)
    return public(assessment, {"questions"})


@router.get("/assessments")
async def listing(db: DB, user: Actor, domain_id: int | None = None):
    return [
        public(x, {"questions"})
        for x in await rows(
            db, Assessment, *([Assessment.domain_id == domain_id] if domain_id else [])
        )
    ]


@router.get("/assessments/{assessment_id}")
async def detail(assessment_id: int, db: DB, user: Actor):
    return public(await get(db, Assessment, assessment_id), {"questions"})


@router.post("/assessments/{assessment_id}/start")
@router.post("/assessments/{assessment_id}/reassess")
async def start(assessment_id: int, db: DB, user: Actor):
    roles(user, "student")
    assessment = await get(db, Assessment, assessment_id)
    attempt = await add(
        db,
        AssessmentAttempt,
        user_id=user.id,
        assessment_id=assessment.id,
        question_snapshot=assessment.questions,
        expires_at=datetime.utcnow() + timedelta(minutes=assessment.duration_minutes),
    )
    return {
        "attempt_id": attempt.id,
        "expires_at": attempt.expires_at,
        "questions": questions_public(attempt.question_snapshot),
    }


@router.post("/assessments/{assessment_id}/submit")
async def submit(assessment_id: int, data: Submission, db: DB, user: Actor):
    roles(user, "student")
    attempt = await get(db, AssessmentAttempt, data.attempt_id, lock=True)
    if attempt.user_id != user.id or attempt.assessment_id != assessment_id:
        raise HTTPException(404, "Attempt not found")
    if attempt.submitted_at or attempt.expires_at < datetime.utcnow():
        raise HTTPException(409, "Attempt already submitted or expired")
    known = {q["id"]: q for q in attempt.question_snapshot}
    if any(
        k not in known or v < 0 or v >= len(known[k]["options"])
        for k, v in data.answers.items()
    ):
        raise HTTPException(422, "Unknown question or invalid answer")
    earned, totals = {}, {}
    for question in attempt.question_snapshot:
        sid, weight = question["skill_id"], question["weight"]
        totals[sid] = totals.get(sid, 0) + weight
        earned[sid] = earned.get(sid, 0) + (
            weight if data.answers.get(question["id"]) == question["answer"] else 0
        )
    scores = {str(k): round(100 * earned[k] / total, 2) for k, total in totals.items()}
    attempt.answers, attempt.scores, attempt.submitted_at = (
        data.answers,
        scores,
        datetime.utcnow(),
    )
    for sid, score in scores.items():
        await set_skill(
            db,
            user.id,
            int(sid),
            score,
            "assessment_verified",
            {"attempt_id": attempt.id, "algorithm": "weighted-mcq-v1"},
        )
    result = await readiness(db, user.id, persist=True)
    return {"attempt_id": attempt.id, "scores": scores, "readiness": result}


@router.get("/assessments/{assessment_id}/result")
async def result(assessment_id: int, db: DB, user: Actor):
    attempt = (
        await db.scalars(
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.user_id == user.id,
                AssessmentAttempt.assessment_id == assessment_id,
                AssessmentAttempt.submitted_at.is_not(None),
            )
            .order_by(AssessmentAttempt.id.desc())
        )
    ).first()
    if not attempt:
        raise HTTPException(404, "No submitted attempt")
    return public(attempt, {"question_snapshot"})


@router.get("/students/me/assessment-history")
async def history(db: DB, user: Actor):
    return [
        public(x, {"question_snapshot"})
        for x in await rows(db, AssessmentAttempt, AssessmentAttempt.user_id == user.id)
    ]


@router.get("/skills/{skill_id}/assessment-framework")
async def framework(skill_id: int, db: DB, user: Actor):
    skill = await get(db, Skill, skill_id)
    assessments = await rows(db, Assessment, Assessment.domain_id == skill.domain_id)
    return {
        "skill": public(skill),
        "assessments": [
            public(x, {"questions"})
            for x in assessments
            if any(q["skill_id"] == skill_id for q in x.questions)
        ],
    }

from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.api.proposed.deps import DB, Actor, administrator, owner, roles
from app.models.platform import (
    LearningResource,
    LearningProgress,
    Skill,
    SkillGap,
    Assessment,
)
from app.repositories.platform import get, add, rows, public, audit
from app.schemas.platform import LearningInput

router = APIRouter(tags=["2.0 Learning"])


@router.get("/students/me/learning-roadmap")
async def learning_roadmap(opportunity_id: int, db: DB, user: Actor):
    roles(user, "student")
    from app.services.learning_roadmap_service import roadmap
    return await roadmap(db, user, opportunity_id)


@router.get("/learning/resources")
async def resources(db: DB, user: Actor, skill_id: int | None = None):
    return [
        public(x)
        for x in await rows(
            db,
            LearningResource,
            *([LearningResource.skill_id == skill_id] if skill_id else []),
        )
    ]


@router.post("/learning/resources", status_code=201)
async def create(data: LearningInput, db: DB, user: Actor):
    administrator(user)
    await get(db, Skill, data.skill_id)
    row = await add(db, LearningResource, **data.model_dump(mode="json"))
    audit(db, user, "learning.resource.create", row.id)
    return public(row)


@router.get("/learning/resources/{resource_id}")
async def resource(resource_id: int, db: DB, user: Actor):
    return public(await get(db, LearningResource, resource_id))


@router.get("/students/me/learning-recommendations")
async def recommendations(db: DB, user: Actor):
    gaps = await rows(
        db, SkillGap, SkillGap.student_id == user.id, SkillGap.gap_score > 0
    )
    result = []
    for gap in sorted(gaps, key=lambda g: -g.gap_score):
        courses = await rows(
            db,
            LearningResource,
            LearningResource.skill_id == gap.skill_id,
            LearningResource.target_level >= gap.required_level,
        )
        result.append(
            {
                "gap": public(gap),
                "resources": [public(x) for x in courses],
                "next_step": "Complete learning, then reassess; completion alone does not validate a skill.",
            }
        )
    return result


@router.post("/learning/{resource_id}/start")
async def start(resource_id: int, db: DB, user: Actor):
    await get(db, LearningResource, resource_id)
    row = (
        await db.scalars(
            select(LearningProgress).where(
                LearningProgress.user_id == user.id,
                LearningProgress.resource_id == resource_id,
            )
        )
    ).first()
    if not row:
        row = await add(db, LearningProgress, user_id=user.id, resource_id=resource_id)
    return public(row)


@router.post("/learning/{resource_id}/complete")
async def complete(resource_id: int, db: DB, user: Actor):
    row = (
        await db.scalars(
            select(LearningProgress).where(
                LearningProgress.user_id == user.id,
                LearningProgress.resource_id == resource_id,
            )
        )
    ).first()
    if not row:
        raise HTTPException(409, "Start this resource first")
    row.status, row.completed_at = "completed", datetime.utcnow()
    return {**public(row), "reassessment_required": True}


@router.get("/students/me/learning-history")
async def history(db: DB, user: Actor):
    return [
        public(x)
        for x in await rows(db, LearningProgress, LearningProgress.user_id == user.id)
    ]


@router.post("/students/me/skill-gaps/{gap_id}/reassess")
async def reassess(gap_id: int, db: DB, user: Actor):
    gap = await get(db, SkillGap, gap_id)
    owner(user, gap.student_id)
    skill = await get(db, Skill, gap.skill_id)
    assessments = await rows(db, Assessment, Assessment.domain_id == skill.domain_id)
    return {
        "gap_id": gap.id,
        "assessments": [
            public(x, {"questions"})
            for x in assessments
            if any(q["skill_id"] == skill.id for q in x.questions)
        ],
    }

from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from app.models.platform import (
    StudentSkill,
    Skill,
    DomainProfile,
    DomainPolicy,
    Competency,
    ReadinessSnapshot,
)
from app.repositories.platform import get, add, rows


async def set_skill(db, user_id, skill_id, score, evidence_type, evidence):
    await get(db, Skill, skill_id)
    row = (
        await db.scalars(
            select(StudentSkill)
            .where(StudentSkill.user_id == user_id, StudentSkill.skill_id == skill_id)
            .with_for_update()
        )
    ).first()
    if (
        row
        and evidence_type == "self_declared"
        and row.evidence_type != "self_declared"
    ):
        raise HTTPException(
            409,
            "Validated skills can only be changed by assessment or authorized feedback",
        )
    if not row:
        row = await add(db, StudentSkill, user_id=user_id, skill_id=skill_id)
    row.score, row.evidence_type, row.evidence = score, evidence_type, evidence
    row.updated_at = datetime.utcnow()
    await db.flush()
    return row


async def competency_scores(db, user_id):
    profile = await get(db, DomainProfile, user_id)
    skills = await rows(db, StudentSkill, StudentSkill.user_id == user_id, limit=10000)
    scores = {x.skill_id: x.score for x in skills if x.evidence_type != "self_declared"}
    output = []
    for c in await rows(
        db, Competency, Competency.domain_id == profile.domain_id, limit=10000
    ):
        total = sum(c.skill_weights.values())
        score = (
            sum(scores.get(int(k), 0) * w for k, w in c.skill_weights.items()) / total
            if total
            else 0
        )
        output.append(
            {
                "id": c.id,
                "name": c.name,
                "score": round(score, 2),
                "skill_weights": c.skill_weights,
            }
        )
    return output


async def readiness(db, user_id, persist=False):
    profile = await get(db, DomainProfile, user_id)
    policy = (
        await db.get(DomainPolicy, profile.domain_id) if profile.domain_id else None
    )
    domain_skills = await rows(
        db, Skill, Skill.domain_id == profile.domain_id, limit=10000
    )
    student_skills = await rows(
        db, StudentSkill, StudentSkill.user_id == user_id, limit=10000
    )
    scores = {
        x.skill_id: x.score
        for x in student_skills
        if x.evidence_type != "self_declared"
    }
    categories = {}
    for skill in domain_skills:
        categories.setdefault(skill.category, []).append(scores.get(skill.id, 0))
    components = {
        key: round(sum(values) / len(values), 2) for key, values in categories.items()
    }
    weights = (
        policy.readiness_weights
        if policy and policy.readiness_weights
        else {key: 1 for key in categories}
    )
    denominator = sum(weights.values())
    score = (
        round(
            sum(components.get(key, 0) * weight for key, weight in weights.items())
            / denominator,
            2,
        )
        if denominator
        else 0
    )
    result = {
        "score": score,
        "components": components,
        "weights": weights,
        "evidence_policy": "assessment and authorized feedback only; missing competencies score zero",
        "model": "domain-category-readiness-v1",
    }
    if persist:
        await add(
            db, ReadinessSnapshot, user_id=user_id, score=score, components=result
        )
    return result

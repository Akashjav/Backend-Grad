from sqlalchemy import select, func
from fastapi import HTTPException
from app.models.user import User
from app.models.platform import (
    DomainProfile,
    StudentSkill,
    Opportunity,
    Requirement,
    Skill,
    Application,
)
from app.repositories.platform import get, rows
from app.services.competency_service import readiness


async def institution_scope(db, user):
    if user.role != "institution_admin":
        raise HTTPException(403, "Institution administrator required")
    profile = await get(db, DomainProfile, user.id)
    if not profile.institution_id:
        raise HTTPException(403, "No institution assigned")
    return profile.institution_id


async def analytics(db, institution_id):
    students = list(
        (
            await db.scalars(
                select(DomainProfile)
                .join(User, User.id == DomainProfile.user_id)
                .where(
                    DomainProfile.institution_id == institution_id,
                    User.role == "student",
                    User.is_active.is_(True),
                )
            )
        ).all()
    )
    ids = [s.user_id for s in students]
    domains = {s.domain_id for s in students}
    # Only requirements published by organizations contribute to demand.
    demand = (
        await db.execute(
            select(
                Requirement.skill_id,
                func.count(Requirement.id),
                func.avg(Requirement.level),
            )
            .join(Opportunity, Opportunity.id == Requirement.opportunity_id)
            .where(
                Opportunity.status == "published", Opportunity.domain_id.in_(domains)
            )
            .group_by(Requirement.skill_id)
        )
    ).all()
    student_skills = await rows(
        db,
        StudentSkill,
        StudentSkill.user_id.in_(ids),
        StudentSkill.evidence_type != "self_declared",
        limit=100000,
    )
    records = []
    for skill_id, count, level in demand:
        skill = await get(db, Skill, skill_id)
        eligible_ids = {s.user_id for s in students if s.domain_id == skill.domain_id}
        avg = (
            sum(
                s.score
                for s in student_skills
                if s.skill_id == skill_id and s.user_id in eligible_ids
            )
            / len(eligible_ids)
            if eligible_ids
            else 0
        )
        records.append(
            {
                "skill_id": skill_id,
                "skill": skill.name,
                "opportunities_requiring_skill": count,
                "required_level": round(float(level), 2),
                "student_average": round(avg, 2),
                "gap": round(max(level - avg, 0), 2),
                "cohort_size": len(eligible_ids),
            }
        )
    readiness_rows = [{"student_id": sid, **(await readiness(db, sid))} for sid in ids]
    applications = await rows(
        db, Application, Application.student_id.in_(ids), limit=100000
    )
    statuses = {}
    for application in applications:
        statuses[application.status] = statuses.get(application.status, 0) + 1
    return {
        "institution_id": institution_id,
        "student_count": len(ids),
        "skill_demand": records,
        "skill_gaps": sorted(records, key=lambda x: -x["gap"]),
        "readiness": readiness_rows,
        "application_outcomes": statuses,
        "training_priorities": [
            r["skill"]
            for r in sorted(records, key=lambda x: -x["gap"])
            if r["gap"] >= 15
        ],
        "method": "Published requirements versus validated skills; missing skill evidence is zero within each domain cohort.",
    }

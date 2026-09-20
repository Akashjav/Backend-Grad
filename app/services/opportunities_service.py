from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from app.api.proposed.deps import roles, owner
from app.models.platform import (
    Opportunity,
    Requirement,
    Application,
    DomainProfile,
    Feedback,
    ProfileItem,
)
from app.repositories.platform import get, add, audit, public
from app.services.competency_service import set_skill, readiness
from app.services.identity_service import validate_domain
from app.models.user import User

PUBLISHERS = ("industry", "academician", "alumni", "admin", "super_admin")
TRANSITIONS = {
    "applied": {"shortlisted", "rejected", "withdrawn"},
    "shortlisted": {"interview", "selected", "rejected", "withdrawn"},
    "interview": {"selected", "rejected", "withdrawn"},
    "selected": {"started", "withdrawn"},
    "started": {"completed", "withdrawn"},
}


async def visible(db, opportunity_id, user):
    row = await get(db, Opportunity, opportunity_id)
    if row.status != "published":
        owner(user, row.owner_id)
    return row


async def create(db, user, data):
    roles(user, *PUBLISHERS)
    await validate_domain(db, data.domain_id, data.discipline_id)
    row = await add(db, Opportunity, owner_id=user.id, **data.model_dump())
    audit(db, user, "opportunity.create", row.id)
    return row


async def apply(db, user, opportunity_id):
    roles(user, "student")
    opportunity = await get(db, Opportunity, opportunity_id, lock=True)
    if opportunity.status != "published" or (
        opportunity.deadline and opportunity.deadline < datetime.utcnow()
    ):
        raise HTTPException(409, "Opportunity is not accepting applications")
    profile = await get(db, DomainProfile, user.id)
    if not opportunity.cross_domain and (
        profile.domain_id != opportunity.domain_id
        or (
            opportunity.discipline_id
            and profile.discipline_id != opportunity.discipline_id
        )
    ):
        raise HTTPException(403, "Domain or discipline eligibility not satisfied")
    previous = (
        await db.scalars(
            select(Application).where(
                Application.student_id == user.id,
                Application.opportunity_id == opportunity_id,
            )
        )
    ).first()
    if previous:
        raise HTTPException(409, "Already applied")
    return await add(db, Application, student_id=user.id, opportunity_id=opportunity_id)


async def transition(db, user, application_id, data):
    application = await get(db, Application, application_id, lock=True)
    opportunity = await get(db, Opportunity, application.opportunity_id)
    if data.status == "withdrawn":
        owner(user, application.student_id)
    else:
        owner(user, opportunity.owner_id)
    if data.status not in TRANSITIONS.get(application.status, set()):
        raise HTTPException(
            409, f"Cannot transition {application.status} to {data.status}"
        )
    if data.mentor_id:
        owner(user, opportunity.owner_id)
        mentor = await get(db, User, data.mentor_id)
        if not mentor.is_active or mentor.role not in PUBLISHERS:
            raise HTTPException(
                422, "Mentor must be an active alumni, academician or industry user"
            )
        application.mentor_id = mentor.id
    application.status = data.status
    if data.status == "completed":
        application.progress = 100
        application.certificate = f"GRAD-{application.id}-{application.student_id[:8]}"
    audit(db, user, "application.status", application.id, status=data.status)
    return application


async def feedback(db, user, application_id, data):
    application = await get(db, Application, application_id, lock=True)
    opportunity = await get(db, Opportunity, application.opportunity_id)
    if user.id not in {opportunity.owner_id, application.mentor_id}:
        raise HTTPException(403, "Only the employer or assigned mentor may evaluate")
    if application.status != "completed":
        raise HTTPException(409, "Complete the engagement before evaluation")
    if (
        await db.scalars(
            select(Feedback).where(
                Feedback.reviewer_id == user.id,
                Feedback.application_id == application_id,
            )
        )
    ).first():
        raise HTTPException(409, "Feedback already submitted")
    required = set(
        (
            await db.scalars(
                select(Requirement.skill_id).where(
                    Requirement.opportunity_id == opportunity.id
                )
            )
        ).all()
    )
    if not set(data.scores).issubset(required):
        raise HTTPException(422, "Only skills in this opportunity may be evaluated")
    row = await add(
        db,
        Feedback,
        application_id=application.id,
        reviewer_id=user.id,
        **data.model_dump(mode="json"),
    )
    for skill_id, score in data.scores.items():
        await set_skill(
            db,
            application.student_id,
            skill_id,
            score,
            "industry_verified",
            {"feedback_id": row.id, "reviewer_id": user.id},
        )
    await add(
        db,
        ProfileItem,
        user_id=application.student_id,
        kind="portfolio",
        title=opportunity.title,
        description=f"Completed {opportunity.kind}; certificate {application.certificate}",
        skill_ids=list(data.scores),
        verified=True,
    )
    await readiness(db, application.student_id, persist=True)
    audit(db, user, "competency.feedback", application.id)
    return public(row)

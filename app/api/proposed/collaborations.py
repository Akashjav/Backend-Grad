from fastapi import APIRouter, HTTPException
from sqlalchemy import select, or_
from app.api.proposed.deps import DB, Actor, owner
from app.models.platform import (
    Collaboration,
    CollaborationMember,
    Opportunity,
    Requirement,
    StudentSkill,
    Application,
)
from app.models.user import User
from app.repositories.platform import get, rows, add, public, audit
from app.schemas.platform import CollaborationInput, Invite, CollaborationPatch
from app.schemas.platform import FeedbackInput

router = APIRouter(prefix="/collaborations", tags=["2.0 Collaboration"])


async def membership(db, collaboration_id, user_id):
    return (
        await db.scalars(
            select(CollaborationMember).where(
                CollaborationMember.collaboration_id == collaboration_id,
                CollaborationMember.user_id == user_id,
            )
        )
    ).first()


async def access(db, collaboration_id, user):
    row = await get(db, Collaboration, collaboration_id)
    member = await membership(db, row.id, user.id)
    if row.owner_id != user.id and (not member or member.status != "active"):
        raise HTTPException(403, "Active collaboration membership required")
    return row


@router.get("")
async def listing(db: DB, user: Actor):
    memberships = select(CollaborationMember.collaboration_id).where(
        CollaborationMember.user_id == user.id
    )
    return [
        public(x)
        for x in await rows(
            db,
            Collaboration,
            or_(Collaboration.owner_id == user.id, Collaboration.id.in_(memberships)),
        )
    ]


@router.post("", status_code=201)
async def create(data: CollaborationInput, db: DB, user: Actor):
    opportunity = await get(db, Opportunity, data.opportunity_id)
    owner(user, opportunity.owner_id)
    if opportunity.kind not in {"project", "research", "consultancy", "fdp"}:
        raise HTTPException(
            422,
            "Collaboration requires a project, research, consultancy or FDP opportunity",
        )
    row = await add(db, Collaboration, owner_id=user.id, **data.model_dump())
    audit(db, user, "collaboration.create", row.id)
    return public(row)


@router.get("/{collaboration_id}")
async def detail(collaboration_id: int, db: DB, user: Actor):
    return public(await access(db, collaboration_id, user))


@router.patch("/{collaboration_id}")
async def patch(collaboration_id: int, data: CollaborationPatch, db: DB, user: Actor):
    row = await get(db, Collaboration, collaboration_id)
    owner(user, row.owner_id)
    from app.models.development import ProjectMilestone
    milestones = await rows(db, ProjectMilestone, ProjectMilestone.collaboration_id == row.id, limit=10000)
    if milestones:
        calculated = round(100 * sum(m.status == "accepted" for m in milestones) / len(milestones))
        if data.progress != calculated or (data.status == "completed" and calculated != 100):
            raise HTTPException(409, "Progress and completion must match accepted milestones")
    row.progress, row.status = data.progress, data.status
    if data.status == "completed":
        row.progress = 100
    audit(db, user, "collaboration.progress", row.id, progress=row.progress)
    return public(row)


@router.post("/{collaboration_id}/invite")
@router.post("/{collaboration_id}/members")
async def invite(collaboration_id: int, data: Invite, db: DB, user: Actor):
    row = await get(db, Collaboration, collaboration_id)
    owner(user, row.owner_id)
    target = await get(db, User, data.user_id)
    if not target.is_active or target.id == row.owner_id:
        raise HTTPException(422, "Invalid invitee")
    if data.role == "mentor" and target.role not in {
        "alumni",
        "academician",
        "industry",
    }:
        raise HTTPException(422, "Invalid mentor role")
    existing = await membership(db, collaboration_id, data.user_id)
    if existing:
        raise HTTPException(409, "Member already invited")
    return public(
        await add(
            db,
            CollaborationMember,
            collaboration_id=collaboration_id,
            **data.model_dump(),
        )
    )


@router.post("/{collaboration_id}/join")
async def join(collaboration_id: int, db: DB, user: Actor):
    row = await get(db, Collaboration, collaboration_id)
    member = await membership(db, row.id, user.id)
    if not member:
        raise HTTPException(403, "An invitation is required")
    member.status = "active"
    return public(member)


@router.delete("/{collaboration_id}/members/{user_id}")
async def remove(collaboration_id: int, user_id: str, db: DB, user: Actor):
    row = await get(db, Collaboration, collaboration_id)
    if user.id != user_id:
        owner(user, row.owner_id)
    member = await membership(db, row.id, user_id)
    if not member:
        raise HTTPException(404, "Member not found")
    await db.delete(member)
    return {"deleted": True}


@router.get("/{collaboration_id}/members")
async def members(collaboration_id: int, db: DB, user: Actor):
    await access(db, collaboration_id, user)
    return [
        public(x)
        for x in await rows(
            db,
            CollaborationMember,
            CollaborationMember.collaboration_id == collaboration_id,
        )
    ]


@router.get("/{collaboration_id}/skills")
async def coverage(collaboration_id: int, db: DB, user: Actor):
    row = await access(db, collaboration_id, user)
    members = await rows(
        db,
        CollaborationMember,
        CollaborationMember.collaboration_id == row.id,
        CollaborationMember.status == "active",
    )
    skills = await rows(
        db,
        StudentSkill,
        StudentSkill.user_id.in_([m.user_id for m in members]),
        StudentSkill.evidence_type != "self_declared",
        limit=10000,
    )
    requirements = await rows(
        db, Requirement, Requirement.opportunity_id == row.opportunity_id
    )
    return [
        {
            "skill_id": r.skill_id,
            "required": r.level,
            "team_level": max(
                [s.score for s in skills if s.skill_id == r.skill_id], default=0
            ),
            "contributors": [
                s.user_id
                for s in skills
                if s.skill_id == r.skill_id and s.score >= r.level
            ],
        }
        for r in requirements
    ]


@router.get("/{collaboration_id}/progress")
async def progress(collaboration_id: int, db: DB, user: Actor):
    row = await access(db, collaboration_id, user)
    return {
        "progress": row.progress,
        "status": row.status,
        "skills": await coverage(row.id, db, user),
    }


@router.post("/{collaboration_id}/feedback")
async def feedback(
    collaboration_id: int, application_id: int, data: FeedbackInput, db: DB, user: Actor
):
    row = await access(db, collaboration_id, user)
    application = await get(db, Application, application_id)
    if application.opportunity_id != row.opportunity_id:
        raise HTTPException(422, "Application does not belong to this collaboration")
    from app.services.opportunities_service import feedback as evaluate

    return await evaluate(db, user, application_id, data)

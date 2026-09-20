from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import or_
from app.api.proposed.deps import DB, Actor, owner, administrator
from app.models.platform import Opportunity, Requirement, Skill, Application
from app.repositories.platform import get, add, rows, public, audit
from app.schemas.platform import (
    OpportunityInput,
    OpportunityPatch,
    RequirementInput,
    ApplicationUpdate,
    FeedbackInput,
    ProgressInput,
)
from app.services import opportunities_service as service

router = APIRouter(tags=["2.0 Opportunities and applications"])


@router.get("/opportunities")
async def listing(
    db: DB,
    user: Actor,
    domain_id: int | None = None,
    kind: str | None = None,
    search: str = "",
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    conditions = [Opportunity.title.ilike(f"%{search}%")]
    if user.role not in {"admin", "super_admin"}:
        conditions.append(or_(Opportunity.status == "published", Opportunity.owner_id == user.id))
    if domain_id:
        conditions.append(
            or_(Opportunity.domain_id == domain_id, Opportunity.cross_domain.is_(True))
        )
    if kind:
        conditions.append(Opportunity.kind == kind)
    return [
        public(x)
        for x in await rows(db, Opportunity, *conditions, limit=limit, offset=offset)
    ]


@router.post("/opportunities", status_code=201)
async def create(data: OpportunityInput, db: DB, user: Actor):
    return public(await service.create(db, user, data))


@router.get("/opportunities/{opportunity_id}")
async def detail(opportunity_id: int, db: DB, user: Actor):
    return public(await service.visible(db, opportunity_id, user))


@router.patch("/opportunities/{opportunity_id}")
async def patch(opportunity_id: int, data: OpportunityPatch, db: DB, user: Actor):
    row = await get(db, Opportunity, opportunity_id)
    owner(user, row.owner_id)
    for key, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(row, key, value)
    row.status, row.approved = "draft", False
    audit(db, user, "opportunity.edit", row.id)
    return public(row)


@router.delete("/opportunities/{opportunity_id}")
async def archive(opportunity_id: int, db: DB, user: Actor):
    row = await get(db, Opportunity, opportunity_id)
    owner(user, row.owner_id)
    row.status = "archived"
    audit(db, user, "opportunity.archive", row.id)
    return {"status": row.status}


@router.post("/opportunities/{opportunity_id}/publish")
async def publish(opportunity_id: int, db: DB, user: Actor):
    row = await get(db, Opportunity, opportunity_id)
    owner(user, row.owner_id)
    if not row.approved:
        raise HTTPException(409, "Administrator approval is required")
    if row.deadline and row.deadline < datetime.utcnow():
        raise HTTPException(409, "Deadline has passed")
    if not await rows(db, Requirement, Requirement.opportunity_id == row.id):
        raise HTTPException(409, "Add requirements before publishing")
    row.status = "published"
    audit(db, user, "opportunity.publish", row.id)
    return public(row)


@router.get("/opportunities/{opportunity_id}/requirements")
async def requirements(opportunity_id: int, db: DB, user: Actor):
    await service.visible(db, opportunity_id, user)
    return [
        public(x)
        for x in await rows(
            db, Requirement, Requirement.opportunity_id == opportunity_id
        )
    ]


async def validate_requirement(db, user, opportunity_id, data):
    opportunity = await get(db, Opportunity, opportunity_id)
    owner(user, opportunity.owner_id)
    skill = await get(db, Skill, data.skill_id)
    if not opportunity.cross_domain and skill.domain_id != opportunity.domain_id:
        raise HTTPException(
            422,
            "Use a skill from the opportunity domain or enable cross-domain matching",
        )
    opportunity.status, opportunity.approved = "draft", False
    return opportunity


@router.post("/opportunities/{opportunity_id}/requirements", status_code=201)
async def add_requirement(
    opportunity_id: int, data: RequirementInput, db: DB, user: Actor
):
    await validate_requirement(db, user, opportunity_id, data)
    return public(
        await add(db, Requirement, opportunity_id=opportunity_id, **data.model_dump())
    )


@router.patch("/opportunities/{opportunity_id}/requirements/{requirement_id}")
async def patch_requirement(
    opportunity_id: int,
    requirement_id: int,
    data: RequirementInput,
    db: DB,
    user: Actor,
):
    await validate_requirement(db, user, opportunity_id, data)
    row = await get(db, Requirement, requirement_id)
    if row.opportunity_id != opportunity_id:
        raise HTTPException(404, "Requirement not found")
    for k, v in data.model_dump().items():
        setattr(row, k, v)
    return public(row)


@router.post("/opportunities/{opportunity_id}/apply", status_code=201)
async def apply(opportunity_id: int, db: DB, user: Actor):
    return public(await service.apply(db, user, opportunity_id))


@router.get("/opportunities/{opportunity_id}/applications")
async def applications(opportunity_id: int, db: DB, user: Actor):
    row = await get(db, Opportunity, opportunity_id)
    owner(user, row.owner_id)
    return [
        public(x)
        for x in await rows(db, Application, Application.opportunity_id == row.id)
    ]


@router.get("/students/me/applications")
async def my_applications(db: DB, user: Actor):
    return [
        public(x)
        for x in await rows(db, Application, Application.student_id == user.id)
    ]


@router.get("/applications/{application_id}")
async def application(application_id: int, db: DB, user: Actor):
    row = await get(db, Application, application_id)
    opp = await get(db, Opportunity, row.opportunity_id)
    if user.id not in {row.student_id, opp.owner_id, row.mentor_id}:
        administrator(user)
    return public(row)


@router.patch("/applications/{application_id}/status")
async def status(application_id: int, data: ApplicationUpdate, db: DB, user: Actor):
    return public(await service.transition(db, user, application_id, data))


@router.patch("/applications/{application_id}/progress")
async def progress(application_id: int, data: ProgressInput, db: DB, user: Actor):
    row = await get(db, Application, application_id)
    opp = await get(db, Opportunity, row.opportunity_id)
    if user.id not in {row.student_id, row.mentor_id, opp.owner_id}:
        raise HTTPException(403, "Not part of this engagement")
    if row.status != "started":
        raise HTTPException(409, "Engagement must be started")
    row.progress = data.progress
    return public(row)


@router.post("/applications/{application_id}/feedback", status_code=201)
async def feedback(application_id: int, data: FeedbackInput, db: DB, user: Actor):
    return await service.feedback(db, user, application_id, data)

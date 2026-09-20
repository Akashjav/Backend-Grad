from fastapi import APIRouter
from app.api.proposed.deps import DB, Actor, administrator
from app.models.platform import Institution, DomainProfile, Discipline
from app.models.platform import Collaboration, CollaborationMember
from sqlalchemy import select
from app.models.user import User
from app.repositories.platform import get, rows, add, public, audit
from app.schemas.platform import DomainInput
from app.services.analytics_service import institution_scope, analytics

router = APIRouter(tags=["2.0 Institutions and analytics"])


@router.get("/institutions")
async def listing(db: DB, user: Actor):
    return [public(x) for x in await rows(db, Institution)]


@router.post("/institutions", status_code=201)
async def create(data: DomainInput, db: DB, user: Actor):
    administrator(user)
    row = await add(db, Institution, **data.model_dump())
    audit(db, user, "institution.create", row.id)
    return public(row)


@router.get("/institutions/me/profile")
async def own(db: DB, user: Actor):
    return public(await get(db, Institution, await institution_scope(db, user)))


@router.patch("/institutions/me/profile")
async def patch(data: DomainInput, db: DB, user: Actor):
    row = await get(db, Institution, await institution_scope(db, user))
    row.name, row.description = data.name, data.description
    audit(db, user, "institution.update", row.id)
    return public(row)


@router.get("/institutions/me/students")
async def students(db: DB, user: Actor):
    institution_id = await institution_scope(db, user)
    profiles = await rows(
        db, DomainProfile, DomainProfile.institution_id == institution_id
    )
    output = []
    for p in profiles:
        target = await get(db, User, p.user_id)
        if target.role == "student" and target.is_active:
            output.append(public(p))
    return output


@router.get("/institutions/me/departments")
async def departments(db: DB, user: Actor):
    profiles = await students(db, user)
    ids = {p["discipline_id"] for p in profiles if p["discipline_id"]}
    return [public(x) for x in await rows(db, Discipline, Discipline.id.in_(ids))]


def analytics_route(path, key=None):
    async def endpoint(db: DB, user: Actor):
        data = await analytics(db, await institution_scope(db, user))
        return data[key] if key else data

    router.add_api_route(
        f"/institutions/me/{path}",
        endpoint,
        methods=["GET"],
        name=f"institution_{path}",
    )


for path, key in [
    ("analytics", None),
    ("reports", None),
    ("skill-demand", "skill_demand"),
    ("skill-gaps", "skill_gaps"),
    ("readiness", "readiness"),
    ("placement", "application_outcomes"),
]:
    analytics_route(path, key)


@router.get("/institutions/{institution_id}")
async def detail(institution_id: int, db: DB, user: Actor):
    return public(await get(db, Institution, institution_id))


@router.get("/institutions/me/industry-collaboration")
async def industry_collaborations(db: DB, user: Actor):
    institution_id = await institution_scope(db, user)
    members = select(DomainProfile.user_id).where(
        DomainProfile.institution_id == institution_id
    )
    collaborations = select(CollaborationMember.collaboration_id).where(
        CollaborationMember.user_id.in_(members), CollaborationMember.status == "active"
    )
    return [
        public(x)
        for x in await rows(db, Collaboration, Collaboration.id.in_(collaborations))
    ]

from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, update, func
from app.api.proposed.deps import DB, Actor, administrator
from app.models.user import User
from app.models.platform import (
    DomainProfile,
    Institution,
    AuthSession,
    Opportunity,
    AuditLog,
    ProfileItem,
)
from app.models.alumni import AlumniProfile
from app.repositories.platform import get, rows, add, public, audit
from app.schemas.platform import RoleUpdate, InstitutionAssignment, SkillInput
from app.schemas.platform import SkillClaim

router = APIRouter(prefix="/admin", tags=["2.0 Governance"])


@router.get("/review-queue")
async def review_queue(db: DB, user: Actor, limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0)):
    """Expose reviewable references without leaking uploaded file storage paths."""
    administrator(user)
    from app.models.student_document import StudentDocument

    drafts = await rows(db, Opportunity, Opportunity.status == "draft", Opportunity.approved.is_(False), limit=limit, offset=offset)
    portfolio = await rows(db, ProfileItem, ProfileItem.kind == "portfolio", ProfileItem.verified.is_(False), limit=limit, offset=offset)
    documents = await rows(db, StudentDocument, StudentDocument.verification_status == "pending", limit=limit, offset=offset)
    candidates = (await db.execute(
        select(User, DomainProfile).join(DomainProfile, DomainProfile.user_id == User.id)
        .where(User.is_active.is_(True), User.role.in_(["alumni", "academician", "industry"]), DomainProfile.verified.is_(False))
        .order_by(User.id).offset(offset).limit(limit)
    )).all()
    return {
        "opportunities": [{"opportunity_id": row.id, "title": row.title, "owner_id": row.owner_id, "domain_id": row.domain_id} for row in drafts],
        "portfolio": [{"item_id": row.id, "title": row.title, "user_id": row.user_id, "description": row.description, "url": row.url, "skill_ids": row.skill_ids} for row in portfolio],
        "student_documents": [{"document_id": row.id, "document_type": row.document_type, "user_id": row.user_id} for row in documents],
        "professional_profiles": [{"user_id": target.id, "email": target.email, "role": target.role, "domain_id": profile.domain_id} for target, profile in candidates],
    }


@router.get("/users")
async def users(
    db: DB,
    user: Actor,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    administrator(user)
    return [
        public(x, {"password_hash"})
        for x in await rows(db, User, limit=limit, offset=offset)
    ]


@router.patch("/users/{user_id}/role")
async def role(user_id: str, data: RoleUpdate, db: DB, user: Actor):
    administrator(user)
    if user.id == user_id:
        raise HTTPException(409, "Cannot change your own administrative role")
    target = await get(db, User, user_id)
    if data.role == "institution_admin" and not data.institution_id:
        raise HTTPException(
            422, "Institution administrators must be assigned an institution"
        )
    if data.institution_id:
        await get(db, Institution, data.institution_id)
    profile = await db.get(DomainProfile, user_id)
    if not profile:
        profile = await add(db, DomainProfile, user_id=user_id)
    profile.institution_id = data.institution_id
    target.role = data.role
    await db.execute(
        update(AuthSession).where(AuthSession.user_id == user_id).values(revoked=True)
    )
    audit(
        db,
        user,
        "user.role",
        user_id,
        role=data.role,
        institution_id=data.institution_id,
    )
    return {"id": target.id, "role": target.role}


@router.patch("/users/{user_id}/institution")
async def assign_institution(
    user_id: str, data: InstitutionAssignment, db: DB, user: Actor
):
    administrator(user)
    await get(db, User, user_id)
    await get(db, Institution, data.institution_id)
    profile = await db.get(DomainProfile, user_id)
    if not profile:
        profile = await add(db, DomainProfile, user_id=user_id)
    profile.institution_id = data.institution_id
    audit(db, user, "user.institution", user_id, institution_id=data.institution_id)
    return public(profile)


def activity_route(action, active):
    async def endpoint(user_id: str, db: DB, user: Actor):
        administrator(user)
        if user.id == user_id:
            raise HTTPException(409, "Cannot suspend yourself")
        target = await get(db, User, user_id)
        target.is_active = active
        if not active:
            await db.execute(
                update(AuthSession)
                .where(AuthSession.user_id == user_id)
                .values(revoked=True)
            )
        audit(db, user, f"user.{action}", user_id)
        return {"id": target.id, "is_active": active}

    router.add_api_route(
        f"/users/{{user_id}}/{action}",
        endpoint,
        methods=["POST"],
        name=f"user_{action}",
    )


activity_route("suspend", False)
activity_route("restore", True)


def verify_route(prefix, expected_role):
    async def endpoint(user_id: str, db: DB, user: Actor):
        administrator(user)
        target = await get(db, User, user_id)
        if target.role != expected_role:
            raise HTTPException(422, "User has a different role")
        profile = await get(db, DomainProfile, target.id)
        profile.verified = True
        if expected_role == "alumni":
            alumni = (
                await db.scalars(
                    select(AlumniProfile).where(AlumniProfile.user_id == target.id)
                )
            ).first()
            if alumni:
                alumni.verified_at = datetime.utcnow()
        audit(db, user, f"{prefix}.verify", target.id)
        return {"verified": True}

    router.add_api_route(
        f"/{prefix}/{{user_id}}/verify",
        endpoint,
        methods=["POST"],
        name=f"verify_{prefix}",
    )


for prefix, role_name in [
    ("alumni", "alumni"),
    ("faculty", "academician"),
    ("industry", "industry"),
]:
    verify_route(prefix, role_name)


@router.post("/opportunities/{opportunity_id}/approve")
async def approve(opportunity_id: int, db: DB, user: Actor):
    administrator(user)
    row = await get(db, Opportunity, opportunity_id)
    row.approved = True
    audit(db, user, "opportunity.approve", row.id)
    return public(row)


@router.post("/portfolio/{item_id}/verify")
async def verify_portfolio(item_id: int, db: DB, user: Actor):
    administrator(user)
    row = await get(db, ProfileItem, item_id)
    row.verified = True
    audit(db, user, "portfolio.verify", row.id)
    return public(row)


@router.get("/audit-logs")
async def logs(
    db: DB,
    user: Actor,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    administrator(user)
    return [public(x) for x in await rows(db, AuditLog, limit=limit, offset=offset)]


@router.get("/analytics")
async def analytics(db: DB, user: Actor):
    administrator(user)
    return {
        "users": await db.scalar(select(func.count()).select_from(User)),
        "opportunities": await db.scalar(select(func.count()).select_from(Opportunity)),
        "institutions": await db.scalar(select(func.count()).select_from(Institution)),
    }


@router.post("/taxonomy/import")
async def import_taxonomy(data: list[SkillInput], db: DB, user: Actor):
    administrator(user)
    if len(data) > 200:
        raise HTTPException(422, "Import at most 200 skills per request")
    from app.api.proposed.taxonomy import create_skill

    return [await create_skill(item, db, user) for item in data]


@router.post("/users/{user_id}/skills/verify")
async def verify_expertise(user_id: str, data: SkillClaim, db: DB, user: Actor):
    administrator(user)
    await get(db, User, user_id)
    from app.services.competency_service import set_skill

    row = await set_skill(
        db,
        user_id,
        data.skill_id,
        data.score,
        "institution_verified",
        {"reviewer_id": user.id},
    )
    audit(db, user, "skill.verify", user_id, skill_id=data.skill_id, score=data.score)
    return public(row)

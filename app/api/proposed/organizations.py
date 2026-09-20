from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, or_
from app.models.settings import UserPrivacySettings
from app.api.proposed.deps import DB, Actor, roles, owner
from app.models.user import User
from app.models.platform import DomainProfile, StudentSkill, Opportunity
from app.models.profile import Profile
from app.repositories.platform import get, rows, public
from app.schemas.platform import ProfileUpdate
from app.services.identity_service import me, update_profile
from app.services.matching_service import match

router = APIRouter(tags=["2.0 Alumni, academia and industry"])


async def directory(db, role, offset=0, limit=100):
    result = await db.execute(
        select(User, DomainProfile, Profile)
        .join(DomainProfile, DomainProfile.user_id == User.id)
        .join(Profile, Profile.user_id == User.id)
        .outerjoin(UserPrivacySettings, UserPrivacySettings.user_id == User.id)
        .where(
            User.role == role,
            User.is_active.is_(True),
            DomainProfile.discoverable.is_(True),
            or_(
                UserPrivacySettings.user_id.is_(None),
                UserPrivacySettings.public_profile.is_(True),
            ),
            or_(
                UserPrivacySettings.user_id.is_(None),
                UserPrivacySettings.discoverable.is_(True),
            ),
        )
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )
    return [
        {"id": u.id, "display_name": p.display_name, "profile": public(d)}
        for u, d, p in result
    ]


def profile_routes(prefix, role):
    async def listing(
        db: DB,
        user: Actor,
        offset: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
    ):
        return await directory(db, role, offset, limit)

    async def own(db: DB, user: Actor):
        roles(user, role)
        return await me(db, user)

    async def patch(data: ProfileUpdate, db: DB, user: Actor):
        roles(user, role)
        return await update_profile(db, user, data)

    async def detail(user_id: str, db: DB, user: Actor):
        target = await get(db, User, user_id)
        profile = await get(db, DomainProfile, user_id)
        privacy = (
            await db.scalars(
                select(UserPrivacySettings).where(
                    UserPrivacySettings.user_id == user_id
                )
            )
        ).first()
        if privacy and not privacy.public_profile and user.id != target.id:
            raise HTTPException(404, "Profile not found")
        if (
            target.role != role
            or not target.is_active
            or (not profile.discoverable and user.id != target.id)
        ):
            raise HTTPException(404, "Profile not found")
        return {"id": target.id, "profile": public(profile)}

    async def expertise(user_id: str, db: DB, user: Actor):
        await detail(user_id, db, user)
        return [
            public(x, {"evidence"})
            for x in await rows(db, StudentSkill, StudentSkill.user_id == user_id)
        ]

    router.add_api_route(f"/{prefix}", listing, methods=["GET"], name=f"{prefix}_list")
    router.add_api_route(
        f"/{prefix}/me/profile", own, methods=["GET"], name=f"{prefix}_own_profile"
    )
    router.add_api_route(
        f"/{prefix}/me/profile",
        patch,
        methods=["PATCH"],
        name=f"{prefix}_update_profile",
    )
    if role == "industry":
        router.add_api_route(
            "/industry/profile", patch, methods=["POST"], name="industry_create_profile"
        )
    router.add_api_route(
        f"/{prefix}/{{user_id}}", detail, methods=["GET"], name=f"{prefix}_profile"
    )
    router.add_api_route(
        f"/{prefix}/{{user_id}}/expertise",
        expertise,
        methods=["GET"],
        name=f"{prefix}_expertise",
    )
    if role == "alumni":
        router.add_api_route(
            "/alumni/{user_id}/skills", expertise, methods=["GET"], name="alumni_skills"
        )


@router.get("/industry/me/opportunities")
async def opportunities(db: DB, user: Actor):
    roles(user, "industry", "academician")
    return [
        public(x) for x in await rows(db, Opportunity, Opportunity.owner_id == user.id)
    ]


async def candidates(db, user, opportunity_id, role):
    opp = await get(db, Opportunity, opportunity_id)
    owner(user, opp.owner_id)
    profiles = await directory(db, role, limit=500)
    results = [
        {
            "user_id": p["id"],
            "display_name": p["display_name"],
            **(await match(db, p["id"], opp)),
        }
        for p in profiles
    ]
    return sorted([x for x in results if x["eligible"]], key=lambda x: -x["score"])[:50]


@router.get("/industry/me/candidate-matches")
async def candidate_matches(opportunity_id: int, db: DB, user: Actor):
    return await candidates(db, user, opportunity_id, "student")


@router.get("/industry/me/faculty-matches")
async def faculty_matches(opportunity_id: int, db: DB, user: Actor):
    return await candidates(db, user, opportunity_id, "academician")


@router.get("/academicians/{academician_id}/research")
async def faculty_research(academician_id: str, db: DB, user: Actor):
    return [
        public(x)
        for x in await rows(
            db,
            Opportunity,
            Opportunity.owner_id == academician_id,
            Opportunity.kind == "research",
            Opportunity.status == "published",
        )
    ]


profile_routes("alumni", "alumni")
profile_routes("faculty", "academician")
profile_routes("industry", "industry")

from fastapi import APIRouter, HTTPException
from app.api.proposed.deps import DB, Actor, roles, owner
from app.models.platform import StudentSkill, ProfileItem, Skill, ReadinessSnapshot
from app.repositories.platform import get, rows, add, public
from app.schemas.platform import ProfileUpdate, SkillsUpdate, ProfileItemInput
from app.services.identity_service import me, update_profile
from app.services.competency_service import set_skill, competency_scores, readiness

router = APIRouter(prefix="/students/me", tags=["2.0 Student competency"])


@router.get("/profile")
async def profile(db: DB, user: Actor):
    roles(user, "student")
    return await me(db, user)


@router.patch("/profile")
async def patch_profile(data: ProfileUpdate, db: DB, user: Actor):
    roles(user, "student")
    return await update_profile(db, user, data)


@router.get("/skills")
async def skills(db: DB, user: Actor):
    return [
        public(x) for x in await rows(db, StudentSkill, StudentSkill.user_id == user.id)
    ]


@router.put("/skills")
async def put_skills(data: SkillsUpdate, db: DB, user: Actor):
    roles(user, "student", "alumni", "academician", "industry")
    if len({s.skill_id for s in data.skills}) != len(data.skills):
        raise HTTPException(422, "Duplicate skill IDs")
    for item in data.skills:
        await set_skill(
            db,
            user.id,
            item.skill_id,
            item.score,
            "self_declared",
            {"source": "profile"},
        )
    return await skills(db, user)


@router.get("/competencies")
@router.post("/competencies/recalculate")
async def competencies(db: DB, user: Actor):
    roles(user, "student")
    return await competency_scores(db, user.id)


@router.get("/readiness")
async def get_readiness(db: DB, user: Actor):
    roles(user, "student")
    return await readiness(db, user.id)


@router.get("/readiness/history")
async def readiness_history(db: DB, user: Actor):
    return [
        public(x)
        for x in await rows(db, ReadinessSnapshot, ReadinessSnapshot.user_id == user.id)
    ]


def profile_item_routes(kind):
    async def listing(db: DB, user: Actor):
        return [
            public(x)
            for x in await rows(
                db,
                ProfileItem,
                ProfileItem.user_id == user.id,
                ProfileItem.kind == kind,
            )
        ]

    async def create(data: ProfileItemInput, db: DB, user: Actor):
        for skill_id in data.skill_ids:
            await get(db, Skill, skill_id)
        return public(
            await add(
                db,
                ProfileItem,
                user_id=user.id,
                kind=kind,
                **data.model_dump(mode="json"),
            )
        )

    async def edit(item_id: int, data: ProfileItemInput, db: DB, user: Actor):
        item = await get(db, ProfileItem, item_id)
        owner(user, item.user_id)
        if item.kind != kind:
            raise HTTPException(404, "Item not found")
        for skill_id in data.skill_ids:
            await get(db, Skill, skill_id)
        for k, v in data.model_dump(mode="json").items():
            setattr(item, k, v)
        item.verified = False
        return public(item)

    async def delete(item_id: int, db: DB, user: Actor):
        item = await get(db, ProfileItem, item_id)
        owner(user, item.user_id)
        if item.kind != kind:
            raise HTTPException(404, "Item not found")
        await db.delete(item)
        return {"deleted": True}

    router.add_api_route(f"/{kind}", listing, methods=["GET"], name=f"list_{kind}")
    router.add_api_route(
        f"/{kind}", create, methods=["POST"], status_code=201, name=f"create_{kind}"
    )
    router.add_api_route(
        f"/{kind}/{{item_id}}", edit, methods=["PATCH"], name=f"update_{kind}"
    )
    router.add_api_route(
        f"/{kind}/{{item_id}}", delete, methods=["DELETE"], name=f"delete_{kind}"
    )


profile_item_routes("education")
profile_item_routes("portfolio")

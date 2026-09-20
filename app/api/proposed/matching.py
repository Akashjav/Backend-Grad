from fastapi import APIRouter, HTTPException
from app.api.proposed.deps import DB, Actor, roles, owner
from app.models.platform import Opportunity, MatchResult, SkillGap, DomainProfile
from app.repositories.platform import get, rows, public
from app.services.matching_service import match, recommendations
from app.services.opportunities_service import visible

router = APIRouter(tags=["2.0 Matching and skill gaps"])


@router.get("/recommendations/opportunities")
async def recommended(db: DB, user: Actor):
    roles(user, "student", "academician", "alumni")
    return await recommendations(db, user)


def recommend_kind(kind):
    async def endpoint(db: DB, user: Actor):
        return await recommendations(db, user, kind)

    router.add_api_route(
        f"/recommendations/{kind}s"
        if kind != "research"
        else "/recommendations/research",
        endpoint,
        methods=["GET"],
        name=f"recommend_{kind}",
    )


for kind in ["job", "internship", "project", "research"]:
    recommend_kind(kind)


@router.post("/matching/opportunities/{opportunity_id}/score")
async def score(opportunity_id: int, db: DB, user: Actor):
    opportunity = await visible(db, opportunity_id, user)
    return await match(db, user.id, opportunity, persist=True)


@router.post("/matching/candidates/{student_id}/score")
async def candidate(student_id: str, opportunity_id: int, db: DB, user: Actor):
    opportunity = await get(db, Opportunity, opportunity_id)
    owner(user, opportunity.owner_id)
    profile = await get(db, DomainProfile, student_id)
    if not profile.discoverable:
        raise HTTPException(404, "Candidate not discoverable")
    return await match(db, student_id, opportunity, persist=True)


async def authorized_match(db, user, match_id):
    row = await get(db, MatchResult, match_id)
    if row.student_id != user.id:
        opportunity = await get(db, Opportunity, row.opportunity_id)
        owner(user, opportunity.owner_id)
    return row


@router.get("/matching/{match_id}/explanation")
async def explanation(match_id: int, db: DB, user: Actor):
    return public(await authorized_match(db, user, match_id))


@router.get("/matching/{match_id}/skill-gaps")
async def match_gaps(match_id: int, db: DB, user: Actor):
    return (await authorized_match(db, user, match_id)).explanation["skill_gaps"]


@router.get("/students/me/skill-gaps")
async def gaps(db: DB, user: Actor):
    return [public(x) for x in await rows(db, SkillGap, SkillGap.student_id == user.id)]


@router.get("/students/me/skill-gaps/{gap_id}")
async def gap(gap_id: int, db: DB, user: Actor):
    row = await get(db, SkillGap, gap_id)
    owner(user, row.student_id)
    return public(row)


@router.post("/students/me/skill-gaps/recalculate")
async def recalculate(opportunity_id: int, db: DB, user: Actor):
    return await score(opportunity_id, db, user)


@router.get("/students/me/career-paths")
async def career_paths(db: DB, user: Actor):
    results = await recommendations(db, user)
    return [
        {
            "opportunity_id": x["opportunity_id"],
            "goal": x["opportunity_title"],
            "score": x["score"],
            "next_skills": x["skill_gaps"],
        }
        for x in results[:10]
    ]

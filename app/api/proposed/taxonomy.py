from fastapi import APIRouter, Query, HTTPException
from app.api.proposed.deps import DB, Actor, administrator
from app.models.subscription import Domain
from app.models.platform import Discipline, Skill, Competency, DomainPolicy
from app.repositories.platform import get, rows, add, public, audit
from app.schemas.platform import (
    DomainInput,
    DisciplineInput,
    SkillInput,
    CompetencyInput,
    DomainWeights,
)

router = APIRouter(tags=["2.0 Taxonomy"])


@router.get("/domains")
async def domains(
    db: DB, limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0)
):
    return [public(x) for x in await rows(db, Domain, limit=limit, offset=offset)]


@router.post("/domains", status_code=201)
async def create_domain(data: DomainInput, db: DB, user: Actor):
    administrator(user)
    row = await add(db, Domain, **data.model_dump())
    audit(db, user, "taxonomy.domain.create", row.id)
    return public(row)


@router.get("/domains/{domain_id}")
async def domain(domain_id: int, db: DB):
    return public(await get(db, Domain, domain_id))


@router.patch("/domains/{domain_id}")
async def update_domain(domain_id: int, data: DomainInput, db: DB, user: Actor):
    administrator(user)
    row = await get(db, Domain, domain_id)
    for k, v in data.model_dump().items():
        setattr(row, k, v)
    audit(db, user, "taxonomy.domain.update", row.id)
    return public(row)


@router.put("/domains/{domain_id}/weights")
async def weights(domain_id: int, data: DomainWeights, db: DB, user: Actor):
    administrator(user)
    await get(db, Domain, domain_id)
    row = await db.get(DomainPolicy, domain_id)
    if not row:
        row = await add(db, DomainPolicy, domain_id=domain_id)
    row.matching_weights = data.matching_weights
    row.readiness_weights = data.readiness_weights
    audit(db, user, "taxonomy.weights.update", domain_id)
    return public(row)


@router.get("/disciplines")
async def disciplines(db: DB, domain_id: int | None = None):
    return [
        public(x)
        for x in await rows(
            db, Discipline, *([Discipline.domain_id == domain_id] if domain_id else [])
        )
    ]


@router.get("/domains/{domain_id}/disciplines")
async def domain_disciplines(domain_id: int, db: DB):
    await get(db, Domain, domain_id)
    return await disciplines(db, domain_id)


@router.post("/disciplines", status_code=201)
async def create_discipline(data: DisciplineInput, db: DB, user: Actor):
    administrator(user)
    await get(db, Domain, data.domain_id)
    row = await add(db, Discipline, **data.model_dump())
    audit(db, user, "taxonomy.discipline.create", row.id)
    return public(row)


@router.get("/disciplines/{discipline_id}")
async def discipline(discipline_id: int, db: DB):
    return public(await get(db, Discipline, discipline_id))


@router.get("/skills")
@router.get("/skills/search")
async def skills(
    db: DB,
    domain_id: int | None = None,
    search: str = "",
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    conditions = [Skill.name.ilike(f"%{search}%")]
    if domain_id:
        conditions.append(Skill.domain_id == domain_id)
    return [
        public(x)
        for x in await rows(db, Skill, *conditions, limit=limit, offset=offset)
    ]


@router.post("/skills", status_code=201)
async def create_skill(data: SkillInput, db: DB, user: Actor):
    administrator(user)
    await get(db, Domain, data.domain_id)
    for skill_id in data.related_skill_ids:
        await get(db, Skill, skill_id)
    row = await add(db, Skill, **data.model_dump())
    audit(db, user, "taxonomy.skill.create", row.id)
    return public(row)


@router.get("/skills/{skill_id}")
async def skill(skill_id: int, db: DB):
    return public(await get(db, Skill, skill_id))


@router.patch("/skills/{skill_id}")
async def update_skill(skill_id: int, data: SkillInput, db: DB, user: Actor):
    administrator(user)
    row = await get(db, Skill, skill_id)
    if row.domain_id != data.domain_id:
        raise HTTPException(409, "A skill cannot be moved to a different domain")
    for related_id in data.related_skill_ids:
        await get(db, Skill, related_id)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    audit(db, user, "taxonomy.skill.update", row.id)
    return public(row)


@router.get("/competencies")
async def competencies(db: DB, domain_id: int | None = None):
    return [
        public(x)
        for x in await rows(
            db, Competency, *([Competency.domain_id == domain_id] if domain_id else [])
        )
    ]


@router.post("/competencies", status_code=201)
async def create_competency(data: CompetencyInput, db: DB, user: Actor):
    administrator(user)
    await get(db, Domain, data.domain_id)
    for skill_id in data.skill_weights:
        skill = await get(db, Skill, skill_id)
        if skill.domain_id != data.domain_id:
            raise HTTPException(422, "Competency skill belongs to another domain")
    row = await add(db, Competency, **data.model_dump(mode="json"))
    audit(db, user, "taxonomy.competency.create", row.id)
    return public(row)


@router.get("/competencies/{competency_id}")
async def competency(competency_id: int, db: DB):
    return public(await get(db, Competency, competency_id))


@router.get("/domains/{domain_id}/competency-map")
async def competency_map(domain_id: int, db: DB):
    await get(db, Domain, domain_id)
    return {
        "domain_id": domain_id,
        "competencies": await competencies(db, domain_id),
        "skills": await skills(db, domain_id, "", 200, 0),
    }

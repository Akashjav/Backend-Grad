"""Projects, research, consultancy and FDP share the opportunity lifecycle."""

from fastapi import APIRouter, HTTPException
from app.api.proposed.deps import DB, Actor
from app.schemas.platform import OpportunityInput, OpportunityPatch
from app.models.platform import Opportunity
from app.repositories.platform import get
from app.api.proposed import opportunities
from app.api.proposed import collaborations
from app.models.platform import Collaboration
from app.schemas.platform import Invite, CollaborationInput
from app.repositories.platform import rows

router = APIRouter(tags=["2.0 Projects and research"])


def project_routes(prefix, kind):
    async def listing(db: DB, user: Actor):
        return await opportunities.listing(db, user, None, kind, "", 100, 0)

    async def create(data: OpportunityInput, db: DB, user: Actor):
        return await opportunities.create(
            data.model_copy(update={"kind": kind}), db, user
        )

    async def check(item_id, db):
        row = await get(db, Opportunity, item_id)
        if row.kind != kind:
            raise HTTPException(404, "Project not found")

    async def detail(item_id: int, db: DB, user: Actor):
        await check(item_id, db)
        return await opportunities.detail(item_id, db, user)

    async def patch(item_id: int, data: OpportunityPatch, db: DB, user: Actor):
        await check(item_id, db)
        return await opportunities.patch(item_id, data, db, user)

    async def delete(item_id: int, db: DB, user: Actor):
        await check(item_id, db)
        return await opportunities.archive(item_id, db, user)

    async def apply(item_id: int, db: DB, user: Actor):
        await check(item_id, db)
        return await opportunities.apply(item_id, db, user)

    for path, endpoint, methods in [
        (prefix, listing, ["GET"]),
        (prefix, create, ["POST"]),
        (prefix + "/{item_id}", detail, ["GET"]),
        (prefix + "/{item_id}", patch, ["PATCH"]),
        (prefix + "/{item_id}", delete, ["DELETE"]),
        (prefix + "/{item_id}/apply", apply, ["POST"]),
    ]:
        router.add_api_route(
            "/" + path, endpoint, methods=methods, name=f"{kind}_{endpoint.__name__}"
        )


for prefix, kind in [
    ("projects", "project"),
    ("research", "research"),
    ("faculty/consultancy", "consultancy"),
    ("faculty/fdp", "fdp"),
]:
    project_routes(prefix, kind)


async def project_collaboration(project_id, db, user, create=False):
    project = await get(db, Opportunity, project_id)
    if project.kind != "project":
        raise HTTPException(404, "Project not found")
    found = await rows(db, Collaboration, Collaboration.opportunity_id == project_id)
    if found:
        return found[0].id
    if create:
        row = await collaborations.create(
            CollaborationInput(opportunity_id=project_id, title=project.title), db, user
        )
        return row["id"]
    raise HTTPException(404, "No team has been created for this project")


@router.get("/projects/{project_id}/members")
async def members(project_id: int, db: DB, user: Actor):
    cid = await project_collaboration(project_id, db, user)
    return await collaborations.members(cid, db, user)


@router.post("/projects/{project_id}/members")
async def add_member(project_id: int, data: Invite, db: DB, user: Actor):
    cid = await project_collaboration(project_id, db, user, create=True)
    return await collaborations.invite(cid, data, db, user)


@router.post("/projects/{project_id}/mentor")
async def assign_mentor(project_id: int, data: Invite, db: DB, user: Actor):
    return await add_member(
        project_id, data.model_copy(update={"role": "mentor"}), db, user
    )

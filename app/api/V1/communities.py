from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.api.deps import get_db
from app.api.V1.users import get_current_user
from app.models.user import User
from app.models.community import Community, CommunityMembership
from app.schemas.community import CommunityCreate

router = APIRouter(prefix="/api/communities", tags=["Communities"])


@router.post("/")
async def create_community(
    data: CommunityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    community = Community(
        name=data.name,
        category=data.category,
        blurb=data.blurb,
        cadence=data.cadence,
        activity=data.activity,
        member_count=0
    )

    db.add(community)
    await db.commit()
    await db.refresh(community)

    return {
        "message": "Community created successfully",
        "community_id": community.id
    }


@router.get("/")
async def get_communities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Community))
    communities = result.scalars().all()

    output = []

    for community in communities:
        membership_result = await db.execute(
            select(CommunityMembership).where(
                CommunityMembership.community_id == community.id,
                CommunityMembership.user_id == current_user.id
            )
        )

        joined = membership_result.scalar_one_or_none() is not None

        output.append({
            "id": community.id,
            "name": community.name,
            "category": community.category,
            "blurb": community.blurb,
            "member_count": community.member_count,
            "cadence": community.cadence,
            "activity": community.activity,
            "joined": joined
        })

    return output


@router.get("/{community_id}")
async def get_community_detail(
    community_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    community_id = str(community_id)

    result = await db.execute(
        select(Community).where(Community.id == community_id)
    )
    community = result.scalar_one_or_none()

    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    membership_result = await db.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community.id,
            CommunityMembership.user_id == current_user.id
        )
    )

    joined = membership_result.scalar_one_or_none() is not None

    return {
        "id": community.id,
        "name": community.name,
        "category": community.category,
        "blurb": community.blurb,
        "member_count": community.member_count,
        "cadence": community.cadence,
        "activity": community.activity,
        "joined": joined
    }


@router.post("/{community_id}/join")
async def join_community(
    community_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    community_id = str(community_id)

    result = await db.execute(
        select(Community).where(Community.id == community_id)
    )
    community = result.scalar_one_or_none()

    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    existing = await db.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community_id,
            CommunityMembership.user_id == current_user.id
        )
    )

    if existing.scalar_one_or_none():
        return {"message": "Already joined"}

    membership = CommunityMembership(
        community_id=community_id,
        user_id=current_user.id
    )

    community.member_count += 1

    db.add(membership)
    await db.commit()

    return {"message": "Joined community successfully"}


@router.delete("/{community_id}/membership")
async def leave_community(
    community_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    community_id = str(community_id)

    result = await db.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community_id,
            CommunityMembership.user_id == current_user.id
        )
    )

    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    community_result = await db.execute(
        select(Community).where(Community.id == community_id)
    )
    community = community_result.scalar_one_or_none()

    if community and community.member_count > 0:
        community.member_count -= 1

    await db.delete(membership)
    await db.commit()

    return {"message": "Left community successfully"}

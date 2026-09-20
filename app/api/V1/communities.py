from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from uuid import UUID

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.community import Community, CommunityMembership

from app.schemas.community import CommunityCreate

from app.services import communities_service

router = APIRouter(prefix="/api/communities", tags=["Communities"])

@router.post('/')
async def create_community(data: CommunityCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await communities_service.create_community(data, current_user, db)

@router.get('/')
async def get_communities(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await communities_service.get_communities(current_user, db)

@router.get('/{community_id}')
async def get_community_detail(community_id: UUID, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await communities_service.get_community_detail(community_id, current_user, db)

@router.post('/{community_id}/join')
async def join_community(community_id: UUID, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await communities_service.join_community(community_id, current_user, db)

@router.delete('/{community_id}/membership')
async def leave_community(community_id: UUID, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await communities_service.leave_community(community_id, current_user, db)

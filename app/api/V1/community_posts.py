from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.community import (
    Community,
    CommunityMembership,
    CommunityPost,
    CommunityPostLike,
    CommunityPostReply
)

from app.schemas.community_post import CommunityPostCreate, CommunityReplyCreate

from app.services import community_posts_service

router = APIRouter(tags=["Community Posts"])

@router.post('/api/communities/{community_id}/posts')
async def create_community_post(community_id: UUID, data: CommunityPostCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await community_posts_service.create_community_post(community_id, data, current_user, db)

@router.get('/api/communities/{community_id}/posts')
async def get_community_posts(community_id: UUID, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await community_posts_service.get_community_posts(community_id, current_user, db)

@router.post('/api/community-posts/{post_id}/like')
async def like_post(post_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await community_posts_service.like_post(post_id, current_user, db)

@router.delete('/api/community-posts/{post_id}/like')
async def unlike_post(post_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await community_posts_service.unlike_post(post_id, current_user, db)

@router.post('/api/community-posts/{post_id}/replies')
async def create_reply(post_id: int, data: CommunityReplyCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await community_posts_service.create_reply(post_id, data, current_user, db)

@router.get('/api/community-posts/{post_id}/replies')
async def get_replies(post_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await community_posts_service.get_replies(post_id, current_user, db)

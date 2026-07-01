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

router = APIRouter(tags=["Community Posts"])


@router.post("/api/communities/{community_id}/posts")
async def create_community_post(
    community_id: UUID,
    data: CommunityPostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    community_id = str(community_id)

    community_result = await db.execute(
        select(Community).where(Community.id == community_id)
    )
    community = community_result.scalar_one_or_none()

    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    membership_result = await db.execute(
        select(CommunityMembership).where(
            CommunityMembership.community_id == community_id,
            CommunityMembership.user_id == current_user.id
        )
    )

    if not membership_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Join community before posting")

    post = CommunityPost(
        community_id=community_id,
        author_id=current_user.id,
        title=data.title,
        body=data.body,
        tags=data.tags
    )

    db.add(post)
    await db.commit()
    await db.refresh(post)

    return {
        "message": "Post created successfully",
        "post_id": post.id
    }


@router.get("/api/communities/{community_id}/posts")
async def get_community_posts(
    community_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    community_id = str(community_id)

    result = await db.execute(
        select(CommunityPost)
        .where(CommunityPost.community_id == community_id)
        .order_by(CommunityPost.created_at.desc())
    )

    posts = result.scalars().all()

    output = []

    for post in posts:
        like_result = await db.execute(
            select(CommunityPostLike).where(
                CommunityPostLike.post_id == post.id,
                CommunityPostLike.user_id == current_user.id
            )
        )

        output.append({
            "id": post.id,
            "community_id": post.community_id,
            "author_id": post.author_id,
            "title": post.title,
            "body": post.body,
            "tags": post.tags,
            "likes_count": post.likes_count,
            "replies_count": post.replies_count,
            "is_liked": like_result.scalar_one_or_none() is not None,
            "created_at": post.created_at
        })

    return output


@router.post("/api/community-posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    post_result = await db.execute(
        select(CommunityPost).where(CommunityPost.id == post_id)
    )
    post = post_result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing_result = await db.execute(
        select(CommunityPostLike).where(
            CommunityPostLike.post_id == post_id,
            CommunityPostLike.user_id == current_user.id
        )
    )

    if existing_result.scalar_one_or_none():
        return {"message": "Already liked"}

    like = CommunityPostLike(
        post_id=post_id,
        user_id=current_user.id
    )

    post.likes_count += 1

    db.add(like)
    await db.commit()

    return {"message": "Post liked successfully"}


@router.delete("/api/community-posts/{post_id}/like")
async def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CommunityPostLike).where(
            CommunityPostLike.post_id == post_id,
            CommunityPostLike.user_id == current_user.id
        )
    )

    like = result.scalar_one_or_none()

    if not like:
        raise HTTPException(status_code=404, detail="Like not found")

    post_result = await db.execute(
        select(CommunityPost).where(CommunityPost.id == post_id)
    )
    post = post_result.scalar_one_or_none()

    if post and post.likes_count > 0:
        post.likes_count -= 1

    await db.delete(like)
    await db.commit()

    return {"message": "Post unliked successfully"}


@router.post("/api/community-posts/{post_id}/replies")
async def create_reply(
    post_id: int,
    data: CommunityReplyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    post_result = await db.execute(
        select(CommunityPost).where(CommunityPost.id == post_id)
    )
    post = post_result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    reply = CommunityPostReply(
        post_id=post_id,
        author_id=current_user.id,
        body=data.body
    )

    post.replies_count += 1

    db.add(reply)
    await db.commit()
    await db.refresh(reply)

    return {
        "message": "Reply added successfully",
        "reply_id": reply.id
    }


@router.get("/api/community-posts/{post_id}/replies")
async def get_replies(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CommunityPostReply)
        .where(CommunityPostReply.post_id == post_id)
        .order_by(CommunityPostReply.created_at)
    )

    replies = result.scalars().all()

    return [
        {
            "id": reply.id,
            "post_id": reply.post_id,
            "author_id": reply.author_id,
            "body": reply.body,
            "created_at": reply.created_at
        }
        for reply in replies
    ]

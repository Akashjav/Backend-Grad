from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.V1.users import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.post("/")
async def create_notification(
    data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = str(data.user_id)
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notification = Notification(
        user_id=user_id,
        kind=data.kind,
        title=data.title,
        body=data.body,
        action_url=data.action_url
    )

    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    return {
        "message": "Notification created successfully",
        "notification_id": notification.id
    }


@router.get("/")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )

    notifications = result.scalars().all()

    return [
        {
            "id": notification.id,
            "kind": notification.kind,
            "title": notification.title,
            "body": notification.body,
            "action_url": notification.action_url,
            "read": notification.read_at is not None,
            "read_at": notification.read_at,
            "created_at": notification.created_at
        }
        for notification in notifications
    ]


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    )

    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read_at = datetime.utcnow()
    await db.commit()

    return {"message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification).where(Notification.user_id == current_user.id)
    )

    notifications = result.scalars().all()

    for notification in notifications:
        notification.read_at = datetime.utcnow()

    await db.commit()

    return {"message": "All notifications marked as read"}

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.notification import Notification

from app.schemas.notification import NotificationCreate

from app.services import notifications_service

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.post('/')
async def create_notification(data: NotificationCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await notifications_service.create_notification(data, current_user, db)

@router.get('/')
async def get_notifications(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await notifications_service.get_notifications(current_user, db)

@router.post('/{notification_id}/read')
async def mark_notification_read(notification_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await notifications_service.mark_notification_read(notification_id, current_user, db)

@router.post('/read-all')
async def mark_all_notifications_read(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await notifications_service.mark_all_notifications_read(current_user, db)

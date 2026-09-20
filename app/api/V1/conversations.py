from datetime import datetime

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

from app.api.V1.users import get_current_user

from app.models.user import User

from app.models.conversation import Conversation, ConversationParticipant, Message

from app.schemas.conversation import ConversationCreate, MessageCreate

from app.services import conversations_service

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])

@router.post('/')
async def create_conversation(data: ConversationCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await conversations_service.create_conversation(data, current_user, db)

@router.get('/')
async def get_conversations(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await conversations_service.get_conversations(current_user, db)

@router.get('/{conversation_id}')
async def get_conversation_detail(conversation_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await conversations_service.get_conversation_detail(conversation_id, current_user, db)

@router.get('/{conversation_id}/messages')
async def get_messages(conversation_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db), after_id: int = Query(0, ge=0), before_id: int | None = Query(None, ge=1), limit: int = Query(100, ge=1, le=200)):
    return await conversations_service.get_messages(conversation_id, current_user, db, after_id, limit, before_id)

@router.post('/{conversation_id}/messages')
async def send_message(conversation_id: int, data: MessageCreate, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await conversations_service.send_message(conversation_id, data, current_user, db)

@router.post('/{conversation_id}/read')
async def mark_conversation_read(conversation_id: int, current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await conversations_service.mark_conversation_read(conversation_id, current_user, db)

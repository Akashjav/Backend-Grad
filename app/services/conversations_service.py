from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.conversation import Conversation, ConversationParticipant, Message
from app.schemas.conversation import ConversationCreate, MessageCreate

async def create_conversation(data: ConversationCreate, current_user: User, db: AsyncSession):
    other_user_id = str(data.other_user_id)
    other_user_result = await db.execute(select(User).where(User.id == other_user_id))
    other_user = other_user_result.scalar_one_or_none()
    if not other_user:
        raise HTTPException(status_code=404, detail='Other user not found')
    conversation = Conversation(title=data.title, created_by=current_user.id)
    db.add(conversation)
    await db.flush()
    participant_1 = ConversationParticipant(conversation_id=conversation.id, user_id=current_user.id)
    participant_2 = ConversationParticipant(conversation_id=conversation.id, user_id=other_user_id)
    db.add(participant_1)
    db.add(participant_2)
    await db.commit()
    await db.refresh(conversation)
    return {'message': 'Conversation created successfully', 'conversation_id': conversation.id}

async def get_conversations(current_user: User, db: AsyncSession):
    result = await db.execute(select(ConversationParticipant).where(ConversationParticipant.user_id == current_user.id))
    memberships = result.scalars().all()
    output = []
    for membership in memberships:
        convo_result = await db.execute(select(Conversation).where(Conversation.id == membership.conversation_id))
        conversation = convo_result.scalar_one_or_none()
        if conversation:
            output.append({'id': conversation.id, 'title': conversation.title, 'created_by': conversation.created_by, 'created_at': conversation.created_at})
    return output

async def get_conversation_detail(conversation_id: int, current_user: User, db: AsyncSession):
    membership_result = await db.execute(select(ConversationParticipant).where(ConversationParticipant.conversation_id == conversation_id, ConversationParticipant.user_id == current_user.id))
    membership = membership_result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail='Not part of this conversation')
    convo_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = convo_result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail='Conversation not found')
    return {'id': conversation.id, 'title': conversation.title, 'created_by': conversation.created_by, 'created_at': conversation.created_at}

async def get_messages(conversation_id: int, current_user: User, db: AsyncSession, after_id: int = 0, limit: int = 100, before_id: int | None = None):
    membership_result = await db.execute(select(ConversationParticipant).where(ConversationParticipant.conversation_id == conversation_id, ConversationParticipant.user_id == current_user.id))
    membership = membership_result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail='Not part of this conversation')
    statement = select(Message).where(Message.conversation_id == conversation_id)
    if after_id:
        statement = statement.where(Message.id > after_id).order_by(Message.id)
    else:
        if before_id:
            statement = statement.where(Message.id < before_id)
        statement = statement.order_by(Message.id.desc())
    result = await db.execute(statement.limit(min(max(limit, 1), 200)))
    messages = list(result.scalars().all())
    if not after_id:
        messages.reverse()
    return [{'id': msg.id, 'conversation_id': msg.conversation_id, 'author_id': msg.author_id, 'body': msg.body, 'created_at': msg.created_at} for msg in messages]

async def send_message(conversation_id: int, data: MessageCreate, current_user: User, db: AsyncSession):
    membership_result = await db.execute(select(ConversationParticipant).where(ConversationParticipant.conversation_id == conversation_id, ConversationParticipant.user_id == current_user.id))
    membership = membership_result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail='Not part of this conversation')
    message = Message(conversation_id=conversation_id, author_id=current_user.id, body=data.body)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return {'message': 'Message sent successfully', 'message_id': message.id}

async def mark_conversation_read(conversation_id: int, current_user: User, db: AsyncSession):
    membership_result = await db.execute(select(ConversationParticipant).where(ConversationParticipant.conversation_id == conversation_id, ConversationParticipant.user_id == current_user.id))
    membership = membership_result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail='Not part of this conversation')
    membership.last_read_at = datetime.utcnow()
    await db.commit()
    return {'message': 'Conversation marked as read'}

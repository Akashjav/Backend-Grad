from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.ai_chat import AIChatMessage
from app.schemas.ai_chat import AIChatRequest
from app.ai.career_assistant import generate_ai_answer

async def ai_chat(data: AIChatRequest, current_user: User, db: AsyncSession):
    user_message = AIChatMessage(user_id=current_user.id, role='user', message=data.prompt)
    answer = generate_ai_answer(data.prompt)
    ai_message = AIChatMessage(user_id=current_user.id, role='assistant', message=answer)
    db.add(user_message)
    db.add(ai_message)
    await db.commit()
    return {'answer': answer}

async def get_ai_chat_history(current_user: User, db: AsyncSession):
    result = await db.execute(select(AIChatMessage).where(AIChatMessage.user_id == current_user.id).order_by(AIChatMessage.created_at))
    messages = result.scalars().all()
    return [{'id': msg.id, 'role': msg.role, 'message': msg.message, 'created_at': msg.created_at} for msg in messages]

async def clear_ai_chat_history(current_user: User, db: AsyncSession):
    result = await db.execute(select(AIChatMessage).where(AIChatMessage.user_id == current_user.id))
    messages = result.scalars().all()
    for msg in messages:
        await db.delete(msg)
    await db.commit()
    return {'message': 'AI chat history cleared successfully'}

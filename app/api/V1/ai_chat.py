from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.V1.users import get_current_user
from app.models.user import User
from app.models.ai_chat import AIChatMessage
from app.schemas.ai_chat import AIChatRequest

router = APIRouter(prefix="/api/ai-chat", tags=["AI Assistant"])


def generate_ai_answer(prompt: str) -> str:
    text = prompt.lower()

    if "resume" in text:
        return (
            "For resume improvement: keep it one page, add strong project points, "
            "mention technologies clearly, include measurable impact, and avoid long paragraphs."
        )

    if "interview" in text:
        return (
            "For interview preparation: revise Java OOP, SQL joins, DBMS basics, "
            "DSA arrays/strings, and practice explaining your project clearly."
        )

    if "roadmap" in text or "career" in text:
        return (
            "Suggested roadmap: strengthen Java basics, learn SQL, build FastAPI/Spring Boot APIs, "
            "connect with PostgreSQL, deploy one project, then practice interview questions."
        )

    if "skill" in text or "gap" in text:
        return (
            "Your likely skill gaps can be found by comparing your target role with your current skills. "
            "For backend roles, focus on API development, database design, authentication, deployment, and DSA."
        )

    return (
        "I can help with resume review, interview preparation, career roadmap, "
        "skill gap analysis, project explanation, and placement preparation."
    )


@router.post("/")
async def ai_chat(
    data: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_message = AIChatMessage(
        user_id=current_user.id,
        role="user",
        message=data.prompt
    )

    answer = generate_ai_answer(data.prompt)

    ai_message = AIChatMessage(
        user_id=current_user.id,
        role="assistant",
        message=answer
    )

    db.add(user_message)
    db.add(ai_message)

    await db.commit()

    return {
        "answer": answer
    }


@router.get("/history")
async def get_ai_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AIChatMessage)
        .where(AIChatMessage.user_id == current_user.id)
        .order_by(AIChatMessage.created_at)
    )

    messages = result.scalars().all()

    return [
        {
            "id": msg.id,
            "role": msg.role,
            "message": msg.message,
            "created_at": msg.created_at
        }
        for msg in messages
    ]


@router.delete("/history")
async def clear_ai_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AIChatMessage).where(AIChatMessage.user_id == current_user.id)
    )

    messages = result.scalars().all()

    for msg in messages:
        await db.delete(msg)

    await db.commit()

    return {"message": "AI chat history cleared successfully"}

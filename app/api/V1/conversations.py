from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.V1.users import get_current_user
from app.models.user import User
from app.models.conversation import Conversation, ConversationParticipant, Message
from app.schemas.conversation import ConversationCreate, MessageCreate

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.post("/")
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    other_user_id = str(data.other_user_id)

    # check other user exists
    other_user_result = await db.execute(
        select(User).where(User.id == other_user_id)
    )
    other_user = other_user_result.scalar_one_or_none()

    if not other_user:
        raise HTTPException(status_code=404, detail="Other user not found")

    # create conversation
    conversation = Conversation(
        title=data.title,
        created_by=current_user.id
    )
    db.add(conversation)
    await db.flush()

    # add current user as participant
    participant_1 = ConversationParticipant(
        conversation_id=conversation.id,
        user_id=current_user.id
    )

    # add other user as participant
    participant_2 = ConversationParticipant(
        conversation_id=conversation.id,
        user_id=other_user_id
    )

    db.add(participant_1)
    db.add(participant_2)

    await db.commit()
    await db.refresh(conversation)

    return {
        "message": "Conversation created successfully",
        "conversation_id": conversation.id
    }


@router.get("/")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.user_id == current_user.id
        )
    )
    memberships = result.scalars().all()

    output = []

    for membership in memberships:
        convo_result = await db.execute(
            select(Conversation).where(Conversation.id == membership.conversation_id)
        )
        conversation = convo_result.scalar_one_or_none()

        if conversation:
            output.append({
                "id": conversation.id,
                "title": conversation.title,
                "created_by": conversation.created_by,
                "created_at": conversation.created_at
            })

    return output

@router.get("/{conversation_id}")
async def get_conversation_detail(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    membership_result = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id
        )
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=403, detail="Not part of this conversation")

    convo_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = convo_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_by": conversation.created_by,
        "created_at": conversation.created_at
    }

@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    membership_result = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id
        )
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=403, detail="Not part of this conversation")

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    return [
        {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "author_id": msg.author_id,
            "body": msg.body,
            "created_at": msg.created_at
        }
        for msg in messages
    ]

@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    membership_result = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id
        )
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=403, detail="Not part of this conversation")

    message = Message(
        conversation_id=conversation_id,
        author_id=current_user.id,
        body=data.body
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    return {
        "message": "Message sent successfully",
        "message_id": message.id
    }

@router.post("/{conversation_id}/read")
async def mark_conversation_read(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    membership_result = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id
        )
    )
    membership = membership_result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=403, detail="Not part of this conversation")

    membership.last_read_at = datetime.utcnow()
    await db.commit()

    return {"message": "Conversation marked as read"}

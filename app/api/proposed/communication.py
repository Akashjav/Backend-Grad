import asyncio
import time
import hashlib
from collections import deque
from app.core import shared
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.api.proposed.deps import authenticate
from app.db.session import AsyncSessionLocal
from app.schemas.conversation import MessageCreate
from app.services import conversations_service

router = APIRouter(tags=["2.0 Real-time messaging"])


@router.websocket("/ws/conversations/{conversation_id}")
async def websocket(websocket: WebSocket, conversation_id: int):
    # Browser clients send a token in the first frame, not in a logged URL.
    origin = websocket.headers.get("origin")
    from app.core.config import settings

    if origin and origin not in settings.CORS_ORIGINS:
        await websocket.close(code=1008)
        return
    if shared.redis_client:
        try:
            address = websocket.client.host if websocket.client else "unknown"
            if await shared.increment("ws-connect:" + hashlib.sha256(address.encode()).hexdigest()) > settings.IP_RATE_LIMIT:
                await websocket.close(code=1008)
                return
        except Exception:
            await websocket.close(code=1013)
            return
    await websocket.accept()
    try:
        auth = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        token = auth.get("token", "")
        async with AsyncSessionLocal() as db:
            user = await authenticate(token, db)
            await conversations_service.get_conversation_detail(
                conversation_id, user, db
            )
            history = await conversations_service.get_messages(
                conversation_id, user, db
            )
        from fastapi.encoders import jsonable_encoder

        await websocket.send_json(
            jsonable_encoder({"type": "history", "messages": history})
        )
        last_id = max([m["id"] for m in history], default=0)
        sent_times = deque()
        while True:
            try:
                payload = await asyncio.wait_for(websocket.receive_json(), timeout=5)
            except asyncio.TimeoutError:
                payload = None
            if payload is not None:
                now = time.monotonic()
                while sent_times and sent_times[0] <= now - 60:
                    sent_times.popleft()
                sent_times.append(now)
                if len(sent_times) > 60:
                    await websocket.close(code=1008)
                    return
                if shared.redis_client:
                    try:
                        if await shared.increment("ws-send:" + user.id) > 60:
                            await websocket.close(code=1008)
                            return
                    except Exception:
                        await websocket.close(code=1013)
                        return
            async with AsyncSessionLocal() as db:
                user = await authenticate(token, db)
                if payload is not None:
                    if (
                        not isinstance(payload, dict)
                        or not isinstance(payload.get("body"), str)
                        or not 1 <= len(payload["body"].strip()) <= 4000
                    ):
                        await websocket.send_json(
                            {
                                "type": "error",
                                "detail": "Message must contain 1-4000 characters",
                            }
                        )
                        continue
                    await conversations_service.send_message(
                        conversation_id, MessageCreate(body=payload["body"]), user, db
                    )
                messages = await conversations_service.get_messages(
                    conversation_id, user, db, after_id=last_id
                )
            # Release the database connection before waiting on a slow client.
            for message in messages:
                if message["id"] > last_id:
                    await asyncio.wait_for(websocket.send_json(
                        jsonable_encoder({"type": "message", **message})
                    ), timeout=10)
                    last_id = message["id"]
    except WebSocketDisconnect:
        pass
    except (HTTPException, asyncio.TimeoutError, ValueError, TypeError, AttributeError):
        await websocket.close(code=1008)

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from app.core.config import settings
from app.core.request_controls import RequestControls
from app.core import shared


async def test_limits_are_shared_and_fail_closed(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_RATE_LIMIT", 2)
    monkeypatch.setattr(shared, "redis_client", object())
    counts = {}

    async def increment(key):
        counts[key] = counts.get(key, 0) + 1
        return counts[key]

    monkeypatch.setattr(shared, "increment", increment)
    apps = [FastAPI(), FastAPI()]
    for app in apps:
        app.add_middleware(RequestControls)
        @app.post("/api/v1/auth/signin")
        async def signin():
            return {"ok": True}
    async with AsyncClient(transport=ASGITransport(app=apps[0]), base_url="http://test") as first, AsyncClient(transport=ASGITransport(app=apps[1]), base_url="http://test") as second:
        assert (await first.post("/api/v1/auth/signin")).status_code == 200
        assert (await second.post("/api/v1/auth/signin")).status_code == 200
        rejected = await first.post("/api/v1/auth/signin")
        assert rejected.status_code == 429
        assert rejected.headers["retry-after"] == "60"
        assert rejected.headers["x-request-id"]
        async def unavailable(key):
            raise ConnectionError("secret Redis URL must never leak")
        monkeypatch.setattr(shared, "increment", unavailable)
        response = await second.post("/api/v1/auth/signin")
        assert response.status_code == 503
        assert "secret" not in response.text


async def test_body_limit_including_chunked_requests(monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
    monkeypatch.setattr(settings, "MAX_REQUEST_BYTES", 20)
    app = FastAPI()
    app.add_middleware(RequestControls)
    @app.post("/echo")
    async def echo():
        return {"ok": True}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/echo", content=b"a" * 21)).status_code == 413
        async def chunks():
            yield b"a" * 11
            yield b"b" * 11
        assert (await client.post("/echo", content=chunks())).status_code == 413
        assert (await client.post("/echo", content=b"ok")).status_code == 200


async def test_production_legacy_signup_cannot_bypass_verification(env, monkeypatch):
    from app.services.auth_service import legacy_registration_guard
    from fastapi import HTTPException
    import pytest
    monkeypatch.setattr(settings, "APP_ENV", "production")
    with pytest.raises(HTTPException) as error:
        legacy_registration_guard()
    assert error.value.status_code == 410


async def test_message_cursor_is_bounded(env):
    from app.models.conversation import Message
    client, factory, users, headers, _ = env
    created = await client.post("/api/v1/conversations", headers=headers["student"], json={"other_user_id": users["alumni"]})
    cid = created.json()["conversation_id"]
    async with factory() as db:
        db.add_all([Message(conversation_id=cid, author_id=users["student"], body=str(i)) for i in range(205)])
        await db.commit()
    endpoint = f"/api/v1/conversations/{cid}/messages"
    latest = (await client.get(endpoint, headers=headers["student"])).json()
    assert len(latest) == 100 and latest[-1]["body"] == "204"
    older = (await client.get(endpoint, headers=headers["student"], params={"before_id": latest[0]["id"]})).json()
    assert len(older) == 100 and older[-1]["id"] < latest[0]["id"]
    assert (await client.get(endpoint, headers=headers["industry"])).status_code == 403
    assert (await client.get(endpoint, headers=headers["student"], params={"limit": 9999})).status_code == 422


async def test_tokens_require_expiry_and_professional_changes_reset_verification(env):
    from app.core.tokens import jwt
    from app.models.platform import DomainProfile
    client, factory, users, headers, _ = env
    token = jwt.encode({"sub": users["student"]}, settings.JWT_SECRET_KEY, algorithm="HS256")
    for path in ["/api/me", "/api/v1/auth/me"]:
        assert (await client.get(path, headers={"Authorization": "Bearer " + token})).status_code == 401
    async with factory() as db:
        profile = await db.get(DomainProfile, users["academician"])
        profile.verified = True
        await db.commit()
    response = await client.patch("/api/v1/auth/me", headers=headers["academician"], json={"organization_name": "New organization"})
    assert response.status_code == 200
    assert response.json()["profile"]["verified"] is False

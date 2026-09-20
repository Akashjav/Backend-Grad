import hashlib
import logging
import time
import uuid
from collections import defaultdict, deque
from starlette.responses import JSONResponse
from app.core.tokens import jwt, JWTError
from app.core.config import settings
from app.core import shared

logger = logging.getLogger("gradalumni.requests")
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)
logger.propagate = False
AUTH_ACTIONS = {"signin", "signup", "signup-student", "signup-alumni", "verify-otp", "forgot-password", "reset-password", "resend-otp", "refresh"}


class RequestControls:
    """ASGI controls; production quotas use Redis, local fallback is development-only."""
    def __init__(self, app):
        self.app = app
        self.requests = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id, started = uuid.uuid4().hex, time.monotonic()
        scope.setdefault("state", {})["request_id"] = request_id
        status = 500

        async def wrapped_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = list(message.get("headers", []))
                headers += [(b"x-request-id", request_id.encode()), (b"x-content-type-options", b"nosniff"), (b"referrer-policy", b"no-referrer")]
                if settings.APP_ENV == "production":
                    headers.append((b"strict-transport-security", b"max-age=31536000"))
                if scope["path"].startswith("/api/"):
                    headers.append((b"cache-control", b"no-store"))
                message["headers"] = headers
            await send(message)

        async def reject(code, detail):
            logger.warning("request rejected id=%s status=%s", request_id, code)
            await JSONResponse({"detail": detail, "request_id": request_id}, code,
                headers={"Retry-After": "60"} if code == 429 else {})(scope, receive, wrapped_send)

        headers = dict(scope.get("headers", []))
        length = headers.get(b"content-length")
        if length:
            try:
                if int(length) < 0:
                    raise ValueError()
                if int(length) > settings.MAX_REQUEST_BYTES:
                    return await reject(413, "Request body too large")
            except ValueError:
                return await reject(400, "Invalid content length")
        path = scope["path"].rstrip("/")
        if settings.RATE_LIMIT_ENABLED and path not in {"/health", "/api/health", "/ready"} and scope["method"] != "OPTIONS":
            ip = (scope.get("client") or ("unknown",))[0]
            auth = path.startswith(("/api/auth/", "/api/v1/auth/")) and path.split("/")[-1] in AUTH_ACTIONS
            identity, limit = "ip:" + ip, settings.AUTH_RATE_LIMIT if auth else settings.IP_RATE_LIMIT
            if not auth:
                bearer = headers.get(b"authorization", b"").decode("latin1")
                if bearer.startswith("Bearer "):
                    try:
                        claims = jwt.decode(bearer[7:], settings.JWT_SECRET_KEY, algorithms=["HS256"], options={"require": ["exp", "sub"]})
                        if claims.get("sub"):
                            identity, limit = "user:" + str(claims["sub"]), settings.USER_RATE_LIMIT
                    except JWTError:
                        pass
            key = ("auth:" if auth else "api:") + hashlib.sha256(identity.encode()).hexdigest()
            if shared.redis_client:
                try:
                    count = await shared.increment(key)
                except Exception:
                    return await reject(503, "Request protection temporarily unavailable")
            else:
                now = time.monotonic()
                bucket = self.requests[key]
                while bucket and bucket[0] <= now - 60:
                    bucket.popleft()
                # Do not grow a denied caller's in-memory queue indefinitely.
                count = len(bucket) + 1
                if count <= limit:
                    bucket.append(now)
                if len(self.requests) > 10000:
                    self.requests = defaultdict(deque, {k: v for k, v in self.requests.items() if v and v[-1] > now - 60})
            if count > limit:
                return await reject(429, "Too many requests")
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > settings.MAX_REQUEST_BYTES:
                return await reject(413, "Request body too large")
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        try:
            await self.app(scope, replay, wrapped_send)
        finally:
            logger.info("request id=%s method=%s route=%s status=%s duration_ms=%.1f", request_id,
                scope["method"], getattr(scope.get("route"), "path", "unmatched"), status, (time.monotonic() - started) * 1000)

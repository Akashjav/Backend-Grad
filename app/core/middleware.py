import os
import time
import uuid
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RequestControls(BaseHTTPMiddleware):
    """Per-process basic abuse control; use a shared gateway limiter when scaled."""

    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(deque)

    async def dispatch(self, request, call_next):
        request_id = uuid.uuid4().hex
        if os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true":
            auth = request.url.path.startswith(("/api/v1/auth", "/api/auth"))
            key = (request.client.host if request.client else "unknown", auth)
            now = time.monotonic()
            bucket = self.requests[key]
            while bucket and bucket[0] <= now - 60:
                bucket.popleft()
            if len(bucket) >= (20 if auth else 300):
                return JSONResponse(
                    {"detail": "Too many requests", "request_id": request_id},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
            bucket.append(now)
            if len(self.requests) > 10000:
                self.requests = defaultdict(
                    deque,
                    {k: v for k, v in self.requests.items() if v and v[-1] > now - 60},
                )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

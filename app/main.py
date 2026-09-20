import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
import logging
from sqlalchemy.exc import IntegrityError, TimeoutError as PoolTimeout, OperationalError
from sqlalchemy import text
from app.db.session import engine
from app.core import shared
from starlette.middleware.trustedhost import TrustedHostMiddleware


@asynccontextmanager
async def lifespan(app):
    yield
    await engine.dispose()
    if shared.redis_client:
        await shared.redis_client.aclose()

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.api.V1.auth import router as auth_router
from app.api.V1.users import router as users_router
from app.api.V1.alumni import router as alumni_router
from app.api.V1.communities import router as communities_router
from app.api.V1.events import router as events_router
from app.api.V1.conversations import router as conversations_router
from app.api.V1.notifications import router as notifications_router
from app.api.V1.settings import router as settings_router
from app.api.V1.dashboard import router as dashboard_router
from app.api.V1.admin import router as admin_router
from app.api.V1.student_documents import router as student_documents_router
from app.api.V1.mentorship import router as mentorship_router
from app.api.V1.jobs import router as jobs_router
from app.api.V1.community_posts import router as community_posts_router
from app.api.V1.subscriptions import router as subscriptions_router
from app.api.V1.ai_chat import router as ai_chat_router

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0", lifespan=lifespan,
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,
)




@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).error("Unhandled request id=%s error_type=%s", getattr(request.state, "request_id", "unknown"), type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


@app.get("/")
async def root():
    return {
        "message": "Alumni Connect API is running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/health")
async def api_health():
    return {"status": "healthy"}


@app.get("/ready", include_in_schema=False)
async def ready():
    try:
        async with asyncio.timeout(3):
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                revision = (await connection.execute(text("SELECT version_num FROM alembic_version"))).scalar()
                if revision != "ga20_production":
                    raise RuntimeError("Database migrations are not current")
            if shared.redis_client:
                await shared.redis_client.ping()
    except Exception:
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(alumni_router)
app.include_router(communities_router)
app.include_router(events_router)
app.include_router(conversations_router)
app.include_router(notifications_router)
app.include_router(settings_router)
app.include_router(dashboard_router)
app.include_router(admin_router)
app.include_router(student_documents_router)
app.include_router(mentorship_router)
app.include_router(jobs_router)
app.include_router(community_posts_router)
app.include_router(subscriptions_router)
app.include_router(ai_chat_router)

from app.api.proposed.router import router as proposed_router
app.include_router(proposed_router)
from app.core.request_controls import RequestControls
app.add_middleware(RequestControls)
if settings.APP_ENV == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"], expose_headers=["X-Request-ID", "Retry-After"])


@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "Duplicate or conflicting record"})


@app.exception_handler(PoolTimeout)
@app.exception_handler(OperationalError)
async def database_unavailable(request: Request, exc):
    return JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable"}, headers={"Retry-After": "5"})

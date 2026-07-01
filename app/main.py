import asyncio

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings

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
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": str(request.url.path)
        }
    )


@app.get("/")
def root():
    return {
        "message": "Alumni Connect API is running",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/health")
def api_health():
    return {"status": "healthy"}


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

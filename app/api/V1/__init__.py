from app.api.V1.auth import router as auth_router
from app.api.V1.users import router as users_router

__all__ = ["auth_router", "users_router"]

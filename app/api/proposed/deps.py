from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.tokens import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.db.session import AsyncSessionLocal
from app.core.config import settings
from app.models.user import User
from app.models.platform import AuthSession


async def transaction():
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise


DB = Annotated[AsyncSession, Depends(transaction)]
authorization = HTTPBearer(auto_error=False, scheme_name='VersionedAccessToken')


async def bearer(credentials: HTTPAuthorizationCredentials | None = Depends(authorization)):
    if credentials is None:
        raise HTTPException(401, 'Bearer access token required', headers={'WWW-Authenticate': 'Bearer'})
    return credentials.credentials


async def authenticate(token: str, db):
    try:
        claims = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
        if claims.get("type") != "access" or not claims.get("sid"):
            raise ValueError("Wrong token type")
        result = (await db.execute(select(AuthSession, User).join(User, User.id == AuthSession.user_id)
            .where(AuthSession.id == claims["sid"]))).first()
        session, user = result if result else (None, None)
        if (
            not session
            or session.revoked
            or session.expires_at <= datetime.utcnow()
            or session.user_id != claims.get("sub")
        ):
            raise ValueError("Session expired")
        if not user or not user.is_active:
            raise ValueError("Account unavailable")
        return user
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            401, "Invalid or expired session", headers={"WWW-Authenticate": "Bearer"}
        )


async def current_user(db: DB, token: str = Depends(bearer)):
    return await authenticate(token, db)


Actor = Annotated[User, Depends(current_user)]


def roles(user, *allowed):
    if user.role not in allowed:
        raise HTTPException(403, "Insufficient permissions")


def administrator(user):
    roles(user, "admin", "super_admin")


def owner(user, owner_id):
    if user.id != owner_id and user.role not in {"admin", "super_admin"}:
        raise HTTPException(403, "Resource belongs to another user")

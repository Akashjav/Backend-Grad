from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, update
from app.api.proposed.deps import DB, Actor, bearer
from app.models.user import User
from app.models.platform import AuthSession
from app.repositories.platform import audit
from app.schemas.platform import (
    Signup,
    Signin,
    Refresh,
    Email,
    OTP,
    Reset,
    ProfileUpdate,
)
from app.services import identity_service as service
from app.core.tokens import jwt
from app.core.config import settings
from app.core.workers import password_work

router = APIRouter(prefix="/auth", tags=["2.0 Identity"])


@router.post("/signup", status_code=201)
async def signup(data: Signup, db: DB):
    return await service.signup(db, data)


@router.post("/signin")
async def signin(data: Signin, db: DB):
    user = (
        await db.scalars(select(User).where(User.email == data.email.lower()))
    ).first()
    if (
        not user
        or not user.is_active
        or not await password_work(service.password_valid, data.password, user.password_hash)
    ):
        raise HTTPException(401, "Invalid credentials")
    if not user.is_verified:
        raise HTTPException(403, "Verify your email before signing in")
    return await service.issue_session(db, user)


@router.post("/verify-otp")
async def verify(data: OTP, db: DB):
    user = await service.consume_challenge(db, data.email, data.code, "verify")
    user.is_verified = True
    return {"message": "Email verified"}


@router.post("/refresh")
async def refresh(data: Refresh, db: DB):
    session = (
        await db.scalars(
            select(AuthSession)
            .where(AuthSession.token_hash == service.digest(data.refresh_token))
            .with_for_update()
        )
    ).first()
    if not session or session.revoked or session.expires_at <= datetime.utcnow():
        raise HTTPException(401, "Invalid refresh token")
    user = await db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "Account unavailable")
    session.revoked = True
    return await service.issue_session(db, user)


@router.post("/signout")
async def signout(db: DB, user: Actor, token: str = Depends(bearer)):
    claims = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    session = await db.get(AuthSession, claims["sid"])
    session.revoked = True
    return {"message": "Signed out"}


@router.post("/forgot-password")
async def forgot(data: Email, db: DB):
    user = (
        await db.scalars(
            select(User).where(
                User.email == data.email.lower(), User.is_active.is_(True)
            )
        )
    ).first()
    if user:
        await service.challenge(db, user, "reset")
    return {"message": "If the account exists, a reset email has been queued"}


@router.post('/resend-otp')
async def resend_otp(data: Email, db: DB):
    user = (await db.scalars(select(User).where(User.email == data.email.lower(), User.is_active.is_(True)))).first()
    if user and not user.is_verified:
        await service.challenge(db, user, 'verify')
    return {'message': 'If verification is needed, a verification email has been queued'}


@router.post("/reset-password")
async def reset(data: Reset, db: DB):
    user = await service.consume_challenge(db, data.email, data.code, "reset")
    user.password_hash = await password_work(service.password_hash, data.password)
    await db.execute(
        update(AuthSession).where(AuthSession.user_id == user.id).values(revoked=True)
    )
    return {"message": "Password reset. Sign in again."}


@router.get("/me")
async def me(db: DB, user: Actor):
    return await service.me(db, user)


@router.patch("/me")
async def update_me(data: ProfileUpdate, db: DB, user: Actor):
    return await service.update_profile(db, user, data)


@router.delete("/me")
async def delete_me(db: DB, user: Actor):
    user.is_active = False
    await db.execute(
        update(AuthSession).where(AuthSession.user_id == user.id).values(revoked=True)
    )
    audit(db, user, "identity.deactivate", user.id)
    return {"message": "Account deactivated; retained records remain for audit"}

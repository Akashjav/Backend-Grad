from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.models.user import User
from app.models.profile import Profile
from app.schemas.auth import SignupRequest, SigninRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/signup", response_model=TokenResponse)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role="student",
        is_active=True,
        is_verified=False
    )

    db.add(user)
    await db.flush()

    profile = Profile(
        user_id=user.id,
        display_name=data.display_name
    )

    db.add(profile)
    await db.commit()

    token = create_access_token({"sub": user.id})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/signin", response_model=TokenResponse)
async def signin(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.id})

    return {
        "access_token": token,
        "token_type": "bearer"
    }
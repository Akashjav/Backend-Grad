from fastapi import APIRouter, Depends, HTTPException

from fastapi.security import OAuth2PasswordBearer

from app.core.tokens import jwt, JWTError

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from uuid import UUID

from app.core.config import settings

from app.api.deps import get_db

from app.models.user import User

from app.models.profile import Profile

from app.models.student import StudentProfile

from app.models.alumni import AlumniProfile

from app.services import users_service

router = APIRouter(prefix="/api", tags=["Users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/signin")

async def get_current_user(token: str=Depends(oauth2_scheme), db: AsyncSession=Depends(get_db)):
    return await users_service.get_current_user(token, db)

@router.get('/me')
async def get_me(current_user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return await users_service.get_me(current_user, db)

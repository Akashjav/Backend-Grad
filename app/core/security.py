from datetime import datetime, timedelta
from jose import jwt
import bcrypt
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


def _normalize_password(password: str) -> bytes:
    if not password:
        return b""
    return password.encode("utf-8")[:72]


def hash_password(password: str):
    return bcrypt.hashpw(_normalize_password(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str):
    return bcrypt.checkpw(_normalize_password(password), hashed_password.encode("utf-8"))


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
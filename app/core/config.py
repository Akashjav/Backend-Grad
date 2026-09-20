import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "alumni-connect-api")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "false").lower() == "true"

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    ).split(",")


settings = Settings()
settings.CORS_ORIGINS = [origin.strip() for origin in settings.CORS_ORIGINS if origin.strip()]
settings.ALLOWED_HOSTS = [v.strip() for v in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if v.strip()]
settings.REDIS_URL = os.getenv("REDIS_URL", "")
settings.RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
settings.DOCS_ENABLED = os.getenv("DOCS_ENABLED", "false" if settings.APP_ENV == "production" else "true").lower() == "true"
for name, default, low, high in [
    ("DB_POOL_SIZE", 10, 1, 100), ("DB_MAX_OVERFLOW", 5, 0, 100),
    ("DB_POOL_TIMEOUT", 10, 1, 120), ("DB_COMMAND_TIMEOUT", 30, 1, 300),
    ("AUTH_RATE_LIMIT", 30, 1, 10000), ("USER_RATE_LIMIT", 300, 1, 10000),
    ("IP_RATE_LIMIT", 3000, 1, 100000), ("MAX_REQUEST_BYTES", 6291456, 1024, 20971520),
]:
    value = int(os.getenv(name, str(default)))
    if not low <= value <= high:
        raise RuntimeError(f"{name} is outside its supported range")
    setattr(settings, name, value)
if settings.APP_ENV == "production":
    if len(settings.JWT_SECRET_KEY) < 32 or len(set(settings.JWT_SECRET_KEY)) < 12 or "replace-with" in settings.JWT_SECRET_KEY:
        raise RuntimeError("Production requires a strong random JWT_SECRET_KEY")
    if not settings.DATABASE_URL.startswith(("postgresql://", "postgresql+asyncpg://")):
        raise RuntimeError("Production requires PostgreSQL")
    if not settings.CORS_ORIGINS or any(not v.startswith("https://") or "*" in v for v in settings.CORS_ORIGINS):
        raise RuntimeError("Production CORS requires explicit HTTPS origins")
    if not settings.ALLOWED_HOSTS or "*" in settings.ALLOWED_HOSTS:
        raise RuntimeError("Production requires explicit ALLOWED_HOSTS")
    if settings.SQL_ECHO:
        raise RuntimeError("SQL_ECHO must be false in production")
    if not settings.RATE_LIMIT_ENABLED or not settings.REDIS_URL:
        raise RuntimeError("Production requires shared Redis rate limiting")

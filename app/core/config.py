import os
import json
from urllib.parse import urlsplit
from dotenv import load_dotenv

load_dotenv()


def cors_origins(raw: str, production: bool) -> list[str]:
    message = (
        "Invalid CORS_ORIGINS: set the deployed frontend origin, for example "
        "https://frontend.example.com. Separate multiple origins with commas "
        "or use a JSON array. Production requires HTTPS, without wildcards, "
        "URL paths, query strings or credentials. Configure this in Render Environment."
    )
    try:
        entries = json.loads(raw) if raw.strip().startswith("[") else raw.split(",")
        if not isinstance(entries, list) or any(not isinstance(v, str) for v in entries):
            raise ValueError
        origins = []
        for entry in entries:
            origin = entry.strip().rstrip("/")
            if not origin:
                continue
            if production:
                parsed = urlsplit(origin)
                if (parsed.scheme != "https" or not parsed.hostname or "*" in origin
                        or parsed.username is not None or parsed.password is not None
                        or parsed.path or "?" in origin or "#" in origin
                        or any(c.isspace() for c in origin) or "\\" in origin):
                    raise ValueError
                _ = parsed.port
            if origin not in origins:
                origins.append(origin)
        if production and not origins:
            raise ValueError
        return origins
    except (ValueError, TypeError):
        raise RuntimeError(message) from None


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

    CORS_ORIGINS: list[str] = cors_origins(os.getenv(
        "CORS_ORIGINS",
        "" if APP_ENV == "production" else "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    ), APP_ENV == "production")


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
    if not settings.ALLOWED_HOSTS or "*" in settings.ALLOWED_HOSTS:
        raise RuntimeError("Production requires explicit ALLOWED_HOSTS")
    if settings.SQL_ECHO:
        raise RuntimeError("SQL_ECHO must be false in production")
    if not settings.RATE_LIMIT_ENABLED or not settings.REDIS_URL:
        raise RuntimeError("Production requires shared Redis rate limiting")

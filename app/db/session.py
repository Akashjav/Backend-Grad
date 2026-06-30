from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.engine import make_url

from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if not url.startswith("postgresql+asyncpg://"):
        return url

    parsed_url = make_url(url)
    query = dict(parsed_url.query)
    sslmode = query.pop("sslmode", None)
    if sslmode is None:
        return url
    if isinstance(sslmode, tuple):
        sslmode = sslmode[-1]
    query.setdefault("ssl", sslmode)

    return parsed_url.set(query=query).render_as_string(hide_password=False)


DATABASE_URL = _normalize_database_url(DATABASE_URL)

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.SQL_ECHO,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

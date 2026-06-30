from logging.config import fileConfig
from pathlib import Path
import sys


_project_root = Path(__file__).resolve().parents[1]
_venv_site_packages = _project_root / "venv" / "Lib" / "site-packages"
if _venv_site_packages.exists():
    sys.path.insert(0, str(_venv_site_packages))

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from app.models.user import Base
from app.db.base import *
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

def _normalize_database_url(url: str | None) -> str | None:
    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if not url or not url.startswith("postgresql+asyncpg://"):
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


# Prefer DATABASE_URL from environment (used by app). Online migrations can run
# with async drivers; offline SQL rendering uses the sync URL variant below.
_db_url = _normalize_database_url(
    os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
)
if _db_url is None:
    _sync_db_url = None
else:
    _sync_db_url = _db_url.replace("+asyncpg", "+psycopg").replace("+aiopg", "+psycopg")
    if _sync_db_url.startswith("postgresql://"):
        _sync_db_url = _sync_db_url.replace("postgresql://", "postgresql+psycopg://", 1)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = _sync_db_url or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    _chosen_url = _sync_db_url or config.get_main_option("sqlalchemy.url")
    if _chosen_url is None or _chosen_url.startswith("driver://"):
        raise RuntimeError(
            "No valid database URL found for Alembic. Set the DATABASE_URL environment variable "
            "or update sqlalchemy.url in alembic.ini to a valid driver URL (e.g. postgresql://user:pass@host/db)."
        )

    if _db_url and ("+asyncpg" in _db_url or "+aiopg" in _db_url):
        asyncio.run(run_async_migrations(_db_url))
        return

    connectable = create_engine(
        _chosen_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(url: str) -> None:
    connectable = create_async_engine(url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

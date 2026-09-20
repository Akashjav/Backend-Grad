import os
import uuid

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-never-used-in-production-123456789"
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.proposed.deps import transaction
from app.api.deps import get_db
from app.models.user import Base, User
from app.db import base  # noqa: F401 - register all tables
from app.models.subscription import Domain
from app.models.platform import DomainProfile
from app.models.profile import Profile
from app.services.identity_service import password_hash, issue_session


@pytest_asyncio.fixture
async def env(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCUMENT_STORAGE_PATH", str(tmp_path / "private"))
    postgres_url = os.getenv("TEST_DATABASE_URL")
    schema = "test_" + uuid.uuid4().hex
    if postgres_url:
        admin_engine = create_async_engine(postgres_url)
        async with admin_engine.begin() as connection:
            await connection.execute(text(f"CREATE SCHEMA {schema}"))
        engine = create_async_engine(
            postgres_url, connect_args={"server_settings": {"search_path": schema}}
        )
    else:
        engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)

        @event.listens_for(engine.sync_engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override():
        async with factory() as db:
            try:
                yield db
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    app.dependency_overrides[transaction] = override
    app.dependency_overrides[get_db] = override
    async with factory() as db:
        domain = Domain(name="Engineering")
        db.add(domain)
        await db.flush()
        users, headers = {}, {}
        for role in [
            "super_admin",
            "student",
            "industry",
            "academician",
            "institution_admin",
            "alumni",
        ]:
            user = User(
                email=f"{role}@example.com",
                password_hash=password_hash("Password123!"),
                role=role,
                is_verified=True,
            )
            db.add(user)
            await db.flush()
            db.add(Profile(user_id=user.id, display_name=role))
            db.add(
                DomainProfile(
                    user_id=user.id, domain_id=domain.id, interests=["backend"]
                )
            )
            tokens = await issue_session(db, user)
            headers[role] = {"Authorization": "Bearer " + tokens["access_token"]}
            users[role] = user.id
        await db.commit()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client, factory, users, headers, domain.id
    app.dependency_overrides.clear()
    await engine.dispose()
    if postgres_url:
        async with admin_engine.begin() as connection:
            await connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        await admin_engine.dispose()

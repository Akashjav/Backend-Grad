"""Create synthetic fixtures only in the dedicated local gradalumni_load database."""
import asyncio
import json
import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.session import AsyncSessionLocal, engine
from app.models.user import User
from app.models.profile import Profile
from app.models.subscription import Domain
from app.models.platform import DomainProfile, AuthSession, Skill, StudentSkill, Opportunity, Requirement
from app.db import base  # noqa: F401
from app.core.tokens import jwt
from app.core.config import settings
from sqlalchemy import select


async def main():
    parsed = urlsplit(settings.DATABASE_URL)
    if parsed.hostname not in {"localhost", "127.0.0.1"} or parsed.path != "/gradalumni_load":
        raise SystemExit("Refusing: fixtures require local database gradalumni_load")
    async with AsyncSessionLocal() as db:
        if (await db.scalars(select(User.id).limit(1))).first():
            raise SystemExit("Fixture database must be empty; reuse existing tmp/load-users.json")
        domain = Domain(name="Load test engineering")
        db.add(domain)
        await db.flush()
        skills = [Skill(domain_id=domain.id, name=f"Test skill {i}") for i in range(10)]
        users = [User(id=str(uuid.uuid4()), email=f"load-{i}@example.invalid", password_hash="disabled-load-account", role="student", is_active=True, is_verified=True) for i in range(1000)]
        db.add_all(skills + users)
        await db.flush()
        tokens = []
        for user in users:
            sid = uuid.uuid4().hex
            db.add(Profile(user_id=user.id, display_name="Synthetic student"))
            db.add(DomainProfile(user_id=user.id, domain_id=domain.id))
            db.add(AuthSession(id=sid, user_id=user.id, token_hash=uuid.uuid4().hex, expires_at=datetime.utcnow()+timedelta(hours=2)))
            db.add_all([StudentSkill(user_id=user.id, skill_id=s.id, score=60, evidence_type="assessment_verified") for s in skills])
            tokens.append(jwt.encode({"sub": user.id, "sid": sid, "type": "access", "exp": datetime.utcnow()+timedelta(hours=2)}, settings.JWT_SECRET_KEY, algorithm="HS256"))
        for i in range(25):
            opportunity = Opportunity(owner_id=users[0].id, domain_id=domain.id, title=f"Synthetic internship {i}", description="Load test fixture", status="published", approved=True)
            db.add(opportunity)
            await db.flush()
            db.add_all([Requirement(opportunity_id=opportunity.id, skill_id=s.id, level=70) for s in skills])
        await db.commit()
    Path("tmp/load-users.json").write_text(json.dumps(tokens))
    print("Created 1000 synthetic identities, 10000 skill scores and 25 opportunities; tokens saved privately in tmp.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

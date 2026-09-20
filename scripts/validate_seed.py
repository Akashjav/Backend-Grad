"""Validate demo seed repeatability in a disposable database only."""
import asyncio
import os
import secrets
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select, func
from httpx import AsyncClient, ASGITransport
from app.db.seed import run
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.platform import Skill, Opportunity, Requirement
from app.main import app


async def counts():
    async with AsyncSessionLocal() as db:
        return [await db.scalar(select(func.count()).select_from(model)) for model in [User, Skill, Opportunity, Requirement]]


async def main():
    if os.getenv('ALLOW_DISPOSABLE_SEED_TEST') != 'yes':
        raise SystemExit('Set ALLOW_DISPOSABLE_SEED_TEST=yes only against a disposable database')
    os.environ.setdefault('DEMO_PASSWORD', secrets.token_urlsafe(24))
    await run(demo=True)
    first = await counts()
    await run(demo=True)
    assert await counts() == first
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        for domain in ['engineering', 'medical', 'ayush']:
            login = await client.post('/api/v1/auth/signin', json={'email': f'student.{domain}@demo.gradalumni.example.com', 'password': os.environ['DEMO_PASSWORD']})
            assert login.status_code == 200, login.text
            headers = {'Authorization': 'Bearer ' + login.json()['access_token']}
            matches = await client.get('/api/v1/recommendations/opportunities', headers=headers)
            assert matches.status_code == 200 and len(matches.json()) >= 2, matches.text
            print(domain + ': login and cross-domain recommendations passed')
    print('Seed is repeatable. Row counts (users, skills, opportunities, requirements):', first)


if __name__ == '__main__':
    asyncio.run(main())

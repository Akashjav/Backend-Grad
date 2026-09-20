from sqlalchemy import event
from app.models.platform import Skill, Opportunity, Requirement, StudentSkill
from app.models.user import User
from app.services.matching_service import match, recommendations


async def test_batched_recommendations_match_individual_scores_with_constant_queries(env):
    _, factory, users, _, domain = env
    async with factory() as db:
        skill = Skill(domain_id=domain, name="Batch scoring")
        db.add(skill)
        await db.flush()
        db.add(StudentSkill(user_id=users["student"], skill_id=skill.id, score=65, evidence_type="assessment_verified"))
        opportunities = []
        for i in range(20):
            row = Opportunity(owner_id=users["industry"], domain_id=domain, title=f"Opportunity {i}", description="Query count test", status="published")
            db.add(row)
            await db.flush()
            db.add(Requirement(opportunity_id=row.id, skill_id=skill.id, level=70+i))
            opportunities.append(row)
        await db.commit()
        user = await db.get(User, users["student"])
        count = 0
        def track(*args):
            nonlocal count
            count += 1
        engine = db.bind.sync_engine
        event.listen(engine, "before_cursor_execute", track)
        try:
            batched = await recommendations(db, user)
        finally:
            event.remove(engine, "before_cursor_execute", track)
        assert count <= 6
        by_id = {r["opportunity_id"]: r for r in batched}
        for opportunity in opportunities:
            expected = await match(db, user.id, opportunity)
            assert by_id[opportunity.id] == expected

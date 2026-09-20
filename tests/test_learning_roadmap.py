from app.models.platform import (
    Skill, Opportunity, Requirement, StudentSkill, LearningResource,
    LearningProgress, Assessment, DomainProfile,
)


async def test_roadmap_uses_live_evidence_and_protects_eligibility(env):
    client, factory, users, headers, domain = env
    async with factory() as db:
        skill = Skill(domain_id=domain, name="Docker")
        db.add(skill)
        await db.flush()
        opportunity = Opportunity(owner_id=users["industry"], domain_id=domain,
            title="Cloud internship", description="Learn deployment", status="published", approved=True)
        db.add(opportunity)
        await db.flush()
        db.add(Requirement(opportunity_id=opportunity.id, skill_id=skill.id, level=70))
        evidence = StudentSkill(user_id=users["student"], skill_id=skill.id, score=95, evidence_type="self_declared")
        db.add(evidence)
        resource = LearningResource(skill_id=skill.id, title="Deployment lab", url="https://example.com/lab", target_level=80)
        db.add(resource)
        db.add(Assessment(domain_id=domain, title="Docker check", questions=[{"skill_id": skill.id, "answer": 0}]))
        for role in ["alumni", "academician"]:
            db.add(StudentSkill(user_id=users[role], skill_id=skill.id, score=90, evidence_type="assessment"))
        hidden = await db.get(DomainProfile, users["academician"])
        hidden.discoverable = False
        await db.commit()
        oid, sid, rid = opportunity.id, skill.id, resource.id
    endpoint = f"/api/v1/students/me/learning-roadmap?opportunity_id={oid}"
    response = await client.get(endpoint, headers=headers["student"])
    assert response.status_code == 200
    step = response.json()["steps"][0]
    assert step["current_level"] == 0  # self-reported claims cannot close a gap
    assert step["gap_score"] == 70
    assert [m["mentor_id"] for m in step["mentors"]] == [users["alumni"]]
    assert "answer" not in str(step["assessments"])
    assert (await client.get(endpoint, headers=headers["industry"])).status_code == 403
    assert (await client.get(endpoint)).status_code == 401
    async with factory() as db:
        db.add(LearningProgress(user_id=users["student"], resource_id=rid, status="completed"))
        await db.commit()
    step = (await client.get(endpoint, headers=headers["student"])).json()["steps"][0]
    assert step["status"] == "ready_for_reassessment"
    assert step["gap_score"] == 70
    async with factory() as db:
        evidence = await db.get(StudentSkill, evidence.id)
        evidence.score, evidence.evidence_type = 80, "assessment"
        await db.commit()
    plan = (await client.get(endpoint, headers=headers["student"])).json()
    assert plan["steps"] == []
    assert plan["status"] == "target_skills_met"
    async with factory() as db:
        profile = await db.get(DomainProfile, users["student"])
        profile.domain_id = None
        await db.commit()
    assert (await client.get(endpoint, headers=headers["student"])).status_code == 403
    async with factory() as db:
        opportunity = await db.get(Opportunity, oid)
        opportunity.cross_domain = True
        await db.commit()
    assert (await client.get(endpoint, headers=headers["student"])).status_code == 200
    async with factory() as db:
        opportunity = await db.get(Opportunity, oid)
        opportunity.status = "draft"
        await db.commit()
    assert (await client.get(endpoint, headers=headers["student"])).status_code == 404

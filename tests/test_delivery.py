from io import BytesIO
from pypdf import PdfReader
from app.models.platform import Opportunity, Application, Feedback, Skill, Collaboration, CollaborationMember, DomainProfile, Institution, StudentSkill
from sqlalchemy import select


async def test_certificate_requires_evaluation_and_supports_revocation(env):
    client, factory, users, headers, domain = env
    async with factory() as db:
        opportunity = Opportunity(owner_id=users["industry"], domain_id=domain, title="Research delivery", description="Supervised project")
        db.add(opportunity)
        await db.flush()
        application = Application(opportunity_id=opportunity.id, student_id=users["student"], status="started")
        db.add(application)
        await db.commit()
        aid = application.id
    endpoint = f"/api/v1/applications/{aid}/certificate"
    assert (await client.post(endpoint, headers=headers["student"])).status_code == 403
    assert (await client.post(endpoint, headers=headers["industry"])).status_code == 409
    async with factory() as db:
        application = await db.get(Application, aid)
        application.status = "completed"
        await db.commit()
    assert (await client.post(endpoint, headers=headers["industry"])).status_code == 409
    async with factory() as db:
        db.add(Feedback(application_id=aid, reviewer_id=users["industry"], scores={}, comment="Reviewed"))
        await db.commit()
    response = await client.post(endpoint, headers=headers["industry"])
    assert response.status_code == 200, response.text
    certificate = response.json()
    assert (await client.post(endpoint, headers=headers["industry"])).json()["id"] == certificate["id"]
    download = f"/api/v1/certificates/{certificate['id']}/download"
    pdf = await client.get(download, headers=headers["student"])
    assert pdf.status_code == 200
    assert "Research delivery" in PdfReader(BytesIO(pdf.content)).pages[0].extract_text()
    assert (await client.get(download, headers=headers["alumni"])).status_code == 403
    verify = f"/api/v1/certificates/verify/{certificate['code']}"
    assert (await client.get(verify, headers=headers["alumni"])).json()["valid"] is True
    assert (await client.get(verify)).status_code == 401
    revoke = f"/api/v1/certificates/{certificate['id']}/revoke"
    assert (await client.post(revoke, headers=headers["student"], json={"reason": "Incorrect"})).status_code == 403
    assert (await client.post(revoke, headers=headers["industry"], json={"reason": "Incorrect completion"})).status_code == 200
    assert (await client.get(verify, headers=headers["alumni"])).json()["valid"] is False
    pdf = await client.get(download, headers=headers["student"])
    assert "REVOKED" in PdfReader(BytesIO(pdf.content)).pages[0].extract_text()


async def test_milestone_requires_membership_and_independent_review(env):
    client, factory, users, headers, domain = env
    async with factory() as db:
        opp = Opportunity(owner_id=users["industry"], domain_id=domain, title="Team project", description="Evidence", kind="project")
        db.add(opp)
        await db.flush()
        team = Collaboration(owner_id=users["industry"], opportunity_id=opp.id, title="Research team")
        db.add(team)
        await db.flush()
        db.add(CollaborationMember(collaboration_id=team.id, user_id=users["student"], status="active"))
        await db.commit()
        cid = team.id
    endpoint = f"/api/v1/collaborations/{cid}/milestones"
    assert (await client.get(endpoint, headers=headers["alumni"])).status_code == 403
    response = await client.post(endpoint, headers=headers["industry"], json={"title": "Prototype"})
    assert response.status_code == 201, response.text
    mid = response.json()["id"]
    assert (await client.patch(f"/api/v1/collaborations/{cid}", headers=headers["industry"], json={"status": "completed", "progress": 100})).status_code == 409
    payload = {"evidence_url": "https://example.com/prototype", "submission_note": "Ready for review"}
    assert (await client.post(f"/api/v1/milestones/{mid}/submit", headers=headers["student"], json=payload)).status_code == 200
    review = f"/api/v1/milestones/{mid}/review"
    result = {"status": "accepted", "review_note": "Meets the milestone criteria"}
    assert (await client.post(review, headers=headers["student"], json=result)).status_code == 403
    assert (await client.post(review, headers=headers["industry"], json=result)).status_code == 200
    assert (await client.post(review, headers=headers["industry"], json=result)).status_code == 409
    assert (await client.get(f"/api/v1/collaborations/{cid}", headers=headers["student"])).json()["progress"] == 100


async def test_training_scopes_cohorts_and_snapshots_validated_scores(env):
    client, factory, users, headers, domain = env
    async with factory() as db:
        institution = Institution(name="Campus One")
        other = Institution(name="Campus Two")
        skill = Skill(domain_id=domain, name="Research")
        db.add_all([institution, other, skill])
        await db.flush()
        for role in ["student", "institution_admin"]:
            profile = await db.get(DomainProfile, users[role])
            profile.institution_id = institution.id
        evidence = StudentSkill(user_id=users["student"], skill_id=skill.id, score=95, evidence_type="self_declared")
        db.add(evidence)
        await db.commit()
        sid, other_id = skill.id, other.id
    endpoint = "/api/v1/institutions/me/training-programs"
    response = await client.post(endpoint, headers=headers["institution_admin"], json={"title": "Research bootcamp", "skill_ids": [sid]})
    assert response.status_code == 201, response.text
    pid = response.json()["id"]
    assert (await client.get(endpoint, headers=headers["industry"])).status_code == 403
    enrollment = await client.post(f"/api/v1/training-programs/{pid}/enroll", headers=headers["student"])
    assert enrollment.status_code == 200
    assert enrollment.json()["baseline"][str(sid)]["score"] == 0
    eid = enrollment.json()["id"]
    async with factory() as db:
        evidence = (await db.scalars(select(StudentSkill).where(StudentSkill.user_id == users["student"]))).one()
        evidence.evidence_type, evidence.score = "assessment_verified", 75
        await db.commit()
    complete = f"{endpoint}/{pid}/enrollments/{eid}/complete"
    assert (await client.post(complete, headers=headers["student"])).status_code == 403
    assert (await client.post(complete, headers=headers["institution_admin"])).status_code == 200
    report = (await client.get(f"{endpoint}/{pid}/report", headers=headers["institution_admin"])).json()
    assert report["skill_outcomes"][0]["change"] == 75
    async with factory() as db:
        profile = await db.get(DomainProfile, users["institution_admin"])
        profile.institution_id = other_id
        await db.commit()
    assert (await client.get(f"{endpoint}/{pid}/report", headers=headers["institution_admin"])).status_code == 403


async def test_practical_requires_verified_reviewer_and_exact_rubric(env):
    client, factory, users, headers, domain = env
    async with factory() as db:
        skill = Skill(domain_id=domain, name="Software design")
        db.add(skill)
        await db.commit()
        sid = skill.id
    payload = {"title": "Design review", "domain_id": domain, "instructions": "Submit a design and explain its tradeoffs.", "rubric": {str(sid): "Correctness, clarity and justified tradeoffs"}}
    assert (await client.post("/api/v1/practical-assessments", headers=headers["academician"], json=payload)).status_code == 403
    async with factory() as db:
        profile = await db.get(DomainProfile, users["academician"])
        profile.verified = True
        await db.commit()
    response = await client.post("/api/v1/practical-assessments", headers=headers["academician"], json=payload)
    assert response.status_code == 201, response.text
    pid = response.json()["id"]
    submit = f"/api/v1/practical-assessments/{pid}/submit"
    evidence = {"evidence_url": "https://example.com/design", "note": "Design document"}
    response = await client.post(submit, headers=headers["student"], json=evidence)
    assert response.status_code == 201, response.text
    assert (await client.post(submit, headers=headers["student"], json=evidence)).status_code == 409
    submission_id = response.json()["id"]
    assert (await client.get("/api/v1/practical-submissions", headers=headers["industry"])).json() == []
    review = f"/api/v1/practical-submissions/{submission_id}/review"
    assert (await client.post(review, headers=headers["academician"], json={"scores": {"99999": 80}, "feedback": "Good"})).status_code == 422
    score = {"scores": {str(sid): 80}, "feedback": "Sound design; improve the failure recovery discussion"}
    assert (await client.post(review, headers=headers["student"], json=score)).status_code == 403
    assert (await client.post(review, headers=headers["academician"], json=score)).status_code == 200
    assert (await client.post(review, headers=headers["academician"], json=score)).status_code == 409
    async with factory() as db:
        skill = (await db.scalars(select(StudentSkill).where(StudentSkill.user_id == users["student"], StudentSkill.skill_id == sid))).one()
        assert skill.score == 80

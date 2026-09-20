from sqlalchemy import select
from app.models.platform import MailOutbox, Institution, DomainProfile


async def test_identity_verification_rotation_and_revocation(env):
    client, factory, users, headers, domain = env
    data = {
        "email": "new@example.com",
        "password": "StrongPassword!",
        "display_name": "New Student",
        "domain_id": domain,
    }
    response = await client.post(
        "/api/v1/auth/signup", json={**data, "role": "super_admin"}
    )
    assert response.status_code == 422
    assert (await client.post("/api/v1/auth/signup", json=data)).status_code == 201
    credentials = {"email": data["email"], "password": data["password"]}
    assert (
        await client.post("/api/v1/auth/signin", json=credentials)
    ).status_code == 403
    async with factory() as db:
        mail = (
            await db.scalars(
                select(MailOutbox).where(MailOutbox.recipient == data["email"])
            )
        ).one()
        code = mail.body.split(": ")[1].splitlines()[0]
    assert (
        await client.post(
            "/api/v1/auth/verify-otp", json={"email": data["email"], "code": code}
        )
    ).status_code == 200
    tokens = (await client.post("/api/v1/auth/signin", json=credentials)).json()
    rotated = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert rotated.status_code == 200
    old = {"Authorization": "Bearer " + tokens["access_token"]}
    assert (await client.get("/api/v1/auth/me", headers=old)).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
    ).status_code == 401
    new = {"Authorization": "Bearer " + rotated.json()["access_token"]}
    assert (await client.get("/api/v1/auth/me", headers=new)).status_code == 200
    assert (await client.post("/api/v1/auth/signout", headers=new)).status_code == 200
    assert (await client.get("/api/v1/auth/me", headers=new)).status_code == 401


async def test_closed_loop_assessment_learning_application_feedback(env):
    c, factory, users, h, domain = env

    async def post(path, data=None, role="super_admin"):
        r = await c.post("/api/v1" + path, json=data, headers=h[role])
        assert r.status_code in (200, 201), (path, r.status_code, r.text)
        return r.json()

    skill = await post(
        "/skills", {"name": "Docker", "domain_id": domain, "category": "technical"}
    )
    sid = skill["id"]
    assessment = await post(
        "/assessments",
        {
            "title": "Containers",
            "domain_id": domain,
            "questions": [
                {
                    "id": "q1",
                    "prompt": "Which packages an app?",
                    "options": ["Container", "Spreadsheet"],
                    "answer": 0,
                    "skill_id": sid,
                }
            ],
        },
    )
    aid = assessment["id"]
    start = await post(f"/assessments/{aid}/start", role="student")
    assert "answer" not in start["questions"][0]
    assert (
        await c.post(
            f"/api/v1/assessments/{aid}/submit",
            json={"attempt_id": start["attempt_id"], "answers": {"q1": 0}},
            headers=h["industry"],
        )
    ).status_code == 403
    await post(
        f"/assessments/{aid}/submit",
        {"attempt_id": start["attempt_id"], "answers": {"q1": 1}},
        "student",
    )
    assert (
        await c.post(
            f"/api/v1/assessments/{aid}/submit",
            json={"attempt_id": start["attempt_id"], "answers": {"q1": 0}},
            headers=h["student"],
        )
    ).status_code == 409
    opp = await post(
        "/opportunities",
        {
            "title": "Backend Internship",
            "description": "Build containers",
            "domain_id": domain,
            "interests": ["backend"],
        },
        "industry",
    )
    oid = opp["id"]
    await post(
        f"/opportunities/{oid}/requirements", {"skill_id": sid, "level": 60}, "industry"
    )
    await post(f"/admin/opportunities/{oid}/approve")
    await post(f"/opportunities/{oid}/publish", role="industry")
    before = await post(f"/matching/opportunities/{oid}/score", role="student")
    assert before["skill_gaps"][0]["gap_score"] == 60
    course = await post(
        "/learning/resources",
        {
            "skill_id": sid,
            "title": "Containers",
            "url": "https://example.com/course",
            "target_level": 80,
        },
    )
    recommendations = (
        await c.get(
            "/api/v1/students/me/learning-recommendations", headers=h["student"]
        )
    ).json()
    assert recommendations[0]["resources"][0]["id"] == course["id"]
    await post(f"/learning/{course['id']}/start", role="student")
    await post(f"/learning/{course['id']}/complete", role="student")
    assert (await post(f"/matching/opportunities/{oid}/score", role="student"))[
        "score"
    ] == before["score"]
    reassess = await post(f"/assessments/{aid}/reassess", role="student")
    await post(
        f"/assessments/{aid}/submit",
        {"attempt_id": reassess["attempt_id"], "answers": {"q1": 0}},
        "student",
    )
    after = await post(f"/matching/opportunities/{oid}/score", role="student")
    assert after["score"] > before["score"] and after["skill_gaps"] == []
    assert (
        await c.put(
            "/api/v1/students/me/skills",
            json={"skills": [{"skill_id": sid, "score": 99}]},
            headers=h["student"],
        )
    ).status_code == 409
    application = await post(f"/opportunities/{oid}/apply", role="student")
    assert (
        await c.post(f"/api/v1/opportunities/{oid}/apply", headers=h["student"])
    ).status_code == 409
    for status in ["shortlisted", "selected", "started", "completed"]:
        response = await c.patch(
            f"/api/v1/applications/{application['id']}/status",
            json={"status": status},
            headers=h["industry"],
        )
        assert response.status_code == 200, response.text
    await post(
        f"/applications/{application['id']}/feedback",
        {"scores": {str(sid): 88}, "comment": "Demonstrated deployment skills"},
        "industry",
    )
    skills = (await c.get("/api/v1/students/me/skills", headers=h["student"])).json()
    assert (
        skills[0]["score"] == 88 and skills[0]["evidence_type"] == "industry_verified"
    )


async def test_institution_scope_and_private_profiles(env):
    c, factory, users, h, domain = env
    async with factory() as db:
        first, second = Institution(name="A"), Institution(name="B")
        db.add_all([first, second])
        await db.flush()
        (
            await db.get(DomainProfile, users["institution_admin"])
        ).institution_id = first.id
        (await db.get(DomainProfile, users["student"])).institution_id = second.id
        await db.commit()
    response = await c.get(
        "/api/v1/institutions/me/analytics", headers=h["institution_admin"]
    )
    assert response.status_code == 200 and response.json()["student_count"] == 0
    assert (
        await c.get("/api/v1/institutions/me/analytics", headers=h["student"])
    ).status_code == 403
    assert (
        await c.patch(
            "/api/v1/auth/me", json={"institution_id": first.id}, headers=h["student"]
        )
    ).status_code == 422
    assert (
        await c.patch(
            "/api/v1/auth/me", json={"discoverable": False}, headers=h["academician"]
        )
    ).status_code == 200
    assert (
        await c.get(f"/api/v1/faculty/{users['academician']}", headers=h["industry"])
    ).status_code == 404


async def test_foundation_routes_and_authorization(env):
    c, factory, users, h, domain = env
    assert (
        await c.get("/api/v1/notifications", headers=h["student"])
    ).status_code == 200
    assert (await c.get("/api/v1/notifications")).status_code == 401
    assert (await c.get("/api/v1/admin/users", headers=h["student"])).status_code == 403
    response = await c.post(
        "/api/v1/conversations",
        json={"other_user_id": users["alumni"]},
        headers=h["student"],
    )
    assert response.status_code == 200, response.text
    cid = response.json()["conversation_id"]
    assert (
        await c.post(
            f"/api/v1/conversations/{cid}/messages",
            json={"body": "Hello"},
            headers=h["student"],
        )
    ).status_code == 200
    assert (
        await c.get(f"/api/v1/conversations/{cid}/messages", headers=h["industry"])
    ).status_code == 403
    response = await c.get(f"/api/v1/conversations/{cid}/messages", headers=h["alumni"])
    assert response.json()[0]["body"] == "Hello"


async def test_document_rejects_fake_pdf(env):
    c, _, _, h, _ = env
    response = await c.post(
        "/api/v1/documents/resume",
        files={"file": ("resume.pdf", b"not a PDF", "application/pdf")},
        headers=h["student"],
    )
    assert response.status_code == 415

from sqlalchemy import select
from app.models.platform import MailOutbox


async def test_cross_domain_team_requires_consent_and_preserves_privacy(env):
    c, factory, users, h, domain = env
    admin, industry, student = h["super_admin"], h["industry"], h["student"]
    medical = (
        await c.post("/api/v1/domains", json={"name": "Medical"}, headers=admin)
    ).json()["id"]
    assert (
        await c.patch("/api/v1/auth/me", json={"domain_id": medical}, headers=student)
    ).status_code == 200
    skill = (
        await c.post(
            "/api/v1/skills",
            json={"name": "Clinical Research", "domain_id": medical},
            headers=admin,
        )
    ).json()["id"]
    await c.post(
        f"/api/v1/admin/users/{users['student']}/skills/verify",
        json={"skill_id": skill, "score": 90},
        headers=admin,
    )
    data = {
        "title": "AI Healthcare",
        "description": "Cross-domain research",
        "domain_id": domain,
        "cross_domain": True,
    }
    project = (await c.post("/api/v1/projects", json=data, headers=industry)).json()
    pid = project["id"]
    r = await c.post(
        f"/api/v1/opportunities/{pid}/requirements",
        json={"skill_id": skill, "level": 70},
        headers=industry,
    )
    assert r.status_code == 201
    await c.post(f"/api/v1/admin/opportunities/{pid}/approve", headers=admin)
    await c.post(f"/api/v1/opportunities/{pid}/publish", headers=industry)
    match = (
        await c.post(f"/api/v1/matching/opportunities/{pid}/score", headers=student)
    ).json()
    assert match["eligible"] and match["strong_matches"][0]["skill_id"] == skill
    collaboration = (
        await c.post(
            "/api/v1/collaborations",
            json={"opportunity_id": pid, "title": "Team"},
            headers=industry,
        )
    ).json()["id"]
    assert (
        await c.post(f"/api/v1/collaborations/{collaboration}/join", headers=student)
    ).status_code == 403
    assert (
        await c.post(
            f"/api/v1/collaborations/{collaboration}/invite",
            json={"user_id": users["student"]},
            headers=industry,
        )
    ).status_code == 200
    assert (
        await c.get(f"/api/v1/collaborations/{collaboration}/skills", headers=student)
    ).status_code == 403
    assert (
        await c.post(f"/api/v1/collaborations/{collaboration}/join", headers=student)
    ).status_code == 200
    result = (
        await c.get(f"/api/v1/collaborations/{collaboration}/skills", headers=student)
    ).json()
    assert result[0]["team_level"] == 90
    assert (
        await c.get(
            f"/api/v1/collaborations/{collaboration}/skills", headers=h["alumni"]
        )
    ).status_code == 403
    response = await c.patch(
        f"/api/v1/collaborations/{collaboration}",
        json={"progress": 100, "status": "completed"},
        headers=student,
    )
    assert response.status_code == 403


async def test_academician_mentorship_and_feedback_state_machine(env):
    c, _, users, h, _ = env
    request = await c.post(
        "/api/v1/mentorship/requests",
        json={"alumni_id": users["academician"], "topic": "Research"},
        headers=h["student"],
    )
    assert request.status_code == 200, request.text
    rid = request.json()["request_id"]
    response = await c.patch(
        f"/api/v1/mentorship/requests/{rid}",
        json={"status": "accepted"},
        headers=h["academician"],
    )
    assert response.status_code == 200, response.text
    assert (
        await c.patch(
            f"/api/v1/mentorship/requests/{rid}",
            json={"status": "rejected"},
            headers=h["academician"],
        )
    ).status_code == 409
    session = await c.post(
        "/api/v1/mentorship/sessions",
        json={
            "request_id": rid,
            "scheduled_at": "2026-09-18T10:00:00",
            "duration_minutes": 30,
        },
        headers=h["academician"],
    )
    assert session.status_code == 200, session.text
    sid = session.json()["session_id"]
    review = {"rating": 5, "comment": "Helpful research guidance"}
    assert (
        await c.post(
            f"/api/v1/mentorship/sessions/{sid}/feedback",
            json=review,
            headers=h["student"],
        )
    ).status_code == 409
    assert (
        await c.patch(
            f"/api/v1/mentorship/sessions/{sid}/complete", headers=h["academician"]
        )
    ).status_code == 200
    assert (
        await c.post(
            f"/api/v1/mentorship/sessions/{sid}/feedback",
            json=review,
            headers=h["student"],
        )
    ).status_code == 200
    assert (
        await c.post(
            f"/api/v1/mentorship/sessions/{sid}/feedback",
            json=review,
            headers=h["student"],
        )
    ).status_code == 409
    assert (
        await c.patch(f"/api/v1/mentorship/sessions/{sid}/cancel", headers=h["student"])
    ).status_code == 409


async def test_reset_invalidates_sessions_and_code_is_single_use(env):
    c, factory, users, h, _ = env
    email = "student@example.com"
    response = await c.post("/api/v1/auth/forgot-password", json={"email": email})
    assert response.status_code == 200
    async with factory() as db:
        mail = (
            await db.scalars(select(MailOutbox).where(MailOutbox.recipient == email))
        ).one()
        code = mail.body.split(": ")[1].splitlines()[0]
    payload = {"email": email, "code": code, "password": "NewStrongPassword!"}
    assert (
        await c.post("/api/v1/auth/reset-password", json=payload)
    ).status_code == 200
    assert (await c.get("/api/v1/auth/me", headers=h["student"])).status_code == 401
    assert (
        await c.post("/api/v1/auth/reset-password", json=payload)
    ).status_code == 400
    assert (
        await c.post(
            "/api/v1/auth/signin",
            json={"email": email, "password": payload["password"]},
        )
    ).status_code == 200


async def test_suspension_and_legacy_session_access(env):
    c, factory, users, h, _ = env
    assert (await c.get("/api/me", headers=h["student"])).status_code == 200
    await c.post(
        f"/api/v1/admin/users/{users['student']}/suspend", headers=h["super_admin"]
    )
    assert (await c.get("/api/v1/auth/me", headers=h["student"])).status_code == 401
    assert (await c.get("/api/me", headers=h["student"])).status_code == 401
    assert (
        await c.post(
            "/api/v1/auth/signin",
            json={"email": "student@example.com", "password": "Password123!"},
        )
    ).status_code == 401

"""Characterize current domain eligibility, including documented isolation gaps.

The gap assertions deliberately describe today's policy; update them when an
approved domain-isolation policy is implemented.
"""


async def test_domain_eligibility_cross_domain_exception_and_owner_access(env):
    c, _, users, h, engineering = env

    async def post(path, data, role="super_admin"):
        response = await c.post("/api/v1" + path, json=data, headers=h[role])
        assert response.status_code in (200, 201), response.text
        return response.json()

    ayush = await post("/domains", {"name": "AYUSH"})
    ayurveda = await post("/disciplines", {"name": "Ayurveda", "domain_id": ayush["id"]})
    skill = await post("/skills", {"name": "Ayurvedic Knowledge", "domain_id": ayush["id"]})
    opportunities = []
    for cross_domain in (False, True):
        opp = await post("/opportunities", {
            "title": "Ayurveda research", "description": "Domain access audit",
            "domain_id": ayush["id"], "discipline_id": ayurveda["id"],
            "cross_domain": cross_domain,
        }, "industry")
        await post(f"/opportunities/{opp['id']}/requirements", {"skill_id": skill["id"], "level": 60}, "industry")
        await post(f"/admin/opportunities/{opp['id']}/approve", {})
        await post(f"/opportunities/{opp['id']}/publish", {}, "industry")
        opportunities.append(opp)

    restricted, shared = opportunities
    denied = await c.post(f"/api/v1/opportunities/{restricted['id']}/apply", headers=h["student"])
    assert denied.status_code == 403
    assert "eligibility" in denied.json()["detail"]
    for opp, eligible in ((restricted, False), (shared, True)):
        score = await post(f"/matching/opportunities/{opp['id']}/score", {}, "student")
        assert score["eligible"] is eligible
        matches = await c.get(f"/api/v1/industry/me/candidate-matches?opportunity_id={opp['id']}", headers=h["industry"])
        assert matches.status_code == 200
        assert (users["student"] in [row["user_id"] for row in matches.json()]) is eligible
    assert (await c.post(f"/api/v1/opportunities/{shared['id']}/apply", headers=h["student"])).status_code == 201
    assert (await c.get(f"/api/v1/opportunities/{shared['id']}/applications", headers=h["alumni"])).status_code == 403
    assert (await c.get("/api/v1/industry/me/profile", headers=h["student"])).status_code == 403

    # Visibility is broader than eligibility: published records are not hidden.
    assert (await c.get(f"/api/v1/opportunities/{restricted['id']}", headers=h["student"])).status_code == 200
    listing = (await c.get("/api/v1/opportunities", headers=h["student"])).json()
    assert restricted["id"] in [row["id"] for row in listing]
    filtered = (await c.get(f"/api/v1/opportunities?domain_id={engineering}", headers=h["student"])).json()
    assert restricted["id"] not in [row["id"] for row in filtered]
    assert shared["id"] in [row["id"] for row in filtered]

    # Current gap: self-service domain changes are not institution-verified.
    changed = await c.patch("/api/v1/students/me/profile", headers=h["student"], json={"domain_id": ayush["id"], "discipline_id": ayurveda["id"]})
    assert changed.status_code == 200, changed.text
    assert (await c.post(f"/api/v1/opportunities/{restricted['id']}/apply", headers=h["student"])).status_code == 201


async def test_assessments_currently_allow_other_domain_students(env):
    c, _, _, h, _ = env
    domain = await c.post("/api/v1/domains", headers=h["super_admin"], json={"name": "AYUSH"})
    assert domain.status_code == 201
    domain_id = domain.json()["id"]
    skill = await c.post("/api/v1/skills", headers=h["super_admin"], json={"name": "Ayurveda", "domain_id": domain_id})
    assert skill.status_code == 201
    assessment = await c.post("/api/v1/assessments", headers=h["super_admin"], json={
        "title": "AYUSH audit assessment", "domain_id": domain_id,
        "questions": [{"id": "q1", "prompt": "Audit fixture", "options": ["A", "B"], "answer": 0, "skill_id": skill.json()["id"]}],
    })
    assert assessment.status_code == 201
    aid = assessment.json()["id"]
    # This is a characterized gap, not a claim of strict domain isolation.
    assert (await c.get(f"/api/v1/assessments/{aid}", headers=h["student"])).status_code == 200
    assert (await c.post(f"/api/v1/assessments/{aid}/start", headers=h["student"])).status_code == 200

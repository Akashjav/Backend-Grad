"""Validate frontend-generated form payloads against real FastAPI models."""
import json
from pathlib import Path

import pytest
from fastapi.routing import APIRoute
from app.main import app


def test_frontend_form_payloads_match_backend_models():
    fixture = Path(__file__).resolve().parents[2] / "Frontend-Grad/tests/generated/frontend-payloads.json"
    if not fixture.exists():
        pytest.skip("Generate frontend fixtures with node --test tests/platform-integration.mjs")
    routes = {}
    for included in app.routes:
        # FastAPI 0.141 keeps included routers as effective route contexts.
        candidates = included.effective_route_contexts() if hasattr(included, "effective_route_contexts") else [included]
        for route in candidates:
            if hasattr(route, "body_field"):
                for method in route.methods or []:
                    routes[f"{method} {route.path}"] = route
    cases = json.loads(fixture.read_text(encoding="utf-8"))
    catalog_path = fixture.parents[2] / "src/lib/generated/apiCatalog.json"
    frontend_operations = {item["key"] for item in json.loads(catalog_path.read_text(encoding="utf-8"))}
    live_operations = {f"{method.upper()} {path}" for path, methods in app.openapi()["paths"].items() for method in methods}
    assert frontend_operations == live_operations
    assert len(cases) > 50
    failures = []
    for case in cases:
        route = routes[case["key"]]
        assert route.body_field is not None, case["key"]
        _, errors = route.body_field.validate(case["payload"], {}, loc=("body",))
        if errors:
            failures.append((case["key"], errors))
    assert not failures, failures


async def test_administrators_can_find_drafts_for_frontend_approval(env):
    client, _, _, headers, domain = env
    response = await client.post("/api/v1/opportunities", headers=headers["industry"], json={
        "domain_id": domain, "title": "Draft for review", "description": "Visible to the owner and platform administrators",
    })
    assert response.status_code == 201
    oid = response.json()["id"]
    for role in ["industry", "super_admin"]:
        listing = await client.get("/api/v1/opportunities", headers=headers[role])
        assert listing.status_code == 200
        assert oid in [row["id"] for row in listing.json()]
    for role in ["student", "alumni", "academician", "institution_admin"]:
        listing = await client.get("/api/v1/opportunities", headers=headers[role])
        assert listing.status_code == 200
        assert oid not in [row["id"] for row in listing.json()]
        assert (await client.get(f"/api/v1/opportunities/{oid}", headers=headers[role])).status_code == 403


async def test_legacy_role_action_revokes_sessions_and_cannot_demote_self(env):
    client, _, users, headers, _ = env
    own = await client.patch(f"/api/admin/users/{users['super_admin']}/role?role=student", headers=headers["super_admin"])
    assert own.status_code == 409
    changed = await client.patch(f"/api/admin/users/{users['student']}/role?role=alumni", headers=headers["super_admin"])
    assert changed.status_code == 200
    assert (await client.get("/api/v1/auth/me", headers=headers["student"])).status_code == 401
    assert (await client.get("/api/me", headers=headers["student"])).status_code == 401


async def test_resume_listing_and_protected_document_review(env, tmp_path, monkeypatch):
    from io import BytesIO
    from pypdf import PdfWriter
    from app.models.student_document import StudentDocument
    from app.services import student_documents_service

    client, factory, users, headers, _ = env
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    pdf = BytesIO()
    writer.write(pdf)
    upload = await client.post("/api/v1/documents/resume", headers=headers["student"], files={"file": ("resume.pdf", pdf.getvalue(), "application/pdf")})
    assert upload.status_code == 201
    documents = await client.get("/api/v1/documents/resume", headers=headers["student"])
    assert documents.status_code == 200
    assert documents.json()[0]["document_id"] == upload.json()["id"]
    assert "storage_name" not in documents.json()[0]
    assert (await client.get("/api/v1/documents/resume", headers=headers["industry"])).json() == []

    root = tmp_path / "proofs"
    root.mkdir()
    monkeypatch.setattr(student_documents_service, "UPLOAD_DIR", str(root))
    path = root / "proof.pdf"
    path.write_bytes(pdf.getvalue())
    async with factory() as db:
        document = StudentDocument(user_id=users["student"], document_type="College ID", file_url=str(path), verification_status="pending")
        db.add(document)
        await db.commit()
        document_id = document.id
    endpoint = f"/api/v1/documents/verification/{document_id}"
    for role in ["student", "super_admin"]:
        response = await client.get(endpoint, headers=headers[role])
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == pdf.getvalue()
    assert (await client.get(endpoint, headers=headers["industry"])).status_code == 403
    queue = await client.get("/api/v1/admin/review-queue", headers=headers["super_admin"])
    assert queue.status_code == 200
    assert queue.json()["student_documents"][0]["document_id"] == document_id
    assert "file_url" not in queue.json()["student_documents"][0]
    assert (await client.get("/api/v1/admin/review-queue", headers=headers["student"])).status_code == 403
    async with factory() as db:
        document = await db.get(StudentDocument, document_id)
        document.file_url = str(tmp_path / "outside.pdf")
        await db.commit()
    (tmp_path / "outside.pdf").write_bytes(pdf.getvalue())
    assert (await client.get(endpoint, headers=headers["super_admin"])).status_code == 404

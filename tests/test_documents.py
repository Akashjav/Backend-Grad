import io
from pypdf import PdfWriter
from app.ai.skill_extractor import extract_skills
from app.models.platform import Skill


async def test_document_storage_ownership_and_delete(env):
    c, _, _, h, _ = env
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    stream = io.BytesIO()
    writer.write(stream)
    response = await c.post(
        "/api/v1/documents/resume",
        files={"file": ("resume.pdf", stream.getvalue(), "application/pdf")},
        headers=h["student"],
    )
    assert response.status_code == 201
    did = response.json()["id"]
    assert (
        await c.get(f"/api/v1/documents/resume/{did}", headers=h["industry"])
    ).status_code == 403
    assert (
        await c.get(f"/api/v1/documents/resume/{did}", headers=h["student"])
    ).content.startswith(b"%PDF-")
    assert (
        await c.post(
            "/api/v1/ai/resume/extract", json={"document_id": did}, headers=h["student"]
        )
    ).status_code == 422
    assert (
        await c.delete(f"/api/v1/documents/resume/{did}", headers=h["student"])
    ).status_code == 200
    assert (
        await c.get(f"/api/v1/documents/resume/{did}", headers=h["student"])
    ).status_code == 404


def test_extractor_normalizes_aliases_without_substring_false_positives():
    skills = [
        Skill(id=1, name="Java", domain_id=1, aliases=[]),
        Skill(id=2, name="AWS", domain_id=1, aliases=["Amazon Web Services"]),
    ]
    result = extract_skills("JavaScript and Amazon Web Services", skills)
    assert [x["skill_id"] for x in result["skills"]] == [2]
    assert result["verified"] is False

from datetime import datetime
from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select
from app.api.proposed.deps import DB, Actor, owner
from app.api.proposed.collaborations import access as collaboration_access
from app.models.platform import Application
from app.models.development import CompletionCertificate, ProjectMilestone
from app.repositories.platform import get, rows, public, add, audit
from app.schemas.development import RevokeCertificate, MilestoneInput, MilestoneSubmission, MilestoneReview
from app.services import certificate_service
from app.core.workers import document_work

router = APIRouter(tags=["2.0 Certificates and milestones"])


@router.post("/applications/{application_id}/certificate")
async def issue(application_id: int, db: DB, user: Actor):
    return public(await certificate_service.issue(db, user, application_id))


@router.get("/certificates/me")
async def mine(db: DB, user: Actor):
    ids = select(Application.id).where(Application.student_id == user.id)
    return [public(c) for c in await rows(db, CompletionCertificate, CompletionCertificate.application_id.in_(ids))]


@router.get("/certificates/verify/{code}")
async def verify(code: str, db: DB, user: Actor):
    certificate = (await db.scalars(select(CompletionCertificate).where(CompletionCertificate.code == code))).first()
    if not certificate:
        raise HTTPException(404, "Certificate not found")
    # Possession of the unguessable code permits verification, not downloading.
    return {"code": certificate.code, "valid": certificate.revoked_at is None,
            "issued_at": certificate.issued_at, "revoked_at": certificate.revoked_at,
            **certificate.snapshot}


@router.get("/certificates/{certificate_id}/download")
async def download(certificate_id: int, db: DB, user: Actor):
    certificate = await get(db, CompletionCertificate, certificate_id)
    await certificate_service.access(db, user, certificate.application_id)
    return Response(await document_work(certificate_service.render_pdf, certificate), media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="certificate-{certificate.id}.pdf"',
                 "Cache-Control": "private, no-store"})


@router.post("/certificates/{certificate_id}/revoke")
async def revoke(certificate_id: int, data: RevokeCertificate, db: DB, user: Actor):
    certificate = await get(db, CompletionCertificate, certificate_id, lock=True)
    _, opportunity = await certificate_service.access(db, user, certificate.application_id)
    owner(user, opportunity.owner_id)
    if not certificate.revoked_at:
        certificate.revoked_at = datetime.utcnow()
        certificate.revocation_reason = data.reason
        audit(db, user, "certificate.revoke", certificate.id, reason=data.reason)
    return public(certificate)


@router.get("/collaborations/{collaboration_id}/milestones")
async def milestones(collaboration_id: int, db: DB, user: Actor):
    await collaboration_access(db, collaboration_id, user)
    return [public(m) for m in await rows(db, ProjectMilestone, ProjectMilestone.collaboration_id == collaboration_id)]


@router.post("/collaborations/{collaboration_id}/milestones", status_code=201)
async def create_milestone(collaboration_id: int, data: MilestoneInput, db: DB, user: Actor):
    collaboration = await collaboration_access(db, collaboration_id, user)
    owner(user, collaboration.owner_id)
    if collaboration.status != "active":
        raise HTTPException(409, "Collaboration is not active")
    row = await add(db, ProjectMilestone, collaboration_id=collaboration_id, **data.model_dump())
    audit(db, user, "milestone.create", row.id)
    return public(row)


async def milestone_access(db, user, milestone_id):
    row = await get(db, ProjectMilestone, milestone_id, lock=True)
    collaboration = await collaboration_access(db, row.collaboration_id, user)
    if collaboration.status != "active":
        raise HTTPException(409, "Collaboration is not active")
    return row, collaboration


@router.post("/milestones/{milestone_id}/submit")
async def submit(milestone_id: int, data: MilestoneSubmission, db: DB, user: Actor):
    row, _ = await milestone_access(db, user, milestone_id)
    if row.status not in {"pending", "changes_requested"}:
        raise HTTPException(409, "Milestone cannot be submitted in its current state")
    row.evidence_url = str(data.evidence_url)
    row.submission_note, row.submitted_by, row.status = data.submission_note, user.id, "submitted"
    audit(db, user, "milestone.submit", row.id)
    return public(row)


@router.post("/milestones/{milestone_id}/review")
async def review(milestone_id: int, data: MilestoneReview, db: DB, user: Actor):
    row, collaboration = await milestone_access(db, user, milestone_id)
    owner(user, collaboration.owner_id)
    if row.submitted_by == user.id:
        raise HTTPException(403, "The submitter cannot review their own evidence")
    if row.status != "submitted":
        raise HTTPException(409, "Submit evidence before reviewing")
    row.status, row.review_note, row.reviewed_by = data.status, data.review_note, user.id
    await db.flush()
    milestones = await rows(db, ProjectMilestone, ProjectMilestone.collaboration_id == collaboration.id, limit=10000)
    collaboration.progress = round(100 * sum(m.status == "accepted" for m in milestones) / len(milestones))
    audit(db, user, "milestone.review", row.id, status=data.status)
    return public(row)

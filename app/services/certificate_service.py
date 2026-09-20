from secrets import token_urlsafe
from fastapi import HTTPException
from sqlalchemy import select
from app.models.platform import Application, Opportunity, Feedback, DomainProfile
from app.models.profile import Profile
from app.models.development import CompletionCertificate
from app.repositories.platform import get, add, audit
from app.api.proposed.deps import owner


async def access(db, user, application_id):
    application = await get(db, Application, application_id)
    opportunity = await get(db, Opportunity, application.opportunity_id)
    if user.id not in {application.student_id, application.mentor_id, opportunity.owner_id}:
        owner(user, opportunity.owner_id)
    return application, opportunity


async def issue(db, user, application_id):
    application = await get(db, Application, application_id, lock=True)
    opportunity = await get(db, Opportunity, application.opportunity_id)
    owner(user, opportunity.owner_id)
    existing = (await db.scalars(select(CompletionCertificate).where(
        CompletionCertificate.application_id == application.id))).first()
    if existing:
        return existing
    if application.status != "completed":
        raise HTTPException(409, "Complete the engagement before issuing a certificate")
    feedback = (await db.scalars(select(Feedback).where(Feedback.application_id == application.id))).first()
    if not feedback:
        raise HTTPException(409, "Record employer or mentor evaluation before issuing a certificate")
    student = (await db.scalars(select(Profile).where(Profile.user_id == application.student_id))).first()
    issuer = (await db.scalars(select(Profile).where(Profile.user_id == opportunity.owner_id))).first()
    if not student or not issuer:
        raise HTTPException(409, "Recipient and issuer profiles are required")
    organization = await db.get(DomainProfile, opportunity.owner_id)
    row = await add(db, CompletionCertificate, application_id=application.id,
        code=token_urlsafe(24), snapshot={"recipient": student.display_name,
            "title": opportunity.title, "kind": opportunity.kind,
            "issuer": (organization.organization_name if organization else None) or issuer.display_name})
    application.certificate = row.code
    audit(db, user, "certificate.issue", row.id)
    return row


def render_pdf(certificate):
    from app.services.certificate_template import render_certificate
    return render_certificate(certificate)

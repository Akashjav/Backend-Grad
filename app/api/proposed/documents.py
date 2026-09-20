from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from app.api.proposed.deps import DB, Actor, owner
from app.models.platform import ResumeDocument, DomainProfile, Skill, StudentSkill
from app.repositories.platform import get, rows, add
from app.schemas.platform import Extraction, ResumeExtraction
from app.services import document_service as storage
from app.ai.skill_extractor import extract_skills
from app.ai.career_assistant import generate_ai_answer
from app.services.competency_service import set_skill
from sqlalchemy import select

router = APIRouter(tags=["2.0 Documents and intelligence"])


@router.get("/documents/verification/{document_id}")
async def verification_document(document_id: int, db: DB, user: Actor):
    from pathlib import Path
    from app.models.student_document import StudentDocument
    from app.services.student_documents_service import UPLOAD_DIR

    row = await get(db, StudentDocument, document_id)
    owner(user, row.user_id)
    path = Path(row.file_url).resolve()
    media = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    if not path.is_relative_to(Path(UPLOAD_DIR).resolve()) or not path.is_file() or path.suffix.lower() not in media:
        raise HTTPException(404, "Stored document unavailable")
    return FileResponse(path, media_type=media[path.suffix.lower()], filename=f"verification-document{path.suffix.lower()}")


@router.get("/documents/resume")
async def my_resumes(db: DB, user: Actor):
    documents = await rows(db, ResumeDocument, ResumeDocument.user_id == user.id)
    return [
        {"id": row.id, "document_id": row.id, "title": f"Resume {row.id}",
         "text_extracted": bool(row.text.strip()),
         "download_url": f"/api/v1/documents/resume/{row.id}"}
        for row in documents
    ]


@router.post("/documents/resume", status_code=201)
async def upload(db: DB, user: Actor, file: UploadFile = File(...)):
    data, text = await storage.read_pdf(file)
    name = await run_in_threadpool(storage.save, data)
    try:
        row = await add(
            db, ResumeDocument, user_id=user.id, storage_name=name, text=text
        )
        await db.commit()
    except Exception:
        storage.path_for(name).unlink(missing_ok=True)
        raise
    return {
        "id": row.id,
        "text_extracted": bool(text.strip()),
        "download_url": f"/api/v1/documents/resume/{row.id}",
    }


@router.get("/documents/resume/{document_id}")
async def download(document_id: int, db: DB, user: Actor):
    row = await get(db, ResumeDocument, document_id)
    owner(user, row.user_id)
    path = storage.path_for(row.storage_name)
    if not path.exists():
        raise HTTPException(404, "Stored document unavailable")
    return FileResponse(path, media_type="application/pdf", filename="resume.pdf")


@router.delete("/documents/resume/{document_id}")
async def delete(document_id: int, db: DB, user: Actor):
    row = await get(db, ResumeDocument, document_id)
    owner(user, row.user_id)
    path = storage.path_for(row.storage_name)
    await db.delete(row)
    await db.commit()
    path.unlink(missing_ok=True)
    return {"deleted": True}


@router.post("/ai/opportunity/extract")
async def extract(data: Extraction, db: DB, user: Actor):
    skills = await rows(
        db,
        Skill,
        *([Skill.domain_id == data.domain_id] if data.domain_id else []),
        limit=10000,
    )
    return extract_skills(data.text, skills)


@router.post("/ai/resume/extract")
async def resume_extract(data: ResumeExtraction, db: DB, user: Actor):
    row = await get(db, ResumeDocument, data.document_id)
    owner(user, row.user_id)
    if not row.text.strip():
        raise HTTPException(
            422, "No text found. Scanned documents require an OCR provider."
        )
    return await extract(Extraction(text=row.text[:50000]), db, user)


@router.post("/ai/resume/map-skills")
async def map_skills(data: ResumeExtraction, db: DB, user: Actor):
    extracted = await resume_extract(data, db, user)
    for skill in extracted["skills"]:
        existing = (
            await db.scalars(
                select(StudentSkill).where(
                    StudentSkill.user_id == user.id,
                    StudentSkill.skill_id == skill["skill_id"],
                )
            )
        ).first()
        if not existing:
            await set_skill(
                db,
                user.id,
                skill["skill_id"],
                0,
                "self_declared",
                {
                    "document_id": data.document_id,
                    "extractor": extracted["provider"],
                    "version": extracted["version"],
                    "matched_term": skill["matched_term"],
                },
            )
    return {
        **extracted,
        "message": "Unverified skill claims recorded without assigning competency scores",
    }


@router.post("/ai/profile/summarize")
async def summarize(db: DB, user: Actor):
    profile = await get(db, DomainProfile, user.id)
    skills = await rows(db, StudentSkill, StudentSkill.user_id == user.id)
    return {
        "summary": f"{user.role} with {len(skills)} recorded skills. Interests: {', '.join(profile.interests)}.",
        "provider": "structured-template-v1",
    }


@router.post("/ai/career-assistant")
async def assistant(data: Extraction, db: DB, user: Actor):
    return {
        "answer": generate_ai_answer(data.text),
        "provider": "local-rule-based",
        "generative_ai": False,
    }

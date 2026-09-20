from datetime import datetime
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.api.proposed.deps import DB, Actor, roles
from app.models.platform import DomainProfile, StudentSkill, Skill, Discipline
from app.models.development import TrainingProgram, TrainingEnrollment
from app.repositories.platform import get, rows, add, public, audit
from app.services.analytics_service import institution_scope
from app.schemas.development import TrainingInput, TrainingStatus

router = APIRouter(tags=["2.0 Institution training"])


async def owned_program(db, user, program_id):
    institution_id = await institution_scope(db, user)
    program = await get(db, TrainingProgram, program_id, lock=True)
    if program.institution_id != institution_id:
        raise HTTPException(403, "Program belongs to another institution")
    return program


async def skill_snapshot(db, student_id, skill_ids):
    skills = await rows(db, StudentSkill, StudentSkill.user_id == student_id,
        StudentSkill.skill_id.in_(skill_ids), StudentSkill.evidence_type != "self_declared", limit=10000)
    scores = {s.skill_id: s for s in skills}
    return {str(sid): {"score": scores[sid].score, "evidence_type": scores[sid].evidence_type,
                      "updated_at": scores[sid].updated_at.isoformat()} if sid in scores else
            {"score": 0, "evidence_type": "missing", "updated_at": None} for sid in skill_ids}


@router.get("/institutions/me/training-programs")
async def programs(db: DB, user: Actor):
    iid = await institution_scope(db, user)
    return [public(p) for p in await rows(db, TrainingProgram, TrainingProgram.institution_id == iid)]


@router.post("/institutions/me/training-programs", status_code=201)
async def create(data: TrainingInput, db: DB, user: Actor):
    iid = await institution_scope(db, user)
    discipline = await get(db, Discipline, data.discipline_id) if data.discipline_id else None
    for sid in set(data.skill_ids):
        skill = await get(db, Skill, sid)
        if discipline and skill.domain_id != discipline.domain_id:
            raise HTTPException(422, "Department training skills must belong to its domain")
    row = await add(db, TrainingProgram, institution_id=iid,
                    **{**data.model_dump(), "skill_ids": sorted(set(data.skill_ids))})
    audit(db, user, "training.create", row.id)
    return public(row)


@router.patch("/institutions/me/training-programs/{program_id}")
async def status(program_id: int, data: TrainingStatus, db: DB, user: Actor):
    program = await owned_program(db, user, program_id)
    program.status = data.status
    audit(db, user, "training.status", program.id, status=data.status)
    return public(program)


@router.get("/students/me/training-programs")
async def available(db: DB, user: Actor):
    roles(user, "student")
    profile = await get(db, DomainProfile, user.id)
    if not profile.institution_id:
        return []
    programs = await rows(db, TrainingProgram, TrainingProgram.institution_id == profile.institution_id)
    enrollments = {e.program_id: e for e in await rows(db, TrainingEnrollment, TrainingEnrollment.student_id == user.id)}
    return [{**public(p), "enrollment": public(enrollments[p.id]) if p.id in enrollments else None}
            for p in programs if p.discipline_id is None or p.discipline_id == profile.discipline_id]


@router.post("/training-programs/{program_id}/enroll")
async def enroll(program_id: int, db: DB, user: Actor):
    roles(user, "student")
    program = await get(db, TrainingProgram, program_id, lock=True)
    profile = await get(db, DomainProfile, user.id)
    if program.institution_id != profile.institution_id or (program.discipline_id and program.discipline_id != profile.discipline_id):
        raise HTTPException(403, "Institution and department eligibility required")
    existing = (await db.scalars(select(TrainingEnrollment).where(
        TrainingEnrollment.program_id == program_id, TrainingEnrollment.student_id == user.id))).first()
    if existing:
        return public(existing)
    if program.status != "open":
        raise HTTPException(409, "Program enrollment is closed")
    row = await add(db, TrainingEnrollment, program_id=program.id, student_id=user.id,
                    baseline=await skill_snapshot(db, user.id, program.skill_ids))
    audit(db, user, "training.enroll", row.id)
    return public(row)


@router.post("/institutions/me/training-programs/{program_id}/enrollments/{enrollment_id}/complete")
async def complete(program_id: int, enrollment_id: int, db: DB, user: Actor):
    program = await owned_program(db, user, program_id)
    enrollment = await get(db, TrainingEnrollment, enrollment_id, lock=True)
    if enrollment.program_id != program.id:
        raise HTTPException(404, "Enrollment not found in program")
    profile = await get(db, DomainProfile, enrollment.student_id)
    if profile.institution_id != program.institution_id:
        raise HTTPException(403, "Student is no longer in this institution")
    if enrollment.status != "completed":
        enrollment.outcome = await skill_snapshot(db, enrollment.student_id, program.skill_ids)
        enrollment.status, enrollment.completed_at = "completed", datetime.utcnow()
        audit(db, user, "training.complete", enrollment.id)
    return public(enrollment)


@router.get("/institutions/me/training-programs/{program_id}/report")
async def report(program_id: int, db: DB, user: Actor):
    program = await owned_program(db, user, program_id)
    members = select(DomainProfile.user_id).where(DomainProfile.institution_id == program.institution_id)
    enrollments = await rows(db, TrainingEnrollment, TrainingEnrollment.program_id == program.id,
                            TrainingEnrollment.student_id.in_(members), limit=10000)
    completed = [e for e in enrollments if e.status == "completed"]
    results = []
    for sid in program.skill_ids:
        key = str(sid)
        skill = await get(db, Skill, sid)
        before = sum(e.baseline[key]["score"] for e in completed) / len(completed) if completed else None
        after = sum(e.outcome[key]["score"] for e in completed) / len(completed) if completed else None
        results.append({"skill_id": sid, "skill": skill.name, "baseline_average": before,
                        "outcome_average": after, "change": after - before if completed else None})
    return {"program": public(program), "enrolled": len(enrollments), "completed": len(completed),
            "enrollments": [public(e) for e in enrollments], "skill_outcomes": results,
            "method": "Paired validated skill snapshots for completed participants; missing evidence is zero. Completion records attendance, not a new skill credential. Observed changes do not establish causation."}

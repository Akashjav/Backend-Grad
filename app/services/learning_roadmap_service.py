"""Build a live learning plan from validated evidence and current requirements."""
from fastapi import HTTPException
from sqlalchemy import select
from app.models.user import User
from app.models.profile import Profile
from app.models.platform import (
    Opportunity, Skill, LearningResource, LearningProgress, Assessment,
    DomainProfile, StudentSkill,
)
from app.repositories.platform import get, rows
from app.services.matching_service import match


async def roadmap(db, user, opportunity_id):
    opportunity = await get(db, Opportunity, opportunity_id)
    if opportunity.status != "published":
        raise HTTPException(404, "Published opportunity not found")
    result = await match(db, user.id, opportunity)
    if not result["eligible"]:
        raise HTTPException(403, "This opportunity is outside your eligibility or its deadline has passed")
    progress = {p.resource_id: p.status for p in await rows(
        db, LearningProgress, LearningProgress.user_id == user.id, limit=10000
    )}
    steps = []
    for gap in sorted(result["skill_gaps"], key=lambda g: (-g["gap_score"], g["skill_id"])):
        skill = await get(db, Skill, gap["skill_id"])
        resources = await rows(db, LearningResource,
            LearningResource.skill_id == skill.id,
            LearningResource.target_level >= gap["required_level"], limit=10000)
        resources.sort(key=lambda r: (r.kind != "course", r.target_level, r.id))
        assessments = await rows(db, Assessment, Assessment.domain_id == skill.domain_id, limit=10000)
        assessments = [{"assessment_id": a.id, "title": a.title} for a in assessments
                       if any(q["skill_id"] == skill.id for q in a.questions)]
        mentors = (await db.execute(select(User.id, Profile.display_name, User.role, StudentSkill.score)
            .join(DomainProfile, DomainProfile.user_id == User.id)
            .join(Profile, Profile.user_id == User.id)
            .join(StudentSkill, StudentSkill.user_id == User.id)
            .where(User.is_active.is_(True), User.is_verified.is_(True),
                   User.role.in_(["alumni", "academician", "industry"]),
                   DomainProfile.discoverable.is_(True),
                   StudentSkill.skill_id == skill.id,
                   StudentSkill.evidence_type != "self_declared",
                   StudentSkill.score >= gap["required_level"])
            .order_by(StudentSkill.score.desc(), User.id).limit(5))).all()
        learning = [{"resource_id": r.id, "title": r.title, "url": r.url,
                     "kind": r.kind, "status": progress.get(r.id, "not_started")}
                    for r in resources]
        steps.append({**gap, "skill": skill.name, "resources": learning,
            "practice": f"Complete a supervised project or portfolio exercise demonstrating {skill.name}.",
            "mentors": [{"mentor_id": m.id, "display_name": m.display_name,
                         "role": m.role, "validated_score": m.score} for m in mentors],
            "assessments": assessments,
            "status": "ready_for_reassessment" if learning and all(r["status"] == "completed" for r in learning) else "learning_needed",
            "resource_missing": not learning, "assessment_missing": not assessments})
    return {"opportunity_id": opportunity.id, "opportunity_title": opportunity.title,
            "match_score": result["score"], "status": "gaps_remaining" if steps else "target_skills_met",
            "steps": steps,
            "guidance": "Learn, practise, consult a mentor, then reassess. Course completion alone does not validate skills. This plan refreshes from your latest validated scores; it does not guarantee selection."}

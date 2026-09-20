from datetime import datetime
from collections import defaultdict
from app.models.platform import (
    Opportunity,
    Requirement,
    StudentSkill,
    DomainProfile,
    DomainPolicy,
    ProfileItem,
    MatchResult,
    SkillGap,
)
from app.repositories.platform import get, rows, add, public
from app.ai.matching_engine import score_match


async def match(db, student_id, opportunity, persist=False):
    profile = await get(db, DomainProfile, student_id)
    skills = await rows(
        db, StudentSkill, StudentSkill.user_id == student_id, limit=10000
    )
    scores = {s.skill_id: s.score for s in skills if s.evidence_type != "self_declared"}
    requirements = await rows(
        db, Requirement, Requirement.opportunity_id == opportunity.id, limit=10000
    )
    projects = await rows(
        db,
        ProfileItem,
        ProfileItem.user_id == student_id,
        ProfileItem.kind == "portfolio",
        ProfileItem.verified.is_(True),
        limit=10000,
    )
    policy = await db.get(DomainPolicy, opportunity.domain_id)
    eligible = opportunity.cross_domain or (
        profile.domain_id == opportunity.domain_id
        and (
            opportunity.discipline_id is None
            or profile.discipline_id == opportunity.discipline_id
        )
    )
    if opportunity.deadline and opportunity.deadline < datetime.utcnow():
        eligible = False
    explanation = score_match(
        [public(r) for r in requirements],
        scores,
        {s for p in projects for s in p.skill_ids},
        profile.interests,
        opportunity.interests,
        eligible,
        policy.matching_weights if policy else None,
    )
    explanation["opportunity_id"] = opportunity.id
    explanation["opportunity_title"] = opportunity.title
    if persist:
        result = await add(
            db,
            MatchResult,
            student_id=student_id,
            opportunity_id=opportunity.id,
            score=explanation["score"],
            explanation=explanation,
        )
        explanation["match_id"] = result.id
        existing = {
            x.skill_id: x
            for x in await rows(
                db,
                SkillGap,
                SkillGap.student_id == student_id,
                SkillGap.opportunity_id == opportunity.id,
                limit=10000,
            )
        }
        current_ids = set()
        for gap in explanation["skill_gaps"]:
            current_ids.add(gap["skill_id"])
            row = existing.get(gap["skill_id"])
            if row:
                for k, v in gap.items():
                    setattr(row, k, v)
            else:
                await add(
                    db,
                    SkillGap,
                    student_id=student_id,
                    opportunity_id=opportunity.id,
                    **gap,
                )
        for sid, row in existing.items():
            if sid not in current_ids:
                await db.delete(row)
    return explanation


async def recommendations(db, user, kind=None):
    conditions = [Opportunity.status == "published"]
    if kind:
        conditions.append(Opportunity.kind == kind)
    opportunities = await rows(db, Opportunity, *conditions, limit=500)
    # Load shared candidate evidence once, not five queries for every opportunity.
    profile = await get(db, DomainProfile, user.id)
    skills = await rows(db, StudentSkill, StudentSkill.user_id == user.id, limit=10000)
    scores = {s.skill_id: s.score for s in skills if s.evidence_type != "self_declared"}
    projects = await rows(db, ProfileItem, ProfileItem.user_id == user.id,
        ProfileItem.kind == "portfolio", ProfileItem.verified.is_(True), limit=10000)
    project_skills = {s for p in projects for s in p.skill_ids}
    requirements = defaultdict(list)
    for r in await rows(db, Requirement, Requirement.opportunity_id.in_([o.id for o in opportunities]), limit=100000):
        requirements[r.opportunity_id].append(public(r))
    policies = {p.domain_id: p.matching_weights for p in await rows(db, DomainPolicy,
        DomainPolicy.domain_id.in_({o.domain_id for o in opportunities}), limit=10000)}
    results = []
    now = datetime.utcnow()
    for opp in opportunities:
        eligible = (opp.cross_domain or (profile.domain_id == opp.domain_id and
            (opp.discipline_id is None or profile.discipline_id == opp.discipline_id))) and (not opp.deadline or opp.deadline >= now)
        result = score_match(requirements[opp.id], scores, project_skills, profile.interests,
                             opp.interests, eligible, policies.get(opp.domain_id))
        results.append({**result, "opportunity_id": opp.id, "opportunity_title": opp.title})
    return sorted([r for r in results if r["eligible"]], key=lambda x: -x["score"])[:50]

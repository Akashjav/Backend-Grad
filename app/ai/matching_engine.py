"""Pure explainable baseline; never presents keyword overlap as semantic AI."""

DEFAULT_WEIGHTS = {
    "skill": 0.4,
    "core": 0.25,
    "project": 0.15,
    "interest": 0.1,
    "eligibility": 0.1,
}


def score_match(
    requirements,
    scores,
    project_skills,
    interests,
    target_interests,
    eligible,
    weights=None,
):
    weights = weights or DEFAULT_WEIGHTS
    gaps, strong, coverage, core_coverage = [], [], [], []
    for r in requirements:
        current = scores.get(r["skill_id"], 0)
        ratio = min(current / r["level"], 1)
        coverage.append((ratio, r["weight"]))
        if r["core"]:
            core_coverage.append((ratio, r["weight"]))
        gap = max(r["level"] - current, 0)
        detail = {
            "skill_id": r["skill_id"],
            "current_level": current,
            "required_level": r["level"],
            "gap_score": gap,
            "priority": "high" if gap >= 30 else "medium" if gap >= 15 else "low",
        }
        (gaps if gap else strong).append(detail)
    average = (
        lambda values: sum(v * w for v, w in values) / sum(w for _, w in values)
        if values
        else 0
    )
    needed = {r["skill_id"] for r in requirements}
    target = {x.casefold() for x in target_interests}
    components = {
        "skill": average(coverage),
        "core": average(core_coverage),
        "project": len(needed & set(project_skills)) / len(needed) if needed else 0,
        "interest": len(target & {x.casefold() for x in interests}) / len(target)
        if target
        else 0,
        "eligibility": float(eligible),
    }
    score = (
        round(100 * sum(components[k] * weights[k] for k in weights), 2)
        if eligible and needed
        else 0
    )
    return {
        "score": score,
        "eligible": eligible,
        "components": components,
        "weights": weights,
        "strong_matches": strong,
        "skill_gaps": sorted(gaps, key=lambda x: -x["gap_score"]),
        "algorithm": "weighted-skills-v1",
        "semantic_matching": False,
        "reason": "Weighted validated skill coverage, verified portfolio, interests and domain eligibility. Missing evidence contributes zero.",
    }

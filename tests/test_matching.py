from app.ai.matching_engine import score_match


def test_missing_skills_and_domain_gate():
    requirements = [
        {"skill_id": 1, "level": 80, "weight": 2, "core": True},
        {"skill_id": 2, "level": 60, "weight": 1, "core": False},
    ]
    result = score_match(requirements, {1: 80}, [], [], [], True)
    assert result["skill_gaps"][0]["skill_id"] == 2
    assert result["skill_gaps"][0]["priority"] == "high"
    assert result["strong_matches"][0]["skill_id"] == 1
    assert (
        score_match(
            requirements, {1: 100, 2: 100}, [1, 2], ["research"], ["research"], False
        )["score"]
        == 0
    )
    assert score_match([], {}, [], [], [], True)["score"] == 0


def test_configured_weights_and_perfect_evidence():
    r = [{"skill_id": 1, "level": 70, "weight": 1, "core": True}]
    assert (
        score_match(r, {1: 90}, [1], ["Research"], ["research"], True)["score"] == 100
    )

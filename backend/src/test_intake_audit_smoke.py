"""Smoke tests for pre-recommendation intake audits."""

from __future__ import annotations

from evaluation.intake_audit import build_intake_audit, build_markdown_intake_audit
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


def test_intake_audit_blocks_missing_rank() -> None:
    profile = UserProfile(
        score=450,
        rank=None,
        subject_group="历史",
        preferred_cities=["广州"],
        preferred_majors=["会计"],
        risk_tolerance=RiskTolerance.CONSERVATIVE,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_MAJOR,
    )

    result = build_intake_audit(profile)

    assert result["status"] == "blocked_missing_core"
    assert result["core_blockers"]
    assert any("全省位次" in blocker["missing"] for blocker in result["core_blockers"])
    markdown = build_markdown_intake_audit(result)
    assert "志愿填报问诊完备度审计" in markdown
    assert "核心阻断项" in markdown


def test_intake_audit_ready_with_core_boundaries() -> None:
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_cities=["广州", "深圳"],
        excluded_cities=["北京"],
        preferred_majors=["计算机"],
        blacklist_majors=["土木"],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_MAJOR,
        preference_confidence=0.8,
        major_cognition_risk=0.2,
        regret_sensitivity=0.4,
        subject_scores={"数学": 135, "英语": 128},
    )

    result = build_intake_audit(profile)

    assert result["status"] == "ready_for_recommendation"
    assert result["readiness_score"] >= 0.80
    assert any("服从调剂" in question for question in result["clarification_questions"])
    markdown = build_markdown_intake_audit(result)
    assert "Readiness score" in markdown
    assert "调剂/预算/培养路径" in markdown


if __name__ == "__main__":
    test_intake_audit_blocks_missing_rank()
    test_intake_audit_ready_with_core_boundaries()
    print("intake audit smoke tests passed")

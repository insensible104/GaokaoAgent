"""Smoke tests for volunteer-plan quality audits."""

from __future__ import annotations

from evaluation.plan_quality_audit import audit_plan_quality, build_markdown_plan_quality_audit
from models.game_matrix import AdjustmentAdvice, MajorOption, StrategyTag, VolunteerChoice, VolunteerPlan
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


def _choice(
    index: int,
    prob: float,
    strategy: StrategyTag,
    *,
    tail_risk: float = 0.10,
    utility: float = 0.80,
    blacklisted: bool = False,
    advice: AdjustmentAdvice = AdjustmentAdvice.RECOMMEND,
    obey_adjustment: bool = True,
) -> VolunteerChoice:
    return VolunteerChoice(
        choice_index=index,
        school_code=f"S{index}",
        school_name=f"测试大学{index}",
        major_group_code=f"20{index}",
        major_choices=[
            MajorOption(
                school_code=f"S{index}",
                school_name=f"测试大学{index}",
                major_group_code=f"20{index}",
                major_name="计算机类" if not blacklisted else "土木类",
                is_preferred=not blacklisted,
                is_blacklisted=blacklisted,
                user_utility=utility,
                major_rank_risk=tail_risk,
            )
        ],
        obey_adjustment=obey_adjustment,
        adjustment_advice=advice,
        group_admission_prob=prob,
        expected_major_utility=utility,
        tail_assignment_risk=tail_risk,
        strategy_tag=strategy,
        explanation="位次缓冲、概率和专业组结构均已解释。",
        quant_evidence=["rank_buffer=stable", "data_confidence=0.80"],
    )


def test_plan_quality_audit_passes_balanced_plan() -> None:
    plan = VolunteerPlan(
        province="广东",
        year=2025,
        subject_group="物理",
        user_score=620,
        user_rank=12000,
        choices=[
            _choice(1, 0.35, StrategyTag.RUSH, tail_risk=0.08),
            _choice(2, 0.55, StrategyTag.TARGET, tail_risk=0.10),
            _choice(3, 0.98, StrategyTag.SAFE, tail_risk=0.06),
        ],
    )
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_cities=["广州"],
        preferred_majors=["计算机"],
        blacklist_majors=["土木"],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_MAJOR,
    )

    result = audit_plan_quality(plan, profile)

    assert result["status"] == "pass"
    assert result["expected_admission_prob"] >= 0.99
    assert result["key_choice_indexes"] == [1, 2, 3]
    markdown = build_markdown_plan_quality_audit(result)
    assert "Volunteer Plan Quality Audit" in markdown
    assert "No blocking plan-quality findings" in markdown


def test_plan_quality_audit_blocks_hard_boundary_violation() -> None:
    plan = VolunteerPlan(
        province="广东",
        year=2025,
        subject_group="历史",
        user_score=450,
        user_rank=198000,
        choices=[
            _choice(1, 0.40, StrategyTag.RUSH, tail_risk=0.55),
            _choice(
                2,
                0.30,
                StrategyTag.RUSH,
                tail_risk=0.65,
                blacklisted=True,
                advice=AdjustmentAdvice.AVOID,
                obey_adjustment=True,
            ),
        ],
    )

    result = audit_plan_quality(plan)

    assert result["status"] == "blocked"
    assert any(item["area"] == "hard_boundary_compliance" for item in result["findings"])
    assert any(item["area"] == "safe_anchor" for item in result["findings"])


if __name__ == "__main__":
    test_plan_quality_audit_passes_balanced_plan()
    test_plan_quality_audit_blocks_hard_boundary_violation()
    print("plan quality audit smoke tests passed")

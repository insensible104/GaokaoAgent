"""Smoke tests for parallel-world volunteer-plan stress testing."""

from __future__ import annotations

from evaluation.parallel_worlds import build_markdown_parallel_world_analysis, run_parallel_world_analysis
from models.game_matrix import AdjustmentAdvice, MajorOption, StrategyTag, VolunteerChoice, VolunteerPlan
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


def _choice(
    index: int,
    prob: float,
    strategy: StrategyTag,
    *,
    tail_risk: float = 0.10,
    heat: float = 0.20,
    low_attention: float = 0.40,
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
                major_name="计算机类",
                is_preferred=True,
                user_utility=0.82,
            )
        ],
        obey_adjustment=True,
        adjustment_advice=AdjustmentAdvice.CAUTIOUS if tail_risk >= 0.25 else AdjustmentAdvice.RECOMMEND,
        group_admission_prob=prob,
        expected_major_utility=0.82,
        tail_assignment_risk=tail_risk,
        strategy_tag=strategy,
        explanation="关键志愿解释完整。",
        quant_evidence=["rank_buffer=stable", "data_confidence=0.80"],
        publicity_rebound_risk=heat,
        segment_rebound_risk=heat,
        low_attention_signal=low_attention,
        market_discount_score=0.35,
        segment_demand_score=0.45,
        arbitrage_score=0.40,
    )


def test_parallel_world_analysis_surfaces_fragile_worlds() -> None:
    plan = VolunteerPlan(
        province="广东",
        year=2025,
        subject_group="物理",
        user_score=620,
        user_rank=12000,
        choices=[
            _choice(1, 0.42, StrategyTag.RUSH, tail_risk=0.18, heat=0.70, low_attention=0.15),
            _choice(2, 0.62, StrategyTag.TARGET, tail_risk=0.18, heat=0.45, low_attention=0.35),
            _choice(3, 0.92, StrategyTag.SAFE, tail_risk=0.16, heat=0.30, low_attention=0.30),
        ],
    )
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_cities=["广州"],
        preferred_majors=["计算机"],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_MAJOR,
    )

    result = run_parallel_world_analysis(plan=plan, profile=profile)

    assert result["world_count"] >= 6
    assert result["weighted_pass_rate"] < 1.0
    assert result["sensitivity_rank"]
    assert any(item["world_id"] == "safe_anchor_slips" for item in result["sensitivity_rank"])
    markdown = build_markdown_parallel_world_analysis(result)
    assert "Parallel World Volunteer Analysis" in markdown
    assert "Most Sensitive Worlds" in markdown


if __name__ == "__main__":
    test_parallel_world_analysis_surfaces_fragile_worlds()
    print("parallel worlds smoke tests passed")

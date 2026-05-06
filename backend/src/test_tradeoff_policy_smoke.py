"""Smoke tests for rank-band tradeoff and parallel-volunteer market signals."""

from __future__ import annotations

from models.game_matrix import MajorGroupRow, QuotaBucket, StrategyTag, VolatilityLevel
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from recommendation.major_choice_planner import build_volunteer_plan
from recommendation.tradeoff_policy import score_tradeoff


def _profile() -> UserProfile:
    return UserProfile(
        score=620,
        rank=25000,
        subject_group="物理",
        preferred_cities=["广州", "深圳"],
        preferred_majors=["计算机", "电子信息"],
        blacklist_majors=["土木"],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_MAJOR,
    )


def _mixed_small_quota_row() -> MajorGroupRow:
    return MajorGroupRow(
        school_name="测试大学",
        school_code="10001",
        major_group_code="201",
        major_list=["计算机类", "电子信息类", "土木类"],
        major_count=3,
        admission_prob=0.72,
        min_rank_pred=26000,
        rank_diff=1000,
        rank_ci_lower=23000,
        rank_ci_upper=30000,
        fear_index=0.0,
        volatility=VolatilityLevel.HIGH,
        quota=8,
        quota_bucket=QuotaBucket.SMALL,
        quota_stability_score=0.20,
        variance_opportunity_score=0.82,
        adjustment_risk=0.65,
        worst_case_major="土木类",
        is_blacklist_risk=True,
        acceptable_major_ratio=0.67,
        blacklist_major_ratio=0.33,
        major_utility_mean=0.82,
        major_utility_min=0.15,
        major_utility_dispersion=0.67,
        tail_assignment_risk=0.65,
        strategy_tag=StrategyTag.TARGET,
        comprehensive_score=0.70,
    )


def test_tradeoff_policy_tags_user_pain_points_and_market_game() -> None:
    row = _mixed_small_quota_row()
    result = score_tradeoff(
        row=row,
        profile=_profile(),
        school_major_score=0.86,
        city_preference_score=1.30,
    )

    assert result.score_band == "upper_middle_choice_rich"
    assert result.breakdown["crowding_risk"] >= 0.62
    assert "tail_major_regret" in result.pain_point_flags
    assert "bait_major_group" in result.pain_point_flags
    assert "high_variance_opportunity" in result.pain_point_flags
    assert any("small_quota_lottery" in note for note in result.market_behavior_notes)
    assert 0.0 <= result.final_score <= 1.0


def test_tradeoff_fields_survive_volunteer_plan_conversion() -> None:
    profile = _profile()
    row = _mixed_small_quota_row()
    result = score_tradeoff(
        row=row,
        profile=profile,
        school_major_score=0.86,
        city_preference_score=1.30,
    )
    row.score_band = result.score_band
    row.tradeoff_breakdown = result.breakdown
    row.pain_point_flags = result.pain_point_flags
    row.market_behavior_notes = result.market_behavior_notes
    row.tradeoff_summary = result.summary

    plan = build_volunteer_plan([row], profile)
    choice = plan.choices[0]

    assert choice.score_band == row.score_band
    assert choice.tradeoff_breakdown["crowding_risk"] == row.tradeoff_breakdown["crowding_risk"]
    assert "tail_major_regret" in choice.pain_point_flags
    assert choice.market_behavior_notes


if __name__ == "__main__":
    test_tradeoff_policy_tags_user_pain_points_and_market_game()
    test_tradeoff_fields_survive_volunteer_plan_conversion()
    print("tradeoff policy smoke tests passed")

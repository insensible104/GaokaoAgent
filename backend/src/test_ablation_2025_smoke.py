"""Smoke tests for 2025 backtest ablation comparisons."""

from __future__ import annotations

from evaluation.ablation_2025 import (
    build_markdown_ablation_report,
    run_ablation_backtest_records,
)
from evaluation.schemas import ActualMajorGroupOutcome
from models.game_matrix import MajorGroupRow, MajorOption, StrategyTag, VolatilityLevel
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from recommendation.major_choice_planner import build_volunteer_plan


def _profile() -> UserProfile:
    return UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_cities=["广州"],
        preferred_majors=["计算机"],
        blacklist_majors=["土木"],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.BALANCED,
    )


def _row(
    *,
    school: str,
    code: str,
    group: str,
    prob: float,
    tag: StrategyTag,
    utility: float,
    major: str,
) -> MajorGroupRow:
    option = MajorOption(
        school_code=code,
        school_name=school,
        major_group_code=group,
        major_name=major,
        user_utility=utility,
        is_preferred="计算机" in major,
        is_blacklisted="土木" in major,
    )
    return MajorGroupRow(
        school_name=school,
        school_code=code,
        major_group_code=group,
        major_list=[major],
        major_count=1,
        major_options=[option],
        suggested_major_choices=[option],
        admission_prob=prob,
        min_rank_pred=12000,
        rank_diff=0,
        rank_ci_lower=11000,
        rank_ci_upper=13000,
        fear_index=0.0,
        volatility=VolatilityLevel.MEDIUM,
        adjustment_risk=0.1,
        tail_assignment_risk=0.1 if utility >= 0.5 else 0.7,
        major_utility_mean=utility,
        major_utility_min=utility,
        strategy_tag=tag,
        comprehensive_score=utility,
    )


def test_ablation_backtest_compares_full_plan_against_baselines():
    profile = _profile()
    rows = [
        _row(
            school="A大学",
            code="10001",
            group="201",
            prob=0.64,
            tag=StrategyTag.TARGET,
            utility=0.95,
            major="计算机类",
        ),
        _row(
            school="B大学",
            code="10002",
            group="202",
            prob=0.95,
            tag=StrategyTag.SAFE,
            utility=0.20,
            major="土木类",
        ),
        _row(
            school="C大学",
            code="10003",
            group="203",
            prob=0.52,
            tag=StrategyTag.RUSH,
            utility=0.80,
            major="软件工程",
        ),
    ]
    full_plan = build_volunteer_plan(rows, profile, max_choices=3)
    record = {
        "case_id": "case_001",
        "user_rank": 12000,
        "preferred_majors": ["计算机"],
        "blacklist_majors": ["土木"],
        "plan": full_plan.model_dump(),
        "candidate_rows": [row.model_dump() for row in rows],
        "user_profile": profile.model_dump(),
    }
    actual = [
        ActualMajorGroupOutcome(
            school_code="10001",
            school_name="A大学",
            major_group_code="201",
            actual_group_min_rank=12500,
            major_min_ranks={"计算机类": 12300},
        ),
        ActualMajorGroupOutcome(
            school_code="10002",
            school_name="B大学",
            major_group_code="202",
            actual_group_min_rank=18000,
            major_min_ranks={"土木类": 18000},
        ),
        ActualMajorGroupOutcome(
            school_code="10003",
            school_name="C大学",
            major_group_code="203",
            actual_group_min_rank=11000,
            major_min_ranks={"软件工程": 10800},
        ),
    ]

    result = run_ablation_backtest_records(
        records=[record],
        actual_outcomes=actual,
        variants=["full", "probability_only", "safe_first"],
    )

    assert result["case_count"] == 1
    assert set(result["variants"]) == {"full", "probability_only", "safe_first"}
    assert result["summaries"]["full"]["success_rate"] == 1.0
    assert result["summaries"]["full"]["preferred_major_hit_rate"] == 1.0
    assert result["summaries"]["probability_only"]["blacklist_hit_rate"] == 1.0
    assert result["deltas_vs_full"]["probability_only"]["preferred_major_hit_rate"] == -1.0
    assert result["per_case"][0]["variant"] == "full"

    report = build_markdown_ablation_report(result)
    assert "| Variant | Cases | Success | Preferred Major | Blacklist | Tail Assignment |" in report
    assert "`probability_only`" in report


if __name__ == "__main__":
    test_ablation_backtest_compares_full_plan_against_baselines()
    print("2025 ablation smoke tests passed")

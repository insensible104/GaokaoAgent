"""Smoke tests for 2025 backtest ablation comparisons."""

from __future__ import annotations

from evaluation.ablation_2025 import (
    build_markdown_ablation_report,
    run_ablation_backtest_records,
)
from evaluation.baselines import build_baseline_plan
from evaluation.schemas import ActualMajorGroupOutcome
from models.game_matrix import MajorGroupRow, MajorOption, StrategyTag, VolatilityLevel
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from recommendation.major_choice_planner import build_volunteer_plan


def _profile() -> UserProfile:
    return UserProfile(
        score=620,
        rank=12000,
        subject_group="physics",
        preferred_cities=["Guangzhou"],
        preferred_majors=["computer"],
        blacklist_majors=["civil"],
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
    arbitrage_score: float = 0.0,
    front_major_arbitrage_score: float = 0.0,
    front_major_hit_prob: float = 0.0,
    relative_lift: float = 0.0,
    market_discount_score: float = 0.0,
    rebound_risk: float = 0.0,
    quant_score: float = 0.0,
) -> MajorGroupRow:
    option = MajorOption(
        school_code=code,
        school_name=school,
        major_group_code=group,
        major_name=major,
        user_utility=utility,
        is_preferred="computer" in major,
        is_blacklisted="civil" in major,
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
        arbitrage_score=arbitrage_score,
        front_major_arbitrage_score=front_major_arbitrage_score,
        front_major_hit_prob=front_major_hit_prob,
        relative_lift=relative_lift,
        market_discount_score=market_discount_score,
        rebound_risk=rebound_risk,
        quant_score=quant_score,
    )


def test_ablation_backtest_compares_full_plan_against_baselines():
    profile = _profile()
    rows = [
        _row(
            school="A University",
            code="10001",
            group="201",
            prob=0.64,
            tag=StrategyTag.TARGET,
            utility=0.95,
            major="computer science",
        ),
        _row(
            school="B University",
            code="10002",
            group="202",
            prob=0.95,
            tag=StrategyTag.SAFE,
            utility=0.20,
            major="civil engineering",
        ),
        _row(
            school="C University",
            code="10003",
            group="203",
            prob=0.52,
            tag=StrategyTag.RUSH,
            utility=0.80,
            major="software engineering",
        ),
    ]
    full_plan = build_volunteer_plan(rows, profile, max_choices=3)
    record = {
        "case_id": "case_001",
        "user_rank": 12000,
        "preferred_majors": ["computer"],
        "blacklist_majors": ["civil"],
        "plan": full_plan.model_dump(),
        "candidate_rows": [row.model_dump() for row in rows],
        "user_profile": profile.model_dump(),
    }
    actual = [
        ActualMajorGroupOutcome(
            school_code="10001",
            school_name="A University",
            major_group_code="201",
            actual_group_min_rank=12500,
            major_min_ranks={"computer science": 12300},
        ),
        ActualMajorGroupOutcome(
            school_code="10002",
            school_name="B University",
            major_group_code="202",
            actual_group_min_rank=18000,
            major_min_ranks={"civil engineering": 18000},
        ),
        ActualMajorGroupOutcome(
            school_code="10003",
            school_name="C University",
            major_group_code="203",
            actual_group_min_rank=11000,
            major_min_ranks={"software engineering": 10800},
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


def test_arbitrage_ablation_variants_expose_signal_families():
    profile = _profile()
    safe_non_arbitrage = _row(
        school="Safe University",
        code="20001",
        group="301",
        prob=0.92,
        tag=StrategyTag.SAFE,
        utility=0.58,
        major="general major",
        arbitrage_score=0.05,
        front_major_arbitrage_score=0.02,
        front_major_hit_prob=0.15,
    )
    brand_discount = _row(
        school="Brand University",
        code="20002",
        group="302",
        prob=0.62,
        tag=StrategyTag.TARGET,
        utility=0.70,
        major="cold brand major",
        arbitrage_score=0.86,
        relative_lift=0.72,
        market_discount_score=0.88,
    )
    front_major = _row(
        school="Front University",
        code="20003",
        group="303",
        prob=0.66,
        tag=StrategyTag.TARGET,
        utility=0.82,
        major="computer science",
        arbitrage_score=0.54,
        front_major_arbitrage_score=0.90,
        front_major_hit_prob=0.94,
        relative_lift=0.30,
    )
    rows = [safe_non_arbitrage, brand_discount, front_major]

    no_arbitrage = build_baseline_plan(
        rows=rows,
        profile=profile,
        baseline="no_arbitrage",
        max_choices=3,
    )
    arbitrage_only = build_baseline_plan(
        rows=rows,
        profile=profile,
        baseline="arbitrage_only",
        max_choices=3,
    )
    front_major_boost = build_baseline_plan(
        rows=rows,
        profile=profile,
        baseline="front_major_boost",
        max_choices=3,
    )

    assert no_arbitrage.choices[0].school_code == "20001"
    assert arbitrage_only.choices[0].school_code == "20002"
    assert front_major_boost.choices[0].school_code == "20003"
    assert front_major_boost.choices[0].front_major_hit_prob == 0.94


def test_quant_tuned_shadow_variant_uses_tuning_weights_without_changing_full_plan():
    profile = _profile()
    safe_bad = _row(
        school="Safe Bad University",
        code="30001",
        group="401",
        prob=0.96,
        tag=StrategyTag.SAFE,
        utility=0.20,
        major="civil engineering",
        quant_score=0.10,
    )
    preferred_target = _row(
        school="Preferred Target University",
        code="30002",
        group="402",
        prob=0.62,
        tag=StrategyTag.TARGET,
        utility=0.95,
        major="computer science",
        quant_score=0.96,
    )
    rows = [safe_bad, preferred_target]
    full_plan = build_volunteer_plan(rows, profile, max_choices=2)
    record = {
        "case_id": "case_shadow",
        "user_rank": 12000,
        "preferred_majors": ["computer"],
        "blacklist_majors": ["civil"],
        "plan": full_plan.model_dump(),
        "candidate_rows": [row.model_dump() for row in rows],
        "user_profile": profile.model_dump(),
    }
    actual = [
        ActualMajorGroupOutcome(
            school_code="30001",
            school_name="Safe Bad University",
            major_group_code="401",
            actual_group_min_rank=20000,
            major_min_ranks={"civil engineering": 20000},
        ),
        ActualMajorGroupOutcome(
            school_code="30002",
            school_name="Preferred Target University",
            major_group_code="402",
            actual_group_min_rank=13000,
            major_min_ranks={"computer science": 12500},
        ),
    ]

    result = run_ablation_backtest_records(
        records=[record],
        actual_outcomes=actual,
        variants=["full"],
        quant_shadow_weights={"quant_score": 1.0},
    )

    assert result["variants"] == ["full", "quant_tuned_shadow"]
    assert result["quant_shadow"]["weights"] == {"quant_score": 1.0}
    assert result["summaries"]["full"]["blacklist_hit_rate"] == 1.0
    assert result["summaries"]["quant_tuned_shadow"]["preferred_major_hit_rate"] == 1.0
    assert result["deltas_vs_full"]["quant_tuned_shadow"]["preferred_major_hit_rate"] == 1.0


if __name__ == "__main__":
    test_ablation_backtest_compares_full_plan_against_baselines()
    test_arbitrage_ablation_variants_expose_signal_families()
    test_quant_tuned_shadow_variant_uses_tuning_weights_without_changing_full_plan()
    print("2025 ablation smoke tests passed")

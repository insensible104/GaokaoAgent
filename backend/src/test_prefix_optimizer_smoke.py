"""Smoke tests for first-hit-aware volunteer prefix optimization."""

from __future__ import annotations

from models.game_matrix import MajorGroupRow, QuotaBucket, StrategyTag, VolatilityLevel
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from recommendation.major_choice_planner import build_volunteer_plan
from recommendation.prefix_optimizer import optimize_prefix_order


def _row(
    *,
    school_name: str,
    admission_prob: float,
    major_utility: float,
    tail_risk: float,
    strategy: StrategyTag,
    arbitrage: float = 0.0,
    front_major: float = 0.0,
    rebound: float = 0.0,
) -> MajorGroupRow:
    return MajorGroupRow(
        school_name=school_name,
        school_code=school_name[:6],
        major_group_code="201",
        major_list=["Test Major"],
        major_count=1,
        admission_prob=admission_prob,
        min_rank_pred=10000,
        rank_diff=0,
        rank_ci_lower=8000,
        rank_ci_upper=12000,
        volatility=VolatilityLevel.MEDIUM,
        quota=20,
        quota_bucket=QuotaBucket.MEDIUM,
        quota_stability_score=0.60,
        variance_opportunity_score=0.45,
        major_utility_mean=major_utility,
        major_utility_min=major_utility,
        major_utility_dispersion=0.10,
        tail_assignment_risk=tail_risk,
        strategy_tag=strategy,
        comprehensive_score=major_utility,
        arbitrage_score=arbitrage,
        front_major_arbitrage_score=front_major,
        front_major_hit_prob=front_major,
        rebound_risk=rebound,
        segment_rebound_risk=rebound,
    )


def _profile() -> UserProfile:
    return UserProfile(
        score=590,
        rank=18888,
        subject_group="physics",
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.BALANCED,
    )


def test_prefix_optimizer_prevents_low_utility_safe_row_from_shadowing_opportunity():
    safe_shadow = _row(
        school_name="Safe Low Utility College",
        admission_prob=0.92,
        major_utility=0.36,
        tail_risk=0.12,
        strategy=StrategyTag.SAFE,
    )
    target_opportunity = _row(
        school_name="Target Front Major University",
        admission_prob=0.58,
        major_utility=0.78,
        tail_risk=0.18,
        strategy=StrategyTag.TARGET,
        arbitrage=0.55,
        front_major=0.46,
    )
    reckless = _row(
        school_name="Reckless Hot Opportunity",
        admission_prob=0.52,
        major_utility=0.82,
        tail_risk=0.76,
        strategy=StrategyTag.RUSH,
        arbitrage=0.85,
        front_major=0.30,
        rebound=0.70,
    )

    ordered = optimize_prefix_order(
        rows=[safe_shadow, reckless, target_opportunity],
        profile=_profile(),
        max_choices=3,
    )

    assert ordered[0].school_name == "Target Front Major University"
    assert ordered[1].school_name == "Safe Low Utility College"
    assert ordered[-1].school_name == "Reckless Hot Opportunity"


def test_prefix_optimizer_keeps_safe_anchor_after_opportunity_prefix():
    rows = [
        _row(
            school_name=f"Opportunity {idx}",
            admission_prob=0.48 + idx * 0.03,
            major_utility=0.72 - idx * 0.01,
            tail_risk=0.18,
            strategy=StrategyTag.RUSH if idx < 2 else StrategyTag.TARGET,
            arbitrage=0.40,
            front_major=0.20,
        )
        for idx in range(4)
    ]
    rows.append(
        _row(
            school_name="Clean Safe Anchor",
            admission_prob=0.93,
            major_utility=0.42,
            tail_risk=0.08,
            strategy=StrategyTag.SAFE,
        )
    )

    ordered = optimize_prefix_order(rows=rows, profile=_profile(), max_choices=5)

    assert ordered[-1].school_name == "Clean Safe Anchor"
    assert any(row.strategy_tag == StrategyTag.SAFE for row in ordered)


def test_prefix_optimizer_reserves_safe_anchors_when_candidate_pool_is_large():
    rows = [
        _row(
            school_name=f"Rush Opportunity {idx}",
            admission_prob=0.42 + idx * 0.02,
            major_utility=0.78 - idx * 0.01,
            tail_risk=0.20,
            strategy=StrategyTag.RUSH,
            arbitrage=0.55,
            front_major=0.24,
        )
        for idx in range(8)
    ]
    rows.extend(
        [
            _row(
                school_name="Safe Anchor A",
                admission_prob=0.91,
                major_utility=0.42,
                tail_risk=0.08,
                strategy=StrategyTag.SAFE,
            ),
            _row(
                school_name="Safe Anchor B",
                admission_prob=0.88,
                major_utility=0.41,
                tail_risk=0.10,
                strategy=StrategyTag.SAFE,
            ),
        ]
    )

    ordered = optimize_prefix_order(rows=rows, profile=_profile(), max_choices=5)

    assert len(ordered) == 5
    assert sum(1 for row in ordered if row.strategy_tag == StrategyTag.SAFE) >= 2
    assert ordered[-1].strategy_tag == StrategyTag.SAFE


def test_prefix_optimizer_keeps_high_probability_target_as_opportunity():
    target = _row(
        school_name="Borderline Target With Real Cutoff Upside",
        admission_prob=0.85,
        major_utility=0.45,
        tail_risk=0.11,
        strategy=StrategyTag.TARGET,
        arbitrage=0.50,
        front_major=0.05,
    )
    safe_rows = [
        _row(
            school_name=f"High Probability Safe {idx}",
            admission_prob=0.99,
            major_utility=0.45,
            tail_risk=0.11,
            strategy=StrategyTag.SAFE,
            arbitrage=0.50,
            front_major=0.05 + idx * 0.01,
        )
        for idx in range(10)
    ]

    ordered = optimize_prefix_order(
        rows=safe_rows + [target],
        profile=_profile(),
        max_choices=10,
    )

    assert target in ordered
    assert ordered.index(target) < 3


def test_build_volunteer_plan_can_apply_prefix_optimizer():
    safe_shadow = _row(
        school_name="Safe Low Utility College",
        admission_prob=0.92,
        major_utility=0.36,
        tail_risk=0.12,
        strategy=StrategyTag.SAFE,
    )
    target_opportunity = _row(
        school_name="Target Front Major University",
        admission_prob=0.58,
        major_utility=0.78,
        tail_risk=0.18,
        strategy=StrategyTag.TARGET,
        arbitrage=0.55,
        front_major=0.46,
    )

    plan = build_volunteer_plan(
        [safe_shadow, target_opportunity],
        _profile(),
        optimize_prefix=True,
    )

    assert plan.choices[0].school_name == "Target Front Major University"


def test_prefix_optimizer_defers_tail_heavy_opportunity_when_clean_option_is_comparable():
    tail_heavy = _row(
        school_name="Tail Heavy Brand Opportunity",
        admission_prob=0.70,
        major_utility=0.62,
        tail_risk=0.56,
        strategy=StrategyTag.TARGET,
        arbitrage=0.62,
        front_major=0.18,
    )
    clean_opportunity = _row(
        school_name="Clean Comparable Opportunity",
        admission_prob=0.66,
        major_utility=0.58,
        tail_risk=0.16,
        strategy=StrategyTag.TARGET,
        arbitrage=0.54,
        front_major=0.16,
    )
    safe_anchor = _row(
        school_name="Clean Safe Anchor",
        admission_prob=0.92,
        major_utility=0.42,
        tail_risk=0.08,
        strategy=StrategyTag.SAFE,
    )

    ordered = optimize_prefix_order(
        rows=[tail_heavy, safe_anchor, clean_opportunity],
        profile=_profile(),
        max_choices=3,
    )

    assert ordered[0].school_name == "Clean Comparable Opportunity"
    assert ordered.index(tail_heavy) > ordered.index(safe_anchor)


def test_prefix_optimizer_promotes_reliable_value_anchor_before_ordinary_rush():
    ordinary_rush = _row(
        school_name="Ordinary Rush Brand",
        admission_prob=0.62,
        major_utility=0.62,
        tail_risk=0.16,
        strategy=StrategyTag.RUSH,
        arbitrage=0.42,
        front_major=0.14,
    )
    reliable_anchor = _row(
        school_name="Reliable Value Anchor",
        admission_prob=0.94,
        major_utility=0.55,
        tail_risk=0.10,
        strategy=StrategyTag.SAFE,
        arbitrage=0.46,
        front_major=0.12,
    )

    ordered = optimize_prefix_order(
        rows=[ordinary_rush, reliable_anchor],
        profile=_profile(),
        max_choices=2,
    )

    assert ordered[0].school_name == "Reliable Value Anchor"


if __name__ == "__main__":
    test_prefix_optimizer_prevents_low_utility_safe_row_from_shadowing_opportunity()
    test_prefix_optimizer_keeps_safe_anchor_after_opportunity_prefix()
    test_prefix_optimizer_reserves_safe_anchors_when_candidate_pool_is_large()
    test_prefix_optimizer_keeps_high_probability_target_as_opportunity()
    test_build_volunteer_plan_can_apply_prefix_optimizer()
    test_prefix_optimizer_defers_tail_heavy_opportunity_when_clean_option_is_comparable()
    test_prefix_optimizer_promotes_reliable_value_anchor_before_ordinary_rush()
    print("prefix optimizer smoke tests passed")

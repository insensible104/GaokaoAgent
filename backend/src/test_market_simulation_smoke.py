"""Smoke tests for segment-demand simulation over arbitrage opportunities."""

from __future__ import annotations

from collections import defaultdict

from models.game_matrix import MajorGroupRow, MajorOption, QuotaBucket, StrategyTag, VolatilityLevel
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from evaluation.baselines import build_baseline_plan
from rl.learnable_prompt import PromptParameters
from rl.runtime_policy import RLRuntimePolicy
from recommendation.arbitrage_adapter import score_major_group_arbitrage
from recommendation.market_evidence import EvidenceCard, assess_market_evidence
from recommendation.market_simulation import (
    default_student_archetypes,
    score_segment_demand,
)


def _brand_discount_row() -> MajorGroupRow:
    options = [
        MajorOption(
            school_code="10141",
            school_name="Dalian University of Technology",
            major_group_code="203",
            major_name="Mathematical Science",
            plan_quota=12,
            tuition=80000,
            remarks="Panjin campus joint program",
            user_utility=0.90,
        ),
        MajorOption(
            school_code="10141",
            school_name="Dalian University of Technology",
            major_group_code="203",
            major_name="Environmental Engineering",
            plan_quota=14,
            tuition=80000,
            remarks="Panjin campus joint program",
            user_utility=0.45,
        ),
    ]
    return MajorGroupRow(
        school_name="Dalian University of Technology",
        school_code="10141",
        major_group_code="203",
        major_list=[option.major_name for option in options],
        major_count=len(options),
        major_options=options,
        admission_prob=0.58,
        min_rank_pred=18000,
        rank_diff=-900,
        rank_ci_lower=14000,
        rank_ci_upper=23000,
        volatility=VolatilityLevel.HIGH,
        quota=26,
        quota_bucket=QuotaBucket.MEDIUM,
        quota_stability_score=0.55,
        variance_opportunity_score=0.72,
        major_utility_mean=0.67,
        major_utility_min=0.45,
        major_utility_dispersion=0.45,
        tail_assignment_risk=0.24,
        strategy_tag=StrategyTag.RUSH,
        comprehensive_score=0.82,
    )


def _profile() -> UserProfile:
    return UserProfile(
        score=590,
        rank=18888,
        subject_group="physics",
        preferred_majors=["Mathematical"],
        risk_tolerance=RiskTolerance.AGGRESSIVE,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_SCHOOL,
    )


def test_default_archetypes_cover_brand_budget_region_and_adjustment_needs():
    archetypes = default_student_archetypes()
    names = {archetype.name for archetype in archetypes}

    assert len(archetypes) >= 12
    assert "brand_face_family" in names
    assert "employment_roi_family" in names
    assert "region_discount_taker" in names
    assert "adjustment_tolerant_climber" in names


def test_segment_demand_identifies_who_can_absorb_brand_discount():
    row = _brand_discount_row()
    assessment = assess_market_evidence(row)

    result = score_segment_demand(
        row=row,
        assessment=assessment,
        user_rank=18888,
    )

    assert result.segment_demand_score > 0.35
    assert result.low_attention_signal > 0.20
    assert "brand_face_family" in result.best_fit_archetypes
    assert result.segment_breakdown["brand_face_family"] > result.segment_breakdown["employment_roi_family"]


def test_publicity_heat_reduces_low_attention_and_raises_rebound_risk():
    row = _brand_discount_row()
    base = score_segment_demand(
        row=row,
        assessment=assess_market_evidence(row),
        user_rank=18888,
    )
    hot_assessment = assess_market_evidence(
        row,
        external_cards=[
            EvidenceCard(
                signal_type="publicity_heat",
                source_type="livestream",
                value=0.95,
                confidence=0.85,
                claim="A counselor promoted this group before deadline.",
            )
        ],
    )
    hot = score_segment_demand(row=row, assessment=hot_assessment, user_rank=18888)

    assert hot.rebound_risk_adjustment > base.rebound_risk_adjustment
    assert hot.low_attention_signal < base.low_attention_signal


def test_adapter_attaches_segment_market_signals_to_rows():
    row = _brand_discount_row()

    score_major_group_arbitrage(
        row=row,
        profile=_profile(),
        school_major_score=0.82,
        city_preference_score=0.55,
    )

    assert row.segment_demand_score > 0.0
    assert row.low_attention_signal > 0.0
    assert row.best_fit_archetypes
    assert "brand_face_family" in row.best_fit_archetypes


def test_segment_market_baseline_prefers_hidden_segment_fit():
    high = _brand_discount_row()
    low = _brand_discount_row()
    low.school_name = "Ordinary College"
    low.school_code = "90002"
    low.major_group_code = "204"
    low.arbitrage_score = 0.20
    low.front_major_arbitrage_score = 0.05
    low.segment_demand_score = 0.18
    low.low_attention_signal = 0.10
    low.segment_rebound_risk = 0.45
    low.admission_prob = 0.62

    high.arbitrage_score = 0.45
    high.front_major_arbitrage_score = 0.18
    high.segment_demand_score = 0.58
    high.low_attention_signal = 0.48
    high.segment_rebound_risk = 0.18
    high.admission_prob = 0.58

    plan = build_baseline_plan(
        rows=[low, high],
        profile=_profile(),
        baseline="segment_market",
        max_choices=2,
    )

    assert plan.choices[0].school_name == high.school_name


def test_guarded_arbitrage_blocks_ungrounded_hot_opportunities():
    reckless = _brand_discount_row()
    reckless.school_name = "Hot Risk College"
    reckless.school_code = "90003"
    reckless.major_group_code = "301"
    reckless.admission_prob = 0.42
    reckless.major_utility_mean = 0.48
    reckless.tail_assignment_risk = 0.72
    reckless.arbitrage_score = 0.82
    reckless.front_major_arbitrage_score = 0.30
    reckless.segment_demand_score = 0.80
    reckless.low_attention_signal = 0.12
    reckless.segment_rebound_risk = 0.70

    guarded = _brand_discount_row()
    guarded.school_name = "Guarded Opportunity University"
    guarded.school_code = "90004"
    guarded.major_group_code = "302"
    guarded.admission_prob = 0.60
    guarded.major_utility_mean = 0.70
    guarded.tail_assignment_risk = 0.18
    guarded.arbitrage_score = 0.56
    guarded.front_major_arbitrage_score = 0.24
    guarded.front_major_hit_prob = 0.58
    guarded.segment_demand_score = 0.54
    guarded.low_attention_signal = 0.42
    guarded.segment_rebound_risk = 0.18

    safe = _brand_discount_row()
    safe.school_name = "Plain Safe College"
    safe.school_code = "90005"
    safe.major_group_code = "303"
    safe.admission_prob = 0.80
    safe.major_utility_mean = 0.48
    safe.tail_assignment_risk = 0.12
    safe.arbitrage_score = 0.18
    safe.front_major_arbitrage_score = 0.04
    safe.segment_demand_score = 0.16
    safe.low_attention_signal = 0.08
    safe.segment_rebound_risk = 0.12

    plan = build_baseline_plan(
        rows=[reckless, safe, guarded],
        profile=_profile(),
        baseline="guarded_arbitrage",
        max_choices=3,
    )

    assert plan.choices[0].school_name == guarded.school_name
    assert plan.choices[-1].school_name == reckless.school_name


def test_runtime_policy_uses_segment_signal_under_tail_and_rebound_guards():
    reckless = _brand_discount_row()
    reckless.school_name = "Hot Risk College"
    reckless.admission_prob = 0.55
    reckless.comprehensive_score = 0.72
    reckless.major_utility_mean = 0.48
    reckless.tail_assignment_risk = 0.74
    reckless.adjustment_risk = 0.18
    reckless.arbitrage_score = 0.82
    reckless.front_major_arbitrage_score = 0.30
    reckless.segment_demand_score = 0.82
    reckless.low_attention_signal = 0.10
    reckless.segment_rebound_risk = 0.70

    guarded = _brand_discount_row()
    guarded.school_name = "Guarded Opportunity University"
    guarded.admission_prob = 0.58
    guarded.comprehensive_score = 0.70
    guarded.major_utility_mean = 0.68
    guarded.tail_assignment_risk = 0.18
    guarded.adjustment_risk = 0.18
    guarded.arbitrage_score = 0.58
    guarded.front_major_arbitrage_score = 0.24
    guarded.front_major_hit_prob = 0.58
    guarded.segment_demand_score = 0.56
    guarded.low_attention_signal = 0.42
    guarded.segment_rebound_risk = 0.18

    policy = RLRuntimePolicy()
    params = PromptParameters()

    reckless_score = policy._policy_score(reckless, params, defaultdict(int))
    guarded_score = policy._policy_score(guarded, params, defaultdict(int))

    assert guarded_score > reckless_score


if __name__ == "__main__":
    test_default_archetypes_cover_brand_budget_region_and_adjustment_needs()
    test_segment_demand_identifies_who_can_absorb_brand_discount()
    test_publicity_heat_reduces_low_attention_and_raises_rebound_risk()
    test_adapter_attaches_segment_market_signals_to_rows()
    test_segment_market_baseline_prefers_hidden_segment_fit()
    test_guarded_arbitrage_blocks_ungrounded_hot_opportunities()
    test_runtime_policy_uses_segment_signal_under_tail_and_rebound_guards()
    print("market simulation smoke tests passed")

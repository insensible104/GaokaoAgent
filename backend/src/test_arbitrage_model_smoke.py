from collections import defaultdict

from models.game_matrix import MajorGroupRow, MajorOption, QuotaBucket, StrategyTag, VolatilityLevel
from recommendation.arbitrage_model import (
    AdmissionContext,
    CandidateContext,
    CounterfactualBaseline,
    OpportunitySignals,
    SacrificeVector,
    StudentValueModel,
    score_arbitrage_opportunity,
)
from recommendation.arbitrage_adapter import score_major_group_arbitrage
from recommendation.major_choice_planner import build_volunteer_plan
from models.user_profile import UserProfile
from rl.learnable_prompt import PromptParameters
from rl.runtime_policy import RLRuntimePolicy


def test_arbitrage_score_rewards_affordable_brand_discount():
    baseline = CounterfactualBaseline(
        school_tier=0.45,
        public_private=0.65,
        major_quality=0.55,
        city_tier=0.45,
        cost_type=0.25,
    )
    candidate = CandidateContext(
        school_tier=0.82,
        public_private=0.95,
        major_quality=0.62,
        city_tier=0.50,
        cost_type=0.90,
        industry_prestige=0.78,
        brand_face=0.88,
        front_major_value=0.82,
    )
    sacrifice = SacrificeVector(
        tuition=0.85,
        campus=0.65,
        major=0.35,
        employment_uncertainty=0.25,
    )
    signals = OpportunitySignals(
        tuition_filter=0.85,
        campus_discount=0.65,
        cold_major_discount=0.35,
        historical_anchor_overdeterrence=0.70,
        low_attention_signal=0.55,
        evidence_strength=0.80,
        rebound_risk=0.20,
    )
    admission = AdmissionContext(
        group_admission_prob=0.58,
        front_major_quota_share=0.35,
        entrant_pool_discount=0.70,
        major_obvious_heat=0.20,
        rank_margin=0.15,
        tail_assignment_risk=0.18,
    )

    brand_family = StudentValueModel(
        brand_face_weight=0.80,
        employment_roi_weight=0.25,
        cost_sensitivity=0.10,
        major_strictness=0.25,
        tuition_tolerance=0.95,
        campus_tolerance=0.80,
        adjustment_tolerance=0.70,
        employment_uncertainty_tolerance=0.75,
    )
    budget_family = StudentValueModel(
        brand_face_weight=0.25,
        employment_roi_weight=0.85,
        cost_sensitivity=0.90,
        major_strictness=0.85,
        tuition_tolerance=0.10,
        campus_tolerance=0.35,
        adjustment_tolerance=0.30,
        employment_uncertainty_tolerance=0.20,
    )

    brand_result = score_arbitrage_opportunity(
        student=brand_family,
        baseline=baseline,
        candidate=candidate,
        sacrifice=sacrifice,
        opportunity=signals,
        admission=admission,
    )
    budget_result = score_arbitrage_opportunity(
        student=budget_family,
        baseline=baseline,
        candidate=candidate,
        sacrifice=sacrifice,
        opportunity=signals,
        admission=admission,
    )

    assert brand_result.arbitrage_score > budget_result.arbitrage_score + 0.20
    assert brand_result.personal_acceptability > 0.70
    assert budget_result.sacrifice_cost > brand_result.sacrifice_cost
    assert brand_result.front_major_hit_prob > 0.40
    assert "tuition_filter" in brand_result.opportunity_types


def test_front_major_probability_penalizes_hot_tiny_quota_major():
    good_options = [
        MajorOption(major_name="数理基础科学", plan_quota=12, user_utility=0.90),
        MajorOption(major_name="应用化学", plan_quota=14, user_utility=0.55),
        MajorOption(major_name="环境生态工程", plan_quota=12, user_utility=0.45),
    ]
    risky_options = [
        MajorOption(major_name="计算机科学与技术", plan_quota=2, user_utility=0.95),
        MajorOption(major_name="材料类", plan_quota=18, user_utility=0.35),
        MajorOption(major_name="化工与制药类", plan_quota=18, user_utility=0.30),
    ]

    base_kwargs = dict(
        group_admission_prob=0.55,
        entrant_pool_discount=0.60,
        historical_anchor_overdeterrence=0.55,
        rank_margin=0.10,
        tail_assignment_risk=0.20,
    )
    good = AdmissionContext.from_major_options(
        good_options,
        preferred_keywords=["数理"],
        major_obvious_heat=0.25,
        **base_kwargs,
    )
    risky = AdmissionContext.from_major_options(
        risky_options,
        preferred_keywords=["计算机"],
        major_obvious_heat=0.90,
        **base_kwargs,
    )

    assert good.front_major_quota_share > risky.front_major_quota_share
    assert good.front_major_hit_prob > risky.front_major_hit_prob + 0.20
    assert risky.tail_assignment_risk >= good.tail_assignment_risk


def test_arbitrage_result_survives_volunteer_plan_conversion():
    profile = UserProfile(score=590, rank=18888, subject_group="物理")
    row = MajorGroupRow(
        school_name="大连理工大学",
        school_code="10141",
        major_group_code="03",
        major_list=["数理基础科学", "应用化学", "环境生态工程"],
        major_count=3,
        major_options=[
            MajorOption(major_name="数理基础科学", plan_quota=12, user_utility=0.90),
            MajorOption(major_name="应用化学", plan_quota=14, user_utility=0.55),
            MajorOption(major_name="环境生态工程", plan_quota=12, user_utility=0.45),
        ],
        admission_prob=0.58,
        min_rank_pred=19000,
        rank_diff=112,
        rank_ci_lower=15000,
        rank_ci_upper=22000,
        volatility=VolatilityLevel.HIGH,
        quota=38,
        quota_bucket=QuotaBucket.MEDIUM,
        quota_stability_score=0.65,
        variance_opportunity_score=0.55,
        major_utility_mean=0.63,
        major_utility_min=0.45,
        major_utility_dispersion=0.45,
        tail_assignment_risk=0.18,
        strategy_tag=StrategyTag.RUSH,
        comprehensive_score=0.62,
    )

    result = score_arbitrage_opportunity(
        student=StudentValueModel(
            brand_face_weight=0.80,
            cost_sensitivity=0.10,
            tuition_tolerance=0.95,
            campus_tolerance=0.80,
        ),
        baseline=CounterfactualBaseline(school_tier=0.45, public_private=0.70),
        candidate=CandidateContext(
            school_tier=0.82,
            public_private=0.95,
            major_quality=0.62,
            brand_face=0.88,
            industry_prestige=0.78,
            front_major_value=0.82,
        ),
        sacrifice=SacrificeVector(tuition=0.85, campus=0.65, major=0.35),
        opportunity=OpportunitySignals(
            tuition_filter=0.85,
            campus_discount=0.65,
            historical_anchor_overdeterrence=0.70,
            low_attention_signal=0.55,
            rebound_risk=0.20,
        ),
        admission=AdmissionContext.from_major_options(
            row.major_options,
            preferred_keywords=["数理"],
            group_admission_prob=row.admission_prob,
            entrant_pool_discount=0.70,
            major_obvious_heat=0.20,
            rank_margin=0.15,
            tail_assignment_risk=row.tail_assignment_risk,
        ),
    )
    row.apply_arbitrage_result(result)

    plan = build_volunteer_plan([row], profile)
    choice = plan.choices[0]

    assert row.arbitrage_score == result.arbitrage_score
    assert "front_major_arbitrage_pool" in row.opportunity_pools
    assert choice.arbitrage_score == result.arbitrage_score
    assert choice.front_major_hit_prob == result.front_major_hit_prob
    assert "tuition_filter" in choice.opportunity_types


def test_adapter_scores_existing_major_group_row():
    profile = UserProfile(
        score=590,
        rank=18888,
        subject_group="物理",
        preferred_majors=["数理"],
        school_major_preference="prioritize_school",
    )
    row = MajorGroupRow(
        school_name="大连理工大学",
        school_code="10141",
        major_group_code="03",
        major_list=["数理基础科学", "应用化学", "环境生态工程"],
        major_count=3,
        major_options=[
            MajorOption(major_name="数理基础科学", plan_quota=12, tuition=80000, user_utility=0.90),
            MajorOption(major_name="应用化学", plan_quota=14, tuition=80000, user_utility=0.55),
            MajorOption(major_name="环境生态工程", plan_quota=12, tuition=80000, user_utility=0.45),
        ],
        admission_prob=0.58,
        min_rank_pred=19000,
        rank_diff=112,
        rank_ci_lower=15000,
        rank_ci_upper=22000,
        volatility=VolatilityLevel.HIGH,
        quota=38,
        quota_bucket=QuotaBucket.MEDIUM,
        quota_stability_score=0.65,
        variance_opportunity_score=0.55,
        major_utility_mean=0.63,
        major_utility_min=0.45,
        major_utility_dispersion=0.45,
        tail_assignment_risk=0.18,
        strategy_tag=StrategyTag.RUSH,
        comprehensive_score=0.62,
    )

    result = score_major_group_arbitrage(
        row=row,
        profile=profile,
        school_major_score=0.82,
        city_preference_score=0.90,
    )

    assert 0.0 <= result.arbitrage_score <= 1.0
    assert result.market_discount_score > 0.20
    assert result.front_major_hit_prob > 0.30
    assert row.arbitrage_score == result.arbitrage_score
    assert row.opportunity_pools


def test_runtime_policy_prefers_arbitrage_when_core_score_is_similar():
    base_kwargs = dict(
        school_name="测试大学",
        school_code="10001",
        major_group_code="201",
        major_list=["数理基础科学"],
        major_count=1,
        admission_prob=0.55,
        min_rank_pred=19000,
        rank_diff=100,
        rank_ci_lower=15000,
        rank_ci_upper=22000,
        volatility=VolatilityLevel.MEDIUM,
        quota=20,
        quota_bucket=QuotaBucket.MEDIUM,
        quota_stability_score=0.60,
        variance_opportunity_score=0.50,
        major_utility_mean=0.65,
        major_utility_min=0.55,
        major_utility_dispersion=0.20,
        tail_assignment_risk=0.20,
        strategy_tag=StrategyTag.RUSH,
        comprehensive_score=0.60,
    )
    high = MajorGroupRow(**base_kwargs)
    high.arbitrage_score = 0.75
    high.front_major_arbitrage_score = 0.25
    high.opportunity_pools = ["front_major_arbitrage_pool"]
    low = MajorGroupRow(**{**base_kwargs, "school_name": "普通测试大学"})
    low.arbitrage_score = 0.10
    low.front_major_arbitrage_score = 0.02

    params = PromptParameters()
    policy = RLRuntimePolicy()
    scores = {
        row.school_name: policy._policy_score(row, params, defaultdict(int))
        for row in [high, low]
    }

    assert scores["测试大学"] > scores["普通测试大学"]

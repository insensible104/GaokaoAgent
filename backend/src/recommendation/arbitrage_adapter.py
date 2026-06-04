"""Adapters from existing recommendation rows to the arbitrage model."""

from __future__ import annotations

from typing import Any, Sequence

from models.game_matrix import MajorGroupRow
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile

from .arbitrage_model import (
    AdmissionContext,
    CandidateContext,
    CounterfactualBaseline,
    OpportunitySignals,
    SacrificeVector,
    StudentValueModel,
    score_arbitrage_opportunity,
)
from .market_evidence import assess_market_evidence, build_decision_evidence_cards
from .market_simulation import score_segment_demand
from .research_evidence_features import derive_research_evidence_signals


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _rank_baseline_tier(rank: int | None) -> float:
    """Estimate same-rank conventional school tier from rank band."""
    if rank is None:
        return 0.45
    if rank <= 5_000:
        return 0.90
    if rank <= 15_000:
        return 0.78
    if rank <= 30_000:
        return 0.64
    if rank <= 60_000:
        return 0.50
    if rank <= 120_000:
        return 0.36
    return 0.24


def _tuition_level(row: MajorGroupRow) -> float:
    tuitions = [
        float(option.tuition)
        for option in row.major_options
        if option.tuition is not None and float(option.tuition) > 0
    ]
    if not tuitions:
        return 0.0
    max_tuition = max(tuitions)
    if max_tuition >= 60_000:
        return 0.90
    if max_tuition >= 30_000:
        return 0.65
    if max_tuition >= 15_000:
        return 0.35
    return 0.10


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _campus_discount(row: MajorGroupRow) -> float:
    text = f"{row.school_name} {' '.join(row.major_list)} " + " ".join(
        str(option.remarks or "") for option in row.major_options
    )
    if _contains_any(text, ("盘锦", "威海", "珠海", "海南", "异地", "校区", "分校")):
        return 0.65
    return 0.0


def _cold_major_discount(row: MajorGroupRow) -> float:
    names = " ".join(row.major_list)
    cold_keywords = (
        "环境",
        "化学",
        "材料",
        "生物",
        "旅游",
        "管理",
        "哲学",
        "历史",
        "社会学",
        "农学",
        "林学",
        "地质",
        "矿业",
    )
    if not row.major_list:
        return 0.0
    cold_count = sum(1 for major in row.major_list if _contains_any(major, cold_keywords))
    return _clamp(cold_count / len(row.major_list))


def _student_value_model(profile: UserProfile) -> StudentValueModel:
    school_first = profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_SCHOOL
    major_first = profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_MAJOR
    conservative = profile.risk_tolerance == RiskTolerance.CONSERVATIVE
    aggressive = profile.risk_tolerance == RiskTolerance.AGGRESSIVE

    cost_sensitivity = 0.55
    if any("学费" in item or "成本" in item or "预算" in item for item in profile.emotional_concerns):
        cost_sensitivity = 0.80

    return StudentValueModel(
        brand_face_weight=0.72 if school_first else 0.42,
        employment_roi_weight=0.72 if major_first else 0.48,
        public_school_preference=0.65,
        cost_sensitivity=cost_sensitivity,
        major_strictness=0.78 if major_first else 0.35,
        city_flexibility=0.35 if profile.preferred_cities else 0.65,
        region_tolerance=0.35 if profile.preferred_cities else 0.65,
        tuition_tolerance=1 - cost_sensitivity,
        campus_tolerance=0.45 if profile.preferred_cities else 0.65,
        pathway_tolerance=0.60,
        adjustment_tolerance=0.35 if conservative else (0.75 if aggressive else 0.55),
        employment_uncertainty_tolerance=0.35 if major_first else 0.60,
        regret_sensitivity=profile.regret_sensitivity,
    )


def _counterfactual_baseline(profile: UserProfile) -> CounterfactualBaseline:
    tier = _rank_baseline_tier(profile.rank)
    return CounterfactualBaseline(
        school_tier=tier,
        public_private=_clamp(tier + 0.12),
        major_quality=_clamp(tier + 0.05),
        city_tier=0.50,
        cost_type=0.30,
    )


def _candidate_context(
    *,
    row: MajorGroupRow,
    school_major_score: float,
    city_preference_score: float,
) -> CandidateContext:
    school_tier = _clamp(max(school_major_score, row.comprehensive_score, 0.35))
    return CandidateContext(
        school_tier=school_tier,
        public_private=_clamp(0.55 + school_tier * 0.40),
        major_quality=_clamp(row.major_utility_mean),
        city_tier=_clamp(0.50 + (city_preference_score - 1.0) * 0.35),
        cost_type=_tuition_level(row),
        industry_prestige=school_tier,
        brand_face=school_tier,
        front_major_value=_clamp(max((option.user_utility for option in row.major_options), default=row.major_utility_mean)),
    )


def _sacrifice_vector(row: MajorGroupRow, city_preference_score: float) -> SacrificeVector:
    tuition = _tuition_level(row)
    campus = _campus_discount(row)
    major = _clamp((1 - row.major_utility_mean) * 0.40 + row.major_utility_dispersion * 0.45)
    adjustment = _clamp(row.tail_assignment_risk)
    employment_uncertainty = _cold_major_discount(row) * 0.55 + row.major_utility_dispersion * 0.25
    region = _clamp(1 - city_preference_score) if city_preference_score < 1.0 else 0.0
    pathway = 0.35 if tuition >= 0.65 or campus >= 0.60 else 0.0
    return SacrificeVector(
        region=region,
        major=major,
        tuition=tuition,
        campus=campus,
        pathway=pathway,
        adjustment=adjustment,
        employment_uncertainty=_clamp(employment_uncertainty),
    )


def _opportunity_signals(
    row: MajorGroupRow,
    profile: UserProfile,
    assessment,
) -> OpportunitySignals:
    segment_demand = score_segment_demand(
        row=row,
        assessment=assessment,
        user_rank=profile.rank,
    )
    row.market_evidence_cards = assessment.card_dicts()
    row.market_evidence_strength = assessment.evidence_strength
    row.publicity_heat_score = assessment.publicity_heat_score
    row.publicity_rebound_risk = max(assessment.rebound_risk, segment_demand.rebound_risk_adjustment)
    row.segment_demand_score = segment_demand.segment_demand_score
    row.low_attention_signal = segment_demand.low_attention_signal
    row.segment_rebound_risk = segment_demand.rebound_risk_adjustment
    row.best_fit_archetypes = list(segment_demand.best_fit_archetypes)
    row.segment_demand_breakdown = dict(segment_demand.segment_breakdown)
    return OpportunitySignals(
        cold_major_discount=assessment.cold_major_discount,
        tuition_filter=assessment.tuition_filter,
        campus_discount=assessment.campus_discount,
        new_major_uncertainty=0.30 if row.major_count and row.major_count != len(row.major_list) else 0.0,
        group_restructure_score=assessment.group_restructure_score,
        historical_anchor_overdeterrence=assessment.historical_anchor_overdeterrence,
        low_attention_signal=segment_demand.low_attention_signal,
        sentiment_shock_discount=assessment.sentiment_shock_discount,
        quota_expansion_score=assessment.quota_pressure,
        evidence_strength=assessment.evidence_strength,
        rebound_risk=row.publicity_rebound_risk,
    )


def score_major_group_arbitrage(
    *,
    row: MajorGroupRow,
    profile: UserProfile,
    school_major_score: float,
    city_preference_score: float,
    research_evidence_cards: Sequence[dict[str, Any]] | None = None,
) -> object:
    """Score and attach personalized arbitrage signals to an existing row."""
    research_signals = None
    if research_evidence_cards:
        research_signals = derive_research_evidence_signals(
            research_evidence_cards,
            scope_terms=[
                row.school_name,
                row.school_code,
                row.major_group_code,
                *row.major_list,
            ],
        )
        row.plan_change_score = max(
            row.plan_change_score,
            research_signals.plan_change_signal,
            research_signals.quota_change_signal,
            research_signals.major_group_restructure_signal,
        )
        if research_signals.plan_change_signal > 0:
            row.plan_change_types.append("research_plan_change")
        if research_signals.quota_change_signal > 0:
            row.plan_change_types.append("research_quota_change")
        if research_signals.major_group_restructure_signal > 0:
            row.plan_change_types.append("research_major_group_restructure")
        if research_signals.publicity_heat_signal > 0:
            row.market_behavior_notes.append("Research evidence indicates public attention or creator heat.")
        row.plan_change_evidence.extend(research_signals.warnings)
        if research_signals.reference_only_card_count and not research_signals.prediction_ready:
            row.audit_flags.append("research_evidence_reference_only")

    assessment = assess_market_evidence(
        row,
        external_cards=research_signals.feature_cards if research_signals else None,
    )
    preferred_keywords = profile.preferred_majors or row.major_list[:1]
    admission = AdmissionContext.from_major_options(
        row.major_options,
        preferred_keywords=preferred_keywords,
        group_admission_prob=row.admission_prob,
        entrant_pool_discount=_clamp(row.variance_opportunity_score),
        historical_anchor_overdeterrence=_clamp(row.variance_opportunity_score),
        major_obvious_heat=_clamp(row.major_utility_mean * 0.55 + row.quota_stability_score * 0.20),
        rank_margin=_clamp(row.rank_diff / max(row.min_rank_pred, 1) + 0.10),
        tail_assignment_risk=row.tail_assignment_risk,
    )
    result = score_arbitrage_opportunity(
        student=_student_value_model(profile),
        baseline=_counterfactual_baseline(profile),
        candidate=_candidate_context(
            row=row,
            school_major_score=school_major_score,
            city_preference_score=city_preference_score,
        ),
        sacrifice=_sacrifice_vector(row, city_preference_score),
        opportunity=_opportunity_signals(row, profile, assessment),
        admission=admission,
    )
    row.apply_arbitrage_result(result)
    decision_cards = build_decision_evidence_cards(
        row=row,
        profile=profile,
        assessment=assessment,
    )
    row.market_evidence_cards.extend(card.to_dict() for card in decision_cards)
    return result

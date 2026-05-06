"""Score-band aware tradeoff policy for major-group recommendation.

This module turns domain judgment into auditable features. It models three
questions that are easy to miss in a plain top-k recommender:

1. What matters at this rank band?
2. What will other families also chase in parallel-volunteer filing?
3. Which user pain point does this row create or reduce?
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from models.game_matrix import MajorGroupRow, QuotaBucket, StrategyTag
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class ScoreBandPolicy:
    band_name: str
    rank_min: int
    rank_max: int
    school_weight: float
    major_weight: float
    city_weight: float
    admission_weight: float
    safety_weight: float
    upside_weight: float
    quota_stability_weight: float
    variance_opportunity_weight: float
    tail_risk_penalty_weight: float
    crowding_penalty_weight: float
    pain_point_focus: str


@dataclass(frozen=True)
class TradeoffScoreResult:
    final_score: float
    score_band: str
    breakdown: Dict[str, float]
    pain_point_flags: List[str]
    market_behavior_notes: List[str]
    summary: str


BASE_POLICIES: List[ScoreBandPolicy] = [
    ScoreBandPolicy(
        band_name="top_platform",
        rank_min=1,
        rank_max=5000,
        school_weight=0.32,
        major_weight=0.22,
        city_weight=0.06,
        admission_weight=0.14,
        safety_weight=0.08,
        upside_weight=0.18,
        quota_stability_weight=0.06,
        variance_opportunity_weight=0.10,
        tail_risk_penalty_weight=0.22,
        crowding_penalty_weight=0.16,
        pain_point_focus="avoid wasting rare top-rank optionality",
    ),
    ScoreBandPolicy(
        band_name="strong_985_211",
        rank_min=5000,
        rank_max=15000,
        school_weight=0.27,
        major_weight=0.25,
        city_weight=0.08,
        admission_weight=0.17,
        safety_weight=0.10,
        upside_weight=0.13,
        quota_stability_weight=0.08,
        variance_opportunity_weight=0.09,
        tail_risk_penalty_weight=0.23,
        crowding_penalty_weight=0.17,
        pain_point_focus="balance platform, major, and first-hit regret",
    ),
    ScoreBandPolicy(
        band_name="upper_middle_choice_rich",
        rank_min=15000,
        rank_max=30000,
        school_weight=0.21,
        major_weight=0.30,
        city_weight=0.10,
        admission_weight=0.20,
        safety_weight=0.13,
        upside_weight=0.08,
        quota_stability_weight=0.10,
        variance_opportunity_weight=0.07,
        tail_risk_penalty_weight=0.26,
        crowding_penalty_weight=0.18,
        pain_point_focus="avoid being pulled by title while missing better-fit majors",
    ),
    ScoreBandPolicy(
        band_name="middle_stability_sensitive",
        rank_min=30000,
        rank_max=60000,
        school_weight=0.15,
        major_weight=0.34,
        city_weight=0.12,
        admission_weight=0.23,
        safety_weight=0.18,
        upside_weight=0.05,
        quota_stability_weight=0.13,
        variance_opportunity_weight=0.05,
        tail_risk_penalty_weight=0.30,
        crowding_penalty_weight=0.16,
        pain_point_focus="reduce sliding risk and major-mismatch regret",
    ),
    ScoreBandPolicy(
        band_name="broad_safety_first",
        rank_min=60000,
        rank_max=10_000_000,
        school_weight=0.10,
        major_weight=0.36,
        city_weight=0.13,
        admission_weight=0.26,
        safety_weight=0.24,
        upside_weight=0.03,
        quota_stability_weight=0.15,
        variance_opportunity_weight=0.03,
        tail_risk_penalty_weight=0.34,
        crowding_penalty_weight=0.12,
        pain_point_focus="secure admission before chasing noisy upside",
    ),
]


def get_score_band_policy(rank: int | None) -> ScoreBandPolicy:
    effective_rank = rank or 10_000_000
    for policy in BASE_POLICIES:
        if policy.rank_min <= effective_rank < policy.rank_max:
            return policy
    return BASE_POLICIES[-1]


def _policy_weights_for_profile(policy: ScoreBandPolicy, profile: UserProfile) -> Dict[str, float]:
    weights = {
        "school": policy.school_weight,
        "major": policy.major_weight,
        "city": policy.city_weight,
        "admission": policy.admission_weight,
        "safety": policy.safety_weight,
        "upside": policy.upside_weight,
        "quota_stability": policy.quota_stability_weight,
        "variance_opportunity": policy.variance_opportunity_weight,
        "tail_risk_penalty": policy.tail_risk_penalty_weight,
        "crowding_penalty": policy.crowding_penalty_weight,
    }

    if profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_SCHOOL:
        weights["school"] += 0.08
        weights["major"] = max(0.05, weights["major"] - 0.06)
    elif profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_MAJOR:
        weights["major"] += 0.08
        weights["school"] = max(0.05, weights["school"] - 0.07)

    if profile.risk_tolerance == RiskTolerance.CONSERVATIVE:
        weights["safety"] += 0.08
        weights["admission"] += 0.04
        weights["upside"] = max(0.0, weights["upside"] - 0.04)
        weights["tail_risk_penalty"] += 0.06
    elif profile.risk_tolerance == RiskTolerance.AGGRESSIVE:
        weights["upside"] += 0.06
        weights["safety"] = max(0.0, weights["safety"] - 0.04)
        weights["tail_risk_penalty"] = max(0.05, weights["tail_risk_penalty"] - 0.03)

    return weights


def _city_value(city_preference_score: float) -> float:
    if city_preference_score <= 0.5:
        return 0.10
    if city_preference_score >= 1.3:
        return 1.00
    return _clamp(0.50 + (city_preference_score - 1.0))


def _crowding_risk(
    *,
    row: MajorGroupRow,
    school_major_value: float,
    city_preference_score: float,
) -> float:
    obvious_value = max(school_major_value, row.major_utility_mean)
    small_quota_pressure = 1.0 - row.quota_stability_score
    hot_city_signal = 1.0 if city_preference_score > 1.0 else 0.0
    boundary_signal = 1.0 if row.strategy_tag in {StrategyTag.RUSH, StrategyTag.TARGET} else 0.45
    return _clamp(
        (
            obvious_value * 0.42
            + row.major_utility_mean * 0.22
            + small_quota_pressure * 0.22
            + hot_city_signal * 0.14
        )
        * boundary_signal
    )


def _market_notes(
    *,
    row: MajorGroupRow,
    crowding_risk: float,
) -> List[str]:
    notes: List[str] = []
    if crowding_risk >= 0.62:
        notes.append("crowding_risk: obvious school/major signal may attract similar applicants")
    if row.quota_bucket == QuotaBucket.SMALL and row.variance_opportunity_score >= 0.60:
        notes.append("small_quota_lottery: high variance can create both leak opportunity and sliding risk")
    if row.quota_bucket == QuotaBucket.LARGE and row.quota_stability_score >= 0.65:
        notes.append("large_quota_anchor: larger plan size supports stability")
    if row.major_utility_dispersion >= 0.45:
        notes.append("mixed_group_game: attractive front majors may hide tail-assignment regret")
    if row.strategy_tag == StrategyTag.RUSH and row.admission_prob >= 0.45:
        notes.append("parallel_volunteer_upside: can be useful before safer anchors")
    return notes


def _pain_points(
    *,
    row: MajorGroupRow,
    city_preference_score: float,
    crowding_risk: float,
    school_major_value: float,
) -> List[str]:
    flags: List[str] = []
    if row.strategy_tag == StrategyTag.RUSH or row.admission_prob < 0.60:
        flags.append("sliding_anxiety")
    if row.strategy_tag == StrategyTag.SAFE and row.admission_prob >= 0.92 and school_major_value < 0.55:
        flags.append("wasted_score_anxiety")
    if row.tail_assignment_risk >= 0.55:
        flags.append("tail_major_regret")
    if row.major_utility_dispersion >= 0.45:
        flags.append("bait_major_group")
    if city_preference_score < 1.0:
        flags.append("city_mismatch")
    if crowding_risk >= 0.62:
        flags.append("herding_crowding")
    if row.quota_bucket == QuotaBucket.SMALL and row.variance_opportunity_score >= 0.60:
        flags.append("high_variance_opportunity")
    return flags


def score_tradeoff(
    *,
    row: MajorGroupRow,
    profile: UserProfile,
    school_major_score: float,
    city_preference_score: float,
) -> TradeoffScoreResult:
    """Score one major group with rank-band and market-behavior awareness."""
    policy = get_score_band_policy(profile.rank)
    weights = _policy_weights_for_profile(policy, profile)

    school_major_value = _clamp(school_major_score)
    major_value = _clamp(row.major_utility_mean)
    city_value = _city_value(city_preference_score)
    admission_value = _clamp(row.admission_prob)
    safety_value = _clamp(row.admission_prob * 0.65 + row.quota_stability_score * 0.35)
    upside_value = _clamp((1.0 - row.admission_prob) * row.variance_opportunity_score)
    quota_stability = _clamp(row.quota_stability_score)
    variance_opportunity = _clamp(row.variance_opportunity_score)
    crowding_risk = _crowding_risk(
        row=row,
        school_major_value=school_major_value,
        city_preference_score=city_preference_score,
    )

    positive_terms = {
        "school": school_major_value * weights["school"],
        "major": major_value * weights["major"],
        "city": city_value * weights["city"],
        "admission": admission_value * weights["admission"],
        "safety": safety_value * weights["safety"],
        "upside": upside_value * weights["upside"],
        "quota_stability": quota_stability * weights["quota_stability"],
        "variance_opportunity": variance_opportunity * weights["variance_opportunity"],
    }
    positive_weight_sum = sum(
        weights[key]
        for key in (
            "school",
            "major",
            "city",
            "admission",
            "safety",
            "upside",
            "quota_stability",
            "variance_opportunity",
        )
    )
    positive_score = sum(positive_terms.values()) / max(positive_weight_sum, 1e-6)
    tail_penalty = row.tail_assignment_risk * weights["tail_risk_penalty"]
    crowding_penalty = crowding_risk * weights["crowding_penalty"]
    blacklist_penalty = 0.18 if row.is_blacklist_risk else 0.0
    final_score = _clamp(positive_score - tail_penalty - crowding_penalty - blacklist_penalty)

    breakdown = {
        "school_value": round(school_major_value, 4),
        "major_value": round(major_value, 4),
        "city_value": round(city_value, 4),
        "admission_value": round(admission_value, 4),
        "safety_value": round(safety_value, 4),
        "upside_value": round(upside_value, 4),
        "quota_stability": round(quota_stability, 4),
        "variance_opportunity": round(variance_opportunity, 4),
        "tail_risk_penalty": round(tail_penalty, 4),
        "crowding_risk": round(crowding_risk, 4),
        "crowding_penalty": round(crowding_penalty, 4),
        "blacklist_penalty": round(blacklist_penalty, 4),
        "positive_score": round(positive_score, 4),
        "final_score": round(final_score, 4),
    }

    pain_flags = _pain_points(
        row=row,
        city_preference_score=city_preference_score,
        crowding_risk=crowding_risk,
        school_major_value=school_major_value,
    )
    market_notes = _market_notes(row=row, crowding_risk=crowding_risk)
    summary = (
        f"{policy.band_name}: {policy.pain_point_focus}; "
        f"score={final_score:.3f}, crowding={crowding_risk:.3f}, "
        f"tail_risk={row.tail_assignment_risk:.3f}"
    )

    return TradeoffScoreResult(
        final_score=round(final_score, 4),
        score_band=policy.band_name,
        breakdown=breakdown,
        pain_point_flags=pain_flags,
        market_behavior_notes=market_notes,
        summary=summary,
    )

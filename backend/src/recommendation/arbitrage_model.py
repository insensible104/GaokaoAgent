"""Quantitative opportunity-arbitrage model for major-group recommendation.

This module models volunteer-planning "leaks" as conditional arbitrage:
the market discounts a school-major group for a concrete reason, and a
specific student can absorb that reason better than the average applicant.
It is intentionally transparent so every score can be audited and backtested.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp
from typing import Iterable, Sequence

from models.game_matrix import MajorOption


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _weighted_mean(terms: Iterable[tuple[float, float]]) -> float:
    numerator = 0.0
    denominator = 0.0
    for value, weight in terms:
        numerator += _clamp(value) * max(0.0, weight)
        denominator += max(0.0, weight)
    if denominator <= 0:
        return 0.0
    return _clamp(numerator / denominator)


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + exp(-value))


@dataclass(frozen=True)
class StudentValueModel:
    """Student/family utility weights and tolerance for sacrifice sources."""

    brand_face_weight: float = 0.50
    employment_roi_weight: float = 0.50
    public_school_preference: float = 0.50
    cost_sensitivity: float = 0.50
    major_strictness: float = 0.50
    city_flexibility: float = 0.50
    region_tolerance: float = 0.50
    tuition_tolerance: float = 0.50
    campus_tolerance: float = 0.50
    pathway_tolerance: float = 0.50
    adjustment_tolerance: float = 0.50
    employment_uncertainty_tolerance: float = 0.50
    regret_sensitivity: float = 0.50


@dataclass(frozen=True)
class CounterfactualBaseline:
    """Expected same-rank conventional outcome before arbitrage."""

    school_tier: float
    public_private: float = 0.50
    major_quality: float = 0.50
    city_tier: float = 0.50
    cost_type: float = 0.50


@dataclass(frozen=True)
class CandidateContext:
    """Value signals for a candidate school-major group."""

    school_tier: float
    public_private: float = 0.50
    major_quality: float = 0.50
    city_tier: float = 0.50
    cost_type: float = 0.50
    industry_prestige: float = 0.50
    brand_face: float = 0.50
    front_major_value: float = 0.50


@dataclass(frozen=True)
class SacrificeVector:
    """Costs the applicant must accept to exploit a discounted opportunity."""

    region: float = 0.0
    major: float = 0.0
    tuition: float = 0.0
    campus: float = 0.0
    pathway: float = 0.0
    adjustment: float = 0.0
    employment_uncertainty: float = 0.0


@dataclass(frozen=True)
class OpportunitySignals:
    """Market-discount signals available before admission outcomes are known."""

    cold_major_discount: float = 0.0
    tuition_filter: float = 0.0
    campus_discount: float = 0.0
    region_discount: float = 0.0
    new_major_uncertainty: float = 0.0
    group_restructure_score: float = 0.0
    historical_anchor_overdeterrence: float = 0.0
    standalone_major_anchor_discount: float = 0.0
    low_attention_signal: float = 0.0
    sentiment_shock_discount: float = 0.0
    quota_expansion_score: float = 0.0
    evidence_strength: float = 0.50
    rebound_risk: float = 0.0

    def active_types(self, threshold: float = 0.45) -> list[str]:
        """Return the discount mechanisms strong enough to explain the opportunity."""
        signal_names = (
            "cold_major_discount",
            "tuition_filter",
            "campus_discount",
            "region_discount",
            "new_major_uncertainty",
            "group_restructure_score",
            "historical_anchor_overdeterrence",
            "standalone_major_anchor_discount",
            "low_attention_signal",
            "sentiment_shock_discount",
            "quota_expansion_score",
        )
        return [
            name
            for name in signal_names
            if getattr(self, name) >= threshold
        ]


@dataclass(frozen=True)
class AdmissionContext:
    """Admission and within-group assignment context."""

    group_admission_prob: float
    front_major_quota_share: float = 0.0
    entrant_pool_discount: float = 0.0
    historical_anchor_overdeterrence: float = 0.0
    major_obvious_heat: float = 0.0
    rank_margin: float = 0.0
    tail_assignment_risk: float = 0.0
    front_major_hit_prob: float | None = None

    def __post_init__(self) -> None:
        if self.front_major_hit_prob is None:
            object.__setattr__(self, "front_major_hit_prob", self.estimate_front_major_hit_prob())
        else:
            object.__setattr__(self, "front_major_hit_prob", _clamp(self.front_major_hit_prob))
        object.__setattr__(self, "group_admission_prob", _clamp(self.group_admission_prob))
        object.__setattr__(self, "tail_assignment_risk", _clamp(self.tail_assignment_risk))

    @classmethod
    def from_major_options(
        cls,
        options: Sequence[MajorOption],
        *,
        preferred_keywords: Sequence[str],
        group_admission_prob: float,
        entrant_pool_discount: float = 0.0,
        historical_anchor_overdeterrence: float = 0.0,
        major_obvious_heat: float = 0.0,
        rank_margin: float = 0.0,
        tail_assignment_risk: float = 0.0,
    ) -> "AdmissionContext":
        """Build assignment context from in-group major options and quotas."""
        total_quota = sum(max(0, option.plan_quota or 0) for option in options)
        normalized_keywords = [keyword.strip() for keyword in preferred_keywords if keyword.strip()]

        front_options = [
            option
            for option in options
            if any(keyword in option.major_name for keyword in normalized_keywords)
        ]
        if not front_options and options:
            front_options = [max(options, key=lambda option: option.user_utility)]

        front_quota = sum(max(0, option.plan_quota or 0) for option in front_options)
        front_major_quota_share = front_quota / total_quota if total_quota > 0 else 0.0

        utilities = [option.user_utility for option in options] or [0.5]
        acceptable_ratio = sum(1 for option in options if option.is_acceptable) / max(1, len(options))
        utility_dispersion = max(utilities) - min(utilities)
        inferred_tail_risk = _clamp(
            (1 - min(utilities)) * 0.35
            + utility_dispersion * 0.25
            + (1 - acceptable_ratio) * 0.30
        )

        return cls(
            group_admission_prob=group_admission_prob,
            front_major_quota_share=front_major_quota_share,
            entrant_pool_discount=entrant_pool_discount,
            historical_anchor_overdeterrence=historical_anchor_overdeterrence,
            major_obvious_heat=major_obvious_heat,
            rank_margin=rank_margin,
            tail_assignment_risk=max(tail_assignment_risk, inferred_tail_risk),
        )

    def estimate_front_major_hit_prob(self) -> float:
        """Estimate P(front major hit | group admitted) with transparent proxies."""
        logit = (
            -1.05
            + 3.20 * _clamp(self.front_major_quota_share)
            + 1.15 * _clamp(self.entrant_pool_discount)
            + 0.85 * _clamp(self.historical_anchor_overdeterrence)
            + 0.70 * _clamp(self.rank_margin)
            - 1.35 * _clamp(self.major_obvious_heat)
            - 0.85 * _clamp(self.tail_assignment_risk)
        )
        return _clamp(_sigmoid(logit))


@dataclass(frozen=True)
class ArbitrageScoreResult:
    """Auditable result of one student-group arbitrage calculation."""

    arbitrage_score: float
    front_major_arbitrage_score: float
    relative_lift: float
    market_discount_score: float
    personal_acceptability: float
    sacrifice_cost: float
    assignment_opportunity: float
    front_major_hit_prob: float
    rebound_risk: float
    tail_assignment_risk: float
    opportunity_types: list[str] = field(default_factory=list)
    breakdown: dict[str, float] = field(default_factory=dict)


def estimate_relative_lift(
    *,
    student: StudentValueModel,
    baseline: CounterfactualBaseline,
    candidate: CandidateContext,
) -> float:
    """Estimate how much the candidate improves over same-rank conventional choices."""
    school_lift = candidate.school_tier - baseline.school_tier
    public_lift = candidate.public_private - baseline.public_private
    major_lift = candidate.major_quality - baseline.major_quality
    city_lift = candidate.city_tier - baseline.city_tier
    brand_lift = candidate.brand_face - baseline.school_tier
    industry_lift = candidate.industry_prestige - baseline.school_tier

    lift = _weighted_mean(
        (
            (_clamp((school_lift + 1) / 2), 0.28 + student.brand_face_weight * 0.12),
            (_clamp((public_lift + 1) / 2), 0.14 + student.public_school_preference * 0.10),
            (_clamp((major_lift + 1) / 2), 0.14 + student.employment_roi_weight * 0.10),
            (_clamp((city_lift + 1) / 2), 0.08 + student.city_flexibility * 0.06),
            (_clamp((brand_lift + 1) / 2), 0.18 + student.brand_face_weight * 0.16),
            (_clamp((industry_lift + 1) / 2), 0.10 + student.brand_face_weight * 0.08),
        )
    )
    return _clamp((lift - 0.50) * 2.0)


def estimate_sacrifice_cost(
    *,
    student: StudentValueModel,
    sacrifice: SacrificeVector,
) -> float:
    """Estimate personalized cost of accepting the discount source."""
    components = (
        sacrifice.region * (1 - student.region_tolerance),
        sacrifice.major * student.major_strictness,
        sacrifice.tuition * student.cost_sensitivity * (1 - student.tuition_tolerance),
        sacrifice.campus * (1 - student.campus_tolerance),
        sacrifice.pathway * (1 - student.pathway_tolerance),
        sacrifice.adjustment * (1 - student.adjustment_tolerance),
        sacrifice.employment_uncertainty
        * student.employment_roi_weight
        * (1 - student.employment_uncertainty_tolerance),
    )
    weighted_cost = _weighted_mean(
        (
            (components[0], 0.12),
            (components[1], 0.18),
            (components[2], 0.22),
            (components[3], 0.12),
            (components[4], 0.12),
            (components[5], 0.12),
            (components[6], 0.12),
        )
    )
    # A single hard blocker, such as unaffordable tuition, should not be averaged
    # away by many easy sacrifices.
    blocker_cost = max(components)
    return _clamp(0.55 * weighted_cost + 0.45 * blocker_cost)


def estimate_market_discount(signals: OpportunitySignals) -> float:
    """Estimate whether the group is cheap for structural, behavioral reasons."""
    positive = _weighted_mean(
        (
            (signals.cold_major_discount, 0.11),
            (signals.tuition_filter, 0.12),
            (signals.campus_discount, 0.10),
            (signals.region_discount, 0.08),
            (signals.new_major_uncertainty, 0.10),
            (signals.group_restructure_score, 0.12),
            (signals.historical_anchor_overdeterrence, 0.15),
            (signals.standalone_major_anchor_discount, 0.10),
            (signals.low_attention_signal, 0.10),
            (signals.sentiment_shock_discount, 0.06),
            (signals.quota_expansion_score, 0.06),
        )
    )
    return _clamp(positive * (0.55 + 0.45 * _clamp(signals.evidence_strength)))


def score_arbitrage_opportunity(
    *,
    student: StudentValueModel,
    baseline: CounterfactualBaseline,
    candidate: CandidateContext,
    sacrifice: SacrificeVector,
    opportunity: OpportunitySignals,
    admission: AdmissionContext,
) -> ArbitrageScoreResult:
    """Score a candidate as a personalized arbitrage opportunity."""
    relative_lift = estimate_relative_lift(student=student, baseline=baseline, candidate=candidate)
    sacrifice_cost = estimate_sacrifice_cost(student=student, sacrifice=sacrifice)
    market_discount = estimate_market_discount(opportunity)
    personal_acceptability = _clamp(1 - sacrifice_cost)
    assignment_opportunity = _clamp(
        0.65 * (admission.front_major_hit_prob or 0.0)
        + 0.35 * (1 - admission.tail_assignment_risk)
    )
    admission_feasibility = _clamp(admission.group_admission_prob)
    rebound_risk = _clamp(opportunity.rebound_risk)
    tail_risk = _clamp(admission.tail_assignment_risk)

    positive = (
        0.26 * relative_lift
        + 0.20 * market_discount
        + 0.20 * personal_acceptability
        + 0.18 * admission_feasibility
        + 0.16 * assignment_opportunity
    )
    penalties = 0.32 * sacrifice_cost + 0.18 * tail_risk + 0.16 * rebound_risk
    arbitrage_score = _clamp(positive - penalties + 0.12)

    front_major_arbitrage_score = _clamp(
        admission_feasibility
        * (admission.front_major_hit_prob or 0.0)
        * _clamp(candidate.front_major_value)
        * _clamp(0.55 + 0.45 * relative_lift)
        * personal_acceptability
        * _clamp(1 - rebound_risk)
        * _clamp(1 - tail_risk * 0.60)
    )

    breakdown = {
        "relative_lift": round(relative_lift, 4),
        "market_discount_score": round(market_discount, 4),
        "personal_acceptability": round(personal_acceptability, 4),
        "sacrifice_cost": round(sacrifice_cost, 4),
        "group_admission_prob": round(admission_feasibility, 4),
        "assignment_opportunity": round(assignment_opportunity, 4),
        "front_major_hit_prob": round(admission.front_major_hit_prob or 0.0, 4),
        "tail_assignment_risk": round(tail_risk, 4),
        "rebound_risk": round(rebound_risk, 4),
        "arbitrage_score": round(arbitrage_score, 4),
        "front_major_arbitrage_score": round(front_major_arbitrage_score, 4),
    }

    return ArbitrageScoreResult(
        arbitrage_score=round(arbitrage_score, 4),
        front_major_arbitrage_score=round(front_major_arbitrage_score, 4),
        relative_lift=round(relative_lift, 4),
        market_discount_score=round(market_discount, 4),
        personal_acceptability=round(personal_acceptability, 4),
        sacrifice_cost=round(sacrifice_cost, 4),
        assignment_opportunity=round(assignment_opportunity, 4),
        front_major_hit_prob=round(admission.front_major_hit_prob or 0.0, 4),
        rebound_risk=round(rebound_risk, 4),
        tail_assignment_risk=round(tail_risk, 4),
        opportunity_types=opportunity.active_types(),
        breakdown=breakdown,
    )

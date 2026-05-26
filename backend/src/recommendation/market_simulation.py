"""Segment-demand simulation for admission-market arbitrage.

The model is deliberately small and auditable. It does not try to simulate
thousands of applicants; it turns a dozen interpretable student/family
archetypes into quantitative demand signals that can be backtested.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from models.game_matrix import MajorGroupRow, QuotaBucket

from .arbitrage_model import SacrificeVector, StudentValueModel, estimate_sacrifice_cost
from .market_evidence import MarketEvidenceAssessment


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _rank_baseline_tier(rank: int | None) -> float:
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


@dataclass(frozen=True)
class StudentArchetype:
    """Interpretable student/family segment used for market-demand scoring."""

    name: str
    label: str
    value_model: StudentValueModel
    segment_share: float
    publicity_susceptibility: float = 0.50
    narrative: str = ""


@dataclass(frozen=True)
class SegmentDemandResult:
    """Auditable demand signals generated from student/family archetypes."""

    segment_demand_score: float
    low_attention_signal: float
    rebound_risk_adjustment: float
    best_fit_archetypes: list[str] = field(default_factory=list)
    segment_breakdown: dict[str, float] = field(default_factory=dict)
    segment_notes: list[str] = field(default_factory=list)


def default_student_archetypes() -> list[StudentArchetype]:
    """Return the first-layer archetypes for volunteer-market simulation."""
    return [
        StudentArchetype(
            name="brand_face_family",
            label="Brand/status seeking family",
            segment_share=0.08,
            publicity_susceptibility=0.55,
            narrative="Prioritizes school tier and public face; can accept cost and pathway sacrifice.",
            value_model=StudentValueModel(
                brand_face_weight=0.92,
                employment_roi_weight=0.28,
                cost_sensitivity=0.10,
                major_strictness=0.22,
                city_flexibility=0.72,
                region_tolerance=0.75,
                tuition_tolerance=0.95,
                campus_tolerance=0.82,
                pathway_tolerance=0.80,
                adjustment_tolerance=0.70,
                employment_uncertainty_tolerance=0.72,
                regret_sensitivity=0.35,
            ),
        ),
        StudentArchetype(
            name="employment_roi_family",
            label="Employment ROI family",
            segment_share=0.14,
            publicity_susceptibility=0.35,
            narrative="Prefers employable majors and dislikes expensive low-ROI sacrifices.",
            value_model=StudentValueModel(
                brand_face_weight=0.30,
                employment_roi_weight=0.90,
                cost_sensitivity=0.78,
                major_strictness=0.82,
                city_flexibility=0.48,
                region_tolerance=0.45,
                tuition_tolerance=0.20,
                campus_tolerance=0.42,
                pathway_tolerance=0.35,
                adjustment_tolerance=0.32,
                employment_uncertainty_tolerance=0.22,
                regret_sensitivity=0.72,
            ),
        ),
        StudentArchetype(
            name="high_tuition_taker",
            label="High tuition filter taker",
            segment_share=0.06,
            publicity_susceptibility=0.50,
            narrative="Uses tuition as a demand filter to exchange money for a higher school tier.",
            value_model=StudentValueModel(
                brand_face_weight=0.78,
                employment_roi_weight=0.42,
                cost_sensitivity=0.08,
                major_strictness=0.38,
                city_flexibility=0.68,
                region_tolerance=0.70,
                tuition_tolerance=0.98,
                campus_tolerance=0.74,
                pathway_tolerance=0.82,
                adjustment_tolerance=0.62,
                employment_uncertainty_tolerance=0.58,
                regret_sensitivity=0.42,
            ),
        ),
        StudentArchetype(
            name="major_purist",
            label="Major purist",
            segment_share=0.10,
            publicity_susceptibility=0.28,
            narrative="Accepts lower school tier if the major is clearly better.",
            value_model=StudentValueModel(
                brand_face_weight=0.24,
                employment_roi_weight=0.86,
                cost_sensitivity=0.55,
                major_strictness=0.92,
                city_flexibility=0.48,
                region_tolerance=0.42,
                tuition_tolerance=0.45,
                campus_tolerance=0.36,
                pathway_tolerance=0.30,
                adjustment_tolerance=0.18,
                employment_uncertainty_tolerance=0.28,
                regret_sensitivity=0.82,
            ),
        ),
        StudentArchetype(
            name="adjustment_tolerant_climber",
            label="Adjustment-tolerant tier climber",
            segment_share=0.08,
            publicity_susceptibility=0.44,
            narrative="Accepts within-group uncertainty to reach a higher school tier.",
            value_model=StudentValueModel(
                brand_face_weight=0.78,
                employment_roi_weight=0.42,
                cost_sensitivity=0.36,
                major_strictness=0.24,
                city_flexibility=0.64,
                region_tolerance=0.66,
                tuition_tolerance=0.62,
                campus_tolerance=0.66,
                pathway_tolerance=0.66,
                adjustment_tolerance=0.92,
                employment_uncertainty_tolerance=0.64,
                regret_sensitivity=0.30,
            ),
        ),
        StudentArchetype(
            name="region_discount_taker",
            label="Region discount taker",
            segment_share=0.09,
            publicity_susceptibility=0.40,
            narrative="Accepts less popular cities or distant regions for a school-tier lift.",
            value_model=StudentValueModel(
                brand_face_weight=0.68,
                employment_roi_weight=0.48,
                cost_sensitivity=0.42,
                major_strictness=0.36,
                city_flexibility=0.88,
                region_tolerance=0.92,
                tuition_tolerance=0.58,
                campus_tolerance=0.70,
                pathway_tolerance=0.58,
                adjustment_tolerance=0.58,
                employment_uncertainty_tolerance=0.56,
                regret_sensitivity=0.38,
            ),
        ),
        StudentArchetype(
            name="campus_discount_taker",
            label="Branch-campus discount taker",
            segment_share=0.08,
            publicity_susceptibility=0.45,
            narrative="Accepts branch campuses, remote campuses, or special pathways.",
            value_model=StudentValueModel(
                brand_face_weight=0.76,
                employment_roi_weight=0.44,
                cost_sensitivity=0.35,
                major_strictness=0.34,
                city_flexibility=0.70,
                region_tolerance=0.72,
                tuition_tolerance=0.68,
                campus_tolerance=0.94,
                pathway_tolerance=0.78,
                adjustment_tolerance=0.60,
                employment_uncertainty_tolerance=0.58,
                regret_sensitivity=0.36,
            ),
        ),
        StudentArchetype(
            name="conservative_safe_family",
            label="Conservative safety family",
            segment_share=0.14,
            publicity_susceptibility=0.32,
            narrative="Prioritizes admission certainty and avoids high tail risk.",
            value_model=StudentValueModel(
                brand_face_weight=0.42,
                employment_roi_weight=0.62,
                cost_sensitivity=0.58,
                major_strictness=0.66,
                city_flexibility=0.42,
                region_tolerance=0.38,
                tuition_tolerance=0.40,
                campus_tolerance=0.42,
                pathway_tolerance=0.34,
                adjustment_tolerance=0.18,
                employment_uncertainty_tolerance=0.32,
                regret_sensitivity=0.86,
            ),
        ),
        StudentArchetype(
            name="risk_seeking_arbitrageur",
            label="Risk-seeking arbitrageur",
            segment_share=0.05,
            publicity_susceptibility=0.52,
            narrative="Actively searches for volatile mispricing and can tolerate uncertainty.",
            value_model=StudentValueModel(
                brand_face_weight=0.70,
                employment_roi_weight=0.54,
                cost_sensitivity=0.34,
                major_strictness=0.32,
                city_flexibility=0.78,
                region_tolerance=0.78,
                tuition_tolerance=0.66,
                campus_tolerance=0.76,
                pathway_tolerance=0.76,
                adjustment_tolerance=0.84,
                employment_uncertainty_tolerance=0.70,
                regret_sensitivity=0.24,
            ),
        ),
        StudentArchetype(
            name="information_advantaged_family",
            label="Information-advantaged family",
            segment_share=0.05,
            publicity_susceptibility=0.20,
            narrative="Reads charters and group structure; less affected by simple historical anchors.",
            value_model=StudentValueModel(
                brand_face_weight=0.66,
                employment_roi_weight=0.62,
                cost_sensitivity=0.42,
                major_strictness=0.46,
                city_flexibility=0.66,
                region_tolerance=0.66,
                tuition_tolerance=0.58,
                campus_tolerance=0.64,
                pathway_tolerance=0.62,
                adjustment_tolerance=0.66,
                employment_uncertainty_tolerance=0.62,
                regret_sensitivity=0.36,
            ),
        ),
        StudentArchetype(
            name="ordinary_follower_family",
            label="Ordinary follower family",
            segment_share=0.10,
            publicity_susceptibility=0.88,
            narrative="Follows teachers, counselors, classmates, and livestream recommendations.",
            value_model=StudentValueModel(
                brand_face_weight=0.55,
                employment_roi_weight=0.55,
                cost_sensitivity=0.50,
                major_strictness=0.52,
                city_flexibility=0.50,
                region_tolerance=0.48,
                tuition_tolerance=0.46,
                campus_tolerance=0.46,
                pathway_tolerance=0.44,
                adjustment_tolerance=0.42,
                employment_uncertainty_tolerance=0.44,
                regret_sensitivity=0.64,
            ),
        ),
        StudentArchetype(
            name="public_school_climber",
            label="Public-school climber",
            segment_share=0.13,
            publicity_susceptibility=0.46,
            narrative="Prefers public school level upgrades over private-school specialization.",
            value_model=StudentValueModel(
                brand_face_weight=0.64,
                employment_roi_weight=0.58,
                public_school_preference=0.90,
                cost_sensitivity=0.56,
                major_strictness=0.48,
                city_flexibility=0.54,
                region_tolerance=0.54,
                tuition_tolerance=0.42,
                campus_tolerance=0.52,
                pathway_tolerance=0.48,
                adjustment_tolerance=0.48,
                employment_uncertainty_tolerance=0.46,
                regret_sensitivity=0.58,
            ),
        ),
    ]


def _sacrifice_from_assessment(row: MajorGroupRow, assessment: MarketEvidenceAssessment) -> SacrificeVector:
    region = _clamp(assessment.low_attention_signal * 0.30 + assessment.campus_discount * 0.25)
    major = _clamp(assessment.cold_major_discount * 0.55 + row.major_utility_dispersion * 0.40)
    tuition = assessment.tuition_filter
    campus = assessment.campus_discount
    pathway = _clamp(max(tuition, campus) * 0.60)
    adjustment = _clamp(row.tail_assignment_risk)
    employment_uncertainty = _clamp(assessment.cold_major_discount * 0.55 + row.major_utility_dispersion * 0.25)
    return SacrificeVector(
        region=region,
        major=major,
        tuition=tuition,
        campus=campus,
        pathway=pathway,
        adjustment=adjustment,
        employment_uncertainty=employment_uncertainty,
    )


def _score_archetype_fit(
    *,
    archetype: StudentArchetype,
    row: MajorGroupRow,
    assessment: MarketEvidenceAssessment,
    user_rank: int | None,
) -> float:
    baseline_tier = _rank_baseline_tier(user_rank)
    school_tier = _clamp(max(row.comprehensive_score, 0.35))
    school_lift = _clamp((school_tier - baseline_tier + 0.45) / 0.90)
    brand_value = _clamp(0.65 * school_tier + 0.35 * row.comprehensive_score)
    major_value = _clamp(row.major_utility_mean)
    market_discount = _clamp(assessment.market_discount_score)
    sacrifice_cost = estimate_sacrifice_cost(
        student=archetype.value_model,
        sacrifice=_sacrifice_from_assessment(row, assessment),
    )
    admission_feasibility = _clamp(row.admission_prob)
    volatility_bonus = _clamp(row.variance_opportunity_score * 0.45 + market_discount * 0.55)
    publicity_pull = _clamp(assessment.publicity_heat_score * archetype.publicity_susceptibility)

    utility = (
        0.24 * school_lift
        + 0.16 * brand_value * archetype.value_model.brand_face_weight
        + 0.14 * major_value * archetype.value_model.employment_roi_weight
        + 0.18 * market_discount
        + 0.12 * admission_feasibility
        + 0.10 * volatility_bonus
        + 0.06 * publicity_pull
        - 0.22 * sacrifice_cost
        - 0.10 * row.tail_assignment_risk * (1 - archetype.value_model.adjustment_tolerance)
    )
    return _clamp(utility)


def score_segment_demand(
    *,
    row: MajorGroupRow,
    assessment: MarketEvidenceAssessment,
    user_rank: int | None = None,
    archetypes: Sequence[StudentArchetype] | None = None,
) -> SegmentDemandResult:
    """Score market demand by checking which archetypes can absorb sacrifices."""
    selected_archetypes = list(archetypes or default_student_archetypes())
    breakdown = {
        archetype.name: round(
            _score_archetype_fit(
                archetype=archetype,
                row=row,
                assessment=assessment,
                user_rank=user_rank,
            ),
            4,
        )
        for archetype in selected_archetypes
    }
    total_share = sum(max(0.0, archetype.segment_share) for archetype in selected_archetypes) or 1.0
    demand_score = _clamp(
        sum(
            breakdown[archetype.name] * max(0.0, archetype.segment_share)
            for archetype in selected_archetypes
        )
        / total_share
    )
    publicity_reach = _clamp(
        assessment.publicity_heat_score
        * sum(
            archetype.publicity_susceptibility * max(0.0, archetype.segment_share)
            for archetype in selected_archetypes
        )
        / total_share
    )
    structural_hiddenness = _clamp(
        0.45 * assessment.market_discount_score
        + 0.25 * assessment.low_attention_signal
        + 0.20 * row.variance_opportunity_score
        + 0.10 * (1 - row.quota_stability_score)
    )
    low_attention = _clamp(structural_hiddenness * (1 - 0.70 * publicity_reach))
    quota_rebound = 0.12 if row.quota_bucket == QuotaBucket.SMALL else 0.0
    rebound = _clamp(
        assessment.rebound_risk
        + 0.32 * publicity_reach
        + 0.16 * demand_score
        + quota_rebound
        - 0.10 * low_attention
    )

    ordered = sorted(breakdown.items(), key=lambda item: item[1], reverse=True)
    best_fit = [name for name, score in ordered[:4] if score >= max(0.34, demand_score)]
    notes = [
        f"{name}:{score:.2f}"
        for name, score in ordered[:4]
    ]
    return SegmentDemandResult(
        segment_demand_score=round(demand_score, 4),
        low_attention_signal=round(low_attention, 4),
        rebound_risk_adjustment=round(rebound, 4),
        best_fit_archetypes=best_fit,
        segment_breakdown=breakdown,
        segment_notes=notes,
    )

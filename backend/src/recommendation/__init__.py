"""Recommendation helpers for Guangdong volunteer-plan generation."""

from .arbitrage_model import (
    AdmissionContext,
    ArbitrageScoreResult,
    CandidateContext,
    CounterfactualBaseline,
    OpportunitySignals,
    SacrificeVector,
    StudentValueModel,
    score_arbitrage_opportunity,
)
from .arbitrage_adapter import score_major_group_arbitrage
from .bundle_risk import analyze_bundle_risk
from .major_choice_planner import build_volunteer_plan, choose_six_majors
from .plan_change_signals import attach_plan_change_signals
from .major_utility import score_major_options
from .market_evidence import (
    EvidenceCard,
    MarketEvidenceAssessment,
    assess_market_evidence,
    build_decision_evidence_cards,
)
from .market_simulation import SegmentDemandResult, StudentArchetype, default_student_archetypes, score_segment_demand
from .prefix_optimizer import optimize_prefix_order, prefix_value_score
from .school_signal import score_school_major_signal

__all__ = [
    "AdmissionContext",
    "ArbitrageScoreResult",
    "CandidateContext",
    "CounterfactualBaseline",
    "OpportunitySignals",
    "SacrificeVector",
    "StudentValueModel",
    "EvidenceCard",
    "MarketEvidenceAssessment",
    "SegmentDemandResult",
    "StudentArchetype",
    "analyze_bundle_risk",
    "assess_market_evidence",
    "build_decision_evidence_cards",
    "build_volunteer_plan",
    "choose_six_majors",
    "default_student_archetypes",
    "score_arbitrage_opportunity",
    "score_major_group_arbitrage",
    "score_major_options",
    "score_segment_demand",
    "score_school_major_signal",
    "optimize_prefix_order",
    "prefix_value_score",
]

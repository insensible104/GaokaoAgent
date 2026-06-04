"""Recommendation helpers for Guangdong volunteer-plan generation.

This package exposes a convenience import surface, but importing the package
itself should not import every scoring subsystem.  Keep exports lazy so tests
can import focused modules such as ``recommendation.bundle_risk`` without
loading LLM-facing utility code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .arbitrage_adapter import score_major_group_arbitrage
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
    from .bundle_risk import analyze_bundle_risk
    from .major_choice_planner import build_volunteer_plan, choose_six_majors
    from .major_utility import score_major_options
    from .market_evidence import (
        EvidenceCard,
        MarketEvidenceAssessment,
        assess_market_evidence,
        build_decision_evidence_cards,
    )
    from .market_simulation import (
        SegmentDemandResult,
        StudentArchetype,
        default_student_archetypes,
        score_segment_demand,
    )
    from .plan_change_signals import attach_plan_change_signals
    from .prefix_optimizer import optimize_prefix_order, prefix_value_score
    from .research_evidence_features import derive_research_evidence_signals
    from .school_signal import score_school_major_signal

_LAZY_EXPORTS = {
    "AdmissionContext": ("recommendation.arbitrage_model", "AdmissionContext"),
    "ArbitrageScoreResult": ("recommendation.arbitrage_model", "ArbitrageScoreResult"),
    "CandidateContext": ("recommendation.arbitrage_model", "CandidateContext"),
    "CounterfactualBaseline": ("recommendation.arbitrage_model", "CounterfactualBaseline"),
    "OpportunitySignals": ("recommendation.arbitrage_model", "OpportunitySignals"),
    "SacrificeVector": ("recommendation.arbitrage_model", "SacrificeVector"),
    "StudentValueModel": ("recommendation.arbitrage_model", "StudentValueModel"),
    "EvidenceCard": ("recommendation.market_evidence", "EvidenceCard"),
    "MarketEvidenceAssessment": ("recommendation.market_evidence", "MarketEvidenceAssessment"),
    "SegmentDemandResult": ("recommendation.market_simulation", "SegmentDemandResult"),
    "StudentArchetype": ("recommendation.market_simulation", "StudentArchetype"),
    "analyze_bundle_risk": ("recommendation.bundle_risk", "analyze_bundle_risk"),
    "assess_market_evidence": ("recommendation.market_evidence", "assess_market_evidence"),
    "attach_plan_change_signals": ("recommendation.plan_change_signals", "attach_plan_change_signals"),
    "build_decision_evidence_cards": ("recommendation.market_evidence", "build_decision_evidence_cards"),
    "build_volunteer_plan": ("recommendation.major_choice_planner", "build_volunteer_plan"),
    "choose_six_majors": ("recommendation.major_choice_planner", "choose_six_majors"),
    "default_student_archetypes": ("recommendation.market_simulation", "default_student_archetypes"),
    "score_arbitrage_opportunity": ("recommendation.arbitrage_model", "score_arbitrage_opportunity"),
    "score_major_group_arbitrage": ("recommendation.arbitrage_adapter", "score_major_group_arbitrage"),
    "score_major_options": ("recommendation.major_utility", "score_major_options"),
    "score_school_major_signal": ("recommendation.school_signal", "score_school_major_signal"),
    "score_segment_demand": ("recommendation.market_simulation", "score_segment_demand"),
    "optimize_prefix_order": ("recommendation.prefix_optimizer", "optimize_prefix_order"),
    "prefix_value_score": ("recommendation.prefix_optimizer", "prefix_value_score"),
    "derive_research_evidence_signals": (
        "recommendation.research_evidence_features",
        "derive_research_evidence_signals",
    ),
}


def __getattr__(name: str) -> Any:
    """Resolve convenience exports on first use."""
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _LAZY_EXPORTS[name]
    from importlib import import_module

    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value

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
    "derive_research_evidence_signals",
]

"""A/B comparison for two ordered volunteer plans."""

from __future__ import annotations

from typing import Any

from models.game_matrix import VolunteerPlan


def _checked(plan: VolunteerPlan) -> VolunteerPlan:
    working = plan.model_copy(deep=True)
    working.calculate_statistics()
    return working


def _metrics(plan: VolunteerPlan) -> dict[str, float | int]:
    return {
        "expected_admission_prob": plan.expected_admission_prob,
        "expected_tail_risk": plan.expected_tail_risk,
        "expected_first_hit_utility": plan.expected_first_hit_utility,
        "expected_plan_value": plan.expected_plan_value,
        "safe_anchor_coverage": plan.safe_anchor_coverage,
        "key_prefix_count": plan.key_prefix_count,
        "shadowed_choice_count": plan.shadowed_choice_count,
        "blacklist_violation_count": plan.blacklist_violation_count,
    }


def _score(metrics: dict[str, float | int]) -> float:
    return (
        float(metrics["expected_admission_prob"]) * 0.32
        + float(metrics["expected_first_hit_utility"]) * 0.22
        + float(metrics["safe_anchor_coverage"]) * 0.14
        + float(metrics["expected_plan_value"]) * 0.12
        - float(metrics["expected_tail_risk"]) * 0.16
        - min(float(metrics["blacklist_violation_count"]) * 0.35, 0.70)
        - min(float(metrics["shadowed_choice_count"]) * 0.01, 0.15)
    )


def _factor(metric: str, delta: float, preferred: str) -> dict[str, Any]:
    return {
        "metric": metric,
        "delta": round(delta, 6),
        "preferred": preferred,
    }


def compare_volunteer_plans(
    *,
    left: VolunteerPlan,
    right: VolunteerPlan,
    left_label: str = "left",
    right_label: str = "right",
) -> dict[str, Any]:
    """Compare two plans and identify the more defensible option."""
    left_plan = _checked(left)
    right_plan = _checked(right)
    left_metrics = _metrics(left_plan)
    right_metrics = _metrics(right_plan)
    deltas = {
        key: round(float(left_metrics[key]) - float(right_metrics[key]), 6)
        for key in left_metrics
    }
    left_score = _score(left_metrics)
    right_score = _score(right_metrics)
    winner = left_label if left_score >= right_score else right_label
    deciding_factors: list[dict[str, Any]] = []
    if abs(deltas["expected_admission_prob"]) >= 0.02:
        deciding_factors.append(
            _factor(
                "expected_admission_prob",
                deltas["expected_admission_prob"],
                left_label if deltas["expected_admission_prob"] > 0 else right_label,
            )
        )
    if abs(deltas["expected_tail_risk"]) >= 0.02:
        deciding_factors.append(
            _factor(
                "expected_tail_risk",
                deltas["expected_tail_risk"],
                left_label if deltas["expected_tail_risk"] < 0 else right_label,
            )
        )
    if abs(deltas["expected_first_hit_utility"]) >= 0.02:
        deciding_factors.append(
            _factor(
                "expected_first_hit_utility",
                deltas["expected_first_hit_utility"],
                left_label if deltas["expected_first_hit_utility"] > 0 else right_label,
            )
        )
    if deltas["blacklist_violation_count"] != 0:
        deciding_factors.append(
            _factor(
                "blacklist_violation_count",
                deltas["blacklist_violation_count"],
                left_label if deltas["blacklist_violation_count"] < 0 else right_label,
            )
        )
    return {
        "protocol_version": "plan-comparison-v1",
        "left_label": left_label,
        "right_label": right_label,
        "winner": winner,
        "left_score": round(left_score, 6),
        "right_score": round(right_score, 6),
        "left_metrics": left_metrics,
        "right_metrics": right_metrics,
        "deltas": deltas,
        "deciding_factors": deciding_factors,
        "claim_boundary": (
            "This comparison ranks plan structure, risk, and utility diagnostics. "
            "It does not prove future admission outcomes."
        ),
    }

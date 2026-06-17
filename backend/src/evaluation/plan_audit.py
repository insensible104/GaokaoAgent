"""Product-facing audit summary for an ordered volunteer plan."""

from __future__ import annotations

from typing import Any

from evaluation.plan_quality_audit import audit_plan_quality
from models.game_matrix import VolunteerPlan
from models.user_profile import UserProfile


def _ensure_statistics(plan: VolunteerPlan) -> VolunteerPlan:
    working = plan.model_copy(deep=True)
    working.calculate_statistics()
    return working


def _coverage_summary(coverage_report: dict[str, Any] | None) -> dict[str, Any]:
    report = coverage_report or {}
    deficits = {
        key: int(value)
        for key, value in (report.get("deficits") or {}).items()
        if int(value or 0) > 0
    }
    return {
        "coverage_sufficient": bool(report.get("coverage_sufficient", not deficits)),
        "selected": dict(report.get("selected") or {}),
        "desired": dict(report.get("desired") or {}),
        "deficits": deficits,
        "actions": list(report.get("actions") or []),
    }


def _data_boundary(data_vintage: dict[str, Any] | None) -> dict[str, Any]:
    vintage = data_vintage or {}
    return {
        "target_year": vintage.get("target_year"),
        "formal_recommendation_ready": bool(vintage.get("formal_recommendation_ready", False)),
        "limitations": list(vintage.get("limitations") or []),
    }


def _student_facing_items(
    *,
    quality: dict[str, Any],
    coverage: dict[str, Any],
    data_boundary: dict[str, Any],
    plan: VolunteerPlan,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not data_boundary["formal_recommendation_ready"]:
        items.append(
            {
                "type": "data_boundary",
                "severity": "P1",
                "title": "Current-year data boundary",
                "detail": "; ".join(data_boundary["limitations"])
                or "Current-year official data is not fully ready.",
            }
        )
    if not coverage["coverage_sufficient"]:
        items.append(
            {
                "type": "coverage_deficit",
                "severity": "P1",
                "title": "Rush/target/safe supply is incomplete",
                "detail": f"Deficits: {coverage['deficits']}",
            }
        )
    if plan.shadowed_choice_count:
        items.append(
            {
                "type": "shadowed_choices",
                "severity": "P2",
                "title": "Some rows are mostly shadowed by earlier choices",
                "detail": f"{plan.shadowed_choice_count} choices have low first-hit effect.",
            }
        )
    for finding in quality.get("findings", [])[:5]:
        items.append(
            {
                "type": str(finding.get("area", "quality")),
                "severity": str(finding.get("severity", "P2")),
                "title": str(finding.get("finding", "Plan quality finding")),
                "detail": str(finding.get("recommendation", "")),
            }
        )
    return items


def build_plan_audit_summary(
    plan: VolunteerPlan,
    profile: UserProfile | None = None,
    *,
    coverage_report: dict[str, Any] | None = None,
    data_vintage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a compact audit payload suitable for UI and delivery review."""
    checked_plan = _ensure_statistics(plan)
    quality = audit_plan_quality(checked_plan, profile)
    coverage = _coverage_summary(coverage_report)
    boundary = _data_boundary(data_vintage)
    key_choices = [
        {
            "choice_index": choice.choice_index,
            "school_name": choice.school_name,
            "major_group_code": choice.major_group_code,
            "first_hit_prob": round(choice.first_hit_prob, 6),
            "prefix_role": choice.prefix_role,
        }
        for choice in checked_plan.choices
        if choice.is_key_prefix
    ]
    items = _student_facing_items(
        quality=quality,
        coverage=coverage,
        data_boundary=boundary,
        plan=checked_plan,
    )
    return {
        "protocol_version": "plan-audit-summary-v1",
        "status": quality["status"],
        "total_score": quality["total_score"],
        "choice_count": len(checked_plan.choices),
        "expected_admission_prob": checked_plan.expected_admission_prob,
        "expected_tail_risk": checked_plan.expected_tail_risk,
        "key_prefix": {
            "count": checked_plan.key_prefix_count,
            "choice_indexes": checked_plan.key_choice_indexes,
            "choices": key_choices,
        },
        "shadowed_choice_count": checked_plan.shadowed_choice_count,
        "coverage": coverage,
        "data_boundary": boundary,
        "student_facing_items": items,
        "claim_boundary": (
            "This audit diagnoses plan structure and evidence boundaries. "
            "It does not prove future admission outcomes."
        ),
    }

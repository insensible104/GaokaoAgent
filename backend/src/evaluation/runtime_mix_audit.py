"""Audit runtime rush/target/safe coverage across representative profiles.

This audit measures candidate supply and selection coverage only. It deliberately
does not consume post-hoc admission outcomes, so it cannot support an admission-
quality claim.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


PROTOCOL_VERSION = "gaokao-runtime-mix-audit-v1"
STRATEGIES = ("rush", "target", "safe")


def _empty_counts() -> dict[str, int]:
    return {strategy: 0 for strategy in STRATEGIES}


def _add_counts(target: dict[str, int], source: Mapping[str, Any] | None) -> None:
    if not source:
        return
    for strategy in STRATEGIES:
        target[strategy] += max(0, int(source.get(strategy, 0) or 0))


def _slice_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    sufficient = sum(
        1
        for case in cases
        if bool((case.get("coverage_report") or {}).get("coverage_sufficient"))
    )
    case_count = len(cases)
    return {
        "case_count": case_count,
        "coverage_sufficient_case_count": sufficient,
        "coverage_sufficient_rate": round(sufficient / case_count, 6) if case_count else 0.0,
        "incomplete_data_case_count": sum(bool(case.get("incomplete_data")) for case in cases),
    }


def audit_runtime_mix_cases(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate coverage reports without using realized admission outcomes."""
    normalized_cases = [dict(case) for case in cases]
    aggregate_classified = _empty_counts()
    aggregate_selected = _empty_counts()
    aggregate_deficits = _empty_counts()
    by_subject_cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_rank_band_cases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    response_seconds: list[float] = []
    plan_change_explanation_count = 0
    plan_change_explained_case_count = 0
    plan_change_applied_count = 0
    plan_change_review_count = 0
    calibrated_case_count = 0
    key_prefix_counts: list[int] = []
    shadowed_ratios: list[float] = []
    plan_probability_lowers: list[float] = []
    plan_probability_uppers: list[float] = []
    capacity_filled_case_count = 0
    capacity_filled_row_count = 0
    remaining_capacity_shortfall = 0

    case_rows: list[dict[str, Any]] = []
    for case in normalized_cases:
        report = dict(case.get("coverage_report") or {})
        capacity_fill = dict(case.get("capacity_fill") or {})
        _add_counts(aggregate_classified, report.get("classified"))
        _add_counts(aggregate_selected, report.get("selected"))
        _add_counts(aggregate_deficits, report.get("deficits"))

        subject_group = str(case.get("subject_group") or "unknown")
        rank_band = str(case.get("rank_band") or "unknown")
        by_subject_cases[subject_group].append(case)
        by_rank_band_cases[rank_band].append(case)
        if isinstance(case.get("response_seconds"), (int, float)):
            response_seconds.append(float(case["response_seconds"]))
        explained_count = max(0, int(case.get("plan_change_explanation_count", 0) or 0))
        plan_change_explanation_count += explained_count
        if explained_count:
            plan_change_explained_case_count += 1
        applied_count = max(0, int(case.get("plan_change_applied_count", 0) or 0))
        review_count = max(0, int(case.get("plan_change_review_count", 0) or 0))
        plan_change_applied_count += applied_count
        plan_change_review_count += review_count
        probability_is_calibrated = bool(case.get("probability_is_calibrated"))
        if probability_is_calibrated:
            calibrated_case_count += 1
        key_prefix_count = max(0, int(case.get("key_prefix_count", 0) or 0))
        shadowed_choice_count = max(0, int(case.get("shadowed_choice_count", 0) or 0))
        row_count = max(0, int(case.get("row_count", 0) or 0))
        key_prefix_counts.append(key_prefix_count)
        if row_count:
            shadowed_ratios.append(shadowed_choice_count / row_count)
        lower = case.get("plan_probability_lower")
        upper = case.get("plan_probability_upper")
        if isinstance(lower, (int, float)):
            plan_probability_lowers.append(float(lower))
        if isinstance(upper, (int, float)):
            plan_probability_uppers.append(float(upper))
        filled_count = max(0, int(capacity_fill.get("filled_count", 0) or 0))
        shortfall = max(0, int(capacity_fill.get("remaining_shortfall", 0) or 0))
        if filled_count:
            capacity_filled_case_count += 1
        capacity_filled_row_count += filled_count
        remaining_capacity_shortfall += shortfall
        case_rows.append(
            {
                "case_id": str(case.get("case_id") or ""),
                "subject_group": subject_group,
                "rank_band": rank_band,
                "incomplete_data": bool(case.get("incomplete_data")),
                "response_seconds": case.get("response_seconds"),
                "row_count": row_count,
                "plan_change_explanation_count": explained_count,
                "plan_change_applied_count": applied_count,
                "plan_change_review_count": review_count,
                "probability_is_calibrated": probability_is_calibrated,
                "plan_probability_lower": lower,
                "plan_probability_upper": upper,
                "key_prefix_count": key_prefix_count,
                "shadowed_choice_count": shadowed_choice_count,
                "capacity_fill": capacity_fill,
                "coverage_sufficient": bool(report.get("coverage_sufficient")),
                "classified": {
                    strategy: int((report.get("classified") or {}).get(strategy, 0) or 0)
                    for strategy in STRATEGIES
                },
                "selected": {
                    strategy: int((report.get("selected") or {}).get(strategy, 0) or 0)
                    for strategy in STRATEGIES
                },
                "deficits": {
                    strategy: int((report.get("deficits") or {}).get(strategy, 0) or 0)
                    for strategy in STRATEGIES
                },
            }
        )

    overall = _slice_summary(normalized_cases)
    return {
        "protocol_version": PROTOCOL_VERSION,
        **overall,
        "aggregate_classified": aggregate_classified,
        "aggregate_selected": aggregate_selected,
        "aggregate_deficits": aggregate_deficits,
        "average_response_seconds": (
            round(sum(response_seconds) / len(response_seconds), 3)
            if response_seconds
            else None
        ),
        "plan_change_explained_case_count": plan_change_explained_case_count,
        "plan_change_explanation_count": plan_change_explanation_count,
        "plan_change_applied_count": plan_change_applied_count,
        "plan_change_review_count": plan_change_review_count,
        "calibrated_case_count": calibrated_case_count,
        "capacity_filled_case_count": capacity_filled_case_count,
        "capacity_filled_row_count": capacity_filled_row_count,
        "remaining_capacity_shortfall": remaining_capacity_shortfall,
        "average_key_prefix_count": (
            round(sum(key_prefix_counts) / len(key_prefix_counts), 6)
            if key_prefix_counts
            else None
        ),
        "average_shadowed_ratio": (
            round(sum(shadowed_ratios) / len(shadowed_ratios), 6)
            if shadowed_ratios
            else None
        ),
        "average_plan_probability_lower": (
            round(sum(plan_probability_lowers) / len(plan_probability_lowers), 6)
            if plan_probability_lowers
            else None
        ),
        "average_plan_probability_upper": (
            round(sum(plan_probability_uppers) / len(plan_probability_uppers), 6)
            if plan_probability_uppers
            else None
        ),
        "by_subject": {
            key: _slice_summary(value)
            for key, value in sorted(by_subject_cases.items())
        },
        "by_rank_band": {
            key: _slice_summary(value)
            for key, value in sorted(by_rank_band_cases.items())
        },
        "quality_claim_allowed": False,
        "claim_boundary": (
            "Runtime mix coverage measures candidate supply and portfolio composition; "
            "it does not establish improved admission quality or calibration."
        ),
        "cases": case_rows,
    }


def write_runtime_mix_audit(
    cases: Sequence[Mapping[str, Any]],
    output_path: str | Path,
) -> dict[str, Any]:
    audit = audit_runtime_mix_cases(cases)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit

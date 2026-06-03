"""Calibration reports for quant-scored volunteer-plan choices.

This module compares prediction-time signals from frozen plans against actual
outcomes. It is deliberately offline-only: online recommendation should freeze
a plan before any actual-outcome labels are loaded.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

from evaluation.backtest_2025 import run_plan_backtest
from evaluation.schemas import ActualMajorGroupOutcome
from models.game_matrix import VolunteerPlan


PROBABILITY_BUCKETS = [
    (0.0, 0.2, "00-20%"),
    (0.2, 0.4, "20-40%"),
    (0.4, 0.6, "40-60%"),
    (0.6, 0.8, "60-80%"),
    (0.8, 1.01, "80-100%"),
]
QUANT_SCORE_BUCKETS = [
    (0.0, 0.2, "0.00-0.20"),
    (0.2, 0.4, "0.20-0.40"),
    (0.4, 0.6, "0.40-0.60"),
    (0.6, 0.8, "0.60-0.80"),
    (0.8, 1.01, "0.80-1.00"),
]
FIRST_HIT_BUCKETS = [
    (0.0, 0.05, "00-05%"),
    (0.05, 0.15, "05-15%"),
    (0.15, 0.3, "15-30%"),
    (0.3, 0.6, "30-60%"),
    (0.6, 1.01, "60-100%"),
]
RISK_BAND_ORDER = [
    "far_rush",
    "boundary_rush",
    "thin_target",
    "solid_target",
    "safe_anchor",
    "unknown",
]


def _clamp_probability(value: object) -> float:
    try:
        numeric = float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, numeric))


def _bucket(value: float, buckets: Sequence[tuple[float, float, str]]) -> str:
    for low, high, label in buckets:
        if low <= value < high:
            return label
    return buckets[-1][2]


def _load_plan_record(record: dict) -> tuple[str, int, VolunteerPlan, list[str], list[str]]:
    plan_payload = record.get("plan") or record.get("volunteer_plan")
    if not plan_payload:
        raise ValueError("Each calibration record must contain `plan` or `volunteer_plan`.")
    plan = plan_payload if isinstance(plan_payload, VolunteerPlan) else VolunteerPlan(**plan_payload)
    user_rank = record.get("user_rank") or plan.user_rank
    if user_rank is None:
        raise ValueError("Each calibration record must contain `user_rank`, or plan.user_rank must be set.")
    return (
        str(record.get("case_id") or ""),
        int(user_rank),
        plan,
        list(record.get("preferred_majors") or []),
        list(record.get("blacklist_majors") or []),
    )


def _choice_prediction_record(*, case_id: str, user_rank: int, choice, outcome) -> dict:
    predicted_prob = _clamp_probability(getattr(choice, "group_admission_prob", 0.0))
    quant_score = _clamp_probability(getattr(choice, "quant_score", 0.0))
    first_hit_prob = _clamp_probability(getattr(choice, "first_hit_prob", 0.0))
    risk_band = str(getattr(choice, "deterministic_risk_band", "") or "unknown")
    group_admitted = bool(getattr(outcome, "group_admitted", False))
    first_hit = bool(getattr(outcome, "is_first_hit", False))
    tail_assignment = bool(getattr(outcome, "tail_assignment_hit", False))
    group_margin = getattr(outcome, "group_rank_margin", None)
    wasted_score = bool(group_admitted and group_margin is not None and int(group_margin) >= 12_000)
    label = 1.0 if group_admitted else 0.0

    return {
        "case_id": case_id,
        "user_rank": user_rank,
        "choice_index": int(getattr(choice, "choice_index", 0) or 0),
        "school_code": str(getattr(choice, "school_code", "") or ""),
        "school_name": str(getattr(choice, "school_name", "") or ""),
        "major_group_code": str(getattr(choice, "major_group_code", "") or ""),
        "predicted_prob": predicted_prob,
        "quant_score": quant_score,
        "rank_buffer_score": _clamp_probability(getattr(choice, "rank_buffer_score", 0.0)),
        "history_stability_score": _clamp_probability(getattr(choice, "history_stability_score", 0.0)),
        "data_confidence_score": _clamp_probability(getattr(choice, "data_confidence_score", 0.0)),
        "trend_score": _clamp_probability(getattr(choice, "trend_score", 0.0)),
        "first_hit_prob": first_hit_prob,
        "deterministic_risk_band": risk_band,
        "probability_bucket": _bucket(predicted_prob, PROBABILITY_BUCKETS),
        "quant_score_bucket": _bucket(quant_score, QUANT_SCORE_BUCKETS),
        "first_hit_bucket": _bucket(first_hit_prob, FIRST_HIT_BUCKETS),
        "group_admitted": group_admitted,
        "first_hit": first_hit,
        "tail_assignment_hit": tail_assignment,
        "wasted_score_risk": wasted_score,
        "group_rank_margin": group_margin,
        "brier_error": round((predicted_prob - label) ** 2, 6),
        "absolute_error": round(abs(predicted_prob - label), 6),
    }


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _summarize_bucket(rows: Sequence[dict]) -> dict:
    count = len(rows)
    admitted = [1.0 if row["group_admitted"] else 0.0 for row in rows]
    predicted = [float(row["predicted_prob"]) for row in rows]
    first_hits = [1.0 if row["first_hit"] else 0.0 for row in rows]
    tail_hits = [1.0 if row["tail_assignment_hit"] else 0.0 for row in rows]
    wasted = [1.0 if row["wasted_score_risk"] else 0.0 for row in rows]
    observed = _mean(admitted)
    expected = _mean(predicted)
    return {
        "choice_count": count,
        "expected_admit_rate": round(expected, 6),
        "observed_admit_rate": round(observed, 6),
        "calibration_error": round(expected - observed, 6),
        "absolute_calibration_error": round(abs(expected - observed), 6),
        "brier_score": round(_mean([float(row["brier_error"]) for row in rows]), 6),
        "mean_absolute_error": round(_mean([float(row["absolute_error"]) for row in rows]), 6),
        "first_hit_rate": round(_mean(first_hits), 6),
        "tail_assignment_rate": round(_mean(tail_hits), 6),
        "wasted_score_rate": round(_mean(wasted), 6),
        "average_quant_score": round(_mean([float(row["quant_score"]) for row in rows]), 6),
        "average_first_hit_prob": round(_mean([float(row["first_hit_prob"]) for row in rows]), 6),
    }


def _group_by(rows: Sequence[dict], key: str, order: Sequence[str] | None = None) -> list[dict]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        buckets[str(row.get(key) or "unknown")].append(row)
    labels = list(order or sorted(buckets))
    for label in sorted(buckets):
        if label not in labels:
            labels.append(label)
    return [
        {"bucket": label, **_summarize_bucket(buckets[label])}
        for label in labels
        if buckets.get(label)
    ]


def run_quant_calibration_records(
    *,
    records: Sequence[dict],
    actual_outcomes: Iterable[ActualMajorGroupOutcome],
) -> dict:
    """Build choice-level calibration diagnostics from frozen plan records."""
    actual_outcomes = list(actual_outcomes)
    choice_rows: list[dict] = []

    for record in records:
        case_id, user_rank, plan, preferred_majors, blacklist_majors = _load_plan_record(record)
        result = run_plan_backtest(
            plan=plan,
            actual_outcomes=actual_outcomes,
            user_rank=user_rank,
            preferred_majors=preferred_majors,
            blacklist_majors=blacklist_majors,
            case_id=case_id,
        )
        outcomes_by_index = {outcome.choice_index: outcome for outcome in result.choice_outcomes}
        for choice in plan.choices:
            outcome = outcomes_by_index.get(choice.choice_index)
            if outcome:
                choice_rows.append(
                    _choice_prediction_record(
                        case_id=case_id,
                        user_rank=user_rank,
                        choice=choice,
                        outcome=outcome,
                    )
                )

    summary = _summarize_bucket(choice_rows) if choice_rows else _summarize_bucket([])
    return {
        "case_count": len(records),
        "choice_count": len(choice_rows),
        "overall": summary,
        "by_probability_bucket": _group_by(
            choice_rows,
            "probability_bucket",
            [label for _, _, label in PROBABILITY_BUCKETS],
        ),
        "by_quant_score_bucket": _group_by(
            choice_rows,
            "quant_score_bucket",
            [label for _, _, label in QUANT_SCORE_BUCKETS],
        ),
        "by_risk_band": _group_by(choice_rows, "deterministic_risk_band", RISK_BAND_ORDER),
        "by_first_hit_bucket": _group_by(
            choice_rows,
            "first_hit_bucket",
            [label for _, _, label in FIRST_HIT_BUCKETS],
        ),
        "choice_rows": choice_rows,
    }


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _table(title: str, rows: Sequence[dict]) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Bucket | Choices | Expected | Observed | Abs Calib Err | Brier | First Hit | Tail | Wasted |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('bucket', '')}`",
                    str(row.get("choice_count", 0)),
                    _pct(float(row.get("expected_admit_rate", 0.0))),
                    _pct(float(row.get("observed_admit_rate", 0.0))),
                    _pct(float(row.get("absolute_calibration_error", 0.0))),
                    f"{float(row.get('brier_score', 0.0)):.3f}",
                    _pct(float(row.get("first_hit_rate", 0.0))),
                    _pct(float(row.get("tail_assignment_rate", 0.0))),
                    _pct(float(row.get("wasted_score_rate", 0.0))),
                ]
            )
            + " |"
        )
    if not rows:
        lines.append("| `empty` | 0 | 0.0% | 0.0% | 0.0% | 0.000 | 0.0% | 0.0% | 0.0% |")
    return lines


def build_markdown_calibration_report(result: dict) -> str:
    """Build a compact Markdown calibration report for experiment logs."""
    overall = result.get("overall", {})
    lines = [
        "# Quant Calibration Report",
        "",
        f"Cases: {result.get('case_count', 0)}",
        f"Choices: {result.get('choice_count', 0)}",
        "",
        "## Overall",
        "",
        "| Expected Admit | Observed Admit | Abs Calib Err | Brier | First Hit | Tail | Wasted |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        "| "
        + " | ".join(
            [
                _pct(float(overall.get("expected_admit_rate", 0.0))),
                _pct(float(overall.get("observed_admit_rate", 0.0))),
                _pct(float(overall.get("absolute_calibration_error", 0.0))),
                f"{float(overall.get('brier_score', 0.0)):.3f}",
                _pct(float(overall.get("first_hit_rate", 0.0))),
                _pct(float(overall.get("tail_assignment_rate", 0.0))),
                _pct(float(overall.get("wasted_score_rate", 0.0))),
            ]
        )
        + " |",
        "",
    ]
    lines.extend(_table("By Probability Bucket", result.get("by_probability_bucket", [])))
    lines.append("")
    lines.extend(_table("By Quant Score Bucket", result.get("by_quant_score_bucket", [])))
    lines.append("")
    lines.extend(_table("By Deterministic Risk Band", result.get("by_risk_band", [])))
    lines.append("")
    lines.extend(_table("By First-Hit Bucket", result.get("by_first_hit_bucket", [])))
    return "\n".join(lines) + "\n"

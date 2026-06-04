"""Case-level failure mining for quant experiments.

Aggregate metrics tell us whether a variant is better. Failure mining tells us
what to fix next. The output is deliberately simple and JSON-first so it can be
stored inside QuantLab manifests and compared across experiment runs.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Sequence


FAILURE_BUCKETS = [
    "sliding",
    "blacklist_hit",
    "tail_assignment",
    "preferred_major_miss",
    "wasted_score",
    "missing_actual_outcome",
]


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def _bool(row: dict[str, Any], key: str) -> bool:
    return bool(row.get(key))


def _choice_outcomes(row: dict[str, Any]) -> list[dict[str, Any]]:
    outcomes = row.get("choice_outcomes") or []
    return [dict(item) for item in outcomes if isinstance(item, dict)]


def _failure_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if _bool(row, "sliding") or not _bool(row, "success"):
        reasons.append("sliding")
    if _bool(row, "blacklist_hit"):
        reasons.append("blacklist_hit")
    if _bool(row, "tail_assignment_hit"):
        reasons.append("tail_assignment")
    if _bool(row, "wasted_score_risk"):
        reasons.append("wasted_score")
    if _bool(row, "success") and not _bool(row, "preferred_major_hit"):
        reasons.append("preferred_major_miss")
    if any(choice.get("failure_reason") == "missing_actual_outcome" for choice in _choice_outcomes(row)):
        reasons.append("missing_actual_outcome")
    return reasons


def _severity_score(row: dict[str, Any], reasons: Sequence[str]) -> float:
    score = 0.0
    weights = {
        "sliding": 1.00,
        "blacklist_hit": 0.95,
        "tail_assignment": 0.70,
        "preferred_major_miss": 0.45,
        "wasted_score": 0.35,
        "missing_actual_outcome": 0.30,
    }
    for reason in reasons:
        score += weights.get(reason, 0.10)
    if _bool(row, "success"):
        score += max(0.0, 0.35 - _float(row.get("assigned_major_utility"))) * 0.60
    first_hit_index = row.get("first_hit_index")
    if first_hit_index is not None:
        score += min(0.20, max(0.0, _float(first_hit_index) - 6.0) * 0.02)
    return round(score, 6)


def mine_backtest_failures(
    results: Sequence[dict[str, Any]],
    *,
    top_k: int = 10,
) -> dict[str, Any]:
    """Summarize case-level failures from backtest result rows."""
    buckets: Counter[str] = Counter()
    worst_cases: list[dict[str, Any]] = []
    missing_actual_choices = 0

    for row in results:
        reasons = _failure_reasons(row)
        for reason in reasons:
            buckets[reason] += 1
        missing_actual_choices += sum(
            1
            for choice in _choice_outcomes(row)
            if choice.get("failure_reason") == "missing_actual_outcome"
        )
        if not reasons:
            continue
        worst_cases.append(
            {
                "case_id": str(row.get("case_id") or ""),
                "user_rank": row.get("user_rank"),
                "failure_reasons": reasons,
                "severity_score": _severity_score(row, reasons),
                "first_hit_index": row.get("first_hit_index"),
                "first_hit_school": row.get("first_hit_school"),
                "first_hit_major_group": row.get("first_hit_major_group"),
                "assigned_major_name": row.get("assigned_major_name"),
                "assigned_major_utility": row.get("assigned_major_utility", 0.0),
                "first_hit_margin": row.get("first_hit_margin"),
            }
        )

    case_count = len(results)
    bucket_rows = [
        {
            "bucket": bucket,
            "case_count": count,
            "case_rate": round(count / case_count, 6) if case_count else 0.0,
        }
        for bucket, count in buckets.most_common()
    ]
    return {
        "case_count": case_count,
        "failure_case_count": len(worst_cases),
        "failure_case_rate": round(len(worst_cases) / case_count, 6) if case_count else 0.0,
        "missing_actual_choice_count": missing_actual_choices,
        "failure_buckets": bucket_rows,
        "worst_cases": sorted(
            worst_cases,
            key=lambda item: (-float(item["severity_score"]), str(item["case_id"])),
        )[:top_k],
        "optimization_hints": _optimization_hints(bucket_rows),
    }


def mine_ablation_failure_deltas(
    per_case_rows: Sequence[dict[str, Any]],
    *,
    baseline_variant: str = "full",
    top_k: int = 10,
) -> dict[str, Any]:
    """Find variants that improve or worsen case-level failure reasons."""
    by_case_variant = {
        (str(row.get("case_id") or ""), str(row.get("variant") or "")): dict(row)
        for row in per_case_rows
    }
    variant_buckets: dict[str, Counter[str]] = defaultdict(Counter)
    case_regressions: list[dict[str, Any]] = []
    for (case_id, variant), row in by_case_variant.items():
        if variant == baseline_variant:
            continue
        baseline = by_case_variant.get((case_id, baseline_variant))
        if not baseline:
            continue
        baseline_reasons = set(_failure_reasons(baseline))
        variant_reasons = set(_failure_reasons(row))
        new_failures = sorted(variant_reasons - baseline_reasons)
        resolved_failures = sorted(baseline_reasons - variant_reasons)
        for reason in new_failures:
            variant_buckets[variant][f"new_{reason}"] += 1
        for reason in resolved_failures:
            variant_buckets[variant][f"resolved_{reason}"] += 1
        if new_failures:
            case_regressions.append(
                {
                    "case_id": case_id,
                    "variant": variant,
                    "new_failures": new_failures,
                    "resolved_failures": resolved_failures,
                    "severity_score": _severity_score(row, new_failures),
                }
            )

    return {
        "baseline_variant": baseline_variant,
        "variant_failure_deltas": {
            variant: [
                {"bucket": bucket, "case_count": count}
                for bucket, count in counts.most_common()
            ]
            for variant, counts in sorted(variant_buckets.items())
        },
        "case_regressions": sorted(
            case_regressions,
            key=lambda item: (-float(item["severity_score"]), str(item["case_id"]), str(item["variant"])),
        )[:top_k],
    }


def _optimization_hints(bucket_rows: Sequence[dict[str, Any]]) -> list[str]:
    buckets = {str(row.get("bucket")): int(row.get("case_count", 0) or 0) for row in bucket_rows}
    hints: list[str] = []
    if buckets.get("sliding", 0):
        hints.append("Increase safe-anchor reliability and inspect first-hit prefix for all-sliding cases.")
    if buckets.get("blacklist_hit", 0):
        hints.append("Escalate blacklist majors to hard constraints or explicit family sign-off.")
    if buckets.get("tail_assignment", 0):
        hints.append("Reduce high-tail-risk rows in key prefix and improve in-group major assignment modeling.")
    if buckets.get("preferred_major_miss", 0):
        hints.append("Optimize front-major hit and preferred-major utility separately from group admission.")
    if buckets.get("wasted_score", 0):
        hints.append("Audit early safe choices that create high first-hit margin and low optionality.")
    if buckets.get("missing_actual_outcome", 0):
        hints.append("Normalize school/group keys and improve actual-outcome label coverage before trusting metrics.")
    return hints


def build_markdown_failure_mining(result: dict[str, Any]) -> str:
    """Build a compact Markdown failure-mining report."""
    lines = [
        "# Backtest Failure Mining",
        "",
        f"Cases: {result.get('case_count', 0)}",
        f"Failure cases: {result.get('failure_case_count', 0)} ({float(result.get('failure_case_rate', 0.0)):.1%})",
        "",
        "## Failure Buckets",
        "",
        "| Bucket | Cases | Rate |",
        "| --- | ---: | ---: |",
    ]
    for row in result.get("failure_buckets", []) or []:
        lines.append(
            f"| `{row.get('bucket', '')}` | {row.get('case_count', 0)} | "
            f"{float(row.get('case_rate', 0.0)):.1%} |"
        )
    if not result.get("failure_buckets"):
        lines.append("| `none` | 0 | 0.0% |")

    lines.extend(["", "## Worst Cases", "", "| Case | Reasons | Severity | First Hit | Utility |", "| --- | --- | ---: | --- | ---: |"])
    for row in result.get("worst_cases", []) or []:
        reasons = ", ".join(f"`{item}`" for item in row.get("failure_reasons", []) or [])
        first_hit = row.get("first_hit_school") or "sliding"
        lines.append(
            f"| `{row.get('case_id', '')}` | {reasons} | "
            f"{float(row.get('severity_score', 0.0)):.3f} | {first_hit} | "
            f"{float(row.get('assigned_major_utility', 0.0)):.3f} |"
        )

    lines.extend(["", "## Optimization Hints", ""])
    for hint in result.get("optimization_hints", []) or []:
        lines.append(f"- {hint}")
    if not result.get("optimization_hints"):
        lines.append("- No failure-specific optimization hint.")
    return "\n".join(lines)

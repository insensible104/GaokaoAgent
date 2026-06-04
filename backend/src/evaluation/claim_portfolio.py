"""Portfolio view for claim-readiness audits.

This module aggregates many ``claim_readiness.json`` files so public-quality
claims are reviewed across experiments, not cherry-picked from one run.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Sequence


PROTOCOL_VERSION = "gaokao-claim-readiness-portfolio-v1"
STATUS_RANK = {
    "blocked_for_agency_grade_claims": 0,
    "research_benchmark_only": 1,
    "limited_benchmark_claim": 2,
    "agency_candidate_claim": 3,
}


def _status_rank(status: str) -> int:
    return STATUS_RANK.get(status, -1)


def _failed_checks(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in report.get("checks") or []
        if not row.get("passed")
    ]


def _portfolio_row(report: dict[str, Any]) -> dict[str, Any]:
    failed = _failed_checks(report)
    p0_failed = [
        row
        for row in failed
        if str(row.get("severity") or "").upper() == "P0"
    ]
    p1_failed = [
        row
        for row in failed
        if str(row.get("severity") or "").upper() == "P1"
    ]
    return {
        "experiment_id": str(report.get("experiment_id") or ""),
        "status": report.get("status") or "unknown",
        "failed_check_count": len(failed),
        "p0_failed_count": len(p0_failed),
        "p1_failed_count": len(p1_failed),
        "allowed_claim_count": len(report.get("allowed_claims") or []),
        "forbidden_claim_count": len(report.get("forbidden_claims") or []),
        "top_failed_checks": [
            str(row.get("name") or "")
            for row in failed[:5]
            if row.get("name")
        ],
    }


def _portfolio_status(status_counts: Counter[str]) -> str:
    if not status_counts:
        return "empty"
    if status_counts.get("agency_candidate_claim"):
        return "has_agency_candidate"
    if status_counts.get("limited_benchmark_claim") or status_counts.get("research_benchmark_only"):
        return "needs_targeted_iteration"
    return "blocked_for_external_claims"


def _recommendation(
    *,
    portfolio_status: str,
    common_blockers: list[dict[str, Any]],
) -> str:
    if portfolio_status == "empty":
        return "Run claim-readiness on at least one QuantLab manifest."
    if portfolio_status == "has_agency_candidate":
        return (
            "Use the candidate as an external-review target, but keep independent "
            "validation and family-facing disclaimers before public agency-grade claims."
        )
    if common_blockers:
        blocker = common_blockers[0]["check"]
        return f"Repair the most common blocker first: {blocker}."
    return "Expand frozen evidence before making external quality claims."


def build_claim_readiness_portfolio(reports: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate claim-readiness audits into a cross-experiment review surface."""
    rows = [_portfolio_row(dict(report)) for report in reports]
    rows = sorted(
        rows,
        key=lambda row: (
            _status_rank(str(row.get("status") or "")),
            -int(row.get("p0_failed_count") or 0),
            -int(row.get("failed_check_count") or 0),
            str(row.get("experiment_id") or ""),
        ),
        reverse=True,
    )
    for index, row in enumerate(rows, start=1):
        row["rank"] = index

    status_counts: Counter[str] = Counter(str(row.get("status") or "unknown") for row in rows)
    blocker_counter: Counter[str] = Counter()
    blocker_reasons: dict[str, str] = {}
    for report in reports:
        for check in _failed_checks(dict(report)):
            name = str(check.get("name") or "unknown_check")
            blocker_counter[name] += 1
            blocker_reasons.setdefault(name, str(check.get("blocker_reason") or ""))

    common_blockers = [
        {
            "check": name,
            "count": count,
            "blocker_reason": blocker_reasons.get(name, ""),
        }
        for name, count in blocker_counter.most_common(10)
    ]
    portfolio_status = _portfolio_status(status_counts)
    best_row = rows[0] if rows else {}
    return {
        "protocol_version": PROTOCOL_VERSION,
        "report_count": len(rows),
        "portfolio_status": portfolio_status,
        "status_counts": dict(status_counts),
        "best_status": best_row.get("status"),
        "best_experiment_id": best_row.get("experiment_id"),
        "agency_candidate_count": status_counts.get("agency_candidate_claim", 0),
        "blocked_count": status_counts.get("blocked_for_agency_grade_claims", 0),
        "common_blockers": common_blockers,
        "experiments": rows,
        "recommendation": _recommendation(
            portfolio_status=portfolio_status,
            common_blockers=common_blockers,
        ),
        "notes": [
            "This portfolio summarizes evidence boundaries across runs; it is not an admission guarantee.",
            "Agency-grade public claims still require independent held-out validation and disclosed constraints.",
        ],
    }


def build_markdown_claim_readiness_portfolio(result: dict[str, Any]) -> str:
    """Render a Markdown report for claim-readiness portfolio review."""
    lines = [
        "# Claim Readiness Portfolio",
        "",
        f"Reports: {result.get('report_count', 0)}",
        f"Portfolio status: `{result.get('portfolio_status', 'unknown')}`",
        f"Best experiment: `{result.get('best_experiment_id') or ''}`",
        f"Best status: `{result.get('best_status') or ''}`",
        "",
        "## Experiments",
        "",
        "| Rank | Experiment | Status | Failed | P0 | P1 | Allowed | Forbidden | Top failed checks |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result.get("experiments") or []:
        lines.append(
            f"| {row.get('rank', '')} | `{row.get('experiment_id', '')}` | "
            f"`{row.get('status', '')}` | {row.get('failed_check_count', 0)} | "
            f"{row.get('p0_failed_count', 0)} | {row.get('p1_failed_count', 0)} | "
            f"{row.get('allowed_claim_count', 0)} | {row.get('forbidden_claim_count', 0)} | "
            f"`{', '.join(row.get('top_failed_checks') or [])}` |"
        )
    if not result.get("experiments"):
        lines.append("|  | `none` |  |  |  |  |  |  |  |")

    lines.extend(["", "## Common Blockers", ""])
    for item in result.get("common_blockers") or []:
        lines.append(
            f"- `{item.get('check', '')}` x {item.get('count', 0)}: "
            f"{item.get('blocker_reason', '')}"
        )
    if not result.get("common_blockers"):
        lines.append("- none")

    lines.extend([
        "",
        "## Recommendation",
        "",
        str(result.get("recommendation") or ""),
        "",
        "## Notes",
        "",
    ])
    for note in result.get("notes") or []:
        lines.append(f"- {note}")
    return "\n".join(lines)

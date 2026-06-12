"""Portfolio-level audit for client delivery bundles.

Single-case gates catch one bad handoff. A service that wants agency-grade
reliability also needs to know which gates fail repeatedly across cases. This
module aggregates delivery-bundle manifests into operational improvement
signals.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable


STATUS_ORDER = {
    "blocked": 0,
    "needs_revision": 1,
    "pending_signoff": 2,
    "ready_to_deliver": 3,
}

PASSING_GATE_STATUSES = {"pass", "ready", "ready_for_recommendation"}


def _float(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _bundle_score(bundle: dict[str, Any]) -> float:
    scores = [
        _float(bundle, "intake_readiness_score"),
        _float(bundle, "plan_quality_score"),
        _float(bundle, "report_quality_score"),
    ]
    nonzero = [score for score in scores if score > 0]
    return _mean(nonzero)


def _failed_gates(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    gates = bundle.get("delivery_gates") or []
    failed: list[dict[str, Any]] = []
    for gate in gates:
        status = str(gate.get("status") or "unknown")
        if status not in PASSING_GATE_STATUSES:
            failed.append(gate)
    return failed


def _client_delivery_state(bundle: dict[str, Any]) -> dict[str, Any]:
    client_delivery = bundle.get("client_delivery")
    if isinstance(client_delivery, dict):
        allowed = bool(client_delivery.get("allowed"))
        return {
            "allowed": allowed,
            "status": str(client_delivery.get("status") or ("allowed" if allowed else "blocked")),
            "blocked_reason": str(client_delivery.get("blocked_reason") or ""),
        }
    status = str(bundle.get("status") or "unknown")
    allowed = status in {"ready_to_deliver", "pending_signoff"}
    return {
        "allowed": allowed,
        "status": "allowed" if allowed else "blocked",
        "blocked_reason": ""
        if allowed
        else "客户交付状态缺少显式 client_delivery 门控，已按交付包 status 保守拦截。",
    }


def _status(manifests: list[dict[str, Any]], ready_rate: float, blocked_rate: float) -> str:
    if not manifests:
        return "no_cases"
    if blocked_rate >= 0.10:
        return "blocked_for_scale"
    if ready_rate < 0.50:
        return "needs_operational_iteration"
    if ready_rate < 0.80:
        return "needs_targeted_iteration"
    return "on_track"


def audit_delivery_portfolio(manifests: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate many delivery-bundle manifests into service-quality metrics."""
    records = [dict(item) for item in manifests]
    case_count = len(records)
    status_counts = Counter(str(item.get("status") or "unknown") for item in records)
    gate_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    failed_gate_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    client_delivery_status_counts: Counter[str] = Counter()
    client_delivery_blocked_reason_counts: Counter[str] = Counter()
    client_delivery_allowed_count = 0
    score_buckets = {
        "intake_readiness_score": [],
        "plan_quality_score": [],
        "report_quality_score": [],
    }
    worst_cases: list[dict[str, Any]] = []

    for bundle in records:
        client_delivery = _client_delivery_state(bundle)
        client_delivery_status_counts[str(client_delivery["status"])] += 1
        if client_delivery["allowed"]:
            client_delivery_allowed_count += 1
        elif client_delivery["blocked_reason"]:
            client_delivery_blocked_reason_counts[str(client_delivery["blocked_reason"])] += 1
        for key in score_buckets:
            value = _float(bundle, key)
            if value > 0:
                score_buckets[key].append(value)
        failed_gates = _failed_gates(bundle)
        for gate in bundle.get("delivery_gates", []) or []:
            gate_status_counts[str(gate.get("gate") or "unknown")][str(gate.get("status") or "unknown")] += 1
        for gate in failed_gates:
            failed_gate_counts[str(gate.get("gate") or "unknown")] += 1
        for action in bundle.get("next_actions", []) or []:
            action_counts[str(action)] += 1
        worst_cases.append(
            {
                "case_id": bundle.get("case_id", ""),
                "status": bundle.get("status", "unknown"),
                "portfolio_score": round(_bundle_score(bundle), 6),
                "failed_gates": [
                    {
                        "gate": gate.get("gate"),
                        "status": gate.get("status"),
                    }
                    for gate in failed_gates
                ],
            }
        )

    ready_count = status_counts["ready_to_deliver"]
    blocked_count = status_counts["blocked"]
    ready_rate = ready_count / case_count if case_count else 0.0
    blocked_rate = blocked_count / case_count if case_count else 0.0
    client_delivery_allowed_rate = client_delivery_allowed_count / case_count if case_count else 0.0
    client_delivery_blocked_rate = 1.0 - client_delivery_allowed_rate if case_count else 0.0
    worst_cases = sorted(
        worst_cases,
        key=lambda item: (
            STATUS_ORDER.get(str(item["status"]), -1),
            float(item["portfolio_score"]),
            str(item["case_id"]),
        ),
    )[:10]
    top_failed_gates = [
        {
            "gate": gate,
            "failed_count": count,
            "failed_rate": round(count / case_count, 6) if case_count else 0.0,
        }
        for gate, count in failed_gate_counts.most_common()
    ]
    top_next_actions = [
        {"action": action, "count": count, "rate": round(count / case_count, 6) if case_count else 0.0}
        for action, count in action_counts.most_common(10)
    ]
    top_client_delivery_blocked_reasons = [
        {"reason": reason, "count": count, "rate": round(count / case_count, 6) if case_count else 0.0}
        for reason, count in client_delivery_blocked_reason_counts.most_common(10)
    ]
    return {
        "status": _status(records, ready_rate, blocked_rate),
        "case_count": case_count,
        "ready_to_deliver_rate": round(ready_rate, 6),
        "blocked_rate": round(blocked_rate, 6),
        "status_counts": dict(status_counts),
        "client_delivery_allowed_rate": round(client_delivery_allowed_rate, 6),
        "client_delivery_blocked_rate": round(client_delivery_blocked_rate, 6),
        "client_delivery_status_counts": dict(client_delivery_status_counts),
        "top_client_delivery_blocked_reasons": top_client_delivery_blocked_reasons,
        "average_scores": {
            key: round(_mean(values), 6)
            for key, values in score_buckets.items()
        },
        "gate_status_counts": {
            gate: dict(counter)
            for gate, counter in sorted(gate_status_counts.items())
        },
        "top_failed_gates": top_failed_gates,
        "top_next_actions": top_next_actions,
        "worst_cases": worst_cases,
        "portfolio_standard": (
            "A scalable Gaokao planning service should keep blocked delivery bundles rare, "
            "raise ready-to-deliver share over time, track client-delivery blocks separately, "
            "and treat repeated failed gates as product work."
        ),
    }


def build_markdown_delivery_portfolio_audit(result: dict[str, Any]) -> str:
    """Render a delivery-portfolio audit as Markdown."""
    lines = [
        "# Delivery Portfolio Audit",
        "",
        f"Status: `{result.get('status', 'unknown')}`",
        f"Cases: {result.get('case_count', 0)}",
        f"Ready-to-deliver rate: {float(result.get('ready_to_deliver_rate', 0.0)):.1%}",
        f"Blocked rate: {float(result.get('blocked_rate', 0.0)):.1%}",
        f"Client delivery allowed rate: {float(result.get('client_delivery_allowed_rate', 0.0)):.1%}",
        f"Client delivery blocked rate: {float(result.get('client_delivery_blocked_rate', 0.0)):.1%}",
        "",
        result.get("portfolio_standard", ""),
        "",
        "## Status Counts",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    for status, count in (result.get("status_counts", {}) or {}).items():
        lines.append(f"| `{status}` | {count} |")

    lines.extend(["", "## Client Delivery Gate", "", "| Status | Count |", "| --- | ---: |"])
    for status, count in (result.get("client_delivery_status_counts", {}) or {}).items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(["", "### Top Blocked Reasons", ""])
    if result.get("top_client_delivery_blocked_reasons"):
        for idx, item in enumerate(result["top_client_delivery_blocked_reasons"], 1):
            lines.append(
                f"{idx}. ({item.get('count', 0)} cases, {float(item.get('rate', 0.0)):.1%}) "
                f"{item.get('reason', '')}"
            )
    else:
        lines.append("1. No repeated client-delivery blocks.")

    lines.extend(["", "## Average Scores", "", "| Metric | Average |", "| --- | ---: |"])
    for key, value in (result.get("average_scores", {}) or {}).items():
        lines.append(f"| `{key}` | {float(value):.1%} |")

    lines.extend(["", "## Top Failed Gates", "", "| Gate | Failed Count | Failed Rate |", "| --- | ---: | ---: |"])
    if result.get("top_failed_gates"):
        for item in result["top_failed_gates"]:
            lines.append(
                f"| `{item.get('gate', '')}` | {item.get('failed_count', 0)} | "
                f"{float(item.get('failed_rate', 0.0)):.1%} |"
            )
    else:
        lines.append("| `none` | 0 | 0.0% |")

    lines.extend(["", "## Top Next Actions", ""])
    if result.get("top_next_actions"):
        for idx, item in enumerate(result["top_next_actions"], 1):
            lines.append(f"{idx}. ({item.get('count', 0)} cases) {item.get('action', '')}")
    else:
        lines.append("1. No repeated next actions.")

    lines.extend(["", "## Worst Cases", "", "| Case | Status | Score | Failed Gates |", "| --- | --- | ---: | --- |"])
    for item in result.get("worst_cases", []) or []:
        failed = ", ".join(
            f"{gate.get('gate')}={gate.get('status')}"
            for gate in item.get("failed_gates", []) or []
        )
        lines.append(
            f"| `{item.get('case_id', '')}` | `{item.get('status', '')}` | "
            f"{float(item.get('portfolio_score', 0.0)):.1%} | {failed} |"
        )
    return "\n".join(lines) + "\n"

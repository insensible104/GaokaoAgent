"""Build replay queues from experiment failure mining.

Mature quant workflows keep failed historical scenarios as first-class test
sets. This module converts backtest worst cases and ablation regressions into a
JSONL-ready queue that can be fed into the next experiment run.
"""

from __future__ import annotations

from typing import Any, Sequence


CRITICAL_REASONS = {"sliding", "blacklist_hit", "tail_assignment"}


def _case_id(record: dict[str, Any]) -> str:
    plan = record.get("plan") or record.get("volunteer_plan") or {}
    if not isinstance(plan, dict):
        plan = {}
    return str(record.get("case_id") or record.get("id") or plan.get("case_id") or "")


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def _clean_reasons(reasons: Sequence[Any]) -> list[str]:
    return sorted({str(reason) for reason in reasons if str(reason)})


def _recommended_focus(reasons: Sequence[str]) -> list[str]:
    reason_set = set(reasons)
    focus: list[str] = []
    if "sliding" in reason_set:
        focus.append("safe_anchor_and_first_hit_prefix")
    if "blacklist_hit" in reason_set:
        focus.append("hard_constraint_enforcement")
    if "tail_assignment" in reason_set:
        focus.append("major_assignment_tail_risk")
    if "preferred_major_miss" in reason_set:
        focus.append("preferred_major_hit_and_utility")
    if "wasted_score" in reason_set:
        focus.append("score_efficiency_and_prefix_ordering")
    if "missing_actual_outcome" in reason_set:
        focus.append("actual_outcome_key_normalization")
    if not focus:
        focus.append("case_level_manual_review")
    return focus


def _priority_band(reasons: Sequence[str], severity_score: float) -> str:
    if set(reasons) & CRITICAL_REASONS or severity_score >= 0.95:
        return "P0"
    if severity_score >= 0.55:
        return "P1"
    return "P2"


def _add_source(
    entries: dict[str, dict[str, Any]],
    *,
    case_id: str,
    source: str,
    failure_reasons: Sequence[Any],
    severity_score: float,
    variant: str | None = None,
) -> None:
    if not case_id:
        return
    reasons = _clean_reasons(failure_reasons)
    entry = entries.setdefault(
        case_id,
        {
            "case_id": case_id,
            "failure_reasons": set(),
            "severity_score": 0.0,
            "sources": [],
        },
    )
    entry["failure_reasons"].update(reasons)
    entry["severity_score"] = max(float(entry["severity_score"]), float(severity_score))
    source_row: dict[str, Any] = {
        "source": source,
        "failure_reasons": reasons,
        "severity_score": round(float(severity_score), 6),
    }
    if variant:
        source_row["variant"] = variant
    entry["sources"].append(source_row)


def _build_source_entries(
    failure_mining: dict[str, Any] | None,
    ablation_failure_deltas: dict[str, Any] | None,
    *,
    top_k: int,
    include_ablation_regressions: bool,
) -> list[dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for row in (failure_mining or {}).get("worst_cases", [])[:top_k]:
        _add_source(
            entries,
            case_id=str(row.get("case_id") or ""),
            source="backtest_failure",
            failure_reasons=row.get("failure_reasons") or [],
            severity_score=_float(row.get("severity_score")),
        )
    if include_ablation_regressions:
        for row in (ablation_failure_deltas or {}).get("case_regressions", [])[:top_k]:
            _add_source(
                entries,
                case_id=str(row.get("case_id") or ""),
                source="ablation_regression",
                failure_reasons=row.get("new_failures") or [],
                severity_score=_float(row.get("severity_score")),
                variant=str(row.get("variant") or ""),
            )

    normalized: list[dict[str, Any]] = []
    for entry in entries.values():
        reasons = sorted(entry["failure_reasons"])
        severity_score = round(float(entry["severity_score"]), 6)
        normalized.append(
            {
                "case_id": entry["case_id"],
                "failure_reasons": reasons,
                "severity_score": severity_score,
                "priority": _priority_band(reasons, severity_score),
                "recommended_focus": _recommended_focus(reasons),
                "sources": entry["sources"],
            }
        )
    return sorted(normalized, key=lambda item: (-float(item["severity_score"]), str(item["case_id"])))[:top_k]


def build_failure_replay_queue(
    records: Sequence[dict[str, Any]],
    *,
    failure_mining: dict[str, Any] | None = None,
    ablation_failure_deltas: dict[str, Any] | None = None,
    top_k: int = 20,
    include_ablation_regressions: bool = True,
) -> dict[str, Any]:
    """Return frozen plan records annotated with replay metadata."""
    records_by_case = {_case_id(dict(record)): dict(record) for record in records if _case_id(dict(record))}
    source_entries = _build_source_entries(
        failure_mining,
        ablation_failure_deltas,
        top_k=top_k,
        include_ablation_regressions=include_ablation_regressions,
    )
    items: list[dict[str, Any]] = []
    missing_cases: list[dict[str, Any]] = []
    for entry in source_entries:
        record = records_by_case.get(entry["case_id"])
        if not record:
            missing_cases.append(entry)
            continue
        item = dict(record)
        original_metadata = item.get("replay_metadata")
        metadata = {
            "case_id": entry["case_id"],
            "priority": entry["priority"],
            "failure_reasons": entry["failure_reasons"],
            "severity_score": entry["severity_score"],
            "recommended_focus": entry["recommended_focus"],
            "sources": entry["sources"],
            "replay_reason": _replay_reason(entry),
        }
        if original_metadata:
            metadata["input_replay_metadata"] = original_metadata
        item["replay_metadata"] = metadata
        items.append(item)

    return {
        "protocol_version": "gaokao-failure-replay-queue-v1",
        "source_case_count": len(source_entries),
        "queue_count": len(items),
        "missing_case_count": len(missing_cases),
        "missing_case_ids": [entry["case_id"] for entry in missing_cases],
        "missing_cases": missing_cases,
        "items": items,
    }


def _replay_reason(entry: dict[str, Any]) -> str:
    reasons = ", ".join(entry.get("failure_reasons") or []) or "case-level failure"
    sources = ", ".join(sorted({str(row.get("source")) for row in entry.get("sources", []) or []}))
    return f"{entry.get('priority', 'P2')} replay for {reasons} from {sources}"


def build_markdown_replay_queue(result: dict[str, Any]) -> str:
    """Build a compact Markdown report for a failure replay queue."""
    lines = [
        "# Failure Replay Queue",
        "",
        f"Source cases: {result.get('source_case_count', 0)}",
        f"Queued cases: {result.get('queue_count', 0)}",
        f"Missing cases: {result.get('missing_case_count', 0)}",
        "",
        "| Case | Priority | Reasons | Severity | Focus |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for item in result.get("items", []) or []:
        metadata = item.get("replay_metadata") or {}
        lines.append(
            f"| `{metadata.get('case_id', '')}` | `{metadata.get('priority', '')}` | "
            f"{', '.join(f'`{reason}`' for reason in metadata.get('failure_reasons', []) or [])} | "
            f"{float(metadata.get('severity_score', 0.0)):.3f} | "
            f"{', '.join(f'`{focus}`' for focus in metadata.get('recommended_focus', []) or [])} |"
        )
    if not result.get("items"):
        lines.append("| `none` |  |  | 0.000 |  |")

    missing_case_ids = result.get("missing_case_ids") or []
    if missing_case_ids:
        lines.extend(["", "## Missing Cases", ""])
        for case_id in missing_case_ids:
            lines.append(f"- `{case_id}`")
    return "\n".join(lines)

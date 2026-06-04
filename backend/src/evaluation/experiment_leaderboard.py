"""Cross-experiment leaderboard for QuantLab manifests."""

from __future__ import annotations

from typing import Any, Sequence


PROTOCOL_VERSION = "gaokao-quant-lab-leaderboard-v1"


def _nested(payload: dict[str, Any], *path: str) -> Any:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _float(payload: dict[str, Any], *path: str, default: float | None = None) -> float | None:
    value = _nested(payload, *path)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _list_winners(manifest: dict[str, Any]) -> list[str]:
    return [
        str(item.get("variant"))
        for item in _nested(manifest, "promotion_gate", "winners") or []
        if item.get("variant")
    ]


def _composite_score(row: dict[str, Any]) -> float | None:
    if row.get("success_rate") is None:
        return None
    score = 0.0
    score += float(row.get("success_rate") or 0.0) * 100.0
    score += float(row.get("preferred_major_hit_rate") or 0.0) * 25.0
    score += float(row.get("average_assigned_major_utility") or 0.0) * 20.0
    score -= float(row.get("sliding_rate") or 0.0) * 120.0
    score -= float(row.get("blacklist_hit_rate") or 0.0) * 100.0
    score -= float(row.get("tail_assignment_rate") or 0.0) * 80.0
    score -= float(row.get("failure_case_rate") or 0.0) * 50.0
    score -= float(row.get("calibration_brier_score") or 0.0) * 20.0
    score -= float(row.get("blocker_count") or 0.0) * 5.0
    score += float(row.get("holdout_objective_delta_vs_current") or 0.0) * 10.0
    score += float(row.get("benchmark_coverage_score") or 0.0) * 5.0
    score -= float(row.get("benchmark_missing_required_tag_count") or 0.0) * 1.0
    score -= float(row.get("benchmark_missing_critical_pair_count") or 0.0) * 1.5
    return round(score, 6)


def _recommendation(row: dict[str, Any]) -> str:
    if int(row.get("blocker_count") or 0) > 0:
        return "hold_slice_or_delivery_blockers"
    if float(row.get("failure_case_rate") or 0.0) >= 0.25:
        return "replay_failures_before_claim"
    if row.get("promotion_status") == "candidate_found":
        return "inspect_winner_then_replay"
    if row.get("success_rate") is None:
        return "missing_backtest_metrics"
    return "hold_current_until_more_evidence"


def _manifest_row(manifest: dict[str, Any]) -> dict[str, Any]:
    digest = manifest.get("metric_digest") or {}
    row = {
        "experiment_id": str(manifest.get("experiment_id") or ""),
        "created_at": manifest.get("created_at"),
        "promotion_status": _nested(manifest, "promotion_gate", "status"),
        "winner_variants": _list_winners(manifest),
        "success_rate": _float(digest, "backtest", "success_rate"),
        "sliding_rate": _float(digest, "backtest", "sliding_rate"),
        "preferred_major_hit_rate": _float(digest, "backtest", "preferred_major_hit_rate"),
        "blacklist_hit_rate": _float(digest, "backtest", "blacklist_hit_rate"),
        "tail_assignment_rate": _float(digest, "backtest", "tail_assignment_rate"),
        "average_assigned_major_utility": _float(digest, "backtest", "average_assigned_major_utility"),
        "calibration_brier_score": _float(digest, "calibration", "brier_score"),
        "holdout_objective_delta_vs_current": _float(
            digest,
            "tuning",
            "holdout_objective_delta_vs_current",
            default=0.0,
        ),
        "failure_case_rate": _float(digest, "failure_mining", "failure_case_rate", default=0.0),
        "replay_queue_count": _float(digest, "replay_queue", "queue_count", default=0.0),
        "replay_p0_count": _float(digest, "replay_queue", "p0_count", default=0.0),
        "blocker_count": _float(digest, "improvement_audit", "blocker_count", default=0.0),
        "benchmark_coverage_status": _nested(digest, "benchmark_coverage", "status"),
        "benchmark_coverage_score": _float(digest, "benchmark_coverage", "coverage_score", default=0.0),
        "benchmark_missing_required_tag_count": _float(
            digest,
            "benchmark_coverage",
            "missing_required_tag_count",
            default=0.0,
        ),
        "benchmark_missing_critical_pair_count": _float(
            digest,
            "benchmark_coverage",
            "missing_critical_pair_count",
            default=0.0,
        ),
    }
    row["composite_score"] = _composite_score(row)
    row["recommendation"] = _recommendation(row)
    return row


def _attach_baseline_deltas(rows: list[dict[str, Any]], baseline_experiment_id: str | None) -> None:
    if not rows:
        return
    baseline = None
    if baseline_experiment_id:
        baseline = next((row for row in rows if row.get("experiment_id") == baseline_experiment_id), None)
    baseline = baseline or rows[-1]
    fields = [
        "composite_score",
        "success_rate",
        "sliding_rate",
        "blacklist_hit_rate",
        "tail_assignment_rate",
        "preferred_major_hit_rate",
        "average_assigned_major_utility",
        "failure_case_rate",
    ]
    for row in rows:
        row["baseline_experiment_id"] = baseline.get("experiment_id")
        for field in fields:
            value = row.get(field)
            base_value = baseline.get(field)
            row[f"{field}_delta_vs_baseline"] = (
                round(float(value) - float(base_value), 6)
                if value is not None and base_value is not None
                else None
            )


def build_quant_lab_leaderboard(
    manifests: Sequence[dict[str, Any]],
    *,
    baseline_experiment_id: str | None = None,
) -> dict[str, Any]:
    """Rank QuantLab manifests for research triage."""
    rows = [_manifest_row(dict(manifest)) for manifest in manifests]
    rows = sorted(
        rows,
        key=lambda row: (
            row.get("composite_score") is not None,
            float(row.get("composite_score") or -10**9),
            str(row.get("created_at") or ""),
        ),
        reverse=True,
    )
    _attach_baseline_deltas(rows, baseline_experiment_id)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return {
        "protocol_version": PROTOCOL_VERSION,
        "experiment_count": len(rows),
        "baseline_experiment_id": rows[0].get("baseline_experiment_id") if rows else None,
        "best_experiment_id": rows[0].get("experiment_id") if rows else None,
        "rows": rows,
        "notes": [
            "Composite score is a triage heuristic, not proof of production superiority.",
            "A candidate still needs replay-queue validation and slice/delivery guardrails before runtime adoption.",
        ],
    }


def build_markdown_quant_lab_leaderboard(result: dict[str, Any]) -> str:
    """Build a Markdown leaderboard for experiment review."""
    lines = [
        "# QuantLab Experiment Leaderboard",
        "",
        f"Experiments: {result.get('experiment_count', 0)}",
        f"Baseline: `{result.get('baseline_experiment_id') or ''}`",
        f"Best: `{result.get('best_experiment_id') or ''}`",
        "",
        "| Rank | Experiment | Score | Success | Sliding | Preferred | Failure | Coverage | Replay | Gate | Recommendation |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in result.get("rows", []) or []:
        score = row.get("composite_score")
        score_text = f"{float(score):.3f}" if score is not None else ""
        lines.append(
            f"| {row.get('rank', '')} | `{row.get('experiment_id', '')}` | "
            f"{score_text} | "
            f"{float(row.get('success_rate') or 0.0):.1%} | "
            f"{float(row.get('sliding_rate') or 0.0):.1%} | "
            f"{float(row.get('preferred_major_hit_rate') or 0.0):.1%} | "
            f"{float(row.get('failure_case_rate') or 0.0):.1%} | "
            f"{float(row.get('benchmark_coverage_score') or 0.0):.1%} | "
            f"{int(row.get('replay_queue_count') or 0)} | "
            f"`{row.get('promotion_status') or ''}` | "
            f"`{row.get('recommendation') or ''}` |"
        )
    if not result.get("rows"):
        lines.append("|  | `none` |  |  |  |  |  |  |  |  |  |")

    lines.extend(["", "## Notes", ""])
    for note in result.get("notes") or []:
        lines.append(f"- {note}")
    return "\n".join(lines)

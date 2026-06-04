"""Experiment registry helpers for GaokaoAgent quant research.

This module turns separate backtest, calibration, tuning, ablation, and audit
outputs into one reproducible experiment manifest. It mirrors the workflow
discipline of mature quant systems without forcing a heavy platform rewrite.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any, Mapping


PROTOCOL_VERSION = "gaokao-quant-lab-v1"
MISSION = "高考志愿平权化：用可评估、可回测、可优化的量化闭环逼近头部填报机构质量。"


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_artifact_manifest(paths: Mapping[str, str | Path | None]) -> dict[str, Any]:
    """Build stable metadata for experiment input/output artifacts."""
    artifacts: dict[str, Any] = {}
    for name, raw_path in paths.items():
        if not raw_path:
            continue
        path = Path(raw_path)
        exists = path.exists()
        stat = path.stat() if exists else None
        artifacts[name] = {
            "path": str(path),
            "exists": exists,
            "size_bytes": stat.st_size if stat else 0,
            "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat() if stat else None,
            "sha256": _sha256(path),
        }
    return artifacts


def _metric(payload: dict[str, Any] | None, key: str) -> float | None:
    if not payload:
        return None
    try:
        return float(payload.get(key))
    except (TypeError, ValueError):
        return None


def _metric_value(payload: dict[str, Any] | None, key: str) -> float:
    value = _metric(payload, key)
    return value if value is not None else 0.0


def _summary_digest(
    *,
    backtest_summary: dict[str, Any] | None = None,
    calibration_summary: dict[str, Any] | None = None,
    tuning_summary: dict[str, Any] | None = None,
    ablation_summary: dict[str, Any] | None = None,
    improvement_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    digest: dict[str, Any] = {}
    if backtest_summary:
        digest["backtest"] = {
            key: _metric(backtest_summary, key)
            for key in (
                "case_count",
                "success_rate",
                "sliding_rate",
                "preferred_major_hit_rate",
                "blacklist_hit_rate",
                "tail_assignment_rate",
                "wasted_score_rate",
                "average_assigned_major_utility",
            )
        }
    if calibration_summary:
        overall = calibration_summary.get("overall") or {}
        digest["calibration"] = {
            key: _metric(overall, key)
            for key in (
                "choice_count",
                "brier_score",
                "absolute_calibration_error",
                "bucket_absolute_calibration_error",
                "tail_assignment_rate",
                "wasted_score_rate",
            )
        }
    if tuning_summary:
        best = tuning_summary.get("best") or {}
        holdout = best.get("holdout") or {}
        digest["tuning"] = {
            "best_name": best.get("name"),
            "best_weights": best.get("weights") or {},
            "train_objective_delta_vs_current": _metric(best, "objective_delta_vs_current"),
            "holdout_objective_delta_vs_current": _metric(holdout, "objective_delta_vs_current"),
            "holdout_brier_delta_vs_current": _metric(holdout, "brier_delta_vs_current"),
        }
    if ablation_summary:
        summaries = ablation_summary.get("summaries") or {}
        deltas = ablation_summary.get("deltas_vs_full") or {}
        digest["ablation"] = {
            "variant_count": len(ablation_summary.get("variants") or []),
            "full": summaries.get("full") or {},
            "deltas_vs_full": deltas,
            "slice_count": (ablation_summary.get("slice_scoreboard") or {}).get("slice_count", 0),
        }
    if improvement_audit:
        digest["improvement_audit"] = {
            "status": improvement_audit.get("status"),
            "priority_count": len(improvement_audit.get("prioritized_actions") or []),
            "blocker_count": len(
                [
                    item
                    for item in improvement_audit.get("prioritized_actions") or []
                    if str(item.get("priority") or "").upper() == "P0"
                ]
            ),
        }
    return digest


def _promotion_gate(ablation_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not ablation_summary:
        return {
            "status": "not_evaluable",
            "reason": "No ablation summary was provided.",
        }
    full = (ablation_summary.get("summaries") or {}).get("full") or {}
    candidates: list[dict[str, Any]] = []
    for variant, summary in (ablation_summary.get("summaries") or {}).items():
        if variant == "full":
            continue
        success_delta = _metric_value(summary, "success_rate") - _metric_value(full, "success_rate")
        blacklist_delta = _metric_value(summary, "blacklist_hit_rate") - _metric_value(full, "blacklist_hit_rate")
        tail_delta = _metric_value(summary, "tail_assignment_rate") - _metric_value(full, "tail_assignment_rate")
        preferred_delta = _metric_value(summary, "preferred_major_hit_rate") - _metric_value(
            full,
            "preferred_major_hit_rate",
        )
        utility_delta = _metric_value(summary, "average_assigned_major_utility") - _metric_value(
            full,
            "average_assigned_major_utility",
        )
        passes = (
            success_delta >= 0
            and blacklist_delta <= 0
            and tail_delta <= 0.03
            and (preferred_delta > 0 or utility_delta > 0)
        )
        candidates.append(
            {
                "variant": variant,
                "passes_shadow_gate": passes,
                "success_delta": round(success_delta, 6),
                "blacklist_delta": round(blacklist_delta, 6),
                "tail_assignment_delta": round(tail_delta, 6),
                "preferred_major_delta": round(preferred_delta, 6),
                "utility_delta": round(utility_delta, 6),
            }
        )
    winners = [item for item in candidates if item["passes_shadow_gate"]]
    return {
        "status": "candidate_found" if winners else "hold_current",
        "rule": (
            "Promote only if success is not worse, blacklist does not worsen, "
            "tail risk rises by no more than 3pp, and preferred-major or utility improves."
        ),
        "candidates": candidates,
        "winners": winners,
    }


def build_quant_lab_experiment(
    *,
    experiment_id: str,
    config: dict[str, Any] | None = None,
    artifacts: dict[str, Any] | None = None,
    backtest_summary: dict[str, Any] | None = None,
    calibration_summary: dict[str, Any] | None = None,
    tuning_summary: dict[str, Any] | None = None,
    ablation_summary: dict[str, Any] | None = None,
    improvement_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a single experiment manifest from quant outputs."""
    return {
        "protocol_version": PROTOCOL_VERSION,
        "experiment_id": experiment_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mission": MISSION,
        "config": config or {},
        "artifacts": artifacts or {},
        "metric_digest": _summary_digest(
            backtest_summary=backtest_summary,
            calibration_summary=calibration_summary,
            tuning_summary=tuning_summary,
            ablation_summary=ablation_summary,
            improvement_audit=improvement_audit,
        ),
        "promotion_gate": _promotion_gate(ablation_summary),
        "required_next_checks": [
            "Keep actual-outcome labels post-hoc only.",
            "Validate any tuned/shadow variant on a later frozen-plan split before runtime adoption.",
            "Inspect slice_scoreboard for boundary-rank and hard-constraint regressions.",
            "Use official-source evidence before turning search signals into prediction features.",
        ],
    }


def build_markdown_quant_lab_report(manifest: dict[str, Any]) -> str:
    """Build a concise Markdown report for one registered experiment."""
    digest = manifest.get("metric_digest") or {}
    gate = manifest.get("promotion_gate") or {}
    lines = [
        "# Gaokao QuantLab Experiment",
        "",
        f"Experiment: `{manifest.get('experiment_id', '')}`",
        f"Protocol: `{manifest.get('protocol_version', '')}`",
        "",
        "## Metric Digest",
        "",
    ]
    for section, payload in digest.items():
        lines.append(f"### {section}")
        for key, value in payload.items():
            if isinstance(value, dict):
                lines.append(f"- `{key}`: `{value}`")
            else:
                lines.append(f"- `{key}`: {value}")
        lines.append("")

    lines.extend(
        [
            "## Promotion Gate",
            "",
            f"Status: `{gate.get('status', 'unknown')}`",
            "",
        ]
    )
    for item in gate.get("candidates") or []:
        marker = "PASS" if item.get("passes_shadow_gate") else "HOLD"
        lines.append(
            f"- `{item.get('variant')}`: {marker}, "
            f"success {item.get('success_delta'):+.3f}, "
            f"preferred {item.get('preferred_major_delta'):+.3f}, "
            f"tail {item.get('tail_assignment_delta'):+.3f}, "
            f"blacklist {item.get('blacklist_delta'):+.3f}"
        )
    if not gate.get("candidates"):
        lines.append("- No shadow candidate evaluated.")

    lines.extend(["", "## Required Next Checks", ""])
    for item in manifest.get("required_next_checks") or []:
        lines.append(f"- {item}")
    return "\n".join(lines)

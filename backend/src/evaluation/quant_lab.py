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
CRITICAL_SLICE_PREFIXES = (
    "rank_boundary_or_lower",
    "rank_60k_120k",
    "region_guangdong_or_city_locked",
    "region_narrow_preference",
    "major_has_blacklist",
    "major_strict_preference",
    "major_cognition_high",
    "regret_sensitive",
    "risk_conservative",
)


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
    failure_mining: dict[str, Any] | None = None,
    ablation_failure_deltas: dict[str, Any] | None = None,
    replay_queue_summary: dict[str, Any] | None = None,
    benchmark_coverage: dict[str, Any] | None = None,
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
    if failure_mining:
        digest["failure_mining"] = {
            "failure_case_count": _metric(failure_mining, "failure_case_count"),
            "failure_case_rate": _metric(failure_mining, "failure_case_rate"),
            "missing_actual_choice_count": _metric(failure_mining, "missing_actual_choice_count"),
            "top_failure_bucket": (
                (failure_mining.get("failure_buckets") or [{}])[0].get("bucket")
                if failure_mining.get("failure_buckets")
                else None
            ),
        }
    if ablation_failure_deltas:
        digest["ablation_failure_deltas"] = {
            "variant_count": len(ablation_failure_deltas.get("variant_failure_deltas") or {}),
            "case_regression_count": len(ablation_failure_deltas.get("case_regressions") or []),
        }
    if replay_queue_summary:
        p0_count = 0
        p1_count = 0
        for item in replay_queue_summary.get("items") or []:
            metadata = item.get("replay_metadata") or {}
            if metadata.get("priority") == "P0":
                p0_count += 1
            if metadata.get("priority") == "P1":
                p1_count += 1
        digest["replay_queue"] = {
            "queue_count": _metric(replay_queue_summary, "queue_count"),
            "source_case_count": _metric(replay_queue_summary, "source_case_count"),
            "missing_case_count": _metric(replay_queue_summary, "missing_case_count"),
            "p0_count": float(p0_count),
            "p1_count": float(p1_count),
        }
    if benchmark_coverage:
        gap_summary = benchmark_coverage.get("gap_summary") or {}
        digest["benchmark_coverage"] = {
            "status": benchmark_coverage.get("status"),
            "case_count": _metric(benchmark_coverage, "case_count"),
            "coverage_score": _metric(benchmark_coverage, "coverage_score"),
            "missing_required_tag_count": _metric(gap_summary, "missing_required_tag_count"),
            "missing_critical_pair_count": _metric(gap_summary, "missing_critical_pair_count"),
            "thin_required_tag_count": _metric(gap_summary, "thin_required_tag_count"),
            "thin_critical_pair_count": _metric(gap_summary, "thin_critical_pair_count"),
        }
    return digest


def _promotion_gate(ablation_summary: dict[str, Any] | None) -> dict[str, Any]:
    if not ablation_summary:
        return {
            "status": "not_evaluable",
            "reason": "No ablation summary was provided.",
        }
    full = (ablation_summary.get("summaries") or {}).get("full") or {}
    slice_guardrails = _slice_guardrails(ablation_summary)
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
        aggregate_passes = (
            success_delta >= 0
            and blacklist_delta <= 0
            and tail_delta <= 0.03
            and (preferred_delta > 0 or utility_delta > 0)
        )
        slice_blockers = slice_guardrails.get("blockers_by_variant", {}).get(variant, [])
        passes = aggregate_passes and not slice_blockers
        candidates.append(
            {
                "variant": variant,
                "aggregate_passes": aggregate_passes,
                "passes_shadow_gate": passes,
                "success_delta": round(success_delta, 6),
                "blacklist_delta": round(blacklist_delta, 6),
                "tail_assignment_delta": round(tail_delta, 6),
                "preferred_major_delta": round(preferred_delta, 6),
                "utility_delta": round(utility_delta, 6),
                "slice_blocker_count": len(slice_blockers),
                "slice_blockers": slice_blockers,
            }
        )
    winners = [item for item in candidates if item["passes_shadow_gate"]]
    return {
        "status": "candidate_found" if winners else "hold_current",
        "rule": (
            "Promote only if success is not worse, blacklist does not worsen, "
            "tail risk rises by no more than 3pp, preferred-major or utility improves, "
            "and critical user slices do not regress."
        ),
        "slice_guardrails": slice_guardrails,
        "candidates": candidates,
        "winners": winners,
    }


def _is_critical_slice(slice_name: str) -> bool:
    return slice_name.startswith(CRITICAL_SLICE_PREFIXES)


def _slice_guardrails(ablation_summary: dict[str, Any]) -> dict[str, Any]:
    """Build promotion blockers from slice-level variant regressions."""
    scoreboard = ablation_summary.get("slice_scoreboard") or {}
    rows = scoreboard.get("rows") or []
    if not rows:
        return {
            "status": "not_evaluable",
            "reason": "No slice_scoreboard rows were provided.",
            "critical_slice_prefixes": list(CRITICAL_SLICE_PREFIXES),
            "blockers_by_variant": {},
        }

    by_slice_variant = {
        (str(row.get("slice") or ""), str(row.get("variant") or "")): row
        for row in rows
    }
    blockers_by_variant: dict[str, list[dict[str, Any]]] = {}
    for (slice_name, variant), row in by_slice_variant.items():
        if variant == "full" or not _is_critical_slice(slice_name):
            continue
        baseline = by_slice_variant.get((slice_name, "full"))
        if not baseline:
            continue
        checks = [
            (
                "success_rate",
                _metric_value(row, "success_rate") - _metric_value(baseline, "success_rate"),
                -0.000001,
                "critical slice success cannot decline",
                "min",
            ),
            (
                "preferred_major_hit_rate",
                _metric_value(row, "preferred_major_hit_rate")
                - _metric_value(baseline, "preferred_major_hit_rate"),
                -0.050001,
                "critical slice preferred-major hit cannot decline by more than 5pp",
                "min",
            ),
            (
                "blacklist_hit_rate",
                _metric_value(row, "blacklist_hit_rate") - _metric_value(baseline, "blacklist_hit_rate"),
                0.000001,
                "critical slice blacklist rate cannot increase",
                "max",
            ),
            (
                "tail_assignment_hit_rate",
                _metric_value(row, "tail_assignment_hit_rate")
                - _metric_value(baseline, "tail_assignment_hit_rate"),
                0.050001,
                "critical slice tail-assignment rate cannot rise by more than 5pp",
                "max",
            ),
        ]
        for metric, delta, threshold, reason, direction in checks:
            blocked = delta < threshold if direction == "min" else delta > threshold
            if not blocked:
                continue
            blockers_by_variant.setdefault(variant, []).append(
                {
                    "slice": slice_name,
                    "metric": metric,
                    "delta_vs_full": round(delta, 6),
                    "case_count": row.get("case_count", 0),
                    "reason": reason,
                }
            )

    return {
        "status": "pass" if not blockers_by_variant else "blocked",
        "critical_slice_prefixes": list(CRITICAL_SLICE_PREFIXES),
        "blockers_by_variant": blockers_by_variant,
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
    failure_mining: dict[str, Any] | None = None,
    ablation_failure_deltas: dict[str, Any] | None = None,
    replay_queue_summary: dict[str, Any] | None = None,
    benchmark_coverage: dict[str, Any] | None = None,
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
            failure_mining=failure_mining,
            ablation_failure_deltas=ablation_failure_deltas,
            replay_queue_summary=replay_queue_summary,
            benchmark_coverage=benchmark_coverage,
        ),
        "promotion_gate": _promotion_gate(ablation_summary),
        "failure_mining": failure_mining or {},
        "ablation_failure_deltas": ablation_failure_deltas or {},
        "replay_queue_summary": replay_queue_summary or {},
        "benchmark_coverage": benchmark_coverage or {},
        "required_next_checks": [
            "Keep actual-outcome labels post-hoc only.",
            "Validate any tuned/shadow variant on a later frozen-plan split before runtime adoption.",
            "Inspect slice_scoreboard for boundary-rank and hard-constraint regressions.",
            "Replay worst failure cases before accepting aggregate metric gains.",
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
            f"blacklist {item.get('blacklist_delta'):+.3f}, "
            f"slice blockers {item.get('slice_blocker_count', 0)}"
        )
    if not gate.get("candidates"):
        lines.append("- No shadow candidate evaluated.")

    slice_guardrails = gate.get("slice_guardrails") or {}
    blockers_by_variant = slice_guardrails.get("blockers_by_variant") or {}
    lines.extend(["", "## Slice Guardrails", "", f"Status: `{slice_guardrails.get('status', 'unknown')}`", ""])
    if blockers_by_variant:
        for variant, blockers in blockers_by_variant.items():
            for blocker in blockers[:8]:
                lines.append(
                    f"- `{variant}` blocked on `{blocker.get('slice')}` "
                    f"`{blocker.get('metric')}` delta {blocker.get('delta_vs_full'):+.3f}: "
                    f"{blocker.get('reason')}"
                )
    else:
        reason = slice_guardrails.get("reason")
        lines.append(f"- {reason}" if reason else "- No critical slice blocker found.")

    failure_mining = manifest.get("failure_mining") or {}
    if failure_mining:
        lines.extend(
            [
                "",
                "## Failure Mining",
                "",
                f"Failure cases: {failure_mining.get('failure_case_count', 0)} "
                f"({float(failure_mining.get('failure_case_rate', 0.0)):.1%})",
                "",
            ]
        )
        for row in (failure_mining.get("failure_buckets") or [])[:6]:
            lines.append(
                f"- `{row.get('bucket')}`: {row.get('case_count', 0)} cases "
                f"({float(row.get('case_rate', 0.0)):.1%})"
            )
        worst = failure_mining.get("worst_cases") or []
        if worst:
            lines.extend(["", "Worst cases:"])
            for row in worst[:5]:
                reasons = ", ".join(str(item) for item in row.get("failure_reasons", []) or [])
                lines.append(
                    f"- `{row.get('case_id')}` severity {float(row.get('severity_score', 0.0)):.3f}: {reasons}"
                )

    ablation_failure_deltas = manifest.get("ablation_failure_deltas") or {}
    regressions = ablation_failure_deltas.get("case_regressions") or []
    if regressions:
        lines.extend(["", "## Ablation Case Regressions", ""])
        for row in regressions[:5]:
            failures = ", ".join(str(item) for item in row.get("new_failures", []) or [])
            lines.append(f"- `{row.get('variant')}` / `{row.get('case_id')}` new failures: {failures}")

    lines.extend(["", "## Required Next Checks", ""])
    for item in manifest.get("required_next_checks") or []:
        lines.append(f"- {item}")
    return "\n".join(lines)

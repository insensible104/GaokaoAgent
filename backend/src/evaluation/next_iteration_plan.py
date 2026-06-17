"""Build the next experiment plan from audit artifacts.

The standard suite produces many review surfaces. This module turns them into
one operator-facing plan so the next iteration is driven by evidence rather
than by the loudest anecdote.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping


PROTOCOL_VERSION = "gaokao-next-iteration-plan-v1"
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def _priority(value: str | None, default: str = "P2") -> str:
    text = str(value or default).upper()
    return text if text in PRIORITY_ORDER else default


def _append_item(
    items: list[dict[str, Any]],
    *,
    priority: str,
    source: str,
    area: str,
    action: str,
    reason: str,
    evidence: dict[str, Any] | None = None,
) -> None:
    items.append(
        {
            "priority": _priority(priority),
            "source": source,
            "area": area,
            "action": action,
            "reason": reason,
            "evidence": evidence or {},
        }
    )


def _sort_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            PRIORITY_ORDER.get(str(item.get("priority")), 9),
            str(item.get("source") or ""),
            str(item.get("area") or ""),
            str(item.get("action") or ""),
        ),
    )


def _add_improvement_items(items: list[dict[str, Any]], improvement_audit: dict[str, Any] | None) -> None:
    if not improvement_audit:
        return
    for finding in (improvement_audit.get("prioritized_actions") or improvement_audit.get("findings") or [])[:12]:
        _append_item(
            items,
            priority=str(finding.get("severity") or "P2"),
            source="improvement_audit",
            area=str(finding.get("area") or "unknown"),
            action=str(finding.get("recommendation") or ""),
            reason=str(finding.get("finding") or ""),
            evidence={
                "target": finding.get("target"),
                "evidence": finding.get("evidence") or {},
            },
        )


def _add_coverage_items(items: list[dict[str, Any]], coverage_repair_plan: dict[str, Any] | None) -> None:
    if not coverage_repair_plan:
        return
    specs = coverage_repair_plan.get("profile_specs") or []
    if not specs:
        return
    critical_count = sum(1 for spec in specs if str(spec.get("priority") or "") == "P0")
    _append_item(
        items,
        priority="P0" if critical_count else "P1",
        source="benchmark_coverage_repair",
        area="frozen_case_coverage",
        action="Generate repaired frozen profiles before trusting aggregate metrics.",
        reason="Benchmark coverage repair plan contains missing or thin critical slices.",
        evidence={
            "repair_spec_count": len(specs),
            "critical_repair_spec_count": critical_count,
            "top_profile_specs": specs[:5],
        },
    )


def _add_replay_items(items: list[dict[str, Any]], replay_queue_summary: dict[str, Any] | None) -> None:
    if not replay_queue_summary:
        return
    queue_count = int(replay_queue_summary.get("queue_count", 0) or 0)
    missing_count = int(replay_queue_summary.get("missing_case_count", 0) or 0)
    if queue_count <= 0 and missing_count <= 0:
        return
    p0_count = 0
    focus_counter: Counter[str] = Counter()
    for item in replay_queue_summary.get("items") or []:
        metadata = item.get("replay_metadata") or {}
        if metadata.get("priority") == "P0":
            p0_count += 1
        focus_counter.update(str(focus) for focus in metadata.get("recommended_focus") or [])
    _append_item(
        items,
        priority="P0" if p0_count else "P1",
        source="failure_replay_queue",
        area="case_replay",
        action="Replay queued failure cases before accepting aggregate metric gains.",
        reason="Known hard cases must become a standard regression set.",
        evidence={
            "queue_count": queue_count,
            "p0_replay_count": p0_count,
            "missing_case_count": missing_count,
            "top_focus": [
                {"focus": focus, "count": count}
                for focus, count in focus_counter.most_common(5)
            ],
        },
    )


def _add_claim_items(items: list[dict[str, Any]], claim_portfolio: dict[str, Any] | None) -> None:
    if not claim_portfolio:
        return
    status = str(claim_portfolio.get("portfolio_status") or "")
    if status == "has_agency_candidate":
        _append_item(
            items,
            priority="P2",
            source="claim_readiness_portfolio",
            area="external_review",
            action="Prepare independent external review for the best agency-candidate experiment.",
            reason="At least one experiment reached agency-candidate claim readiness.",
            evidence={
                "best_experiment_id": claim_portfolio.get("best_experiment_id"),
                "best_status": claim_portfolio.get("best_status"),
            },
        )
        return
    for blocker in (claim_portfolio.get("common_blockers") or [])[:5]:
        _append_item(
            items,
            priority="P1",
            source="claim_readiness_portfolio",
            area="claim_blocker",
            action=f"Repair claim-readiness blocker: {blocker.get('check')}.",
            reason=str(blocker.get("blocker_reason") or "Claim readiness is not strong enough."),
            evidence=blocker,
        )


def _add_research_items(items: list[dict[str, Any]], research_evidence_audit: dict[str, Any] | None) -> None:
    if not research_evidence_audit:
        return
    status = str(research_evidence_audit.get("status") or "")
    if status in {"prediction_feature_ready", ""}:
        return
    severity = "P0" if status == "blocked_for_quant_ingestion" else "P1"
    _append_item(
        items,
        priority=severity,
        source="research_evidence_audit",
        area="search_evidence_quality",
        action="Repair research evidence before allowing it to influence quant features.",
        reason=f"Research evidence audit status is {status}.",
        evidence={
            "status": status,
            "failed_checks": [
                row
                for row in research_evidence_audit.get("checks", []) or []
                if not row.get("passed")
            ][:5],
            "next_required_evidence": research_evidence_audit.get("next_required_evidence", [])[:5],
        },
    )


def _has_delivery_portfolio_work(improvement_audit: dict[str, Any] | None) -> bool:
    if not improvement_audit:
        return False
    delivery_areas = {
        "delivery_portfolio",
        "delivery_portfolio_gate",
        "delivery_portfolio_client_delivery",
    }
    findings = list(improvement_audit.get("prioritized_actions") or [])
    findings.extend(improvement_audit.get("findings") or [])
    for finding in findings:
        if str(finding.get("area") or "") in delivery_areas:
            return True
    return False


def _commands(
    *,
    improvement_audit: dict[str, Any] | None,
    source_paths: Mapping[str, str] | None,
    coverage_repair_plan: dict[str, Any] | None,
    replay_queue_summary: dict[str, Any] | None,
) -> list[str]:
    paths = dict(source_paths or {})
    commands: list[str] = []
    if coverage_repair_plan and int(coverage_repair_plan.get("repair_spec_count", 0) or 0) > 0:
        repair_path = paths.get("coverage_repair_plan") or "logs/benchmark_coverage_repair_plan.json"
        commands.append(
            "python scripts/generate_frozen_plans_2025.py "
            "--output logs/frozen_plans_2025_repaired.jsonl "
            "--num-cases 40 "
            f"--coverage-repair-plan {repair_path}"
        )
    if replay_queue_summary and int(replay_queue_summary.get("queue_count", 0) or 0) > 0:
        queue_path = paths.get("replay_queue_jsonl") or "logs/failure_replay_queue.jsonl"
        commands.append(
            "python scripts/run_experiment_suite.py "
            "--output-dir logs/experiments/replay_next "
            "--actual-outcomes data/actual_2025.csv "
            f"--plans-jsonl {queue_path} "
            "--run-ablation"
        )
    if _has_delivery_portfolio_work(improvement_audit):
        bundle_glob = paths.get("delivery_bundle_glob") or "logs/delivery_*/delivery_bundle.json"
        commands.append(
            "python scripts/gaokao_agent.py "
            "delivery-portfolio-audit "
            f'--bundle-glob "{bundle_glob}" '
            "--output logs/delivery_portfolio_audit.json "
            "--report-md logs/delivery_portfolio_audit.md"
        )
    if not commands:
        commands.append(
            "python scripts/run_experiment_suite.py "
            "--output-dir logs/experiments/next "
            "--actual-outcomes data/actual_2025.csv "
            "--plans-jsonl logs/frozen_plans_2025.jsonl "
            "--run-ablation"
        )
    return commands


def _status(items: list[dict[str, Any]]) -> str:
    if any(item.get("priority") == "P0" for item in items):
        return "repair_p0_before_next_claim"
    if any(item.get("priority") == "P1" for item in items):
        return "run_targeted_iteration"
    if items:
        return "run_validation_iteration"
    return "continue_benchmark_collection"


def build_next_iteration_plan(
    *,
    improvement_audit: dict[str, Any] | None = None,
    coverage_repair_plan: dict[str, Any] | None = None,
    replay_queue_summary: dict[str, Any] | None = None,
    claim_readiness_portfolio: dict[str, Any] | None = None,
    research_evidence_audit: dict[str, Any] | None = None,
    source_paths: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build a unified plan for the next experiment cycle."""
    items: list[dict[str, Any]] = []
    _add_improvement_items(items, improvement_audit)
    _add_coverage_items(items, coverage_repair_plan)
    _add_replay_items(items, replay_queue_summary)
    _add_claim_items(items, claim_readiness_portfolio)
    _add_research_items(items, research_evidence_audit)
    items = _sort_items(items)
    priority_counts = Counter(str(item.get("priority") or "P2") for item in items)
    return {
        "protocol_version": PROTOCOL_VERSION,
        "status": _status(items),
        "work_item_count": len(items),
        "priority_counts": {priority: priority_counts.get(priority, 0) for priority in ("P0", "P1", "P2", "P3")},
        "work_items": items,
        "next_run_commands": _commands(
            improvement_audit=improvement_audit,
            source_paths=source_paths,
            coverage_repair_plan=coverage_repair_plan,
            replay_queue_summary=replay_queue_summary,
        ),
        "evidence_summary": {
            "improvement_status": (improvement_audit or {}).get("status"),
            "coverage_repair_spec_count": (coverage_repair_plan or {}).get("repair_spec_count", 0),
            "replay_queue_count": (replay_queue_summary or {}).get("queue_count", 0),
            "claim_portfolio_status": (claim_readiness_portfolio or {}).get("portfolio_status"),
            "research_evidence_status": (research_evidence_audit or {}).get("status"),
        },
        "notes": [
            "Treat P0 items as blockers before public quality claims.",
            "Run replay and coverage-repair loops before celebrating aggregate metric gains.",
        ],
    }


def build_markdown_next_iteration_plan(result: dict[str, Any]) -> str:
    """Render the next-iteration plan as Markdown."""
    lines = [
        "# Next Iteration Plan",
        "",
        f"Status: `{result.get('status', 'unknown')}`",
        f"Work items: {result.get('work_item_count', 0)}",
        "",
        "## Priority Summary",
        "",
        "| Priority | Count |",
        "| --- | ---: |",
    ]
    for priority, count in (result.get("priority_counts") or {}).items():
        lines.append(f"| `{priority}` | {count} |")

    lines.extend([
        "",
        "## Work Items",
        "",
        "| Priority | Source | Area | Action | Reason |",
        "| --- | --- | --- | --- | --- |",
    ])
    for item in result.get("work_items") or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item.get('priority', '')}`",
                    f"`{item.get('source', '')}`",
                    f"`{item.get('area', '')}`",
                    str(item.get("action", "")).replace("|", "/"),
                    str(item.get("reason", "")).replace("|", "/"),
                ]
            )
            + " |"
        )
    if not result.get("work_items"):
        lines.append("| `P3` | `none` | `benchmark_collection` | Continue collecting frozen labels. | No blockers found. |")

    lines.extend(["", "## Next Run Commands", ""])
    for index, command in enumerate(result.get("next_run_commands") or [], 1):
        lines.append(f"{index}. `{command}`")
    lines.extend(["", "## Notes", ""])
    for note in result.get("notes") or []:
        lines.append(f"- {note}")
    return "\n".join(lines)

"""Claim-readiness gate for QuantLab experiments.

This audit translates experiment metrics into allowed and forbidden public
claims. It keeps the project honest: a strong leaderboard row is not the same
as proof that GaokaoAgent can make agency-grade claims.
"""

from __future__ import annotations

from typing import Any


PROTOCOL_VERSION = "gaokao-claim-readiness-v1"
TARGETS = {
    "case_count": 20,
    "success_rate": 0.95,
    "sliding_rate": 0.03,
    "blacklist_hit_rate": 0.01,
    "tail_assignment_rate": 0.12,
    "preferred_major_hit_rate": 0.55,
    "failure_case_rate": 0.10,
    "brier_score": 0.18,
    "coverage_score": 0.90,
}


def _nested(payload: dict[str, Any], *path: str) -> Any:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _float(payload: dict[str, Any], *path: str, default: float = 0.0) -> float:
    value = _nested(payload, *path)
    try:
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def _add_check(
    checks: list[dict[str, Any]],
    *,
    name: str,
    passed: bool,
    severity: str,
    evidence: Any,
    target: str,
    blocker_reason: str,
) -> None:
    checks.append(
        {
            "name": name,
            "passed": passed,
            "severity": "" if passed else severity,
            "evidence": evidence,
            "target": target,
            "blocker_reason": "" if passed else blocker_reason,
        }
    )


def _claim_status(checks: list[dict[str, Any]]) -> str:
    if any(not row["passed"] and row["severity"] == "P0" for row in checks):
        return "blocked_for_agency_grade_claims"
    if any(not row["passed"] and row["severity"] == "P1" for row in checks):
        return "research_benchmark_only"
    if any(not row["passed"] for row in checks):
        return "limited_benchmark_claim"
    return "agency_candidate_claim"


def build_claim_readiness(manifest: dict[str, Any]) -> dict[str, Any]:
    """Audit which claims one QuantLab manifest can support."""
    digest = manifest.get("metric_digest") or {}
    gate = manifest.get("promotion_gate") or {}
    checks: list[dict[str, Any]] = []

    case_count = _float(digest, "backtest", "case_count")
    _add_check(
        checks,
        name="minimum_backtest_cases",
        passed=case_count >= TARGETS["case_count"],
        severity="P0",
        evidence=case_count,
        target=f">= {TARGETS['case_count']} frozen cases",
        blocker_reason="Backtest sample is too small for agency-grade claims.",
    )
    coverage_status = _nested(digest, "benchmark_coverage", "status")
    coverage_score = _float(digest, "benchmark_coverage", "coverage_score")
    _add_check(
        checks,
        name="benchmark_coverage",
        passed=coverage_status == "ready" and coverage_score >= TARGETS["coverage_score"],
        severity="P0" if coverage_status == "insufficient" else "P1",
        evidence={"status": coverage_status, "coverage_score": coverage_score},
        target=f"coverage ready and score >= {TARGETS['coverage_score']:.0%}",
        blocker_reason="Frozen cases do not yet cover enough critical user slices.",
    )
    for metric, target, severity, reason in [
        ("success_rate", TARGETS["success_rate"], "P0", "Success rate is below agency-grade target."),
        ("preferred_major_hit_rate", TARGETS["preferred_major_hit_rate"], "P1", "Preferred-major hit is not strong enough."),
    ]:
        value = _float(digest, "backtest", metric)
        _add_check(
            checks,
            name=metric,
            passed=value >= target,
            severity=severity,
            evidence=value,
            target=f">= {target:.0%}",
            blocker_reason=reason,
        )
    for metric, target, severity, reason in [
        ("sliding_rate", TARGETS["sliding_rate"], "P0", "Sliding risk is too high for broad claims."),
        ("blacklist_hit_rate", TARGETS["blacklist_hit_rate"], "P0", "Blacklist-hit risk violates hard constraints."),
        ("tail_assignment_rate", TARGETS["tail_assignment_rate"], "P1", "Tail-assignment risk remains too high."),
    ]:
        value = _float(digest, "backtest", metric)
        _add_check(
            checks,
            name=metric,
            passed=value <= target,
            severity=severity,
            evidence=value,
            target=f"<= {target:.0%}",
            blocker_reason=reason,
        )
    failure_rate = _float(digest, "failure_mining", "failure_case_rate")
    _add_check(
        checks,
        name="failure_case_rate",
        passed=failure_rate <= TARGETS["failure_case_rate"],
        severity="P1",
        evidence=failure_rate,
        target=f"<= {TARGETS['failure_case_rate']:.0%}",
        blocker_reason="Too many cases still require failure replay before external claims.",
    )
    brier = _float(digest, "calibration", "brier_score")
    _add_check(
        checks,
        name="calibration_brier_score",
        passed=brier <= TARGETS["brier_score"],
        severity="P1",
        evidence=brier,
        target=f"<= {TARGETS['brier_score']:.0%}",
        blocker_reason="Probability calibration is not yet reliable enough for strong claims.",
    )
    blocker_count = _float(digest, "improvement_audit", "blocker_count")
    _add_check(
        checks,
        name="improvement_p0_blockers",
        passed=blocker_count == 0,
        severity="P0",
        evidence=blocker_count,
        target="0 P0 blockers",
        blocker_reason="Self-improvement audit still has P0 blockers.",
    )
    slice_guardrails_status = _nested(gate, "slice_guardrails", "status")
    if slice_guardrails_status in {"blocked", "not_evaluable"}:
        severity = "P0" if slice_guardrails_status == "blocked" else "P1"
        passed = False
    else:
        severity = ""
        passed = True
    _add_check(
        checks,
        name="critical_slice_guardrails",
        passed=passed,
        severity=severity or "P1",
        evidence=slice_guardrails_status,
        target="slice guardrails pass",
        blocker_reason="Critical user-slice guardrails are blocked or not evaluable.",
    )

    status = _claim_status(checks)
    return {
        "protocol_version": PROTOCOL_VERSION,
        "experiment_id": manifest.get("experiment_id"),
        "status": status,
        "mission": manifest.get("mission"),
        "checks": checks,
        "allowed_claims": _allowed_claims(status),
        "forbidden_claims": _forbidden_claims(status),
        "next_required_evidence": [
            row["blocker_reason"]
            for row in checks
            if not row["passed"]
        ][:8],
    }


def _allowed_claims(status: str) -> list[str]:
    if status == "agency_candidate_claim":
        return [
            "This experiment is a candidate for agency-grade quality review.",
            "Metrics passed coverage, backtest, calibration, failure replay, and critical-slice gates.",
        ]
    if status == "limited_benchmark_claim":
        return [
            "This experiment has limited benchmark evidence, but remaining issues must be disclosed.",
        ]
    if status == "research_benchmark_only":
        return [
            "This run is useful internal benchmark evidence.",
            "The system is still a research prototype and needs targeted iteration before strong public claims.",
        ]
    return [
        "This run is diagnostic only.",
        "Use it to guide repair, replay, calibration, and slice-guardrail work.",
    ]


def _forbidden_claims(status: str) -> list[str]:
    common = [
        "Do not claim guaranteed admission outcomes.",
        "Do not claim superiority over paid agencies without independent held-out validation.",
    ]
    if status != "agency_candidate_claim":
        common.extend(
            [
                "Do not claim the project already matches top agencies or top livestream counselors.",
                "Do not market aggregate success rate without explaining coverage, failure replay, and calibration gaps.",
            ]
        )
    return common


def build_markdown_claim_readiness(result: dict[str, Any]) -> str:
    """Build a Markdown report for claim readiness."""
    lines = [
        "# Claim Readiness Audit",
        "",
        f"Experiment: `{result.get('experiment_id', '')}`",
        f"Status: `{result.get('status', 'unknown')}`",
        "",
        "## Checks",
        "",
        "| Check | Pass | Evidence | Target | Blocker |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in result.get("checks", []) or []:
        lines.append(
            f"| `{row.get('name', '')}` | {'yes' if row.get('passed') else 'no'} | "
            f"`{row.get('evidence')}` | {row.get('target', '')} | {row.get('blocker_reason', '')} |"
        )
    lines.extend(["", "## Allowed Claims", ""])
    for item in result.get("allowed_claims") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden Claims", ""])
    for item in result.get("forbidden_claims") or []:
        lines.append(f"- {item}")
    return "\n".join(lines)

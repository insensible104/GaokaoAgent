"""Self-improvement audit for GaokaoAgent experiment outputs.

The audit turns backtest, calibration, and ablation metrics into prioritized
engineering work. It is a guardrail against optimizing anecdotes instead of the
mission: broadly accessible, agency-grade volunteer-planning quality.
"""

from __future__ import annotations

from typing import Any, Sequence


TARGETS = {
    "success_rate": 0.95,
    "sliding_rate": 0.03,
    "preferred_major_hit_rate": 0.55,
    "blacklist_hit_rate": 0.01,
    "tail_assignment_rate": 0.12,
    "wasted_score_rate": 0.20,
    "absolute_calibration_error": 0.10,
    "brier_score": 0.18,
    "bucket_abs_calibration_error": 0.15,
}

RISK_BAND_ORDER = [
    "far_rush",
    "boundary_rush",
    "thin_target",
    "solid_target",
    "safe_anchor",
]


def _float(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _severity(metric: str, value: float, target: float, *, higher_is_better: bool) -> str:
    if higher_is_better:
        gap = target - value
        if gap <= 0:
            return ""
        if metric == "success_rate" and gap >= 0.10:
            return "P0"
        if gap >= 0.15:
            return "P1"
        if gap >= 0.07:
            return "P2"
        return "P3"

    gap = value - target
    if gap <= 0:
        return ""
    if metric in {"sliding_rate", "blacklist_hit_rate"} and gap >= 0.05:
        return "P0"
    if gap >= 0.15:
        return "P1"
    if gap >= 0.07:
        return "P2"
    return "P3"


def _finding(
    *,
    severity: str,
    area: str,
    finding: str,
    target: str,
    recommendation: str,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "area": area,
        "finding": finding,
        "target": target,
        "recommendation": recommendation,
        "evidence": evidence or {},
    }


def _audit_backtest(summary: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    checks = [
        (
            "success_rate",
            True,
            "录取成功率低于平权化交付目标",
            "优先补强保底锚点、前序遮蔽和低分段安全垫策略。",
        ),
        (
            "sliding_rate",
            False,
            "滑档率高于可接受边界",
            "收紧 safe_anchor 门槛，增加保底覆盖率和低置信候选惩罚。",
        ),
        (
            "preferred_major_hit_rate",
            True,
            "目标专业命中率不足",
            "提高前置专业适配权重，并单独优化 front-major hit 而非只优化投档。",
        ),
        (
            "blacklist_hit_rate",
            False,
            "黑名单专业命中风险过高",
            "把黑名单从惩罚项升级为硬约束或强制家长确认项。",
        ),
        (
            "tail_assignment_rate",
            False,
            "尾部专业风险过高",
            "加强专业组混搭识别，降低高尾部风险行在关键前缀中的排序。",
        ),
        (
            "wasted_score_rate",
            False,
            "浪费分风险偏高",
            "优化 safe_first 与 prefix optimizer 的平衡，避免高概率低效用行过早遮蔽。",
        ),
    ]
    for metric, higher_is_better, finding, recommendation in checks:
        value = _float(summary, metric)
        target = TARGETS[metric]
        severity = _severity(metric, value, target, higher_is_better=higher_is_better)
        if not severity:
            continue
        direction = ">=" if higher_is_better else "<="
        findings.append(
            _finding(
                severity=severity,
                area="backtest",
                finding=finding,
                target=f"{metric} {direction} {target:.2%}",
                recommendation=recommendation,
                evidence={"metric": metric, "value": round(value, 6), "target": target},
            )
        )
    return findings


def _audit_calibration(calibration: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    overall = calibration.get("overall", {}) or {}
    for metric, recommendation in [
        (
            "absolute_calibration_error",
            "对 admission_prob 做后验校准，优先修正系统性高估/低估。",
        ),
        (
            "brier_score",
            "重新评估概率模型的波动宽度、样本惩罚和数据置信权重。",
        ),
    ]:
        value = _float(overall, metric)
        target = TARGETS[metric]
        severity = _severity(metric, value, target, higher_is_better=False)
        if severity:
            findings.append(
                _finding(
                    severity=severity,
                    area="calibration",
                    finding=f"{metric} 超出概率校准目标",
                    target=f"{metric} <= {target:.2%}",
                    recommendation=recommendation,
                    evidence={"metric": metric, "value": round(value, 6), "target": target},
                )
            )

    for row in calibration.get("by_probability_bucket", []) or []:
        err = _float(row, "absolute_calibration_error")
        count = int(row.get("choice_count", 0) or 0)
        if count < 3 or err <= TARGETS["bucket_abs_calibration_error"]:
            continue
        findings.append(
            _finding(
                severity="P2" if err < 0.25 else "P1",
                area="calibration",
                finding=f"概率桶 {row.get('bucket')} 校准误差过大",
                target=f"bucket abs error <= {TARGETS['bucket_abs_calibration_error']:.0%}",
                recommendation="按概率桶学习后验映射，避免把未校准概率直接写入交付报告。",
                evidence={
                    "bucket": row.get("bucket"),
                    "choice_count": count,
                    "expected_admit_rate": row.get("expected_admit_rate"),
                    "observed_admit_rate": row.get("observed_admit_rate"),
                    "absolute_calibration_error": err,
                },
            )
        )

    band_rows = {
        str(row.get("bucket")): row
        for row in calibration.get("by_risk_band", []) or []
    }
    previous_rate = None
    previous_band = None
    for band in RISK_BAND_ORDER:
        row = band_rows.get(band)
        if not row:
            continue
        rate = _float(row, "observed_admit_rate")
        if previous_rate is not None and rate + 1e-9 < previous_rate:
            findings.append(
                _finding(
                    severity="P1",
                    area="risk_band",
                    finding=f"风险档不单调：{band} 真实命中率低于 {previous_band}",
                    target="risk bands should be monotonic by observed admit rate",
                    recommendation="重新调 risk_band 阈值或 uncertainty_width，先保证风险档顺序可信。",
                    evidence={
                        "previous_band": previous_band,
                        "previous_observed": previous_rate,
                        "current_band": band,
                        "current_observed": rate,
                    },
                )
            )
        previous_rate = rate
        previous_band = band
    return findings


def _audit_ablation(ablation: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    deltas = ablation.get("deltas_vs_full", {}) or {}
    for variant, delta in deltas.items():
        success_delta = _float(delta, "success_rate")
        preferred_delta = _float(delta, "preferred_major_hit_rate")
        tail_delta = _float(delta, "tail_assignment_rate")
        blacklist_delta = _float(delta, "blacklist_hit_rate")
        if success_delta > 0.02 and tail_delta <= 0.02 and blacklist_delta <= 0.01:
            findings.append(
                _finding(
                    severity="P2",
                    area="ablation",
                    finding=f"Baseline `{variant}` 在成功率上打赢 full system",
                    target="full system should dominate simple baselines",
                    recommendation=f"吸收 `{variant}` 的排序逻辑，或解释 full system 为什么保留当前权衡。",
                    evidence={
                        "variant": variant,
                        "success_delta": success_delta,
                        "tail_delta": tail_delta,
                        "blacklist_delta": blacklist_delta,
                    },
                )
            )
        if preferred_delta > 0.04 and tail_delta <= 0.03:
            findings.append(
                _finding(
                    severity="P2",
                    area="ablation",
                    finding=f"Baseline `{variant}` 的目标专业命中优于 full system",
                    target="full system should win preferred-major utility",
                    recommendation=f"复盘 `{variant}` 的专业优先逻辑，纳入 prefix 或 tradeoff 权重搜索。",
                    evidence={
                        "variant": variant,
                        "preferred_major_hit_delta": preferred_delta,
                        "tail_delta": tail_delta,
                    },
                )
            )
    return findings


def _sort_findings(findings: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return sorted(findings, key=lambda item: (order.get(item["severity"], 9), item["area"], item["finding"]))


def _overall_status(findings: Sequence[dict[str, Any]]) -> str:
    if any(item["severity"] == "P0" for item in findings):
        return "blocked_for_agency_grade_claims"
    if any(item["severity"] == "P1" for item in findings):
        return "needs_model_iteration"
    if any(item["severity"] == "P2" for item in findings):
        return "needs_targeted_iteration"
    return "on_track"


def build_improvement_audit(
    *,
    backtest_summary: dict[str, Any] | None = None,
    calibration_summary: dict[str, Any] | None = None,
    ablation_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return prioritized self-improvement findings from experiment summaries."""
    findings: list[dict[str, Any]] = []
    if backtest_summary:
        findings.extend(_audit_backtest(backtest_summary))
    if calibration_summary:
        findings.extend(_audit_calibration(calibration_summary))
    if ablation_summary:
        findings.extend(_audit_ablation(ablation_summary))
    findings = _sort_findings(findings)
    return {
        "mission": "高考志愿平权化：以可负担、可解释、可回测的系统能力逼近头部填报机构和主播。",
        "status": _overall_status(findings),
        "target_scorecard": TARGETS,
        "finding_count": len(findings),
        "severity_counts": {
            severity: sum(1 for item in findings if item["severity"] == severity)
            for severity in ("P0", "P1", "P2", "P3")
        },
        "findings": findings,
        "next_actions": [
            item["recommendation"]
            for item in findings[:5]
        ],
    }


def build_markdown_improvement_audit(result: dict[str, Any]) -> str:
    """Build a Markdown report for the self-improvement audit."""
    lines = [
        "# GaokaoAgent Self-Improvement Audit",
        "",
        f"Mission: {result.get('mission', '')}",
        f"Status: `{result.get('status', 'unknown')}`",
        f"Findings: {result.get('finding_count', 0)}",
        "",
        "## Severity Summary",
        "",
        "| Severity | Count |",
        "| --- | ---: |",
    ]
    for severity, count in (result.get("severity_counts", {}) or {}).items():
        lines.append(f"| `{severity}` | {count} |")

    lines.extend(
        [
            "",
            "## Findings",
            "",
            "| Severity | Area | Finding | Target | Recommendation |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in result.get("findings", []) or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item.get('severity', '')}`",
                    str(item.get("area", "")),
                    str(item.get("finding", "")).replace("|", "/"),
                    str(item.get("target", "")).replace("|", "/"),
                    str(item.get("recommendation", "")).replace("|", "/"),
                ]
            )
            + " |"
        )
    if not result.get("findings"):
        lines.append("| `OK` | all | No blocking findings | Maintain current gates | Continue frozen-plan collection |")

    lines.extend(["", "## Next Actions", ""])
    for idx, action in enumerate(result.get("next_actions", []) or [], 1):
        lines.append(f"{idx}. {action}")
    if not result.get("next_actions"):
        lines.append("1. Continue collecting frozen plans and actual-outcome labels.")
    return "\n".join(lines) + "\n"

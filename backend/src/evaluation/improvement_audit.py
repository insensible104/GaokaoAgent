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
    "intake_readiness_score": 0.72,
    "plan_quality_score": 0.78,
    "report_quality_score": 0.78,
    "portfolio_ready_to_deliver_rate": 0.80,
    "portfolio_blocked_rate": 0.05,
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


def _audit_tuning(tuning: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    best = tuning.get("best") or {}
    baseline = tuning.get("baseline") or {}
    if not best or not baseline:
        return findings

    best_eval = best.get("holdout") or best
    baseline_eval = baseline.get("holdout") or tuning.get("holdout_baseline") or baseline
    split = "holdout" if best.get("holdout") and baseline_eval else "train"
    brier_delta = _float(best_eval, "brier_score") - _float(baseline_eval, "brier_score")
    objective_delta = _float(best_eval, "objective") - _float(baseline_eval, "objective")
    if brier_delta <= -0.015 or objective_delta <= -0.020:
        findings.append(
            _finding(
                severity="P2",
                area="quant_tuning",
                finding=f"离线权重搜索在 {split} 上找到优于当前概率口径的候选配置",
                target="candidate must improve on held-out frozen-plan split before runtime adoption",
                recommendation="把 best 权重加入下一轮独立 frozen-plan 回测/校准，不要直接线上替换。",
                evidence={
                    "best_name": best.get("name"),
                    "best_weights": best.get("weights"),
                    "split": split,
                    "brier_delta": round(brier_delta, 6),
                    "objective_delta": round(objective_delta, 6),
                },
            )
        )
    return findings


def _delivery_severity(status: str, score: float, target: float) -> str:
    if status in {"blocked", "blocked_missing_core"}:
        return "P0"
    if status in {"not_provided", "needs_revision"}:
        return "P1"
    if status in {"needs_clarification", "pending_signoff", "needs_confirmation"}:
        return "P2"
    if score and score < target:
        return "P2"
    return ""


def _audit_intake_readiness(intake: dict[str, Any]) -> list[dict[str, Any]]:
    status = str(intake.get("status") or "unknown")
    score = _float(intake, "readiness_score")
    severity = _delivery_severity(status, score, TARGETS["intake_readiness_score"])
    if not severity:
        return []
    blockers = intake.get("core_blockers") or intake.get("missing_items") or []
    return [
        _finding(
            severity=severity,
            area="intake_readiness",
            finding=f"问诊完备度未达到推荐前门槛：{status}",
            target=f"status ready_for_recommendation and readiness_score >= {TARGETS['intake_readiness_score']:.0%}",
            recommendation="把缺失项转成强制问诊字段；缺分数、位次、选科时禁止生成推荐。",
            evidence={
                "status": status,
                "readiness_score": round(score, 6),
                "blockers": blockers[:3] if isinstance(blockers, list) else blockers,
            },
        )
    ]


def _audit_plan_quality(plan_quality: dict[str, Any]) -> list[dict[str, Any]]:
    status = str(plan_quality.get("status") or "unknown")
    score = _float(plan_quality, "total_score")
    severity = _delivery_severity(status, score, TARGETS["plan_quality_score"])
    if not severity:
        return []
    findings = plan_quality.get("findings") or []
    return [
        _finding(
            severity=severity,
            area="plan_quality",
            finding=f"志愿表结构质量未达到交付门槛：{status}",
            target=f"status pass and total_score >= {TARGETS['plan_quality_score']:.0%}",
            recommendation="优先修复保底安全垫、冲稳保比例、尾部/调剂风险、黑名单硬边界和关键志愿依据。",
            evidence={
                "status": status,
                "total_score": round(score, 6),
                "top_findings": findings[:3] if isinstance(findings, list) else findings,
            },
        )
    ]


def _audit_report_quality(report_quality: dict[str, Any]) -> list[dict[str, Any]]:
    status = str(report_quality.get("status") or "unknown")
    score = _float(report_quality, "total_score")
    severity = _delivery_severity(status, score, TARGETS["report_quality_score"])
    if not severity:
        return []
    findings = report_quality.get("findings") or []
    return [
        _finding(
            severity=severity,
            area="report_quality",
            finding=f"报告交付质量未达到专业交付门槛：{status}",
            target=f"status pass and total_score >= {TARGETS['report_quality_score']:.0%}",
            recommendation="补齐学生画像、限制条件、风险解释、推荐依据、执行动作、预期管理和官方复核边界。",
            evidence={
                "status": status,
                "total_score": round(score, 6),
                "top_findings": findings[:3] if isinstance(findings, list) else findings,
            },
        )
    ]


def _audit_delivery_bundle(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    status = str(bundle.get("status") or "unknown")
    if status == "ready_to_deliver":
        return []
    severity = "P0" if status == "blocked" else "P1" if status == "needs_revision" else "P2"
    gates = bundle.get("delivery_gates") or []
    failed_gates = [
        gate
        for gate in gates
        if str(gate.get("status") or "") not in {"pass", "ready", "ready_for_recommendation"}
    ]
    return [
        _finding(
            severity=severity,
            area="delivery_bundle",
            finding=f"客户交付包未达到最终交付状态：{status}",
            target="delivery bundle status ready_to_deliver",
            recommendation="按交付包 gate 顺序修复 intake、plan quality、expectation signoff 和 report quality。",
            evidence={
                "status": status,
                "failed_gates": failed_gates[:5],
                "next_actions": bundle.get("next_actions", [])[:5] if isinstance(bundle.get("next_actions"), list) else [],
            },
        )
    ]


def _audit_delivery_portfolio(portfolio: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    case_count = int(portfolio.get("case_count", 0) or 0)
    if case_count <= 0:
        findings.append(
            _finding(
                severity="P2",
                area="delivery_portfolio",
                finding="批量交付审计没有覆盖任何案例",
                target="delivery portfolio should include at least one delivery bundle",
                recommendation="收集一批 delivery_bundle.json 后再运行组合审计，避免用单案感受判断服务质量。",
                evidence={"case_count": case_count, "status": portfolio.get("status")},
            )
        )
        return findings

    ready_rate = _float(portfolio, "ready_to_deliver_rate")
    blocked_rate = _float(portfolio, "blocked_rate")
    ready_severity = _severity(
        "portfolio_ready_to_deliver_rate",
        ready_rate,
        TARGETS["portfolio_ready_to_deliver_rate"],
        higher_is_better=True,
    )
    blocked_severity = _severity(
        "portfolio_blocked_rate",
        blocked_rate,
        TARGETS["portfolio_blocked_rate"],
        higher_is_better=False,
    )
    if ready_severity:
        findings.append(
            _finding(
                severity=ready_severity,
                area="delivery_portfolio",
                finding="批量交付 ready_to_deliver 比例低于规模化服务目标",
                target=f"ready_to_deliver_rate >= {TARGETS['portfolio_ready_to_deliver_rate']:.0%}",
                recommendation="按 top_failed_gates 排序修复高频交付阻断项，并把重复 next actions 转成产品化流程。",
                evidence={
                    "case_count": case_count,
                    "ready_to_deliver_rate": round(ready_rate, 6),
                    "top_failed_gates": portfolio.get("top_failed_gates", [])[:5],
                    "top_next_actions": portfolio.get("top_next_actions", [])[:5],
                },
            )
        )
    if blocked_severity:
        findings.append(
            _finding(
                severity="P0" if blocked_rate >= 0.10 else blocked_severity,
                area="delivery_portfolio",
                finding="批量交付 blocked 比例高于规模化服务边界",
                target=f"blocked_rate <= {TARGETS['portfolio_blocked_rate']:.0%}",
                recommendation="优先处理核心问诊缺失、志愿表硬边界和严重报告质量问题，避免低质量案例进入客户交付。",
                evidence={
                    "case_count": case_count,
                    "blocked_rate": round(blocked_rate, 6),
                    "worst_cases": portfolio.get("worst_cases", [])[:5],
                },
            )
        )
    for gate in portfolio.get("top_failed_gates", [])[:3]:
        failed_rate = _float(gate, "failed_rate")
        if failed_rate < 0.20:
            continue
        findings.append(
            _finding(
                severity="P1" if failed_rate >= 0.40 else "P2",
                area="delivery_portfolio_gate",
                finding=f"交付 gate `{gate.get('gate')}` 在批量案例中高频失败",
                target="single delivery gate failed_rate < 20%",
                recommendation=f"把 `{gate.get('gate')}` 的失败原因拆成强制输入、自动审计或推荐器约束，降低人工补救成本。",
                evidence=gate,
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
    tuning_summary: dict[str, Any] | None = None,
    intake_audit: dict[str, Any] | None = None,
    plan_quality_audit: dict[str, Any] | None = None,
    report_quality_audit: dict[str, Any] | None = None,
    delivery_bundle: dict[str, Any] | None = None,
    delivery_portfolio: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return prioritized self-improvement findings from experiment summaries."""
    findings: list[dict[str, Any]] = []
    if backtest_summary:
        findings.extend(_audit_backtest(backtest_summary))
    if calibration_summary:
        findings.extend(_audit_calibration(calibration_summary))
    if ablation_summary:
        findings.extend(_audit_ablation(ablation_summary))
    if tuning_summary:
        findings.extend(_audit_tuning(tuning_summary))
    if intake_audit:
        findings.extend(_audit_intake_readiness(intake_audit))
    if plan_quality_audit:
        findings.extend(_audit_plan_quality(plan_quality_audit))
    if report_quality_audit:
        findings.extend(_audit_report_quality(report_quality_audit))
    if delivery_bundle:
        findings.extend(_audit_delivery_bundle(delivery_bundle))
    if delivery_portfolio:
        findings.extend(_audit_delivery_portfolio(delivery_portfolio))
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

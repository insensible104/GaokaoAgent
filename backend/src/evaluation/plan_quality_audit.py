"""Deterministic quality audit for a generated volunteer plan.

Top counselors do not only explain recommendations well; they also inspect
whether the ordered plan itself has enough safety anchors, useful active rows,
acceptable tail risk, and documented evidence. This module makes that review
repeatable before a plan is delivered or backtested.
"""

from __future__ import annotations

from typing import Any

from models.game_matrix import AdjustmentAdvice, StrategyTag, VolunteerChoice, VolunteerPlan
from models.user_profile import RiskTolerance, UserProfile


CHECK_WEIGHTS = {
    "admission_security": 0.22,
    "safe_anchor": 0.16,
    "rush_target_safe_balance": 0.14,
    "key_prefix_efficiency": 0.14,
    "tail_and_adjustment_risk": 0.16,
    "hard_boundary_compliance": 0.10,
    "decision_evidence": 0.08,
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _risk_policy(profile: UserProfile | None) -> RiskTolerance:
    return profile.risk_tolerance if profile else RiskTolerance.BALANCED


def _ensure_statistics(plan: VolunteerPlan) -> VolunteerPlan:
    working = plan.model_copy(deep=True)
    working.calculate_statistics()
    return working


def _severity(score: float, weight: float) -> str:
    if score <= 0.20 and weight >= 0.14:
        return "P0"
    if score <= 0.45:
        return "P1"
    if score <= 0.70:
        return "P2"
    return "P3"


def _check(
    *,
    check: str,
    label: str,
    score: float,
    evidence: list[str],
    missing: list[str],
    recommendation: str,
) -> dict[str, Any]:
    bounded_score = _clamp(score)
    return {
        "check": check,
        "label": label,
        "score": round(bounded_score, 6),
        "weight": CHECK_WEIGHTS[check],
        "passed": bounded_score >= 0.72,
        "severity": _severity(bounded_score, CHECK_WEIGHTS[check]),
        "evidence": evidence,
        "missing": missing,
        "recommendation": recommendation,
    }


def _admission_security(plan: VolunteerPlan, profile: UserProfile | None) -> dict[str, Any]:
    risk_policy = _risk_policy(profile)
    threshold = 0.985 if risk_policy == RiskTolerance.CONSERVATIVE else 0.960
    if risk_policy == RiskTolerance.AGGRESSIVE:
        threshold = 0.920
    expected = float(plan.expected_admission_prob or 0.0)
    score = expected / threshold if threshold else expected
    missing = [] if expected >= threshold else [f"整体录取概率低于 {threshold:.1%}"]
    return _check(
        check="admission_security",
        label="整体录取安全性",
        score=score,
        evidence=[
            f"expected_admission_prob={expected:.3f}",
            f"risk_policy={risk_policy.value}",
            f"threshold={threshold:.3f}",
        ],
        missing=missing,
        recommendation="提高保底专业组质量或降低前序过度冲刺比例，直到整体录取安全性符合风险偏好。",
    )


def _safe_anchor(plan: VolunteerPlan, profile: UserProfile | None) -> dict[str, Any]:
    risk_policy = _risk_policy(profile)
    min_safe_count = 2 if risk_policy == RiskTolerance.CONSERVATIVE else 1
    if risk_policy == RiskTolerance.AGGRESSIVE:
        min_safe_count = 1
    safe_count = sum(1 for choice in plan.choices if choice.strategy_tag == StrategyTag.SAFE)
    high_prob_anchor_count = sum(1 for choice in plan.choices if choice.group_admission_prob >= 0.90)
    anchor_count = max(safe_count, high_prob_anchor_count)
    score = min(1.0, anchor_count / max(min_safe_count, 1))
    missing = [] if anchor_count >= min_safe_count else [f"至少 {min_safe_count} 个高确定性安全垫"]
    return _check(
        check="safe_anchor",
        label="保底安全垫",
        score=score,
        evidence=[
            f"safe_count={safe_count}",
            f"high_prob_anchor_count={high_prob_anchor_count}",
            f"safe_anchor_coverage={plan.safe_anchor_coverage:.3f}",
        ],
        missing=missing,
        recommendation="补足可接受的保底专业组，且保底组内不能包含不可承受的尾部专业。",
    )


def _rush_target_safe_balance(plan: VolunteerPlan, profile: UserProfile | None) -> dict[str, Any]:
    total = max(len(plan.choices), 1)
    rush_ratio = sum(1 for choice in plan.choices if choice.strategy_tag == StrategyTag.RUSH) / total
    target_ratio = sum(1 for choice in plan.choices if choice.strategy_tag == StrategyTag.TARGET) / total
    safe_ratio = sum(1 for choice in plan.choices if choice.strategy_tag == StrategyTag.SAFE) / total
    risk_policy = _risk_policy(profile)
    max_rush = 0.30 if risk_policy == RiskTolerance.CONSERVATIVE else 0.45
    if risk_policy == RiskTolerance.AGGRESSIVE:
        max_rush = 0.60
    score = 1.0
    missing: list[str] = []
    if rush_ratio > max_rush:
        score -= min(0.55, (rush_ratio - max_rush) * 1.4)
        missing.append(f"冲刺比例高于 {max_rush:.0%}")
    if target_ratio <= 0.0:
        score -= 0.30
        missing.append("缺少稳妥区间")
    if safe_ratio <= 0.0:
        score -= 0.35
        missing.append("缺少保底区间")
    return _check(
        check="rush_target_safe_balance",
        label="冲稳保结构",
        score=score,
        evidence=[
            f"rush_ratio={rush_ratio:.3f}",
            f"target_ratio={target_ratio:.3f}",
            f"safe_ratio={safe_ratio:.3f}",
        ],
        missing=missing,
        recommendation="根据家庭风险偏好控制冲刺比例，确保稳妥区和保底区都真实存在。",
    )


def _key_prefix_efficiency(plan: VolunteerPlan) -> dict[str, Any]:
    total = max(len(plan.choices), 1)
    key_count = int(plan.key_prefix_count or 0)
    shadowed_ratio = float(plan.shadowed_choice_count or 0) / total
    score = 1.0
    missing: list[str] = []
    if key_count < 2:
        score -= 0.45
        missing.append("关键前缀选择少于 2 个")
    if shadowed_ratio >= 0.70:
        score -= 0.30
        missing.append("过多志愿被前序志愿遮蔽")
    if not plan.key_choice_indexes:
        score -= 0.20
        missing.append("缺少关键志愿索引")
    return _check(
        check="key_prefix_efficiency",
        label="关键前缀有效性",
        score=score,
        evidence=[
            f"key_prefix_count={key_count}",
            f"key_choice_indexes={plan.key_choice_indexes}",
            f"shadowed_choice_count={plan.shadowed_choice_count}",
        ],
        missing=missing,
        recommendation="重排前序志愿，让真正影响录取结果的关键选择更清晰，减少无效尾部堆叠。",
    )


def _high_risk_adjustment_choices(choices: list[VolunteerChoice]) -> list[str]:
    results: list[str] = []
    for choice in choices:
        if choice.adjustment_advice == AdjustmentAdvice.AVOID and choice.obey_adjustment:
            results.append(f"{choice.choice_index}:{choice.school_name}{choice.major_group_code}")
        elif choice.adjustment_advice == AdjustmentAdvice.CAUTIOUS and choice.tail_assignment_risk >= 0.45:
            results.append(f"{choice.choice_index}:{choice.school_name}{choice.major_group_code}")
    return results


def _tail_and_adjustment_risk(plan: VolunteerPlan) -> dict[str, Any]:
    high_tail_count = sum(1 for choice in plan.choices if choice.tail_assignment_risk >= 0.45)
    adjustment_conflicts = _high_risk_adjustment_choices(plan.choices)
    score = 1.0
    missing: list[str] = []
    if plan.expected_tail_risk >= 0.25:
        score -= 0.35
        missing.append("计划级尾部专业风险偏高")
    if high_tail_count:
        score -= min(0.30, high_tail_count * 0.08)
        missing.append(f"{high_tail_count} 个志愿尾部专业风险偏高")
    if adjustment_conflicts:
        score -= min(0.35, len(adjustment_conflicts) * 0.12)
        missing.append("存在需谨慎/避免调剂的高风险志愿")
    return _check(
        check="tail_and_adjustment_risk",
        label="尾部专业与调剂风险",
        score=score,
        evidence=[
            f"expected_tail_risk={plan.expected_tail_risk:.3f}",
            f"average_tail_risk={plan.average_tail_risk:.3f}",
            f"adjustment_conflicts={adjustment_conflicts[:5]}",
        ],
        missing=missing,
        recommendation="对高尾部风险专业组降低顺位、改为不服从或替换为组内专业更干净的备选。",
    )


def _hard_boundary_compliance(plan: VolunteerPlan) -> dict[str, Any]:
    blacklist_choice_count = sum(
        1 for choice in plan.choices if any(major.is_blacklisted for major in choice.major_choices)
    )
    avoid_obey_count = sum(
        1
        for choice in plan.choices
        if choice.adjustment_advice == AdjustmentAdvice.AVOID and choice.obey_adjustment
    )
    score = 1.0
    missing: list[str] = []
    if blacklist_choice_count:
        score -= 0.70
        missing.append("志愿中包含黑名单专业")
    if avoid_obey_count:
        score -= 0.40
        missing.append("建议避免调剂的志愿仍设置服从调剂")
    return _check(
        check="hard_boundary_compliance",
        label="硬边界合规",
        score=score,
        evidence=[
            f"blacklist_choice_count={blacklist_choice_count}",
            f"plan_blacklist_violation_count={plan.blacklist_violation_count}",
            f"avoid_obey_count={avoid_obey_count}",
        ],
        missing=missing,
        recommendation="硬性黑名单、不能接受调剂的专业组必须在最终填报前被替换或重新确认。",
    )


def _decision_evidence(plan: VolunteerPlan) -> dict[str, Any]:
    key_choices = [choice for choice in plan.choices if choice.is_key_prefix]
    if not key_choices:
        key_choices = plan.choices[: min(3, len(plan.choices))]
    documented = [
        choice
        for choice in key_choices
        if choice.explanation
        or choice.quant_evidence
        or choice.tradeoff_summary
        or choice.market_evidence_cards
        or choice.audit_flags
    ]
    score = len(documented) / max(len(key_choices), 1)
    missing = [] if score >= 0.72 else ["关键志愿缺少量化依据或人工可读解释"]
    return _check(
        check="decision_evidence",
        label="关键决策依据",
        score=score,
        evidence=[
            f"key_choice_count={len(key_choices)}",
            f"documented_key_choice_count={len(documented)}",
        ],
        missing=missing,
        recommendation="关键前缀志愿必须说明概率、位次缓冲、组内专业风险和取舍理由。",
    )


def audit_plan_quality(plan: VolunteerPlan, profile: UserProfile | None = None) -> dict[str, Any]:
    """Return deterministic diagnostics for one ordered volunteer plan."""
    checked_plan = _ensure_statistics(plan)
    checks = [
        _admission_security(checked_plan, profile),
        _safe_anchor(checked_plan, profile),
        _rush_target_safe_balance(checked_plan, profile),
        _key_prefix_efficiency(checked_plan),
        _tail_and_adjustment_risk(checked_plan),
        _hard_boundary_compliance(checked_plan),
        _decision_evidence(checked_plan),
    ]
    total_score = sum(item["score"] * item["weight"] for item in checks) / sum(CHECK_WEIGHTS.values())
    findings = [
        {
            "severity": item["severity"],
            "area": item["check"],
            "finding": f"{item['label']}未达到专业填报门槛",
            "recommendation": item["recommendation"],
            "missing": item["missing"],
            "evidence": item["evidence"],
        }
        for item in checks
        if not item["passed"]
    ]
    findings = sorted(
        findings,
        key=lambda item: {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(str(item["severity"]), 9),
    )
    hard_blockers = [
        item
        for item in findings
        if item["severity"] == "P0" or item["area"] == "hard_boundary_compliance"
    ]
    status = "pass"
    if hard_blockers:
        status = "blocked"
    elif total_score < 0.78 or findings:
        status = "needs_revision"
    return {
        "status": status,
        "total_score": round(total_score, 6),
        "choice_count": len(checked_plan.choices),
        "expected_admission_prob": checked_plan.expected_admission_prob,
        "expected_tail_risk": checked_plan.expected_tail_risk,
        "key_choice_indexes": checked_plan.key_choice_indexes,
        "checks": checks,
        "finding_count": len(findings),
        "findings": findings,
        "advisor_standard": (
            "Agency-grade volunteer plans need a real safety floor, a risk-policy-consistent "
            "rush/target/safe structure, low hard-boundary violations, and evidence for key rows."
        ),
    }


def build_markdown_plan_quality_audit(result: dict[str, Any]) -> str:
    """Build a compact Markdown plan-quality audit."""
    lines = [
        "# Volunteer Plan Quality Audit",
        "",
        f"Status: `{result.get('status', 'unknown')}`",
        f"Total score: {float(result.get('total_score', 0.0)):.1%}",
        f"Expected admission probability: {float(result.get('expected_admission_prob', 0.0)):.1%}",
        f"Expected tail risk: {float(result.get('expected_tail_risk', 0.0)):.1%}",
        f"Key choice indexes: {result.get('key_choice_indexes', [])}",
        "",
        result.get("advisor_standard", ""),
        "",
        "## Checks",
        "",
        "| Check | Score | Passed | Missing | Recommendation |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for item in result.get("checks", []) or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{item.get('check', '')}`",
                    f"{float(item.get('score', 0.0)):.1%}",
                    "yes" if item.get("passed") else "no",
                    "、".join(item.get("missing", []) or []),
                    str(item.get("recommendation", "")).replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Findings", ""])
    if result.get("findings"):
        for idx, item in enumerate(result["findings"], 1):
            lines.append(f"{idx}. `{item['severity']}` {item['area']}: {item['recommendation']}")
    else:
        lines.append("No blocking plan-quality findings.")
    return "\n".join(lines) + "\n"

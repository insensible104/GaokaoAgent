"""Pre-recommendation intake readiness audit.

This module turns an expert counselor's first interview into deterministic
checks. The goal is to stop recommendation work when core information is
missing, and to produce a clear clarification checklist when the case is
under-specified.
"""

from __future__ import annotations

from typing import Any

from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


DIMENSION_WEIGHTS = {
    "academic_core": 0.24,
    "region_boundary": 0.14,
    "major_boundary": 0.14,
    "school_major_tradeoff": 0.12,
    "risk_policy": 0.10,
    "adjustment_budget_pathway": 0.12,
    "preference_cognition": 0.08,
    "restriction_review": 0.06,
}


def _clean_values(values: list[str]) -> list[str]:
    return [str(value).strip() for value in values if str(value).strip()]


def _dimension(
    *,
    dimension: str,
    label: str,
    status: str,
    score: float,
    evidence: list[str],
    missing: list[str],
    question: str,
    severity: str = "P2",
) -> dict[str, Any]:
    return {
        "dimension": dimension,
        "label": label,
        "status": status,
        "score": round(max(0.0, min(1.0, score)), 6),
        "weight": DIMENSION_WEIGHTS[dimension],
        "evidence": evidence,
        "missing": missing,
        "question": question,
        "severity": severity,
    }


def _academic_core(profile: UserProfile) -> dict[str, Any]:
    evidence: list[str] = []
    missing: list[str] = []
    if profile.score and profile.score > 0:
        evidence.append(f"score={profile.score}")
    else:
        missing.append("高考总分")
    if profile.rank is not None and profile.rank > 0:
        evidence.append(f"rank={profile.rank}")
    else:
        missing.append("全省位次")
    if profile.subject_group and profile.subject_group.strip():
        evidence.append(f"subject_group={profile.subject_group}")
    else:
        missing.append("选科组合")

    score = (3 - len(missing)) / 3
    return _dimension(
        dimension="academic_core",
        label="分数/位次/选科硬信息",
        status="known" if not missing else "missing",
        score=score,
        evidence=evidence,
        missing=missing,
        question="请先核对总分、全省位次、选科组合，并确认使用的是最终一分一段表口径。",
        severity="P0" if missing else "P3",
    )


def _region_boundary(profile: UserProfile) -> dict[str, Any]:
    preferred = _clean_values(profile.preferred_cities)
    excluded = _clean_values(profile.excluded_cities)
    evidence: list[str] = []
    if preferred:
        evidence.append("偏好城市=" + "、".join(preferred))
    if excluded:
        evidence.append("排除城市=" + "、".join(excluded))
    missing = [] if evidence else ["是否接受省外/外市", "城市优先级", "不可接受地区"]
    return _dimension(
        dimension="region_boundary",
        label="地域边界",
        status="known" if evidence else "needs_clarification",
        score=1.0 if evidence else 0.25,
        evidence=evidence,
        missing=missing,
        question="是否接受省外？若只看省内，请按城市/通勤/气候/家庭照顾给出不可突破边界。",
        severity="P1" if missing else "P3",
    )


def _major_boundary(profile: UserProfile) -> dict[str, Any]:
    preferred = _clean_values(profile.preferred_majors)
    blacklist = _clean_values(profile.blacklist_majors)
    evidence: list[str] = []
    if preferred:
        evidence.append("意向专业=" + "、".join(preferred))
    if blacklist:
        evidence.append("黑名单专业=" + "、".join(blacklist))
    missing = [] if evidence else ["目标专业", "可接受专业范围", "绝对不接受专业"]
    score = 1.0 if preferred and blacklist else 0.75 if preferred or blacklist else 0.25
    return _dimension(
        dimension="major_boundary",
        label="专业边界",
        status="known" if evidence else "needs_clarification",
        score=score,
        evidence=evidence,
        missing=missing,
        question="请列出目标专业、可接受相邻专业、绝对不接受专业，并确认专业组内尾部专业能否承受。",
        severity="P1" if missing else "P3",
    )


def _school_major_tradeoff(profile: UserProfile) -> dict[str, Any]:
    known = profile.school_major_preference != SchoolMajorPreference.UNKNOWN
    evidence = [profile.school_major_preference.value] if known else []
    return _dimension(
        dimension="school_major_tradeoff",
        label="学校/专业权衡",
        status="known" if known else "needs_clarification",
        score=1.0 if known else 0.20,
        evidence=evidence,
        missing=[] if known else ["学校优先、专业优先或均衡策略"],
        question="同样分数下，是优先学校层级、目标专业命中，还是两者均衡？请给出可接受的降档边界。",
        severity="P1" if not known else "P3",
    )


def _risk_policy(profile: UserProfile) -> dict[str, Any]:
    labels = {
        RiskTolerance.CONSERVATIVE: "保守",
        RiskTolerance.BALANCED: "平衡",
        RiskTolerance.AGGRESSIVE: "激进",
    }
    evidence = [labels.get(profile.risk_tolerance, profile.risk_tolerance.value)]
    if profile.emotional_concerns:
        evidence.append("担忧=" + "、".join(_clean_values(profile.emotional_concerns)))
    if profile.regret_sensitivity >= 0.7:
        evidence.append(f"后悔敏感度={profile.regret_sensitivity:.2f}")
    score = 0.85 if profile.risk_tolerance == RiskTolerance.BALANCED else 1.0
    if profile.regret_sensitivity >= 0.7 and profile.risk_tolerance == RiskTolerance.AGGRESSIVE:
        score = 0.45
    return _dimension(
        dimension="risk_policy",
        label="风险偏好",
        status="known" if score >= 0.70 else "conflict",
        score=score,
        evidence=evidence,
        missing=[] if score >= 0.70 else ["激进策略与高后悔敏感度冲突"],
        question="请确认冲稳保比例，以及最不能接受的是滑档、浪费分、调剂进差专业，还是学校层级下降。",
        severity="P1" if score < 0.70 else "P3",
    )


def _adjustment_budget_pathway(profile: UserProfile) -> dict[str, Any]:
    evidence: list[str] = []
    if any("民办" in item or "中外" in item or "高收费" in item for item in profile.preference_assumptions):
        evidence.extend(_clean_values(profile.preference_assumptions))
    return _dimension(
        dimension="adjustment_budget_pathway",
        label="调剂/预算/培养路径",
        status="needs_confirmation",
        score=0.35 if not evidence else 0.60,
        evidence=evidence,
        missing=["是否服从调剂", "民办/中外合作/高收费预算", "异地校区和特殊培养路径"],
        question="是否接受服从调剂、民办、中外合作、高收费、异地校区、专升本/转专业等路径差异？请逐项回答。",
        severity="P2",
    )


def _preference_cognition(profile: UserProfile) -> dict[str, Any]:
    evidence = [
        f"preference_confidence={profile.preference_confidence:.2f}",
        f"major_cognition_risk={profile.major_cognition_risk:.2f}",
        f"regret_sensitivity={profile.regret_sensitivity:.2f}",
    ]
    evidence.extend(_clean_values(profile.stated_misconceptions[:3]))
    evidence.extend(_clean_values(profile.family_pressure_points[:3]))
    missing: list[str] = []
    score = 1.0
    if profile.preference_confidence < 0.45:
        missing.append("偏好可信度偏低")
        score -= 0.35
    if profile.major_cognition_risk >= 0.55:
        missing.append("专业认知风险偏高")
        score -= 0.30
    if profile.family_pressure_points and profile.preference_confidence < 0.65:
        missing.append("家庭压力可能扭曲学生偏好")
        score -= 0.20
    return _dimension(
        dimension="preference_cognition",
        label="偏好认知可靠性",
        status="known" if not missing else "needs_clarification",
        score=score,
        evidence=evidence,
        missing=missing,
        question="请用学生自己的话解释目标专业学什么、毕业去向、不能接受什么，以及家长意见是否与学生一致。",
        severity="P2" if missing else "P3",
    )


def _restriction_review(profile: UserProfile) -> dict[str, Any]:
    evidence: list[str] = []
    if profile.medical_restrictions:
        evidence.append("体检限制=" + ", ".join(f"{key}={value}" for key, value in profile.medical_restrictions.items()))
    if profile.subject_scores:
        evidence.append("单科成绩=" + ", ".join(f"{key}={value}" for key, value in profile.subject_scores.items()))
    return _dimension(
        dimension="restriction_review",
        label="体检/单科/章程限制",
        status="known" if evidence else "needs_confirmation",
        score=1.0 if evidence else 0.55,
        evidence=evidence,
        missing=[] if evidence else ["体检受限项", "单科受限项", "招生章程特殊要求"],
        question="请确认色盲色弱、视力、口语、单科成绩、身高等限制，并在最终填报前逐条对照招生章程。",
        severity="P2" if not evidence else "P3",
    )


def _status(blockers: list[dict[str, Any]], dimensions: list[dict[str, Any]], readiness_score: float) -> str:
    if blockers:
        return "blocked_missing_core"
    if readiness_score < 0.72:
        return "needs_clarification"
    if any(item["severity"] == "P1" and item["status"] != "known" for item in dimensions):
        return "needs_clarification"
    return "ready_for_recommendation"


def build_intake_audit(profile: UserProfile) -> dict[str, Any]:
    """Build a deterministic intake-readiness audit for one student profile."""
    dimensions = [
        _academic_core(profile),
        _region_boundary(profile),
        _major_boundary(profile),
        _school_major_tradeoff(profile),
        _risk_policy(profile),
        _adjustment_budget_pathway(profile),
        _preference_cognition(profile),
        _restriction_review(profile),
    ]
    readiness_score = sum(item["score"] * item["weight"] for item in dimensions) / sum(DIMENSION_WEIGHTS.values())
    blockers = [
        {
            "dimension": item["dimension"],
            "missing": item["missing"],
            "question": item["question"],
        }
        for item in dimensions
        if item["severity"] == "P0" and item["status"] != "known"
    ]
    clarification_questions = [
        item["question"]
        for item in dimensions
        if item["status"] != "known"
    ]
    missing_items = [
        {
            "dimension": item["dimension"],
            "label": item["label"],
            "severity": item["severity"],
            "missing": item["missing"],
        }
        for item in dimensions
        if item["missing"]
    ]
    status = _status(blockers, dimensions, readiness_score)
    return {
        "status": status,
        "readiness_score": round(readiness_score, 6),
        "core_blockers": blockers,
        "dimensions": dimensions,
        "missing_items": missing_items,
        "clarification_questions": clarification_questions,
        "minimum_next_step": _minimum_next_step(status),
        "advisor_standard": (
            "Do not start ranking recommendations until score, rank, subject group, region boundary, "
            "major boundary, and school-major tradeoff are explicitly reviewed."
        ),
    }


def _minimum_next_step(status: str) -> str:
    if status == "blocked_missing_core":
        return "先补齐分数、位次、选科等硬信息，再开始任何院校推荐。"
    if status == "needs_clarification":
        return "先完成问诊清单，再生成候选池和志愿排序。"
    return "可进入候选池生成，但最终交付前仍需完成预期确认单和官方章程复核。"


def build_markdown_intake_audit(result: dict[str, Any]) -> str:
    """Render intake audit as Markdown for operators and clients."""
    lines = [
        "# 志愿填报问诊完备度审计",
        "",
        f"Status: `{result.get('status', 'unknown')}`",
        f"Readiness score: {float(result.get('readiness_score', 0.0)):.1%}",
        "",
        result.get("advisor_standard", ""),
        "",
        "## 维度检查",
        "",
        "| 维度 | 状态 | 分数 | 缺失项 |",
        "| --- | --- | ---: | --- |",
    ]
    for item in result.get("dimensions", []) or []:
        lines.append(
            f"| {item.get('label', '')} | `{item.get('status', '')}` | "
            f"{float(item.get('score', 0.0)):.1%} | "
            f"{'、'.join(item.get('missing', []) or [])} |"
        )
    lines.extend(["", "## 必问问题", ""])
    for idx, question in enumerate(result.get("clarification_questions", []) or [], 1):
        lines.append(f"{idx}. {question}")
    if result.get("core_blockers"):
        lines.extend(["", "## 核心阻断项", ""])
        for blocker in result["core_blockers"]:
            lines.append(f"- `{blocker['dimension']}`: {'、'.join(blocker.get('missing') or [])}")
    lines.extend(["", "## 最小下一步", "", result.get("minimum_next_step", "")])
    return "\n".join(lines) + "\n"

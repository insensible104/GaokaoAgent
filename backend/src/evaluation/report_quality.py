"""Delivery-quality audit for recommendation reports.

Top agencies do not only produce a ranked list. They document constraints,
risks, evidence, action steps, and responsibility boundaries. This module turns
those delivery expectations into deterministic checks that can be run on every
generated report.
"""

from __future__ import annotations

import json
import re
from typing import Any, Sequence


CHECKS = {
    "student_context": {
        "weight": 0.12,
        "required": ["位次", "分", "选科"],
        "optional": ["省", "物理", "历史", "城市"],
        "recommendation": "报告开头必须复述学生基础画像，避免推荐脱离输入条件。",
    },
    "constraint_confirmation": {
        "weight": 0.16,
        "required": ["限制", "偏好", "城市"],
        "optional": ["不出省", "省内", "预算", "民办", "中外", "专业偏好", "黑名单"],
        "recommendation": "补充限制条件确认：地域、预算、民办/中外合作、不可接受专业和是否服从调剂。",
    },
    "risk_explanation": {
        "weight": 0.18,
        "required": ["风险"],
        "optional": ["滑档", "调剂", "尾部", "黑名单", "浪费", "混搭", "保底"],
        "recommendation": "风险说明必须覆盖滑档、调剂、尾部专业、浪费分和黑名单命中场景。",
    },
    "recommendation_evidence": {
        "weight": 0.18,
        "required": ["推荐"],
        "optional": ["量化校验", "位次缓冲", "数据置信", "历史", "首命中", "关键志愿解释", "概率"],
        "recommendation": "每个关键推荐需要给出量化依据，而不是只给院校名称。",
    },
    "actionability": {
        "weight": 0.14,
        "required": ["调剂建议"],
        "optional": ["第1志愿", "第2志愿", "专业1-6", "服从调剂", "复核", "招生章程"],
        "recommendation": "补充可执行填报动作：志愿顺序、1-6专业建议、服从调剂建议和复核事项。",
    },
    "expectation_management": {
        "weight": 0.12,
        "required": ["概率"],
        "optional": ["不保证", "不确定", "可能", "边界", "复核", "最终", "官方"],
        "recommendation": "明确概率不是承诺，说明不确定性和需要家长/学生确认的边界。",
    },
    "disclaimer_boundary": {
        "weight": 0.10,
        "required": ["复核"],
        "optional": ["官方", "招生章程", "最终以", "仅供参考", "政策", "数据更新"],
        "recommendation": "加入免责和复核边界：最终以考试院、招生章程和当年官方数据为准。",
    },
}


def _as_text(payload: str | dict[str, Any]) -> str:
    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            return ""
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return text
        return _as_text(parsed)

    fields: list[str] = []
    for key in (
        "full_markdown",
        "title",
        "executive_summary",
        "strategy_analysis",
        "school_recommendations",
        "risk_warnings",
    ):
        value = payload.get(key)
        if isinstance(value, list):
            fields.extend(str(item) for item in value)
        elif value:
            fields.append(str(value))
    if not fields:
        fields.append(json.dumps(payload, ensure_ascii=False))
    return "\n".join(fields)


def _contains_all(text: str, terms: Sequence[str]) -> bool:
    return all(term in text for term in terms)


def _coverage(text: str, terms: Sequence[str]) -> float:
    if not terms:
        return 1.0
    return sum(1 for term in terms if term in text) / len(terms)


def _severity(score: float, weight: float) -> str:
    if score <= 0.20 and weight >= 0.15:
        return "P0"
    if score <= 0.35:
        return "P1"
    if score <= 0.65:
        return "P2"
    return "P3"


def _audit_check(name: str, spec: dict[str, Any], text: str) -> dict[str, Any]:
    required = list(spec["required"])
    optional = list(spec["optional"])
    required_score = 1.0 if _contains_all(text, required) else _coverage(text, required)
    optional_score = _coverage(text, optional)
    score = min(1.0, required_score * 0.65 + optional_score * 0.35)
    missing_required = [term for term in required if term not in text]
    missing_optional = [term for term in optional if term not in text]
    return {
        "check": name,
        "score": round(score, 6),
        "weight": spec["weight"],
        "passed": score >= 0.70,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "recommendation": spec["recommendation"],
        "severity": _severity(score, float(spec["weight"])),
    }


def _line_count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.MULTILINE))


def audit_report_quality(payload: str | dict[str, Any]) -> dict[str, Any]:
    """Return deterministic delivery-quality diagnostics for one report."""
    text = _as_text(payload)
    checks = [_audit_check(name, spec, text) for name, spec in CHECKS.items()]
    weighted_score = sum(item["score"] * item["weight"] for item in checks)
    weight_sum = sum(item["weight"] for item in checks)
    total_score = weighted_score / max(weight_sum, 1e-6)
    recommendation_count = max(
        _line_count(r"^\s*\d+\.\s+", text),
        text.count("第1志愿") + text.count("第2志愿") + text.count("第3志愿"),
    )
    warning_count = max(
        _line_count(r"^\s*-\s+.*风险", text),
        text.count("风险"),
    )
    findings = [
        {
            "severity": item["severity"],
            "area": item["check"],
            "finding": f"{item['check']} 未达到专业交付门槛",
            "recommendation": item["recommendation"],
            "missing_required": item["missing_required"],
            "missing_optional": item["missing_optional"][:5],
        }
        for item in checks
        if not item["passed"]
    ]
    findings = sorted(
        findings,
        key=lambda item: {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(item["severity"], 9),
    )
    status = "pass" if total_score >= 0.78 and not any(item["severity"] == "P0" for item in findings) else "needs_revision"
    return {
        "status": status,
        "total_score": round(total_score, 6),
        "recommendation_count": recommendation_count,
        "warning_count": warning_count,
        "checks": checks,
        "finding_count": len(findings),
        "findings": findings,
        "delivery_standard": (
            "Agency-grade reports must restate constraints, explain probabilistic risk, "
            "show evidence, give actionable fill-in steps, and state official-data boundaries."
        ),
    }


def build_markdown_report_quality_audit(result: dict[str, Any]) -> str:
    """Build a compact Markdown report-quality audit."""
    lines = [
        "# Report Quality Audit",
        "",
        f"Status: `{result.get('status', 'unknown')}`",
        f"Total score: {float(result.get('total_score', 0.0)):.1%}",
        f"Recommendations detected: {result.get('recommendation_count', 0)}",
        f"Risk mentions detected: {result.get('warning_count', 0)}",
        "",
        result.get("delivery_standard", ""),
        "",
        "## Checks",
        "",
        "| Check | Score | Passed | Missing Required | Recommendation |",
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
                    ", ".join(item.get("missing_required", []) or []),
                    str(item.get("recommendation", "")).replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Findings", ""])
    if result.get("findings"):
        for idx, item in enumerate(result["findings"], 1):
            lines.append(
                f"{idx}. `{item['severity']}` {item['area']}: {item['recommendation']}"
            )
    else:
        lines.append("No blocking delivery-quality findings.")
    return "\n".join(lines) + "\n"

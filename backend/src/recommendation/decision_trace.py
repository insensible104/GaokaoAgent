"""Build a compact, student-facing trace from existing recommendation scores."""

from __future__ import annotations

from typing import Any


SUPPORT_LABELS = {
    "major_value": "专业匹配",
    "school_value": "院校与专业实力",
    "city_value": "城市匹配",
    "quant_score": "位次与历史量化",
}

RISK_LABELS = {
    "tail_risk_penalty": "尾部调剂惩罚",
    "crowding_penalty": "热门拥挤惩罚",
    "blacklist_penalty": "黑名单专业惩罚",
}


def _factor(code: str, label: str, value: float) -> dict[str, Any]:
    return {"code": code, "label": label, "value": round(float(value), 4)}


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def build_decision_trace(row: Any) -> dict[str, Any]:
    """Expose why a surviving candidate is recommended and where it can fail."""
    breakdown = dict(getattr(row, "tradeoff_breakdown", {}) or {})

    supporting = [
        _factor(code, label, breakdown.get(code, 0.0))
        for code, label in SUPPORT_LABELS.items()
        if float(breakdown.get(code, 0.0) or 0.0) > 0
    ]
    supporting.sort(key=lambda item: item["value"], reverse=True)

    risks = [
        _factor(code, label, breakdown.get(code, 0.0))
        for code, label in RISK_LABELS.items()
        if float(breakdown.get(code, 0.0) or 0.0) > 0
    ]
    risks.sort(key=lambda item: item["value"], reverse=True)

    data_confidence = float(breakdown.get("data_confidence_score", 0.0) or 0.0)
    if data_confidence >= 0.75:
        confidence_level = "high"
    elif data_confidence >= 0.50:
        confidence_level = "medium"
    else:
        confidence_level = "low"

    warnings = list(getattr(row, "risk_reasons", []) or [])
    worst_case_major = getattr(row, "worst_case_major", None)
    if getattr(row, "is_blacklist_risk", False):
        warnings.append(f"最差调剂可能触及黑名单专业：{worst_case_major or '未明确专业'}")
    if confidence_level == "low":
        warnings.append("历史数据置信度偏低，结论需结合最新招生章程人工复核")
    warnings = _dedupe(warnings)

    verdict = "recommended_with_caution" if risks or warnings else "recommended"
    top_support = supporting[0]["label"] if supporting else "综合条件"
    summary = f"主要优势：{top_support}"
    if risks:
        summary += f"；主要风险：{risks[0]['label']}"
    if confidence_level == "low":
        summary += "；数据置信度偏低"
    summary += "。"

    return {
        "verdict": verdict,
        "summary": summary,
        "confidence_level": confidence_level,
        "data_confidence_score": round(data_confidence, 4),
        "supporting_factors": supporting[:4],
        "risk_factors": risks,
        "supporting_evidence": list(getattr(row, "quant_evidence", []) or [])[:3],
        "warnings": warnings,
        "eligibility_checks": [
            {"code": "critical_inputs", "label": "分数、位次与选科完整", "status": "passed"},
            {"code": "not_all_blacklisted", "label": "专业组并非全部命中黑名单", "status": "passed"},
        ],
    }

"""Resolve official plan changes and reference-only claims into one explanation."""

from __future__ import annotations

from typing import Any


def _direction(text: object) -> str:
    value = str(text or "").lower()
    if any(token in value for token in ("increase", "increased", "扩招", "增加", "上升")):
        return "increase"
    if any(token in value for token in ("decrease", "decreased", "缩招", "减少", "下降")):
        return "decrease"
    return "unknown"


def build_plan_change_explanation(row: Any) -> dict[str, Any]:
    """Prefer deterministic official diffs and surface contradictory references."""
    official_changes = [dict(item) for item in (getattr(row, "plan_change_details", []) or [])]
    reference_claims: list[dict[str, Any]] = []
    for card in getattr(row, "market_evidence_cards", []) or []:
        if str(card.get("signal_type") or "") not in {
            "plan_change_signal",
            "quota_change_signal",
            "major_group_restructure",
        }:
            continue
        reference_claims.append(
            {
                "claim": str(card.get("claim") or ""),
                "source": str(card.get("source") or ""),
                "source_tier": "reference_only",
                "applied_to_ranking": False,
            }
        )

    official_directions = {
        _direction(item.get("change_type"))
        for item in official_changes
        if _direction(item.get("change_type")) != "unknown"
    }
    reference_directions = {
        _direction(item.get("claim"))
        for item in reference_claims
        if _direction(item.get("claim")) != "unknown"
    }
    conflict = bool(
        ("increase" in official_directions and "decrease" in reference_directions)
        or ("decrease" in official_directions and "increase" in reference_directions)
    )

    review_items: list[str] = []
    if conflict:
        review_items.append("参考信息与官方招生计划差分方向冲突，正式填报前需核对最新招生章程。")

    ranking_impact = "none"
    if official_changes:
        ranking_impact = (
            "official_diff_applied"
            if float(getattr(row, "plan_change_score", 0.0) or 0.0) > 0
            else "official_diff_considered"
        )

    if official_changes:
        primary = official_changes[0]
        before = primary.get("before")
        after = primary.get("after")
        if before is not None or after is not None:
            summary = f"{primary.get('change_type', 'plan_change')}: {before} -> {after}"
        else:
            summary = str(primary.get("evidence") or primary.get("change_type") or "招生计划发生变化")
    elif reference_claims:
        summary = "存在参考性方案变化信息，尚未纳入量化排序。"
    else:
        summary = "未检测到可用于排序的高置信招生计划变化。"

    if conflict:
        status = "review_required"
    elif official_changes:
        status = "resolved"
    elif reference_claims:
        status = "reference_only"
    else:
        status = "none"

    return {
        "status": status,
        "summary": summary,
        "source_priority": ["official_current", "official_diff", "historical", "reference_only"],
        "ranking_impact": ranking_impact,
        "official_changes": official_changes,
        "reference_claims": reference_claims,
        "review_items": review_items,
    }

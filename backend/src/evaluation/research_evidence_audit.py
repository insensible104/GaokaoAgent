"""Audit deep-research evidence cards before they feed quant features."""

from __future__ import annotations

from collections import Counter
from typing import Any, Sequence

from recommendation.research_evidence_features import (
    PREDICTION_SOURCE_TYPES,
    SOCIAL_SOURCE_TYPES,
    derive_research_evidence_signals,
)


PROTOCOL_VERSION = "gaokao-research-evidence-audit-v1"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _card_dict(card: dict[str, Any]) -> dict[str, Any]:
    return dict(card)


def _source_type(card: dict[str, Any]) -> str:
    return str(card.get("source_type") or "unknown")


def _is_prediction_source(card: dict[str, Any]) -> bool:
    return _source_type(card) in PREDICTION_SOURCE_TYPES


def _is_social_source(card: dict[str, Any]) -> bool:
    return _source_type(card) in SOCIAL_SOURCE_TYPES


def _usable(card: dict[str, Any]) -> bool:
    return bool(card.get("usable_for_prediction"))


def _has_source(card: dict[str, Any]) -> bool:
    return bool(str(card.get("source") or "").strip())


def _has_cutoff(card: dict[str, Any]) -> bool:
    return bool(str(card.get("cutoff_date") or "").strip())


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


def _status(checks: list[dict[str, Any]], usable_prediction_count: int) -> str:
    if any(not row["passed"] and row["severity"] == "P0" for row in checks):
        return "blocked_for_quant_ingestion"
    if usable_prediction_count > 0 and all(row["passed"] or row["severity"] != "P1" for row in checks):
        return "prediction_feature_ready"
    if usable_prediction_count > 0:
        return "limited_prediction_feature"
    return "reference_only_research"


def audit_research_evidence_cards(
    evidence_cards: Sequence[dict[str, Any]],
    *,
    scope_terms: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Audit whether research evidence can safely influence quant features."""
    cards = [_card_dict(card) for card in evidence_cards]
    source_counts = Counter(_source_type(card) for card in cards)
    usable_prediction_cards = [
        card
        for card in cards
        if _usable(card) and _is_prediction_source(card)
    ]
    social_prediction_leaks = [
        card
        for card in cards
        if _usable(card) and _is_social_source(card)
    ]
    manual_prediction_leaks = [
        card
        for card in cards
        if _usable(card) and _source_type(card) == "manual_verification_required"
    ]
    missing_source_count = sum(1 for card in cards if not _has_source(card))
    missing_cutoff_count = sum(1 for card in cards if not _has_cutoff(card))
    manual_count = source_counts.get("manual_verification_required", 0)
    social_count = sum(source_counts.get(source_type, 0) for source_type in SOCIAL_SOURCE_TYPES)
    prediction_source_count = sum(source_counts.get(source_type, 0) for source_type in PREDICTION_SOURCE_TYPES)
    average_confidence = (
        sum(_clamp(float(card.get("confidence", 0.0) or 0.0)) for card in cards) / len(cards)
        if cards
        else 0.0
    )
    signals = derive_research_evidence_signals(cards, scope_terms=scope_terms)
    signal_payload = signals.to_dict()
    prediction_signal_count = sum(
        1
        for key in (
            "official_policy_signal",
            "plan_change_signal",
            "quota_change_signal",
            "major_group_restructure_signal",
        )
        if float(signal_payload.get(key) or 0.0) > 0
    )
    reference_signal_count = sum(
        1
        for key in ("publicity_heat_signal", "sentiment_shock_signal")
        if float(signal_payload.get(key) or 0.0) > 0
    )

    checks: list[dict[str, Any]] = []
    _add_check(
        checks,
        name="minimum_evidence_cards",
        passed=len(cards) >= 1,
        severity="P0",
        evidence=len(cards),
        target=">= 1 evidence card",
        blocker_reason="No structured evidence cards were provided.",
    )
    _add_check(
        checks,
        name="source_attribution_present",
        passed=missing_source_count == 0,
        severity="P0",
        evidence=missing_source_count,
        target="0 cards missing source",
        blocker_reason="Some evidence cards have no source attribution.",
    )
    _add_check(
        checks,
        name="cutoff_date_present",
        passed=missing_cutoff_count == 0,
        severity="P1",
        evidence=missing_cutoff_count,
        target="0 cards missing cutoff_date",
        blocker_reason="Some evidence cards lack a collection or cutoff date.",
    )
    _add_check(
        checks,
        name="social_sources_are_reference_only",
        passed=not social_prediction_leaks,
        severity="P0",
        evidence=len(social_prediction_leaks),
        target="0 social/creator cards marked usable_for_prediction",
        blocker_reason="Social, WeChat, livestream, or creator evidence leaked into prediction use.",
    )
    _add_check(
        checks,
        name="manual_fallback_is_reference_only",
        passed=not manual_prediction_leaks,
        severity="P0",
        evidence=len(manual_prediction_leaks),
        target="0 manual-verification cards marked usable_for_prediction",
        blocker_reason="Manual fallback evidence cannot support prediction features.",
    )
    _add_check(
        checks,
        name="official_prediction_boundary",
        passed=not usable_prediction_cards or prediction_source_count > 0,
        severity="P0",
        evidence={
            "usable_prediction_card_count": len(usable_prediction_cards),
            "prediction_source_count": prediction_source_count,
        },
        target="prediction-ready cards must be official or semi-official",
        blocker_reason="Prediction-ready evidence lacks official or semi-official source support.",
    )
    _add_check(
        checks,
        name="prediction_signal_coverage",
        passed=not usable_prediction_cards or prediction_signal_count > 0,
        severity="P1",
        evidence=prediction_signal_count,
        target=">= 1 controlled prediction signal when prediction cards exist",
        blocker_reason="Official evidence exists but does not map to controlled quant signals.",
    )

    result_status = _status(checks, len(usable_prediction_cards))
    return {
        "protocol_version": PROTOCOL_VERSION,
        "status": result_status,
        "card_count": len(cards),
        "source_type_counts": dict(source_counts),
        "usable_prediction_card_count": len(usable_prediction_cards),
        "prediction_source_count": prediction_source_count,
        "reference_only_card_count": len(cards) - len(usable_prediction_cards),
        "social_reference_card_count": social_count,
        "manual_verification_card_count": manual_count,
        "missing_source_count": missing_source_count,
        "missing_cutoff_date_count": missing_cutoff_count,
        "average_confidence": round(average_confidence, 4),
        "prediction_signal_count": prediction_signal_count,
        "reference_signal_count": reference_signal_count,
        "controlled_signals": signal_payload,
        "checks": checks,
        "next_required_evidence": [
            row["blocker_reason"]
            for row in checks
            if not row["passed"]
        ],
        "notes": [
            "Official and semi-official cards may support controlled prediction features.",
            "WeChat, livestream, creator, and social cards are reference-only market heat or sentiment evidence.",
            "Fallback/manual cards must trigger human verification before family-facing recommendations.",
        ],
    }


def build_markdown_research_evidence_audit(result: dict[str, Any]) -> str:
    """Render research-evidence audit as Markdown."""
    lines = [
        "# Research Evidence Audit",
        "",
        f"Status: `{result.get('status', 'unknown')}`",
        f"Cards: {result.get('card_count', 0)}",
        f"Usable prediction cards: {result.get('usable_prediction_card_count', 0)}",
        f"Average confidence: {float(result.get('average_confidence') or 0.0):.1%}",
        "",
        "## Source Types",
        "",
        "| Source type | Count |",
        "| --- | ---: |",
    ]
    for source_type, count in sorted((result.get("source_type_counts") or {}).items()):
        lines.append(f"| `{source_type}` | {count} |")
    if not result.get("source_type_counts"):
        lines.append("| `none` | 0 |")

    lines.extend([
        "",
        "## Checks",
        "",
        "| Check | Pass | Severity | Evidence | Target | Blocker |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for row in result.get("checks") or []:
        lines.append(
            f"| `{row.get('name', '')}` | {'yes' if row.get('passed') else 'no'} | "
            f"`{row.get('severity', '')}` | `{row.get('evidence')}` | "
            f"{row.get('target', '')} | {row.get('blocker_reason', '')} |"
        )

    lines.extend(["", "## Controlled Signals", ""])
    signals = result.get("controlled_signals") or {}
    for key in (
        "official_policy_signal",
        "plan_change_signal",
        "quota_change_signal",
        "major_group_restructure_signal",
        "publicity_heat_signal",
        "sentiment_shock_signal",
    ):
        lines.append(f"- `{key}`: {float(signals.get(key) or 0.0):.3f}")

    lines.extend(["", "## Next Required Evidence", ""])
    for item in result.get("next_required_evidence") or []:
        lines.append(f"- {item}")
    if not result.get("next_required_evidence"):
        lines.append("- none")

    lines.extend(["", "## Notes", ""])
    for note in result.get("notes") or []:
        lines.append(f"- {note}")
    return "\n".join(lines)

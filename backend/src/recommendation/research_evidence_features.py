"""Convert deep-research evidence cards into controlled quant signals.

Research/search evidence is useful only when the source boundary is explicit.
Official and semi-official sources may support prediction features such as
policy, plan-change, quota, and group-restructure signals. Social or creator
sources are limited to market-heat and rebound-risk signals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from recommendation.market_evidence import EvidenceCard


PREDICTION_SOURCE_TYPES = {"official_or_school", "semi_official_aggregator"}
SOCIAL_SOURCE_TYPES = {"social_media", "livestream", "wechat", "creator_content"}

POLICY_KEYWORDS = (
    "招生章程",
    "章程",
    "录取规则",
    "投档",
    "选科要求",
    "考试院",
    "教育厅",
    "admission policy",
    "charter",
)
PLAN_CHANGE_KEYWORDS = (
    "招生计划",
    "计划变化",
    "新增",
    "停招",
    "扩招",
    "缩招",
    "调整",
    "中外合作",
    "校区",
    "plan change",
    "new program",
)
QUOTA_KEYWORDS = (
    "计划数",
    "招生人数",
    "名额",
    "扩招",
    "缩招",
    "quota",
    "enrollment",
)
GROUP_RESTRUCTURE_KEYWORDS = (
    "院校专业组",
    "专业组",
    "组内",
    "大类",
    "单列",
    "拆分",
    "合并",
    "调剂",
    "major group",
    "professional group",
)
PUBLICITY_KEYWORDS = (
    "直播",
    "主播",
    "博主",
    "公众号",
    "微信",
    "小红书",
    "抖音",
    "热推",
    "热门",
    "爆",
    "livestream",
    "viral",
    "creator",
)
SENTIMENT_KEYWORDS = (
    "舆情",
    "争议",
    "事故",
    "曝光",
    "负面",
    "风波",
    "sentiment",
    "controversy",
    "incident",
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _text(card: dict[str, Any]) -> str:
    return " ".join(
        str(card.get(key) or "")
        for key in ("claim", "source", "source_type", "signal_type")
    ).lower()


def _contains(text: str, keywords: Sequence[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def _card_dict(card: EvidenceCard | dict[str, Any]) -> dict[str, Any]:
    if isinstance(card, EvidenceCard):
        return card.to_dict()
    return dict(card)


def _base_strength(card: dict[str, Any]) -> float:
    value = _clamp(float(card.get("value", 0.5) or 0.5))
    confidence = _clamp(float(card.get("confidence", 0.5) or 0.5))
    return _clamp(value * confidence)


def _source_type(card: dict[str, Any]) -> str:
    return str(card.get("source_type") or "unknown")


def _usable_for_prediction(card: dict[str, Any]) -> bool:
    return bool(card.get("usable_for_prediction")) and _source_type(card) in PREDICTION_SOURCE_TYPES


def _matches_scope(card: dict[str, Any], scope_terms: Sequence[str] | None) -> bool:
    terms = [str(term).strip().lower() for term in scope_terms or [] if str(term).strip()]
    if not terms:
        return True
    haystack = _text(card)
    return any(term in haystack for term in terms)


@dataclass(frozen=True)
class ResearchEvidenceSignals:
    """Aggregated controlled signals derived from research evidence."""

    official_policy_signal: float = 0.0
    plan_change_signal: float = 0.0
    quota_change_signal: float = 0.0
    major_group_restructure_signal: float = 0.0
    publicity_heat_signal: float = 0.0
    sentiment_shock_signal: float = 0.0
    evidence_confidence: float = 0.0
    prediction_ready: bool = False
    usable_prediction_card_count: int = 0
    reference_only_card_count: int = 0
    rejected_card_count: int = 0
    feature_cards: list[EvidenceCard] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "official_policy_signal": round(self.official_policy_signal, 4),
            "plan_change_signal": round(self.plan_change_signal, 4),
            "quota_change_signal": round(self.quota_change_signal, 4),
            "major_group_restructure_signal": round(self.major_group_restructure_signal, 4),
            "publicity_heat_signal": round(self.publicity_heat_signal, 4),
            "sentiment_shock_signal": round(self.sentiment_shock_signal, 4),
            "evidence_confidence": round(self.evidence_confidence, 4),
            "prediction_ready": self.prediction_ready,
            "usable_prediction_card_count": self.usable_prediction_card_count,
            "reference_only_card_count": self.reference_only_card_count,
            "rejected_card_count": self.rejected_card_count,
            "warnings": list(self.warnings),
            "feature_cards": [card.to_dict() for card in self.feature_cards],
        }


def derive_research_evidence_signals(
    evidence_cards: Iterable[EvidenceCard | dict[str, Any]],
    *,
    scope_terms: Sequence[str] | None = None,
) -> ResearchEvidenceSignals:
    """Convert research/search cards into prediction-safe quant features."""
    raw_cards = [_card_dict(card) for card in evidence_cards]
    scoped_cards = [card for card in raw_cards if _matches_scope(card, scope_terms)]
    rejected = len(raw_cards) - len(scoped_cards)
    feature_cards: list[EvidenceCard] = []
    strengths = {
        "official_policy_signal": 0.0,
        "plan_change_signal": 0.0,
        "quota_change_signal": 0.0,
        "major_group_restructure_signal": 0.0,
        "publicity_heat_signal": 0.0,
        "sentiment_shock_signal": 0.0,
    }
    usable_count = 0
    reference_count = 0

    for card in scoped_cards:
        text = _text(card)
        strength = _base_strength(card)
        source_type = _source_type(card)
        usable = _usable_for_prediction(card)
        if usable:
            usable_count += 1
        else:
            reference_count += 1

        def add(signal_type: str, value: float, claim: str, prediction_allowed: bool) -> None:
            nonlocal feature_cards
            feature_cards.append(
                EvidenceCard(
                    signal_type=signal_type,
                    source_type=source_type,
                    value=value,
                    confidence=_clamp(float(card.get("confidence", 0.5) or 0.5)),
                    claim=claim,
                    source=str(card.get("source") or ""),
                    cutoff_date=str(card.get("cutoff_date") or ""),
                    usable_for_prediction=prediction_allowed,
                )
            )

        if usable and _contains(text, POLICY_KEYWORDS):
            strengths["official_policy_signal"] = max(strengths["official_policy_signal"], strength)
            add("official_policy_signal", strength, "Official/semi-official policy evidence matched.", True)
        if usable and _contains(text, PLAN_CHANGE_KEYWORDS):
            strengths["plan_change_signal"] = max(strengths["plan_change_signal"], strength)
            add("plan_change_signal", strength, "Official/semi-official plan-change evidence matched.", True)
        if usable and _contains(text, QUOTA_KEYWORDS):
            strengths["quota_change_signal"] = max(strengths["quota_change_signal"], strength)
            add("quota_change_signal", strength, "Official/semi-official quota-change evidence matched.", True)
        if usable and _contains(text, GROUP_RESTRUCTURE_KEYWORDS):
            strengths["major_group_restructure_signal"] = max(
                strengths["major_group_restructure_signal"],
                strength,
            )
            add(
                "major_group_restructure_signal",
                strength,
                "Official/semi-official major-group restructuring evidence matched.",
                True,
            )
        if _contains(text, PUBLICITY_KEYWORDS) or source_type in SOCIAL_SOURCE_TYPES:
            add("publicity_heat", strength, "Reference-only market heat evidence matched.", False)
            strengths["publicity_heat_signal"] = max(strengths["publicity_heat_signal"], strength)
        if _contains(text, SENTIMENT_KEYWORDS):
            add("sentiment_shock_discount", strength, "Reference-only sentiment shock evidence matched.", False)
            strengths["sentiment_shock_signal"] = max(strengths["sentiment_shock_signal"], strength)

    if scoped_cards:
        evidence_confidence = sum(_clamp(float(card.get("confidence", 0.5) or 0.5)) for card in scoped_cards) / len(scoped_cards)
    else:
        evidence_confidence = 0.0
    warnings: list[str] = []
    if reference_count and not usable_count:
        warnings.append("Only reference/social/manual cards matched; do not use them for admission prediction.")
    if rejected:
        warnings.append(f"{rejected} evidence cards were outside the row scope and ignored.")

    return ResearchEvidenceSignals(
        official_policy_signal=strengths["official_policy_signal"],
        plan_change_signal=strengths["plan_change_signal"],
        quota_change_signal=strengths["quota_change_signal"],
        major_group_restructure_signal=strengths["major_group_restructure_signal"],
        publicity_heat_signal=strengths["publicity_heat_signal"],
        sentiment_shock_signal=strengths["sentiment_shock_signal"],
        evidence_confidence=_clamp(evidence_confidence),
        prediction_ready=usable_count > 0,
        usable_prediction_card_count=usable_count,
        reference_only_card_count=reference_count,
        rejected_card_count=rejected,
        feature_cards=feature_cards,
        warnings=warnings,
    )

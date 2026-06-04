"""Evidence-card modeling for admission-market arbitrage signals.

This module turns public signals into auditable evidence cards. It is not a
search crawler by itself; external collectors can pass additional cards from
LLM/search pipelines, while the structured extractor handles enrollment-plan
and historical-feature signals already present on a MajorGroupRow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from models.game_matrix import MajorGroupRow, QuotaBucket
from models.user_profile import SchoolMajorPreference, UserProfile


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _contains_any(text: str, keywords: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


@dataclass(frozen=True)
class EvidenceCard:
    """One auditable piece of evidence behind a market signal."""

    signal_type: str
    source_type: str
    value: float
    confidence: float
    claim: str
    source: str = ""
    cutoff_date: str = ""
    usable_for_prediction: bool = True

    def to_dict(self) -> dict:
        return {
            "signal_type": self.signal_type,
            "source_type": self.source_type,
            "value": round(_clamp(self.value), 4),
            "confidence": round(_clamp(self.confidence), 4),
            "claim": self.claim,
            "source": self.source,
            "cutoff_date": self.cutoff_date,
            "usable_for_prediction": self.usable_for_prediction,
        }


@dataclass(frozen=True)
class MarketEvidenceAssessment:
    """Aggregated market evidence used by the arbitrage model."""

    cards: list[EvidenceCard] = field(default_factory=list)
    tuition_filter: float = 0.0
    campus_discount: float = 0.0
    cold_major_discount: float = 0.0
    group_restructure_score: float = 0.0
    historical_anchor_overdeterrence: float = 0.0
    quota_pressure: float = 0.0
    low_attention_signal: float = 0.0
    publicity_heat_score: float = 0.0
    sentiment_shock_discount: float = 0.0
    market_discount_score: float = 0.0
    rebound_risk: float = 0.0
    evidence_strength: float = 0.0

    def card_dicts(self) -> list[dict]:
        return [card.to_dict() for card in self.cards]


def tuition_filter_score(row: MajorGroupRow) -> float:
    tuitions = [
        float(option.tuition)
        for option in row.major_options
        if option.tuition is not None and float(option.tuition) > 0
    ]
    if not tuitions:
        return 0.0
    max_tuition = max(tuitions)
    if max_tuition >= 60_000:
        return 0.90
    if max_tuition >= 30_000:
        return 0.65
    if max_tuition >= 15_000:
        return 0.35
    return 0.10


def campus_discount_score(row: MajorGroupRow) -> float:
    text = f"{row.school_name} {' '.join(row.major_list)} " + " ".join(
        str(option.remarks or "") for option in row.major_options
    )
    if _contains_any(
        text,
        (
            "panjin",
            "weihai",
            "zhuhai",
            "hainan",
            "campus",
            "branch",
            "joint program",
            "cooperation",
            "鐩橀敠",
            "濞佹捣",
            "鐝犳捣",
            "娴峰崡",
            "寮傚湴",
            "鏍″尯",
            "鍒嗘牎",
        ),
    ):
        return 0.65
    return 0.0


def cold_major_discount_score(row: MajorGroupRow) -> float:
    cold_keywords = (
        "environment",
        "chemistry",
        "material",
        "biology",
        "pharmacy",
        "tourism",
        "management",
        "philosophy",
        "history",
        "sociology",
        "agriculture",
        "forestry",
        "geology",
        "mining",
        "鐜",
        "鍖栧",
        "鏉愭枡",
        "鐢熺墿",
        "鏃呮父",
        "绠＄悊",
        "鍝插",
        "鍘嗗彶",
        "鍐滃",
        "鏋楀",
        "鍦拌川",
        "鐭夸笟",
    )
    if not row.major_list:
        return 0.0
    cold_count = sum(1 for major in row.major_list if _contains_any(major, cold_keywords))
    return _clamp(cold_count / len(row.major_list))


def _weighted_average(values: Iterable[tuple[float, float]]) -> float:
    numerator = 0.0
    denominator = 0.0
    for value, weight in values:
        numerator += _clamp(value) * max(0.0, weight)
        denominator += max(0.0, weight)
    return _clamp(numerator / denominator) if denominator else 0.0


def _card(signal_type: str, source_type: str, value: float, confidence: float, claim: str) -> EvidenceCard:
    return EvidenceCard(
        signal_type=signal_type,
        source_type=source_type,
        value=value,
        confidence=confidence,
        claim=claim,
        source="structured_public_fields",
    )


def build_decision_evidence_cards(
    *,
    row: MajorGroupRow,
    profile: UserProfile,
    assessment: MarketEvidenceAssessment,
) -> list[EvidenceCard]:
    """Build decision-grade cards explaining why this opportunity fits."""
    cards: list[EvidenceCard] = []
    top_discount = max(
        (
            ("tuition_filter", assessment.tuition_filter),
            ("campus_discount", assessment.campus_discount),
            ("cold_major_discount", assessment.cold_major_discount),
            ("historical_anchor_overdeterrence", assessment.historical_anchor_overdeterrence),
            ("low_attention_signal", assessment.low_attention_signal),
        ),
        key=lambda item: item[1],
    )
    front_signal = max(row.front_major_arbitrage_score, row.front_major_hit_prob * row.major_utility_mean)
    thesis_value = _clamp(
        0.38 * assessment.market_discount_score
        + 0.28 * row.arbitrage_score
        + 0.20 * front_signal
        + 0.14 * row.admission_prob
    )
    cards.append(
        _card(
            "opportunity_thesis",
            "model_summary",
            thesis_value,
            max(0.55, assessment.evidence_strength),
            (
                f"Primary leak mechanism is {top_discount[0]}={top_discount[1]:.2f}; "
                f"admission_prob={row.admission_prob:.2f}, arbitrage_score={row.arbitrage_score:.2f}."
            ),
        )
    )

    major_first = profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_MAJOR
    school_first = profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_SCHOOL
    fit_value = _clamp(
        0.36 * row.personal_acceptability
        + 0.30 * row.major_utility_mean
        + 0.20 * row.relative_lift
        + 0.14 * (1 - row.sacrifice_cost)
    )
    fit_reason = "major utility" if major_first else ("school/tier lift" if school_first else "balanced fit")
    cards.append(
        _card(
            "student_fit",
            "personalized_model",
            fit_value,
            0.72,
            (
                f"Student fit is driven by {fit_reason}; acceptability={row.personal_acceptability:.2f}, "
                f"sacrifice_cost={row.sacrifice_cost:.2f}, relative_lift={row.relative_lift:.2f}."
            ),
        )
    )

    downside = _clamp(
        0.45 * row.tail_assignment_risk
        + 0.30 * max(row.rebound_risk, row.publicity_rebound_risk, row.segment_rebound_risk)
        + (0.25 if row.is_blacklist_risk else 0.0)
    )
    cards.append(
        _card(
            "downside_guard",
            "risk_model",
            downside,
            0.78,
            (
                f"Downside guard: tail_risk={row.tail_assignment_risk:.2f}, "
                f"rebound_risk={max(row.rebound_risk, row.publicity_rebound_risk, row.segment_rebound_risk):.2f}, "
                f"blacklist={row.is_blacklist_risk}."
            ),
        )
    )
    return cards


def assess_market_evidence(
    row: MajorGroupRow,
    *,
    external_cards: Sequence[EvidenceCard] | None = None,
) -> MarketEvidenceAssessment:
    """Build evidence cards and aggregate market signals for one group."""
    cards: list[EvidenceCard] = []
    tuition = tuition_filter_score(row)
    campus = campus_discount_score(row)
    cold_major = cold_major_discount_score(row)
    external_cards = list(external_cards or [])
    research_group_restructure = max(
        (
            card.value * card.confidence
            for card in external_cards
            if card.usable_for_prediction and card.signal_type == "major_group_restructure_signal"
        ),
        default=0.0,
    )
    research_plan_change = max(
        (
            card.value * card.confidence
            for card in external_cards
            if card.usable_for_prediction and card.signal_type == "plan_change_signal"
        ),
        default=0.0,
    )
    research_quota_change = max(
        (
            card.value * card.confidence
            for card in external_cards
            if card.usable_for_prediction and card.signal_type == "quota_change_signal"
        ),
        default=0.0,
    )
    group_restructure = max(_clamp(row.major_utility_dispersion), _clamp(research_group_restructure))
    historical_anchor = _clamp(
        0.35 * row.variance_opportunity_score
        + 0.35 * row.major_utility_dispersion
        + 0.30 * (1 - row.admission_prob)
    )
    quota_pressure = max(0.55 if row.quota_bucket == QuotaBucket.SMALL else 0.0, _clamp(research_quota_change))

    if tuition >= 0.30:
        cards.append(_card("tuition_filter", "enrollment_plan", tuition, 0.90, "High tuition can filter demand."))
    if campus >= 0.30:
        cards.append(_card("campus_discount", "enrollment_plan", campus, 0.82, "Campus/pathway label can depress demand."))
    if cold_major >= 0.30:
        cards.append(_card("cold_major_discount", "major_group_structure", cold_major, 0.72, "Group contains cold or hard-to-price majors."))
    if group_restructure >= 0.25:
        cards.append(_card("group_restructure", "major_group_structure", group_restructure, 0.65, "In-group utility dispersion suggests mixed-bundle risk."))
    if historical_anchor >= 0.45:
        cards.append(_card("historical_anchor_overdeterrence", "historical_admission", historical_anchor, 0.62, "Historical line may over-deter applicants."))
    if quota_pressure >= 0.45:
        cards.append(_card("quota_pressure", "enrollment_plan", quota_pressure, 0.70, "Small quota increases volatility and opportunity dispersion."))

    if research_plan_change >= 0.25:
        cards.append(
            _card(
                "plan_change_signal",
                "research_evidence",
                research_plan_change,
                0.70,
                "Official/semi-official research evidence indicates enrollment-plan change.",
            )
        )

    for external in external_cards:
        cards.append(external)

    publicity_heat = max((card.value * card.confidence for card in cards if card.signal_type == "publicity_heat"), default=0.0)
    sentiment_shock = max((card.value * card.confidence for card in cards if card.signal_type == "sentiment_shock_discount"), default=0.0)
    low_attention = _clamp(max(tuition, campus, cold_major) * 0.55 + row.variance_opportunity_score * 0.25 - publicity_heat * 0.30)
    market_discount = _weighted_average(
        (
            (tuition, 0.16),
            (campus, 0.14),
            (cold_major, 0.16),
            (group_restructure, 0.12),
            (historical_anchor, 0.18),
            (quota_pressure, 0.10),
            (research_plan_change, 0.08),
            (low_attention, 0.10),
            (sentiment_shock, 0.04),
        )
    )
    if cards:
        evidence_strength = _clamp(sum(card.confidence for card in cards) / len(cards))
    else:
        evidence_strength = 0.30 if row.major_options else 0.15

    rebound_risk = _clamp(
        0.12
        + 0.45 * publicity_heat
        + 0.18 * (1 - row.quota_stability_score)
        + 0.12 * quota_pressure
        + 0.10 * research_plan_change
        - 0.14 * low_attention
    )

    return MarketEvidenceAssessment(
        cards=cards,
        tuition_filter=tuition,
        campus_discount=campus,
        cold_major_discount=cold_major,
        group_restructure_score=group_restructure,
        historical_anchor_overdeterrence=historical_anchor,
        quota_pressure=quota_pressure,
        low_attention_signal=low_attention,
        publicity_heat_score=_clamp(publicity_heat),
        sentiment_shock_discount=_clamp(sentiment_shock),
        market_discount_score=market_discount,
        rebound_risk=rebound_risk,
        evidence_strength=evidence_strength,
    )

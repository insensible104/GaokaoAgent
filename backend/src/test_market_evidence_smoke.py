"""Smoke tests for explicit market-evidence modeling."""

from __future__ import annotations

from models.game_matrix import MajorGroupRow, MajorOption, QuotaBucket, StrategyTag, VolatilityLevel
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from recommendation.arbitrage_adapter import score_major_group_arbitrage
from recommendation.market_evidence import EvidenceCard, assess_market_evidence


def _row() -> MajorGroupRow:
    options = [
        MajorOption(
            school_code="90001",
            school_name="Brand Institute",
            major_group_code="801",
            major_name="Environmental Engineering",
            plan_quota=2,
            tuition=80000,
            remarks="Hainan campus, joint program",
            user_utility=0.62,
        ),
        MajorOption(
            school_code="90001",
            school_name="Brand Institute",
            major_group_code="801",
            major_name="Pharmacy",
            plan_quota=2,
            tuition=80000,
            remarks="Hainan campus, joint program",
            user_utility=0.60,
        ),
    ]
    return MajorGroupRow(
        school_name="Brand Institute",
        school_code="90001",
        major_group_code="801",
        major_list=[option.major_name for option in options],
        major_count=len(options),
        major_options=options,
        suggested_major_choices=options,
        admission_prob=0.62,
        min_rank_pred=18000,
        rank_diff=-2500,
        rank_ci_lower=15000,
        rank_ci_upper=23000,
        fear_index=0.0,
        volatility=VolatilityLevel.HIGH,
        quota=4,
        quota_bucket=QuotaBucket.SMALL,
        quota_stability_score=0.35,
        variance_opportunity_score=0.75,
        adjustment_risk=0.35,
        tail_assignment_risk=0.32,
        major_utility_mean=0.61,
        major_utility_min=0.60,
        major_utility_dispersion=0.02,
        strategy_tag=StrategyTag.TARGET,
        comprehensive_score=0.58,
    )


def _profile() -> UserProfile:
    return UserProfile(
        score=590,
        rank=18888,
        subject_group="physics",
        preferred_majors=["Environmental"],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_SCHOOL,
    )


def test_structured_market_evidence_cards_are_generated_from_public_fields():
    assessment = assess_market_evidence(_row())

    signal_types = {card.signal_type for card in assessment.cards}

    assert "tuition_filter" in signal_types
    assert "campus_discount" in signal_types
    assert "cold_major_discount" in signal_types
    assert "quota_pressure" in signal_types
    assert assessment.market_discount_score > 0.45
    assert assessment.evidence_strength >= 0.60


def test_external_publicity_evidence_increases_rebound_risk():
    base = assess_market_evidence(_row())
    external = EvidenceCard(
        signal_type="publicity_heat",
        source_type="livestream",
        value=0.90,
        confidence=0.80,
        claim="This group was heavily promoted by counselors before application deadline.",
        source="manual_public_observation",
    )

    with_external = assess_market_evidence(_row(), external_cards=[external])

    assert with_external.publicity_heat_score > base.publicity_heat_score
    assert with_external.rebound_risk > base.rebound_risk
    assert any(card.signal_type == "publicity_heat" for card in with_external.cards)


def test_market_evidence_is_attached_to_arbitrage_scored_rows():
    row = _row()

    score_major_group_arbitrage(
        row=row,
        profile=_profile(),
        school_major_score=0.78,
        city_preference_score=0.55,
    )

    assert row.market_evidence_strength > 0
    assert row.publicity_rebound_risk >= 0
    assert row.market_evidence_cards
    assert "tuition_filter" in {card["signal_type"] for card in row.market_evidence_cards}


def test_arbitrage_rows_include_decision_grade_opportunity_cards():
    row = _row()

    score_major_group_arbitrage(
        row=row,
        profile=_profile(),
        school_major_score=0.78,
        city_preference_score=0.55,
    )

    signal_types = {card["signal_type"] for card in row.market_evidence_cards}
    opportunity_card = next(
        card for card in row.market_evidence_cards if card["signal_type"] == "opportunity_thesis"
    )

    assert "opportunity_thesis" in signal_types
    assert "student_fit" in signal_types
    assert "downside_guard" in signal_types
    assert row.arbitrage_score > 0
    assert f"arbitrage_score={row.arbitrage_score:.2f}" in opportunity_card["claim"]
    assert all(card["claim"] for card in row.market_evidence_cards)


if __name__ == "__main__":
    test_structured_market_evidence_cards_are_generated_from_public_fields()
    test_external_publicity_evidence_increases_rebound_risk()
    test_market_evidence_is_attached_to_arbitrage_scored_rows()
    test_arbitrage_rows_include_decision_grade_opportunity_cards()
    print("market evidence smoke tests passed")

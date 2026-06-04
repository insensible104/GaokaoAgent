"""Smoke tests for game-agent score normalization."""

import pandas as pd

from agents.game_agent import (
    _extract_research_evidence_cards,
    _limit_precision_candidates,
    _normalize_percent_score,
    _score_row_arbitrage,
)
from models.game_matrix import MajorGroupRow, MajorOption, StrategyTag, VolatilityLevel
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


def test_normalize_percent_score_clamps_to_schema_range() -> None:
    assert _normalize_percent_score(102.86) == 1.0
    assert _normalize_percent_score(72.5) == 0.725
    assert _normalize_percent_score(-4.0) == 0.0


def test_precision_candidate_limit_keeps_rank_bands() -> None:
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_cities=["广州", "深圳"],
        preferred_majors=["计算机"],
    )
    rows = []
    for idx, min_rank in enumerate(range(2000, 50000, 1200)):
        rows.append(
            {
                "school": "深圳大学" if idx % 7 == 0 else f"测试大学{idx}",
                "school_code": f"{10000 + idx}",
                "major_group": str(200 + idx),
                "major": ["计算机类"] if idx % 5 == 0 else ["管理类"],
                "min_rank": min_rank,
                "quota": 20 + idx,
            }
        )

    limited = _limit_precision_candidates(
        pd.DataFrame(rows),
        profile,
        total_recommend=2,
        max_candidates=12,
    )

    assert len(limited) == 12
    rank_diffs = limited["min_rank"] - profile.rank
    assert any(rank_diffs < 0)
    assert any((rank_diffs >= 0) & (rank_diffs <= 6000))
    assert any(rank_diffs > 6000)


def test_game_agent_arbitrage_helper_consumes_research_evidence_cards() -> None:
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="physics",
        preferred_majors=["computer"],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.BALANCED,
    )
    option = MajorOption(
        school_code="90001",
        school_name="Evidence University",
        major_group_code="801",
        major_name="computer science",
        plan_quota=12,
        user_utility=0.85,
    )
    row = MajorGroupRow(
        school_name="Evidence University",
        school_code="90001",
        major_group_code="801",
        major_list=["computer science"],
        major_count=1,
        major_options=[option],
        suggested_major_choices=[option],
        admission_prob=0.62,
        min_rank_pred=12500,
        rank_diff=500,
        rank_ci_lower=11000,
        rank_ci_upper=14000,
        volatility=VolatilityLevel.MEDIUM,
        adjustment_risk=0.10,
        tail_assignment_risk=0.10,
        major_utility_mean=0.85,
        major_utility_min=0.85,
        strategy_tag=StrategyTag.TARGET,
        comprehensive_score=0.72,
    )
    state = {
        "research_evidence_cards": [
            {
                "signal_type": "external_research",
                "source_type": "official_or_school",
                "value": 0.80,
                "confidence": 0.90,
                "claim": "Evidence University 801 招生计划 扩招，院校专业组调整，招生人数增加。",
                "source": "https://admission.evidence.example/plan",
                "usable_for_prediction": True,
            },
            "bad-card",
        ]
    }

    cards = _extract_research_evidence_cards(state)
    _score_row_arbitrage(
        row=row,
        profile=profile,
        school_major_score=0.75,
        city_preference_score=1.0,
        research_evidence_cards=cards,
    )

    assert len(cards) == 1
    assert row.plan_change_score > 0
    assert "research_plan_change" in row.plan_change_types
    assert any(card["signal_type"] == "plan_change_signal" for card in row.market_evidence_cards)


if __name__ == "__main__":
    test_normalize_percent_score_clamps_to_schema_range()
    test_precision_candidate_limit_keeps_rank_bands()
    test_game_agent_arbitrage_helper_consumes_research_evidence_cards()
    print("game agent score bounds smoke tests passed")

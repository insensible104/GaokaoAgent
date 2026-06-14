"""Smoke tests for game-agent score normalization."""

import pandas as pd

from agents.game_agent import (
    _extract_research_evidence_cards,
    _limit_precision_candidates,
    _normalize_percent_score,
    _score_row_arbitrage,
    refresh_game_matrix_research_evidence,
)
from models.game_matrix import GameMatrix, MajorGroupRow, MajorOption, StrategyTag, VolatilityLevel
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from recommendation.major_choice_planner import build_volunteer_plan


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


def test_late_research_refresh_updates_game_matrix_and_volunteer_plan() -> None:
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
        tradeoff_breakdown={"school_value": 0.75, "city_value": 0.50},
    )
    matrix = GameMatrix(
        major_group_rows=[row],
        volunteer_plan=build_volunteer_plan([row], profile, optimize_prefix=False),
    )
    state = {
        "user_profile": profile,
        "game_matrix": matrix,
        "research_evidence_cards": [
            {
                "signal_type": "external_research",
                "source_type": "official_or_school",
                "value": 0.80,
                "confidence": 0.90,
                "claim": "Evidence University 801 招生计划 扩招，院校专业组调整，招生人数增加。",
                "source": "https://admission.evidence.example/plan",
                "usable_for_prediction": True,
            }
        ],
    }

    update = refresh_game_matrix_research_evidence(state)
    refreshed_matrix = update["game_matrix"]
    refreshed_row = refreshed_matrix.major_group_rows[0]
    refreshed_choice = refreshed_matrix.volunteer_plan.choices[0]

    assert update["current_agent"] == "research_evidence_refresh"
    assert refreshed_row.plan_change_score > 0
    assert refreshed_row.decision_trace["summary"]
    assert refreshed_row.decision_trace["confidence_level"] == "low"
    assert any(card["signal_type"] == "plan_change_signal" for card in refreshed_row.market_evidence_cards)
    assert any(card["signal_type"] == "plan_change_signal" for card in refreshed_choice.market_evidence_cards)

    second_update = refresh_game_matrix_research_evidence({**state, "game_matrix": refreshed_matrix})
    second_row = second_update["game_matrix"].major_group_rows[0]
    keys = [
        (card["signal_type"], card.get("source"), card.get("claim"))
        for card in second_row.market_evidence_cards
    ]
    assert len(keys) == len(set(keys))


def test_late_research_refresh_preserves_prefix_strategy_order() -> None:
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="physics",
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.BALANCED,
    )
    base = MajorGroupRow(
        school_name="Base University",
        school_code="90001",
        major_group_code="801",
        major_list=["computer science"],
        major_count=1,
        admission_prob=0.55,
        min_rank_pred=12500,
        rank_diff=500,
        rank_ci_lower=11000,
        rank_ci_upper=14000,
        volatility=VolatilityLevel.MEDIUM,
        tail_assignment_risk=0.10,
        major_utility_mean=0.70,
        major_utility_min=0.70,
        strategy_tag=StrategyTag.TARGET,
        comprehensive_score=0.70,
        tradeoff_breakdown={"school_value": 0.70, "city_value": 0.50},
    )
    rush = base.model_copy(
        update={"school_name": "Rush University", "school_code": "90002", "strategy_tag": StrategyTag.RUSH}
    )
    target = base.model_copy(
        update={"school_name": "Target University", "school_code": "90003", "strategy_tag": StrategyTag.TARGET}
    )
    safe = base.model_copy(
        update={"school_name": "Safe University", "school_code": "90004", "strategy_tag": StrategyTag.SAFE}
    )
    rows = [safe, target, rush]
    matrix = GameMatrix(
        major_group_rows=rows,
        volunteer_plan=build_volunteer_plan(rows, profile, optimize_prefix=True),
    )
    state = {
        "user_profile": profile,
        "game_matrix": matrix,
        "research_evidence_cards": [
            {
                "signal_type": "external_research",
                "source_type": "official_or_school",
                "value": 0.8,
                "confidence": 0.9,
                "claim": "2026 招生计划已更新。",
                "source": "https://example.edu/plan",
                "usable_for_prediction": True,
            }
        ],
    }

    refreshed = refresh_game_matrix_research_evidence(state)["game_matrix"]

    assert [choice.strategy_tag for choice in refreshed.volunteer_plan.choices] == [
        StrategyTag.RUSH,
        StrategyTag.TARGET,
        StrategyTag.SAFE,
    ]


if __name__ == "__main__":
    test_normalize_percent_score_clamps_to_schema_range()
    test_precision_candidate_limit_keeps_rank_bands()
    test_game_agent_arbitrage_helper_consumes_research_evidence_cards()
    test_late_research_refresh_updates_game_matrix_and_volunteer_plan()
    test_late_research_refresh_preserves_prefix_strategy_order()
    print("game agent score bounds smoke tests passed")

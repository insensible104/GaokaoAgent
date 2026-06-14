"""Smoke tests for strategy-aware Pareto retention and coverage reporting."""

from models.game_matrix import MajorGroupRow, StrategyTag, VolatilityLevel
from recommendation.strategy_coverage import (
    build_coverage_report,
    count_strategy_rows,
    fill_plan_capacity,
    retain_strategy_candidates,
)
from agents.game_agent import _prepare_strategy_candidate_pool


def _row(tag: StrategyTag, index: int) -> MajorGroupRow:
    base_probability = {
        StrategyTag.RUSH: 0.38,
        StrategyTag.TARGET: 0.72,
        StrategyTag.SAFE: 0.92,
    }[tag]
    return MajorGroupRow(
        school_name=f"{tag.value}-{index}",
        school_code=f"{tag.value}-{index}",
        major_group_code=str(200 + index),
        major_list=["Test Major"],
        admission_prob=min(0.99, base_probability + index * 0.002),
        min_rank_pred=12000 + index * 100,
        rank_ci_lower=10000,
        rank_ci_upper=15000,
        volatility=VolatilityLevel.MEDIUM,
        adjustment_risk=max(0.0, 0.20 - index * 0.005),
        strategy_tag=tag,
        comprehensive_score=min(0.99, 0.60 + index * 0.01),
    )


def test_strategy_aware_retention_preserves_requested_bucket_capacity() -> None:
    rows = [
        *[_row(StrategyTag.RUSH, index) for index in range(12)],
        *[_row(StrategyTag.TARGET, index) for index in range(12)],
        *[_row(StrategyTag.SAFE, index) for index in range(12)],
    ]
    desired = {"rush": 3, "target": 4, "safe": 3}

    retained = retain_strategy_candidates(rows, desired=desired, reserve=2)
    counts = count_strategy_rows(retained)

    assert counts == {"rush": 5, "target": 6, "safe": 5}


def test_coverage_report_exposes_unfilled_strategy_deficit() -> None:
    classified = [
        *[_row(StrategyTag.RUSH, index) for index in range(4)],
        *[_row(StrategyTag.TARGET, index) for index in range(2)],
        *[_row(StrategyTag.SAFE, index) for index in range(3)],
    ]
    selected = [classified[0], classified[1], classified[4], classified[6], classified[7]]

    report = build_coverage_report(
        desired={"rush": 2, "target": 3, "safe": 2},
        classified_rows=classified,
        post_pareto_rows=classified,
        selected_rows=selected,
    )

    assert report["coverage_sufficient"] is False
    assert report["deficits"] == {"target": 2}
    assert report["classified"] == {"rush": 4, "target": 2, "safe": 3}
    assert any("target" in action for action in report["actions"])


def test_game_agent_prepares_strategy_aware_candidate_pool() -> None:
    rows = [
        *[_row(StrategyTag.RUSH, index) for index in range(8)],
        *[_row(StrategyTag.TARGET, index) for index in range(8)],
        *[_row(StrategyTag.SAFE, index) for index in range(8)],
    ]

    retained = _prepare_strategy_candidate_pool(
        rows,
        desired={"rush": 3, "target": 3, "safe": 2},
        reserve=1,
    )

    assert count_strategy_rows(retained) == {"rush": 4, "target": 4, "safe": 3}


def test_capacity_fill_preserves_strategy_labels_and_reports_fill_count() -> None:
    target = _row(StrategyTag.TARGET, 1)
    selected = [target]
    remaining = [
        _row(StrategyTag.RUSH, 2),
        _row(StrategyTag.SAFE, 3),
        _row(StrategyTag.RUSH, 4),
    ]

    filled, summary = fill_plan_capacity(
        selected_rows=selected,
        all_rows=[target, *remaining],
        total_count=3,
    )

    assert len(filled) == 3
    assert summary == {
        "requested_count": 3,
        "initial_count": 1,
        "filled_count": 2,
        "final_count": 3,
        "remaining_shortfall": 0,
    }
    assert count_strategy_rows(filled) == {"rush": 1, "target": 1, "safe": 1}
    assert target.strategy_tag == StrategyTag.TARGET


if __name__ == "__main__":
    test_strategy_aware_retention_preserves_requested_bucket_capacity()
    test_coverage_report_exposes_unfilled_strategy_deficit()
    test_game_agent_prepares_strategy_aware_candidate_pool()
    print("strategy coverage smoke tests passed")

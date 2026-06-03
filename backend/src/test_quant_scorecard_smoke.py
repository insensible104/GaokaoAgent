"""Smoke tests for deterministic quant scorecards."""

import pandas as pd

from recommendation.quant_scorecard import build_quant_scorecard


def test_quant_scorecard_labels_safe_anchor_with_stable_buffer() -> None:
    hist = pd.DataFrame(
        {
            "year": [2021, 2022, 2023, 2024],
            "min_rank": [15000, 15400, 15800, 16200],
        }
    )

    scorecard = build_quant_scorecard(
        hist_data=hist,
        user_rank=12000,
        min_rank_pred=15600,
        rank_ci_lower=14500,
        rank_ci_upper=16700,
        quota_stability=0.85,
    )

    assert scorecard.deterministic_risk_band == "safe_anchor"
    assert scorecard.rank_buffer_score > 0.8
    assert scorecard.data_confidence_score > 0.6
    assert scorecard.quant_score > 0.7
    assert scorecard.evidence


def test_quant_scorecard_labels_boundary_rush_when_buffer_is_negative() -> None:
    hist = pd.DataFrame(
        {
            "year": [2021, 2022, 2023, 2024],
            "min_rank": [10800, 11200, 11600, 12000],
        }
    )

    scorecard = build_quant_scorecard(
        hist_data=hist,
        user_rank=12000,
        min_rank_pred=11600,
        rank_ci_lower=10800,
        rank_ci_upper=12400,
        quota_stability=0.65,
    )

    assert scorecard.deterministic_risk_band == "boundary_rush"
    assert scorecard.rank_buffer < 0
    assert scorecard.rank_buffer_score < 0.5


if __name__ == "__main__":
    test_quant_scorecard_labels_safe_anchor_with_stable_buffer()
    test_quant_scorecard_labels_boundary_rush_when_buffer_is_negative()
    print("quant scorecard smoke tests passed")

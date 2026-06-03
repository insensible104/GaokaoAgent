"""Smoke tests for offline quant-weight tuning."""

from __future__ import annotations

from evaluation.quant_tuning import (
    build_markdown_quant_tuning_report,
    tune_quant_probability_blends,
)


def test_quant_tuning_can_improve_over_raw_probability() -> None:
    rows = [
        {
            "predicted_prob": 0.80,
            "quant_score": 0.20,
            "rank_buffer_score": 0.20,
            "history_stability_score": 0.40,
            "data_confidence_score": 0.50,
            "trend_score": 0.50,
            "group_admitted": False,
        },
        {
            "predicted_prob": 0.75,
            "quant_score": 0.25,
            "rank_buffer_score": 0.25,
            "history_stability_score": 0.40,
            "data_confidence_score": 0.50,
            "trend_score": 0.50,
            "group_admitted": False,
        },
        {
            "predicted_prob": 0.35,
            "quant_score": 0.95,
            "rank_buffer_score": 0.90,
            "history_stability_score": 0.80,
            "data_confidence_score": 0.80,
            "trend_score": 0.70,
            "group_admitted": True,
        },
        {
            "predicted_prob": 0.30,
            "quant_score": 0.90,
            "rank_buffer_score": 0.85,
            "history_stability_score": 0.80,
            "data_confidence_score": 0.80,
            "trend_score": 0.70,
            "group_admitted": True,
        },
    ]
    result = tune_quant_probability_blends(
        choice_rows=rows,
        step=0.20,
        min_prob_weight=0.40,
        top_k=5,
    )

    assert result["choice_count"] == 4
    assert result["best"]["brier_score"] < result["baseline"]["brier_score"]
    assert result["best"]["weights"].get("quant_score", 0.0) > 0.0
    markdown = build_markdown_quant_tuning_report(result)
    assert "Quant Probability Tuning Report" in markdown
    assert "Top Candidates" in markdown


if __name__ == "__main__":
    test_quant_tuning_can_improve_over_raw_probability()
    print("quant tuning smoke tests passed")

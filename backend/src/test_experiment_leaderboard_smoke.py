"""Smoke tests for QuantLab cross-experiment leaderboards."""

from __future__ import annotations

from evaluation.experiment_leaderboard import (
    build_markdown_quant_lab_leaderboard,
    build_quant_lab_leaderboard,
)
from evaluation.quant_lab import build_quant_lab_experiment


def _manifest(
    experiment_id: str,
    *,
    success_rate: float,
    sliding_rate: float,
    preferred_rate: float,
    failure_rate: float,
    replay_count: int,
    p0_count: int,
) -> dict:
    return build_quant_lab_experiment(
        experiment_id=experiment_id,
        backtest_summary={
            "case_count": 10,
            "success_rate": success_rate,
            "sliding_rate": sliding_rate,
            "preferred_major_hit_rate": preferred_rate,
            "blacklist_hit_rate": 0.0,
            "tail_assignment_rate": 0.1,
            "average_assigned_major_utility": 0.6,
        },
        calibration_summary={
            "overall": {
                "brier_score": 0.1,
            }
        },
        failure_mining={
            "failure_case_rate": failure_rate,
        },
        replay_queue_summary={
            "queue_count": replay_count,
            "source_case_count": replay_count,
            "missing_case_count": 0,
            "items": [
                {
                    "case_id": f"{experiment_id}_p0_{index}",
                    "replay_metadata": {"priority": "P0"},
                }
                for index in range(p0_count)
            ],
        },
    )


def test_quant_lab_leaderboard_ranks_and_attaches_replay_metrics():
    baseline = _manifest(
        "baseline",
        success_rate=0.70,
        sliding_rate=0.20,
        preferred_rate=0.40,
        failure_rate=0.30,
        replay_count=5,
        p0_count=2,
    )
    candidate = _manifest(
        "candidate",
        success_rate=0.80,
        sliding_rate=0.10,
        preferred_rate=0.50,
        failure_rate=0.12,
        replay_count=3,
        p0_count=1,
    )

    result = build_quant_lab_leaderboard(
        [baseline, candidate],
        baseline_experiment_id="baseline",
    )
    markdown = build_markdown_quant_lab_leaderboard(result)

    top = result["rows"][0]
    assert top["experiment_id"] == "candidate"
    assert top["rank"] == 1
    assert top["success_rate_delta_vs_baseline"] > 0
    assert top["failure_case_rate_delta_vs_baseline"] < 0
    assert top["replay_queue_count"] == 3.0
    assert top["replay_p0_count"] == 1.0
    assert "QuantLab Experiment Leaderboard" in markdown


if __name__ == "__main__":
    test_quant_lab_leaderboard_ranks_and_attaches_replay_metrics()
    print("experiment leaderboard smoke tests passed")

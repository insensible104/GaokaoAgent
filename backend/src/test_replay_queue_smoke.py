"""Smoke tests for failure replay queues."""

from __future__ import annotations

from evaluation.failure_mining import mine_ablation_failure_deltas, mine_backtest_failures
from evaluation.replay_queue import build_failure_replay_queue, build_markdown_replay_queue


def test_failure_replay_queue_preserves_records_and_metadata():
    records = [
        {"case_id": "slide_case", "plan": {"choices": []}, "user_rank": 120000},
        {"case_id": "unsafe_case", "plan": {"choices": []}, "user_rank": 30000},
    ]
    failure_mining = mine_backtest_failures(
        [
            {
                "case_id": "slide_case",
                "success": False,
                "sliding": True,
                "preferred_major_hit": False,
                "blacklist_hit": False,
                "tail_assignment_hit": False,
                "choice_outcomes": [],
            },
            {
                "case_id": "missing_case",
                "success": True,
                "sliding": False,
                "preferred_major_hit": False,
                "blacklist_hit": False,
                "tail_assignment_hit": False,
                "choice_outcomes": [],
            },
        ]
    )
    ablation_deltas = mine_ablation_failure_deltas(
        [
            {
                "case_id": "unsafe_case",
                "variant": "full",
                "success": True,
                "sliding": False,
                "preferred_major_hit": True,
                "blacklist_hit": False,
                "tail_assignment_hit": False,
            },
            {
                "case_id": "unsafe_case",
                "variant": "unsafe_variant",
                "success": True,
                "sliding": False,
                "preferred_major_hit": True,
                "blacklist_hit": True,
                "tail_assignment_hit": True,
            },
            {
                "case_id": "slide_case",
                "variant": "full",
                "success": False,
                "sliding": True,
                "preferred_major_hit": False,
                "blacklist_hit": False,
                "tail_assignment_hit": False,
            },
            {
                "case_id": "slide_case",
                "variant": "unsafe_variant",
                "success": True,
                "sliding": False,
                "preferred_major_hit": False,
                "blacklist_hit": True,
                "tail_assignment_hit": False,
            },
        ]
    )

    queue = build_failure_replay_queue(
        records,
        failure_mining=failure_mining,
        ablation_failure_deltas=ablation_deltas,
        top_k=10,
    )
    markdown = build_markdown_replay_queue(queue)

    assert queue["queue_count"] == 2
    assert queue["missing_case_ids"] == ["missing_case"]
    by_case = {item["case_id"]: item["replay_metadata"] for item in queue["items"]}
    assert by_case["slide_case"]["priority"] == "P0"
    assert "sliding" in by_case["slide_case"]["failure_reasons"]
    assert "blacklist_hit" in by_case["slide_case"]["failure_reasons"]
    assert "hard_constraint_enforcement" in by_case["unsafe_case"]["recommended_focus"]
    assert {source["source"] for source in by_case["slide_case"]["sources"]} == {
        "backtest_failure",
        "ablation_regression",
    }
    assert "Failure Replay Queue" in markdown


if __name__ == "__main__":
    test_failure_replay_queue_preserves_records_and_metadata()
    print("replay queue smoke tests passed")

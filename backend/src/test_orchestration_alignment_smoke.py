"""Smoke test for orchestration alignment dataset export and action ranker training."""

from __future__ import annotations

from pathlib import Path
import tempfile

from rl.orchestration_alignment import (
    SupervisorActionRanker,
    build_grpo_tasks_from_rollouts,
    build_preference_examples,
    build_sft_examples_from_rollouts,
)


PAIRWISE_RECORDS = [
    {
        "case_id": "C1",
        "message": "帮我看看要不要继续调研",
        "stage": "after_game",
        "observation": {
            "active_loop": "fast",
            "intent_type": "mixed",
            "requires_search": True,
            "candidate_count": 8,
            "safe_count": 0,
            "target_count": 4,
            "rush_count": 4,
            "retry_count": 0,
            "research_loop_count": 0,
            "has_deep_research_trigger": True,
        },
        "chosen_action": "deep_research",
        "rejected_action": "report_agent",
        "margin": 0.8,
    },
    {
        "case_id": "C2",
        "message": "方案已经够稳了",
        "stage": "after_game",
        "observation": {
            "active_loop": "fast",
            "intent_type": "quant",
            "requires_search": False,
            "candidate_count": 30,
            "safe_count": 10,
            "target_count": 10,
            "rush_count": 10,
            "retry_count": 0,
            "research_loop_count": 0,
            "has_deep_research_trigger": False,
        },
        "chosen_action": "report_agent",
        "rejected_action": "deep_research",
        "margin": 0.7,
    },
]


ROLLOUT_RECORDS = [
    {
        "case": {"case_id": "C1", "message": "帮我看看要不要继续调研"},
        "summary": {"reward": 0.9, "approved": True, "success": True},
        "trace": [
            {
                "stage": "after_game",
                "selected_action": "deep_research",
                "candidate_actions": ["report_agent", "deep_research"],
                "rationale": "Need more evidence.",
                "observation": PAIRWISE_RECORDS[0]["observation"],
            }
        ],
    }
]


def test_alignment_exports_and_ranker_training() -> None:
    sft_examples = build_sft_examples_from_rollouts(ROLLOUT_RECORDS)
    preference_examples = build_preference_examples(PAIRWISE_RECORDS)
    grpo_tasks = build_grpo_tasks_from_rollouts(ROLLOUT_RECORDS)

    assert len(sft_examples) == 1
    assert len(preference_examples) == 2
    assert len(grpo_tasks) == 1

    ranker = SupervisorActionRanker()
    metrics = ranker.fit(PAIRWISE_RECORDS)
    assert metrics["train_samples"] == 4

    scores = ranker.score_actions(
        stage="after_game",
        observation=PAIRWISE_RECORDS[0]["observation"],
        candidate_actions=["report_agent", "deep_research"],
    )
    assert scores["deep_research"] > scores["report_agent"]

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = ranker.save(Path(tmp_dir) / "ranker.pkl")
        loaded = SupervisorActionRanker.load(path)
        original_scores = ranker.score_actions(
            stage="after_game",
            observation=PAIRWISE_RECORDS[1]["observation"],
            candidate_actions=["report_agent", "deep_research"],
        )
        loaded_scores = loaded.score_actions(
            stage="after_game",
            observation=PAIRWISE_RECORDS[1]["observation"],
            candidate_actions=["report_agent", "deep_research"],
        )
        assert loaded_scores == original_scores


if __name__ == "__main__":
    test_alignment_exports_and_ranker_training()
    print("orchestration alignment smoke tests passed")

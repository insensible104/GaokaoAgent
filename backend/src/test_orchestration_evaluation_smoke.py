"""Smoke tests for orchestration evaluation helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from rl.orchestration_alignment import SupervisorActionRanker


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_orchestration_policies.py"
SPEC = importlib.util.spec_from_file_location("evaluate_orchestration_policies", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


PAIRWISE_RECORDS = [
    {
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
        "summary": {"reward": 0.6, "trace_length": 4, "retry_count": 1, "approved": True, "success": True},
        "trace": [{"selected_action": "deep_research"}],
        "error": None,
        "game_matrix_stats": {"agentic_rl_used": True},
    },
    {
        "summary": {"reward": 0.2, "trace_length": 3, "retry_count": 0, "approved": False, "success": True},
        "trace": [{"selected_action": "report_agent"}],
        "error": None,
        "game_matrix_stats": {"agentic_rl_used": False},
    },
]


def test_rollout_summary_and_ranker_eval() -> None:
    summary = MODULE.summarize_rollouts(ROLLOUT_RECORDS)
    assert summary["case_count"] == 2
    assert summary["deep_research_rate"] == 0.5
    assert summary["agentic_rl_usage_rate"] == 0.5

    ranker = SupervisorActionRanker()
    ranker.fit(PAIRWISE_RECORDS)
    eval_result = MODULE.evaluate_ranker(PAIRWISE_RECORDS, ranker)
    assert eval_result["pairwise_count"] == 2
    assert 0.0 <= eval_result["accuracy"] <= 1.0

    baseline = {
        "avg_reward": 0.3,
        "approval_rate": 0.5,
        "success_rate": 1.0,
        "avg_trace_length": 5.0,
        "avg_retry_count": 1.0,
        "deep_research_rate": 0.5,
        "error_rate": 0.0,
        "agentic_rl_usage_rate": 0.0,
    }
    candidate = {
        "avg_reward": 0.6,
        "approval_rate": 1.0,
        "success_rate": 1.0,
        "avg_trace_length": 4.0,
        "avg_retry_count": 0.0,
        "deep_research_rate": 0.2,
        "error_rate": 0.0,
        "agentic_rl_usage_rate": 1.0,
    }
    delta = MODULE.compare_rollout_summaries(baseline, candidate)
    assert delta["avg_reward"] == 0.3
    report = MODULE.build_markdown_report(
        {
            "baseline_comparison": {
                "baseline": baseline,
                "candidate": candidate,
                "delta": delta,
            },
            "ranker_eval": eval_result,
        }
    )
    assert "Baseline" in report
    assert "avg_reward" in report


if __name__ == "__main__":
    test_rollout_summary_and_ranker_eval()
    print("orchestration evaluation smoke tests passed")

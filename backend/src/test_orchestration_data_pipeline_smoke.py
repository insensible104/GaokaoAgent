"""Smoke tests for orchestration data pipeline helpers."""

from __future__ import annotations

from pathlib import Path
import tempfile

from rl.orchestration_data_pipeline import (
    build_initial_state,
    build_pairwise_preferences,
    generate_synthetic_cases,
    load_cases,
    save_cases_jsonl,
)


def test_generate_and_reload_cases() -> None:
    cases = generate_synthetic_cases(num_cases=8, seed=7, include_seed_cases=False)
    assert len(cases) == 8
    assert all(case.message for case in cases)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_cases_jsonl(cases, Path(tmpdir) / "cases.jsonl")
        loaded = load_cases(path)
        assert len(loaded) == 8
        assert loaded[0].case_id == cases[0].case_id


def test_initial_state_exposes_reward_components() -> None:
    case = generate_synthetic_cases(num_cases=1, seed=11, include_seed_cases=False)[0]
    state = build_initial_state(case)
    assert state["orchestration_reward"] is None
    assert state["orchestration_reward_components"] is None
    assert state["protocol_violations"] == []


def test_build_pairwise_preferences() -> None:
    rollout_records = [
        {
            "case": {"case_id": "SYN0001", "message": "dummy"},
            "summary": {"reward": 0.6},
            "trace": [
                {
                    "stage": "after_game",
                    "selected_action": "report_agent",
                    "candidate_actions": ["report_agent", "deep_research"],
                    "observation": {
                        "requires_search": False,
                        "research_loop_count": 0,
                        "candidate_count": 30,
                        "has_deep_research_trigger": False,
                    },
                }
            ],
        }
    ]
    preferences = build_pairwise_preferences(rollout_records)
    assert len(preferences) == 1
    assert preferences[0]["chosen_action"] == "report_agent"
    assert preferences[0]["margin"] > 0


def test_protocol_violation_prefers_deep_research() -> None:
    rollout_records = [
        {
            "case": {"case_id": "SYN0002", "message": "dummy"},
            "summary": {"reward": 0.4},
            "trace": [
                {
                    "stage": "after_game",
                    "selected_action": "deep_research",
                    "candidate_actions": ["report_agent", "deep_research"],
                    "observation": {
                        "requires_search": False,
                        "research_loop_count": 0,
                        "candidate_count": 30,
                        "has_deep_research_trigger": False,
                        "protocol_violation_count": 1,
                    },
                }
            ],
        }
    ]
    preferences = build_pairwise_preferences(rollout_records)
    assert preferences[0]["chosen_action"] == "deep_research"
    assert preferences[0]["rejected_action"] == "report_agent"
    assert preferences[0]["margin"] > 0


if __name__ == "__main__":
    test_generate_and_reload_cases()
    test_initial_state_exposes_reward_components()
    test_build_pairwise_preferences()
    test_protocol_violation_prefers_deep_research()
    print("orchestration data pipeline smoke tests passed")

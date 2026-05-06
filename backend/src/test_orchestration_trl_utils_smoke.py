"""Smoke tests for TRL orchestration utility functions."""

from __future__ import annotations

from rl.orchestration_trl_utils import (
    build_grpo_examples,
    build_reward_model_examples,
    extract_action_from_completion,
    format_reward_func,
    proxy_reward_shaping_func,
    reference_match_reward_func,
    valid_action_reward_func,
)


def test_extract_action_from_completion() -> None:
    text = '{"next_action":"deep_research","rationale":"need more evidence"}'
    assert extract_action_from_completion(text) == "deep_research"


def test_build_reward_and_grpo_examples() -> None:
    preference_records = [
        {
            "prompt": "choose next action",
            "chosen": '{"next_action":"deep_research"}',
            "rejected": '{"next_action":"report_agent"}',
            "stage": "after_game",
            "margin": 0.8,
        }
    ]
    grpo_records = [
        {
            "prompt": "choose next action",
            "allowed_actions": ["deep_research", "report_agent"],
            "reference_action": "deep_research",
            "stage": "after_game",
            "reward_proxy": 0.9,
            "approved": True,
            "success": True,
        }
    ]

    reward_examples = build_reward_model_examples(preference_records)
    grpo_examples = build_grpo_examples(grpo_records)

    assert len(reward_examples) == 1
    assert reward_examples[0]["prompt"][0]["role"] == "user"
    assert len(grpo_examples) == 1
    assert grpo_examples[0]["reference_action"] == "deep_research"


def test_custom_reward_functions() -> None:
    completions = [
        '{"next_action":"deep_research","rationale":"need more evidence"}',
        '{"next_action":"report_agent","rationale":"enough evidence"}',
    ]
    allowed_actions = [
        ["deep_research", "report_agent"],
        ["deep_research", "report_agent"],
    ]
    reference_action = ["deep_research", "deep_research"]
    reward_proxy = [0.9, 0.8]

    format_rewards = format_reward_func(completions)
    validity_rewards = valid_action_reward_func(completions, allowed_actions=allowed_actions)
    match_rewards = reference_match_reward_func(completions, reference_action=reference_action)
    proxy_rewards = proxy_reward_shaping_func(
        completions,
        reference_action=reference_action,
        reward_proxy=reward_proxy,
    )

    assert format_rewards[0] >= 0.8
    assert validity_rewards == [1.0, 1.0]
    assert match_rewards == [1.0, 0.0]
    assert proxy_rewards[0] > proxy_rewards[1]


if __name__ == "__main__":
    test_extract_action_from_completion()
    test_build_reward_and_grpo_examples()
    test_custom_reward_functions()
    print("orchestration trl utils smoke tests passed")

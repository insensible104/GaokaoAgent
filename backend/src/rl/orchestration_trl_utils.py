"""Utilities for TRL-based orchestration alignment training."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


ACTION_PATTERN = re.compile(r'"next_action"\s*:\s*"([^"]+)"')


def load_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    """Load one JSON object per line."""
    file_path = Path(path)
    return [
        json.loads(line)
        for line in file_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def normalize_completion(completion: Any) -> str:
    """Normalize TRL completion payloads to plain text."""
    if isinstance(completion, str):
        return completion
    if isinstance(completion, Sequence) and completion and isinstance(completion[0], dict):
        return str(completion[0].get("content", ""))
    if isinstance(completion, dict):
        return str(completion.get("content", ""))
    return str(completion)


def extract_action_from_completion(completion: Any) -> str | None:
    """Extract `next_action` from a JSON-like completion."""
    text = normalize_completion(completion).strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
        action = parsed.get("next_action")
        return str(action) if action else None
    except Exception:
        pass

    match = ACTION_PATTERN.search(text)
    if match:
        return match.group(1)

    for token in [
        "profiling_agent",
        "game_agent",
        "report_agent",
        "deep_research",
        "multimodal_parser",
        "critic_agent",
        "END",
    ]:
        if token in text:
            return token
    return None


def build_reward_model_examples(preference_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert preference records into RewardTrainer-friendly conversational examples."""
    examples: List[Dict[str, Any]] = []
    for record in preference_records:
        prompt = record.get("prompt")
        chosen = record.get("chosen")
        rejected = record.get("rejected")
        if not prompt or not chosen or not rejected:
            continue
        examples.append(
            {
                "prompt": [{"role": "user", "content": prompt}],
                "chosen": [{"role": "assistant", "content": chosen}],
                "rejected": [{"role": "assistant", "content": rejected}],
                "stage": record.get("stage", "unknown"),
                "margin": float(record.get("margin", 0.0) or 0.0),
                "label_source": record.get("label_source", "unknown"),
            }
        )
    return examples


def build_grpo_examples(grpo_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert rollout-derived GRPO tasks into Dataset rows."""
    examples: List[Dict[str, Any]] = []
    for record in grpo_records:
        prompt = record.get("prompt")
        allowed_actions = record.get("allowed_actions", [])
        reference_action = record.get("reference_action")
        if not prompt or not allowed_actions:
            continue
        examples.append(
            {
                "prompt": prompt,
                "allowed_actions": allowed_actions,
                "reference_action": reference_action,
                "stage": record.get("stage", "unknown"),
                "reward_proxy": float(record.get("reward_proxy", 0.0) or 0.0),
                "approved": bool(record.get("approved", False)),
                "success": bool(record.get("success", False)),
            }
        )
    return examples


def format_reward_func(completions, **kwargs) -> List[float]:
    """Reward well-formed JSON action outputs."""
    rewards: List[float] = []
    for completion in completions:
        text = normalize_completion(completion).strip()
        action = extract_action_from_completion(text)
        reward = 0.0
        if text.startswith("{") and text.endswith("}"):
            reward += 0.4
        if action:
            reward += 0.4
        if "rationale" in text:
            reward += 0.2
        rewards.append(reward)
    return rewards


def valid_action_reward_func(completions, allowed_actions, **kwargs) -> List[float]:
    """Reward completions that pick one of the allowed supervisor actions."""
    rewards: List[float] = []
    for completion, candidate_actions in zip(completions, allowed_actions):
        action = extract_action_from_completion(completion)
        rewards.append(1.0 if action and action in candidate_actions else -0.5)
    return rewards


def reference_match_reward_func(completions, reference_action, **kwargs) -> List[float]:
    """Reward exact agreement with the current reference action."""
    rewards: List[float] = []
    for completion, target_action in zip(completions, reference_action):
        action = extract_action_from_completion(completion)
        rewards.append(1.0 if action and action == target_action else 0.0)
    return rewards


def proxy_reward_shaping_func(completions, reference_action, reward_proxy, **kwargs) -> List[float]:
    """Shape GRPO rewards using the rollout proxy reward."""
    rewards: List[float] = []
    for completion, target_action, proxy in zip(completions, reference_action, reward_proxy):
        action = extract_action_from_completion(completion)
        proxy_value = float(proxy or 0.0)
        if action == target_action:
            rewards.append(max(-1.0, min(1.0, proxy_value)))
        elif action is None:
            rewards.append(-0.5)
        else:
            rewards.append(max(-1.0, min(0.0, -abs(proxy_value) * 0.35)))
    return rewards

"""Alignment utilities for orchestration-focused RLHF / GRPO experiments."""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any, Dict, Iterable, List

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


def _to_feature_dict(
    observation: Dict[str, Any],
    *,
    stage: str,
    candidate_action: str,
) -> Dict[str, Any]:
    """Build one flat feature dict for action ranking."""
    return {
        "stage": stage,
        "candidate_action": candidate_action,
        "active_loop": observation.get("active_loop") or "none",
        "intent_type": observation.get("intent_type") or "unknown",
        "has_user_profile": bool(observation.get("has_user_profile", False)),
        "has_game_matrix": bool(observation.get("has_game_matrix", False)),
        "has_report": bool(observation.get("has_report", False)),
        "has_research_report": bool(observation.get("has_research_report", False)),
        "requires_search": bool(observation.get("requires_search", False)),
        "requires_vision": bool(observation.get("requires_vision", False)),
        "has_deep_research_trigger": bool(observation.get("has_deep_research_trigger", False)),
        "intent_confidence": float(observation.get("intent_confidence", 0.0) or 0.0),
        "retry_count": int(observation.get("retry_count", 0) or 0),
        "research_loop_count": int(observation.get("research_loop_count", 0) or 0),
        "candidate_count": int(observation.get("candidate_count", 0) or 0),
        "safe_count": int(observation.get("safe_count", 0) or 0),
        "target_count": int(observation.get("target_count", 0) or 0),
        "rush_count": int(observation.get("rush_count", 0) or 0),
        "has_volunteer_plan": bool(observation.get("has_volunteer_plan", False)),
        "expected_admission_prob": float(observation.get("expected_admission_prob", 0.0) or 0.0),
        "key_prefix_count": int(observation.get("key_prefix_count", 0) or 0),
        "key_high_tail_count": int(observation.get("key_high_tail_count", 0) or 0),
        "shadowed_choice_count": int(observation.get("shadowed_choice_count", 0) or 0),
        "debug_log_count": int(observation.get("debug_log_count", 0) or 0),
        "reflection_count": int(observation.get("reflection_count", 0) or 0),
        "negative_step_ratio": float(observation.get("negative_step_ratio", 0.0) or 0.0),
        "issue_count": int(observation.get("issue_count", 0) or 0),
    }


def format_supervisor_prompt(
    *,
    message: str | None,
    stage: str,
    observation: Dict[str, Any],
    candidate_actions: List[str],
) -> str:
    """Render one compact text prompt for SFT / GRPO style data export."""
    return (
        "You are a supervisor policy for a graph-orchestrated multi-agent system.\n"
        f"User request: {message or 'N/A'}\n"
        f"Stage: {stage}\n"
        f"Observation: {json.dumps(observation, ensure_ascii=False, sort_keys=True)}\n"
        f"Allowed actions: {candidate_actions}\n"
        "Choose the next action and explain why in one short paragraph."
    )


class SupervisorActionRanker:
    """Binary action scorer trained from orchestration preference data."""

    def __init__(self) -> None:
        self.vectorizer = DictVectorizer(sparse=False)
        self.model = LogisticRegression(max_iter=1000, class_weight="balanced")
        self.metadata: Dict[str, Any] = {}

    def fit(self, pairwise_records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        """Train a binary preference scorer from chosen/rejected action pairs."""
        feature_rows: List[Dict[str, Any]] = []
        labels: List[int] = []
        sample_weights: List[float] = []

        for record in pairwise_records:
            stage = record.get("stage", "unknown")
            observation = record.get("observation", {})
            chosen_action = record.get("chosen_action")
            rejected_action = record.get("rejected_action")
            margin = float(record.get("margin", 0.1) or 0.1)

            if chosen_action:
                feature_rows.append(
                    _to_feature_dict(observation, stage=stage, candidate_action=chosen_action)
                )
                labels.append(1)
                sample_weights.append(max(0.05, margin))

            if rejected_action:
                feature_rows.append(
                    _to_feature_dict(observation, stage=stage, candidate_action=rejected_action)
                )
                labels.append(0)
                sample_weights.append(max(0.05, margin))

        if not feature_rows:
            raise ValueError("No valid pairwise preference records found for training.")

        X = self.vectorizer.fit_transform(feature_rows)
        self.model.fit(X, labels, sample_weight=sample_weights)
        predictions = self.model.predict(X)
        train_accuracy = accuracy_score(labels, predictions)

        self.metadata = {
            "train_samples": len(labels),
            "train_accuracy": round(float(train_accuracy), 4),
            "positive_ratio": round(sum(labels) / max(len(labels), 1), 4),
            "feature_dim": int(X.shape[1]),
        }
        return self.metadata

    def score_actions(
        self,
        *,
        stage: str,
        observation: Dict[str, Any],
        candidate_actions: List[str],
    ) -> Dict[str, float]:
        """Return preference scores for each candidate action."""
        if not candidate_actions:
            return {}

        X = self.vectorizer.transform(
            [
                _to_feature_dict(observation, stage=stage, candidate_action=action)
                for action in candidate_actions
            ]
        )
        probs = self.model.predict_proba(X)
        positive_index = list(self.model.classes_).index(1)
        return {
            action: round(float(prob[positive_index]), 6)
            for action, prob in zip(candidate_actions, probs)
        }

    def save(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as handle:
            pickle.dump(
                {
                    "vectorizer": self.vectorizer,
                    "model": self.model,
                    "metadata": self.metadata,
                },
                handle,
            )
        return path

    @classmethod
    def load(cls, input_path: str | Path) -> "SupervisorActionRanker":
        path = Path(input_path)
        with path.open("rb") as handle:
            payload = pickle.load(handle)
        obj = cls()
        obj.vectorizer = payload["vectorizer"]
        obj.model = payload["model"]
        obj.metadata = payload.get("metadata", {})
        return obj


def build_sft_examples_from_rollouts(rollout_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert rollout traces into instruction-tuning style examples."""
    examples: List[Dict[str, Any]] = []
    for record in rollout_records:
        case = record.get("case", {})
        message = case.get("message")
        for step_index, decision in enumerate(record.get("trace", [])):
            stage = decision.get("stage", "unknown")
            observation = decision.get("observation", {})
            candidate_actions = decision.get("candidate_actions", [])
            selected_action = decision.get("selected_action")
            rationale = decision.get("rationale", "")
            if not selected_action:
                continue
            examples.append(
                {
                    "case_id": case.get("case_id"),
                    "step_index": step_index,
                    "stage": stage,
                    "prompt": format_supervisor_prompt(
                        message=message,
                        stage=stage,
                        observation=observation,
                        candidate_actions=candidate_actions,
                    ),
                    "response": json.dumps(
                        {
                            "next_action": selected_action,
                            "rationale": rationale,
                        },
                        ensure_ascii=False,
                    ),
                    "label_source": "orchestration_trace",
                }
            )
    return examples


def build_preference_examples(pairwise_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert pairwise action preferences into preference-learning format."""
    examples: List[Dict[str, Any]] = []
    for record in pairwise_records:
        stage = record.get("stage", "unknown")
        observation = record.get("observation", {})
        chosen_action = record.get("chosen_action")
        rejected_action = record.get("rejected_action")
        if not chosen_action or not rejected_action:
            continue
        candidate_actions = [chosen_action, rejected_action]
        prompt = format_supervisor_prompt(
            message=record.get("message"),
            stage=stage,
            observation=observation,
            candidate_actions=candidate_actions,
        )
        examples.append(
            {
                "case_id": record.get("case_id"),
                "stage": stage,
                "prompt": prompt,
                "chosen": json.dumps({"next_action": chosen_action}, ensure_ascii=False),
                "rejected": json.dumps({"next_action": rejected_action}, ensure_ascii=False),
                "margin": record.get("margin", 0.0),
                "label_source": record.get("label_source", "pairwise_proxy"),
            }
        )
    return examples


def build_grpo_tasks_from_rollouts(rollout_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Export rollout traces as task/reward tuples for GRPO style experimentation."""
    tasks: List[Dict[str, Any]] = []
    for record in rollout_records:
        case = record.get("case", {})
        summary = record.get("summary", {})
        for step_index, decision in enumerate(record.get("trace", [])):
            stage = decision.get("stage", "unknown")
            observation = decision.get("observation", {})
            candidate_actions = decision.get("candidate_actions", [])
            if not candidate_actions:
                continue
            tasks.append(
                {
                    "case_id": case.get("case_id"),
                    "step_index": step_index,
                    "stage": stage,
                    "prompt": format_supervisor_prompt(
                        message=case.get("message"),
                        stage=stage,
                        observation=observation,
                        candidate_actions=candidate_actions,
                    ),
                    "allowed_actions": candidate_actions,
                    "reference_action": decision.get("selected_action"),
                    "reward_proxy": summary.get("reward", 0.0),
                    "approved": summary.get("approved", False),
                    "success": summary.get("success", False),
                }
            )
    return tasks


def save_jsonl(records: Iterable[Dict[str, Any]], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path

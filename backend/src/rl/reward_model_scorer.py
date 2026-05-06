"""Runtime reward-model scoring for supervisor action reranking."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from rl.orchestration_alignment import format_supervisor_prompt


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _evaluate_rule(observation: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    field = rule.get("field")
    operator = rule.get("operator", "eq")
    if not field:
        return False
    value = observation.get(field)
    target = rule.get("value")

    if operator == "eq":
        return value == target
    if operator == "neq":
        return value != target
    if operator == "lt":
        return _coerce_float(value) < _coerce_float(target)
    if operator == "lte":
        return _coerce_float(value) <= _coerce_float(target)
    if operator == "gt":
        return _coerce_float(value) > _coerce_float(target)
    if operator == "gte":
        return _coerce_float(value) >= _coerce_float(target)
    if operator == "truthy":
        return bool(value)
    if operator == "falsy":
        return not bool(value)
    if operator == "contains":
        return str(target) in str(value)
    return False


class SupervisorRewardModelScorer:
    """Score supervisor candidate actions with either a ruleset or a reward model."""

    def __init__(self) -> None:
        self.backend = "rules"
        self.metadata: Dict[str, Any] = {}
        self.rules_payload: Dict[str, Any] = {}
        self.model = None
        self.tokenizer = None

    @classmethod
    def load(cls, input_path: str | Path) -> "SupervisorRewardModelScorer":
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Reward model path not found: {path}")

        scorer = cls()
        if path.is_file() and path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            scorer.backend = payload.get("backend", "rules")
            scorer.rules_payload = payload
            scorer.metadata = payload.get("metadata", {})
            return scorer

        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except Exception as exc:
            raise RuntimeError(
                "Transformers is required to load a trained reward model checkpoint."
            ) from exc

        scorer.backend = "transformers"
        scorer.tokenizer = AutoTokenizer.from_pretrained(str(path), use_fast=True)
        scorer.model = AutoModelForSequenceClassification.from_pretrained(str(path))
        if scorer.tokenizer.pad_token is None:
            scorer.tokenizer.pad_token = scorer.tokenizer.eos_token
        scorer.model.eval()
        scorer.metadata = {"checkpoint_path": str(path)}
        return scorer

    def _score_with_rules(
        self,
        *,
        stage: str,
        observation: Dict[str, Any],
        candidate_actions: List[str],
    ) -> Dict[str, float]:
        action_bias = self.rules_payload.get("action_bias", {})
        stage_bias = self.rules_payload.get("stage_bias", {}).get(stage, {})
        rules = self.rules_payload.get("rules", [])
        scores = {
            action: _coerce_float(action_bias.get(action, 0.0)) + _coerce_float(stage_bias.get(action, 0.0))
            for action in candidate_actions
        }

        for rule in rules:
            if not _evaluate_rule(observation, rule):
                continue
            action = rule.get("action")
            if action not in scores:
                continue
            scores[action] += _coerce_float(rule.get("weight", 0.0))

        return {action: round(score, 6) for action, score in scores.items()}

    def _score_with_transformers(
        self,
        *,
        message: str | None,
        stage: str,
        observation: Dict[str, Any],
        candidate_actions: List[str],
    ) -> Dict[str, float]:
        assert self.model is not None
        assert self.tokenizer is not None

        prompt = format_supervisor_prompt(
            message=message,
            stage=stage,
            observation=observation,
            candidate_actions=candidate_actions,
        )
        inputs = [
            (
                prompt
                + "\nAssistant response:\n"
                + json.dumps({"next_action": action}, ensure_ascii=False)
            )
            for action in candidate_actions
        ]
        batch = self.tokenizer(
            inputs,
            padding=True,
            truncation=True,
            max_length=1024,
            return_tensors="pt",
        )
        outputs = self.model(**batch)
        logits = outputs.logits.squeeze(-1).detach().cpu().tolist()
        if not isinstance(logits, list):
            logits = [float(logits)]
        return {
            action: round(float(score), 6)
            for action, score in zip(candidate_actions, logits)
        }

    def score_actions(
        self,
        *,
        message: str | None,
        stage: str,
        observation: Dict[str, Any],
        candidate_actions: List[str],
    ) -> Dict[str, float]:
        if not candidate_actions:
            return {}
        if self.backend == "transformers":
            return self._score_with_transformers(
                message=message,
                stage=stage,
                observation=observation,
                candidate_actions=candidate_actions,
            )
        return self._score_with_rules(
            stage=stage,
            observation=observation,
            candidate_actions=candidate_actions,
        )

"""Smoke test for reward-model-based supervisor reranking."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from models.game_matrix import GameMatrix, MajorGroupRow, StrategyTag, VolatilityLevel
from models.intent import IntentClassification, IntentType, LoopType
from rl.supervisor_policy import HeuristicSupervisorPolicy


def _base_state() -> dict:
    rows = [
        MajorGroupRow(
            school_name=f"Test School {index}",
            school_code=f"{1000 + index}",
            major_group_code=f"G{index}",
            major_list=["计算机科学与技术"],
            major_count=1,
            admission_prob=0.65,
            min_rank_pred=10000,
            rank_diff=100,
            rank_ci_lower=9800,
            rank_ci_upper=10200,
            fear_index=0.0,
            volatility=VolatilityLevel.MEDIUM,
            adjustment_risk=0.05,
            strategy_tag=StrategyTag.TARGET,
            comprehensive_score=0.8,
        )
        for index in range(20)
    ]
    return {
        "messages": [],
        "intent_classification": IntentClassification(
            primary_intent=IntentType.QUANT,
            secondary_intents=[],
            reasoning="reward-model-smoke",
            requires_quant=True,
            requires_search=False,
            requires_vision=False,
            confidence=0.88,
        ),
        "active_loop": LoopType.FAST,
        "loop_history": [],
        "user_profile": None,
        "game_matrix": GameMatrix(major_group_rows=rows),
        "report_draft": None,
        "research_topic": None,
        "search_queries": [],
        "web_research_results": [],
        "knowledge_gaps": [],
        "research_loop_count": 0,
        "research_report": None,
        "pdf_sources": [],
        "vision_results": [],
        "health_restrictions": [],
        "audit_result": None,
        "step_rewards": [],
        "reflection_history": [],
        "orchestration_trace": [],
        "next_action": None,
        "orchestration_reward": None,
        "agent_messages": [],
        "agent_memories": [],
        "deliberation_summaries": [],
        "recommended_next_action": None,
        "current_agent": "",
        "retry_count": 0,
        "human_approved": False,
        "max_loops": 3,
        "debug_logs": [],
    }


def test_reward_model_can_override_after_game_decision() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        reward_model_path = Path(tmpdir) / "reward_rules.json"
        reward_model_path.write_text(
            json.dumps(
                {
                    "backend": "rules",
                    "stage_bias": {"after_game": {"deep_research": 0.12}},
                    "rules": [
                        {
                            "field": "candidate_count",
                            "operator": "lte",
                            "value": 20,
                            "action": "deep_research",
                            "weight": 0.2,
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        os.environ["ENABLE_REWARD_MODEL_SUPERVISOR"] = "1"
        os.environ["SUPERVISOR_REWARD_MODEL_PATH"] = str(reward_model_path)
        HeuristicSupervisorPolicy._cached_reward_scorer = None
        HeuristicSupervisorPolicy._reward_scorer_loaded = False

        policy = HeuristicSupervisorPolicy()
        decision = policy.decide_after_game(_base_state())

        assert decision.selected_action == "deep_research"
        assert decision.metadata["reward_model_used"] is True
        assert decision.metadata["reward_model_backend"] == "rules"
        assert decision.metadata["reward_model_prior_action"] == "report_agent"

        os.environ.pop("ENABLE_REWARD_MODEL_SUPERVISOR", None)
        os.environ.pop("SUPERVISOR_REWARD_MODEL_PATH", None)
        HeuristicSupervisorPolicy._cached_reward_scorer = None
        HeuristicSupervisorPolicy._reward_scorer_loaded = False


if __name__ == "__main__":
    test_reward_model_can_override_after_game_decision()
    print("supervisor reward model smoke tests passed")

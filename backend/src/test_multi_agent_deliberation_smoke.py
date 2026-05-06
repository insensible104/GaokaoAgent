"""Smoke tests for the parallel multi-agent deliberation layer."""

from __future__ import annotations

from models.game_matrix import GameMatrix, MajorGroupRow, StrategyTag, VolatilityLevel
from models.intent import IntentClassification, IntentType, LoopType
from models.state import SupervisorState
from rl.supervisor_policy import HeuristicSupervisorPolicy
from agents.deliberation_agents import (
    deliberation_coordinator_node,
    evidence_guardian_agent_node,
    opportunity_advocate_agent_node,
    risk_guardian_agent_node,
)
from utils.agent_bus import publish_agent_message


LIST_FIELDS = {
    "messages",
    "loop_history",
    "search_queries",
    "web_research_results",
    "knowledge_gaps",
    "pdf_sources",
    "vision_results",
    "health_restrictions",
    "step_rewards",
    "reflection_history",
    "orchestration_trace",
    "debug_logs",
    "agent_messages",
    "agent_memories",
    "deliberation_summaries",
    "protocol_violations",
}


def _merge_state(state: SupervisorState, update: dict) -> SupervisorState:
    merged = dict(state)
    for key, value in update.items():
        if key in LIST_FIELDS and value is not None:
            merged[key] = list(merged.get(key, [])) + list(value)
        else:
            merged[key] = value
    return merged


def _make_row(name: str, tag: StrategyTag, prob: float) -> MajorGroupRow:
    return MajorGroupRow(
        school_name=name,
        school_code=f"{name[:2]}01",
        major_group_code=f"{name[:2]}-G1",
        major_list=["计算机科学与技术"],
        major_count=1,
        admission_prob=prob,
        min_rank_pred=12000,
        rank_diff=100,
        rank_ci_lower=11000,
        rank_ci_upper=13000,
        fear_index=0.0,
        volatility=VolatilityLevel.MEDIUM,
        adjustment_risk=0.1,
        strategy_tag=tag,
        comprehensive_score=0.8,
        sentiment_score=0.0,
    )


def _base_state(*, requires_search: bool, rows: list[MajorGroupRow]) -> SupervisorState:
    game_matrix = GameMatrix(major_group_rows=rows)
    game_matrix.calculate_statistics()
    return {
        "messages": [],
        "intent_classification": IntentClassification(
            primary_intent=IntentType.MIXED if requires_search else IntentType.QUANT,
            secondary_intents=[IntentType.RESEARCH] if requires_search else [],
            reasoning="smoke-test",
            requires_quant=True,
            requires_search=requires_search,
            requires_vision=False,
            confidence=0.92,
        ),
        "active_loop": LoopType.HYBRID if requires_search else LoopType.FAST,
        "loop_history": [],
        "user_profile": None,
        "game_matrix": game_matrix,
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
        "orchestration_reward_components": None,
        "agent_messages": publish_agent_message(
            sender="game_agent",
            stage="post_game_deliberation",
            message_type="proposal",
            content="Initial candidate slate",
            recipients=[
                "risk_guardian_agent",
                "opportunity_advocate_agent",
                "evidence_guardian_agent",
                "deliberation_coordinator",
            ],
            thread_id="post_game_deliberation",
            priority="high",
            requires_ack=True,
            action_preference="report_agent",
            confidence=0.75,
            metadata={
                "candidate_count": len(rows),
                "rush_count": game_matrix.total_rush,
                "target_count": game_matrix.total_target,
                "safe_count": game_matrix.total_safe,
                "portfolio_risk": game_matrix.portfolio_risk,
            },
        )["agent_messages"],
        "agent_memories": [],
        "deliberation_summaries": [],
        "protocol_violations": [],
        "recommended_next_action": None,
        "current_agent": "",
        "retry_count": 0,
        "human_approved": False,
        "max_loops": 3,
        "debug_logs": [],
    }


def test_deliberation_recommends_deep_research_for_search_required_case() -> None:
    state = _base_state(
        requires_search=True,
        rows=[
            _make_row("A大学", StrategyTag.RUSH, 0.48),
            _make_row("B大学", StrategyTag.TARGET, 0.74),
        ],
    )
    for node in (
        risk_guardian_agent_node,
        opportunity_advocate_agent_node,
        evidence_guardian_agent_node,
        deliberation_coordinator_node,
    ):
        state = _merge_state(state, node(state))

    assert state["deliberation_summaries"], "deliberation summary should be produced"
    assert state["recommended_next_action"] == "deep_research"
    assert state["deliberation_summaries"][-1].missing_required_agents == []
    assert state["deliberation_summaries"][-1].protocol_violations == []

    decision = HeuristicSupervisorPolicy().decide_after_game(state)
    assert decision.selected_action == "deep_research"
    assert decision.metadata["consensus_strength"] >= 0.0


def test_deliberation_recommends_report_when_evidence_is_sufficient() -> None:
    state = _base_state(
        requires_search=False,
        rows=[
            _make_row("C大学", StrategyTag.SAFE, 0.94),
            _make_row("D大学", StrategyTag.TARGET, 0.83),
            _make_row("E大学", StrategyTag.RUSH, 0.62),
        ],
    )
    for node in (
        risk_guardian_agent_node,
        opportunity_advocate_agent_node,
        evidence_guardian_agent_node,
        deliberation_coordinator_node,
    ):
        state = _merge_state(state, node(state))

    decision = HeuristicSupervisorPolicy().decide_after_game(state)
    assert state["recommended_next_action"] == "report_agent"
    assert decision.selected_action == "report_agent"


def test_coordinator_blocks_incomplete_protocol() -> None:
    state = _base_state(
        requires_search=False,
        rows=[
            _make_row("F澶у", StrategyTag.SAFE, 0.93),
            _make_row("G澶у", StrategyTag.TARGET, 0.82),
            _make_row("H澶у", StrategyTag.RUSH, 0.60),
        ],
    )
    state = _merge_state(state, risk_guardian_agent_node(state))
    state = _merge_state(state, deliberation_coordinator_node(state))

    summary = state["deliberation_summaries"][-1]
    assert state["recommended_next_action"] == "deep_research"
    assert "opportunity_advocate_agent" in summary.missing_required_agents
    assert summary.protocol_violations
    assert state["protocol_violations"]


if __name__ == "__main__":
    test_deliberation_recommends_deep_research_for_search_required_case()
    test_deliberation_recommends_report_when_evidence_is_sufficient()
    test_coordinator_blocks_incomplete_protocol()
    print("multi-agent deliberation smoke tests passed")

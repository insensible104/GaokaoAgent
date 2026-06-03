"""Smoke tests for the orchestration-focused supervisor policy."""

from __future__ import annotations

from langgraph.graph import END

from models.audit_result import AuditResult, AuditStatus
from models.game_matrix import GameMatrix, MajorGroupRow, MajorOption, StrategyTag, VolatilityLevel
from models.intent import IntentClassification, IntentType, LoopType
from models.user_profile import UserProfile
from recommendation.major_choice_planner import build_volunteer_plan
from graph.dual_loop_supervisor import route_after_critic
from rl.supervisor_policy import HeuristicSupervisorPolicy, compute_episode_summary


def _base_state() -> dict:
    return {
        "messages": [],
        "intent_classification": None,
        "active_loop": LoopType.FAST,
        "loop_history": [],
        "user_profile": None,
        "game_matrix": None,
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
        "agent_messages": [],
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


def test_mixed_intent_triggers_research() -> None:
    policy = HeuristicSupervisorPolicy()
    state = _base_state()
    state["intent_classification"] = IntentClassification(
        primary_intent=IntentType.MIXED,
        secondary_intents=[IntentType.QUANT, IntentType.RESEARCH],
        reasoning="mixed",
        requires_quant=True,
        requires_search=True,
        requires_vision=False,
        confidence=0.9,
    )
    decision = policy.decide_after_profiling(state)
    assert decision.selected_action == "deep_research"


def test_small_candidate_pool_triggers_research() -> None:
    policy = HeuristicSupervisorPolicy()
    state = _base_state()
    rows = [
        MajorGroupRow(
            school_name=f"Test School {i}",
            school_code=f"{1000 + i}",
            major_group_code=f"{i}",
            major_list=["CS"],
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
        for i in range(10)
    ]
    state["game_matrix"] = GameMatrix(major_group_rows=rows)
    decision = policy.decide_after_game(state)
    assert decision.selected_action == "deep_research"


def test_key_prefix_tail_risk_triggers_research() -> None:
    policy = HeuristicSupervisorPolicy()
    state = _base_state()
    option = MajorOption(
        school_code="10001",
        school_name="Risk School",
        major_group_code="201",
        major_name="Computer Science",
        user_utility=0.9,
    )
    rows = [
        MajorGroupRow(
            school_name="Risk School",
            school_code="10001",
            major_group_code="201",
            major_list=[option.major_name],
            major_count=1,
            major_options=[option],
            suggested_major_choices=[option],
            admission_prob=0.80,
            min_rank_pred=10000,
            rank_diff=100,
            rank_ci_lower=9800,
            rank_ci_upper=10200,
            fear_index=0.0,
            volatility=VolatilityLevel.MEDIUM,
            adjustment_risk=0.70,
            tail_assignment_risk=0.70,
            strategy_tag=StrategyTag.TARGET,
            comprehensive_score=0.8,
        )
    ]
    plan = build_volunteer_plan(rows, UserProfile(score=610, rank=20000, subject_group="physics"))
    state["game_matrix"] = GameMatrix(major_group_rows=rows, volunteer_plan=plan)
    decision = policy.decide_after_game(state)
    assert decision.selected_action == "deep_research"
    assert decision.metadata["first_hit_reason"] == "key_prefix_high_tail_risk"


def test_key_prefix_market_game_triggers_research() -> None:
    policy = HeuristicSupervisorPolicy()
    state = _base_state()
    option = MajorOption(
        school_code="10002",
        school_name="Crowded School",
        major_group_code="301",
        major_name="Computer Science",
        user_utility=0.9,
    )
    rows = [
        MajorGroupRow(
            school_name="Crowded School",
            school_code="10002",
            major_group_code="301",
            major_list=[option.major_name, "Civil Engineering"],
            major_count=2,
            major_options=[option],
            suggested_major_choices=[option],
            admission_prob=0.95,
            min_rank_pred=10000,
            rank_diff=100,
            rank_ci_lower=9800,
            rank_ci_upper=10200,
            fear_index=0.0,
            volatility=VolatilityLevel.MEDIUM,
            adjustment_risk=0.10,
            tail_assignment_risk=0.10,
            strategy_tag=StrategyTag.SAFE,
            comprehensive_score=0.8,
            tradeoff_breakdown={"crowding_risk": 0.75},
            pain_point_flags=["bait_major_group", "herding_crowding"],
            market_behavior_notes=["crowding_risk: obvious school/major signal"],
        )
    ]
    plan = build_volunteer_plan(rows, UserProfile(score=610, rank=20000, subject_group="physics"))
    state["game_matrix"] = GameMatrix(major_group_rows=rows, volunteer_plan=plan)

    decision = policy.decide_after_game(state)

    assert decision.selected_action == "deep_research"
    assert decision.metadata["first_hit_reason"] == "market_game_requires_evidence"
    assert decision.observation.high_crowding_count == 1
    assert decision.observation.bait_group_count == 1


def test_repeated_critic_failure_triggers_root_cause_research() -> None:
    policy = HeuristicSupervisorPolicy()
    state = _base_state()
    state["retry_count"] = 3
    state["audit_result"] = AuditResult(
        status=AuditStatus.REJECT_LOGIC,
        issues=["保底不足，存在滑档风险"],
        reroute_to="game_agent",
    )
    decision = policy.decide_after_critic(state)
    assert decision.selected_action == "deep_research"


def test_route_after_critic_maps_business_end_to_langgraph_end() -> None:
    assert route_after_critic({"next_action": "END"}) == END


def test_episode_summary_reward_is_bounded() -> None:
    state = _base_state()
    state["report_draft"] = object()
    state["audit_result"] = AuditResult(status=AuditStatus.PASS)
    state["orchestration_trace"] = [{"stage": "after_router"}] * 4
    summary = compute_episode_summary(state)
    assert -1.0 <= summary.reward <= 1.0
    assert summary.approved is True
    assert "approval" in summary.reward_components


def test_protocol_violation_penalizes_episode_reward() -> None:
    clean_state = _base_state()
    clean_state["report_draft"] = object()
    clean_state["audit_result"] = AuditResult(status=AuditStatus.PASS)
    clean_state["orchestration_trace"] = [{"stage": "after_router"}] * 4

    dirty_state = dict(clean_state)
    dirty_state["protocol_violations"] = [
        "missing vote from evidence_guardian_agent at stage=post_game_deliberation"
    ]

    clean_summary = compute_episode_summary(clean_state)
    dirty_summary = compute_episode_summary(dirty_state)

    assert dirty_summary.protocol_violation_count == 1
    assert dirty_summary.reward < clean_summary.reward
    assert dirty_summary.reward_components["protocol_violation_penalty"] < 0


def test_market_game_penalizes_episode_reward() -> None:
    state = _base_state()
    state["report_draft"] = object()
    state["audit_result"] = AuditResult(status=AuditStatus.PASS)
    state["orchestration_trace"] = [{"stage": "after_router"}] * 4
    option = MajorOption(
        school_code="10003",
        school_name="Market School",
        major_group_code="401",
        major_name="Computer Science",
        user_utility=0.9,
    )
    rows = [
        MajorGroupRow(
            school_name="Market School",
            school_code="10003",
            major_group_code="401",
            major_list=[option.major_name, "Civil Engineering"],
            major_count=2,
            major_options=[option],
            suggested_major_choices=[option],
            admission_prob=0.95,
            min_rank_pred=10000,
            rank_diff=100,
            rank_ci_lower=9800,
            rank_ci_upper=10200,
            fear_index=0.0,
            volatility=VolatilityLevel.MEDIUM,
            adjustment_risk=0.10,
            tail_assignment_risk=0.10,
            strategy_tag=StrategyTag.SAFE,
            comprehensive_score=0.8,
            tradeoff_breakdown={"crowding_risk": 0.75},
            pain_point_flags=["bait_major_group", "high_variance_opportunity"],
        )
    ]
    plan = build_volunteer_plan(rows, UserProfile(score=610, rank=20000, subject_group="physics"))
    state["game_matrix"] = GameMatrix(major_group_rows=rows, volunteer_plan=plan)

    summary = compute_episode_summary(state)

    assert summary.reward_components["market_crowding_penalty"] < 0
    assert summary.reward_components["bait_group_penalty"] < 0
    assert summary.reward_components["hidden_opportunity_bonus"] > 0


if __name__ == "__main__":
    test_mixed_intent_triggers_research()
    test_small_candidate_pool_triggers_research()
    test_key_prefix_tail_risk_triggers_research()
    test_key_prefix_market_game_triggers_research()
    test_repeated_critic_failure_triggers_root_cause_research()
    test_route_after_critic_maps_business_end_to_langgraph_end()
    test_episode_summary_reward_is_bounded()
    test_protocol_violation_penalizes_episode_reward()
    test_market_game_penalizes_episode_reward()
    print("supervisor policy smoke tests passed")

"""GaokaoAgent Dual-Loop Supervisor Graph（双循环架构）"""
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig

from models.state import SupervisorState
from models.intent import LoopType
from agents import (
    router_agent_node,
    profiling_agent_node,
    game_agent_node,
    report_agent_node,
    critic_agent_node,
    deep_research_agent_node,
    multimodal_agent_node,
    risk_guardian_agent_node,
    opportunity_advocate_agent_node,
    evidence_guardian_agent_node,
    deliberation_coordinator_node,
)
from rl.supervisor_policy import (
    HeuristicSupervisorPolicy,
    append_trace_record,
    compute_episode_summary,
)


def safe_print(msg: str):
    """安全打印函数，处理Windows控制台GBK编码无法显示emoji的问题"""
    try:
        print(msg)
    except UnicodeEncodeError:
        # 移除emoji后打印
        print(msg.encode('ascii', errors='ignore').decode('ascii'))


def route_from_router(state: SupervisorState) -> str:
    """Read the next action selected by the supervisor policy."""
    return state.get("next_action") or "profiling_agent"


def route_after_profiling(state: SupervisorState) -> str:
    """Read the next action selected by the supervisor policy."""
    return state.get("next_action") or "game_agent"


def route_after_game(state: SupervisorState) -> str:
    """Read the next action selected by the supervisor policy."""
    return state.get("next_action") or "report_agent"


def route_after_report(state: SupervisorState) -> str:
    """Read the next action selected by the supervisor policy."""
    return state.get("next_action") or "critic_agent"


def route_after_critic(state: SupervisorState) -> str:
    """Read the next action selected by the supervisor policy."""
    next_action = state.get("next_action")
    return END if next_action == END else (next_action or END)


def _build_policy_update(state: SupervisorState, decision) -> dict:
    update = append_trace_record(state, decision)
    update["current_agent"] = "supervisor_policy"
    return update


def supervisor_after_profiling_node(state: SupervisorState) -> dict:
    policy = HeuristicSupervisorPolicy()
    decision = policy.decide_after_profiling(state)
    return _build_policy_update(state, decision)


def supervisor_after_game_node(state: SupervisorState) -> dict:
    policy = HeuristicSupervisorPolicy()
    decision = policy.decide_after_game(state)
    return _build_policy_update(state, decision)


def supervisor_after_report_node(state: SupervisorState) -> dict:
    policy = HeuristicSupervisorPolicy()
    decision = policy.decide_after_report(state)
    return _build_policy_update(state, decision)


def supervisor_after_critic_node(state: SupervisorState) -> dict:
    policy = HeuristicSupervisorPolicy()
    decision = policy.decide_after_critic(state)
    summary = compute_episode_summary({
        **state,
        "next_action": decision.selected_action,
        "orchestration_trace": state.get("orchestration_trace", []) + [decision.model_dump()],
    })
    update = _build_policy_update(state, decision)
    update["orchestration_reward"] = summary.reward
    update["orchestration_reward_components"] = summary.reward_components
    component_preview = ", ".join(
        f"{key}={value:.3f}" for key, value in summary.reward_components.items()
    )
    update["debug_logs"] = update["debug_logs"] + [
        (
            f"[SupervisorPolicy:episode] reward={summary.reward:.3f}, "
            f"approved={summary.approved}, retries={summary.retry_count}, "
            f"components=({component_preview})"
        )
    ]
    return update


def create_dual_loop_supervisor() -> StateGraph:
    """
    创建双循环 Supervisor Graph

    新流程：
    START -> Router -> [Fast / Slow / Multimodal / Hybrid] -> ... -> Critic -> END
    """
    builder = StateGraph(SupervisorState)

    # === 添加节点 ===
    # 元认知层
    builder.add_node("router_agent", router_agent_node)

    # 快思考循环（Fast Loop - Quant）
    builder.add_node("profiling_agent", profiling_agent_node)
    builder.add_node("supervisor_after_profiling", supervisor_after_profiling_node)
    builder.add_node("game_agent", game_agent_node)
    builder.add_node("risk_guardian_agent", risk_guardian_agent_node)
    builder.add_node("opportunity_advocate_agent", opportunity_advocate_agent_node)
    builder.add_node("evidence_guardian_agent", evidence_guardian_agent_node)
    builder.add_node("deliberation_coordinator", deliberation_coordinator_node)
    builder.add_node("supervisor_after_game", supervisor_after_game_node)
    builder.add_node("report_agent", report_agent_node)
    builder.add_node("supervisor_after_report", supervisor_after_report_node)

    # 慢思考循环（Slow Loop - Research）
    builder.add_node("deep_research", deep_research_agent_node)

    # 多模态循环（Multimodal Loop）
    builder.add_node("multimodal_parser", multimodal_agent_node)

    # 审计层
    builder.add_node("critic_agent", critic_agent_node)
    builder.add_node("supervisor_after_critic", supervisor_after_critic_node)

    # === 设置入口 ===
    builder.add_edge(START, "router_agent")

    # === 条件路由 ===

    # Router -> [Fast / Slow / Multimodal / Hybrid]
    builder.add_conditional_edges(
        "router_agent",
        route_from_router,
        {
            "profiling_agent": "profiling_agent",
            "deep_research": "deep_research",
            "multimodal_parser": "multimodal_parser"
        }
    )

    # Profiling -> Supervisor Policy -> Game 或 Deep Research
    builder.add_edge("profiling_agent", "supervisor_after_profiling")
    builder.add_conditional_edges(
        "supervisor_after_profiling",
        route_after_profiling,
        {
            "game_agent": "game_agent",
            "deep_research": "deep_research"
        }
    )

    # Game -> Supervisor Policy -> Report 或 Deep Research
    builder.add_edge("game_agent", "risk_guardian_agent")
    builder.add_edge("game_agent", "opportunity_advocate_agent")
    builder.add_edge("game_agent", "evidence_guardian_agent")
    builder.add_edge("risk_guardian_agent", "deliberation_coordinator")
    builder.add_edge("opportunity_advocate_agent", "deliberation_coordinator")
    builder.add_edge("evidence_guardian_agent", "deliberation_coordinator")
    builder.add_edge("deliberation_coordinator", "supervisor_after_game")
    builder.add_conditional_edges(
        "supervisor_after_game",
        route_after_game,
        {
            "report_agent": "report_agent",
            "deep_research": "deep_research"
        }
    )

    # Report -> Supervisor Policy -> Critic
    builder.add_edge("report_agent", "supervisor_after_report")
    builder.add_conditional_edges(
        "supervisor_after_report",
        route_after_report,
        {
            "critic_agent": "critic_agent"
        }
    )

    # Critic -> Supervisor Policy -> END 或回退
    builder.add_edge("critic_agent", "supervisor_after_critic")
    builder.add_conditional_edges(
        "supervisor_after_critic",
        route_after_critic,
        {
            "game_agent": "game_agent",
            "report_agent": "report_agent",
            "profiling_agent": "profiling_agent",
            "deep_research": "deep_research",
            END: END
        }
    )

    # Deep Research -> Report（研究完成后生成报告）
    builder.add_edge("deep_research", "report_agent")

    # Multimodal -> Critic（多模态解析后直接审计）
    builder.add_edge("multimodal_parser", "critic_agent")

    # 编译图（设置更高的 recursion_limit 以支持审计回退）
    # 默认25步不够用，扩展到50步（支持更多次审计回退）
    graph = builder.compile(
        checkpointer=None,
        interrupt_before=None,
        interrupt_after=None,
        debug=False
    )
    # Note: LangGraph recursion_limit 在 invoke() 时设置，而非 compile()

    return graph


# 创建全局图实例
def create_dual_loop_graph() -> StateGraph:
    """Backward-compatible wrapper kept for older tests/scripts."""
    return create_dual_loop_supervisor()


supervisor_graph = create_dual_loop_supervisor()


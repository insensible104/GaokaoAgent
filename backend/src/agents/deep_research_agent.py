"""Deep research adapter node that bridges supervisor state and the research subgraph."""

from __future__ import annotations

from langchain_core.messages import AIMessage

from models.research_state import DeepResearchState
from models.state import SupervisorState
from subgraphs import deep_research_subgraph
from utils.agent_bus import get_messages_for_stage, publish_agent_message, remember


def deep_research_agent_node(state: SupervisorState) -> dict:
    """Run the deep research subgraph and emit structured protocol artifacts."""
    print("[Deep Research Agent] starting slow-loop research...")

    inbound_messages = get_messages_for_stage(
        state,
        stage="routing",
        recipients=["deep_research"],
    ) + get_messages_for_stage(
        state,
        stage="profiling",
        recipients=["deep_research"],
    ) + get_messages_for_stage(
        state,
        stage="post_game_deliberation",
        recipients=["deep_research"],
    )

    messages = state.get("messages", [])
    if not messages:
        return {
            "current_agent": "deep_research_agent",
            "agent_messages": publish_agent_message(
                sender="deep_research_agent",
                stage="deep_research",
                message_type="failure",
                content="Deep research aborted because the supervisor state had no user messages.",
                recipients=["critic_agent"],
                action_preference="critic_agent",
                confidence=0.2,
            )["agent_messages"],
            "agent_memories": remember(
                agent_name="deep_research_agent",
                stage="deep_research",
                note_type="failure",
                content="No user messages available for research topic extraction.",
                importance=0.8,
            )["agent_memories"],
            "debug_logs": ["[ERROR] Deep Research: missing input messages"],
            "messages": [AIMessage(content="Deep research failed because no input messages were available.")],
        }

    user_message = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
    research_topic = state.get("research_topic") or user_message

    subgraph_input: DeepResearchState = {
        "research_topic": research_topic,
        "sub_questions": [],
        "search_queries": [],
        "search_results": [],
        "is_sufficient": False,
        "knowledge_gaps": [],
        "information_density": 0.0,
        "research_loop_count": 0,
        "max_research_loops": 2,
        "research_report": None,
        "debug_logs": [],
    }

    try:
        result = deep_research_subgraph.invoke(subgraph_input)
        research_report = result.get("research_report", "")
        loop_count = result.get("research_loop_count", 0)
        info_density = float(result.get("information_density", 0.0))
        search_queries = result.get("search_queries", [])
        search_results = result.get("search_results", [])
        debug_logs = result.get("debug_logs", [])

        return {
            "research_report": research_report,
            "research_loop_count": loop_count,
            "web_research_results": search_results,
            "search_queries": search_queries,
            "loop_history": ["slow"],
            "agent_messages": publish_agent_message(
                sender="deep_research_agent",
                stage="deep_research",
                message_type="summary",
                content=(
                    f"Deep research completed with loop_count={loop_count}, "
                    f"information_density={info_density:.2f}, inbound_context={len(inbound_messages)}."
                ),
                recipients=["report_agent", "critic_agent"],
                action_preference="report_agent",
                confidence=min(1.0, max(0.45, info_density)),
                metadata={
                    "loop_count": loop_count,
                    "information_density": round(info_density, 3),
                    "query_count": len(search_queries),
                    "result_count": len(search_results),
                },
            )["agent_messages"],
            "agent_memories": remember(
                agent_name="deep_research_agent",
                stage="deep_research",
                note_type="research_summary",
                content=(
                    f"Completed topic '{research_topic[:80]}' with density={info_density:.2f} "
                    f"after {loop_count} loops."
                ),
                importance=min(1.0, max(0.5, info_density)),
            )["agent_memories"],
            "current_agent": "deep_research_agent",
            "debug_logs": debug_logs
            + [f"[Deep Research] completed {loop_count} loops with density={info_density:.2f}"],
            "messages": [AIMessage(content=f"Deep research completed.\n\n{research_report}")],
        }
    except Exception as exc:
        return {
            "research_report": f"Deep research failed: {exc}",
            "agent_messages": publish_agent_message(
                sender="deep_research_agent",
                stage="deep_research",
                message_type="failure",
                content=f"Deep research failed: {exc}",
                recipients=["critic_agent", "report_agent"],
                action_preference="critic_agent",
                confidence=0.2,
            )["agent_messages"],
            "agent_memories": remember(
                agent_name="deep_research_agent",
                stage="deep_research",
                note_type="failure",
                content=f"Subgraph execution failed: {exc}",
                importance=0.8,
            )["agent_memories"],
            "current_agent": "deep_research_agent",
            "debug_logs": [f"[ERROR] Deep Research Subgraph failed: {exc}"],
            "messages": [AIMessage(content=f"Deep research failed: {exc}")],
        }

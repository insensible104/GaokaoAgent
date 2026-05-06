"""Smoke test for research-only report generation."""

from __future__ import annotations

from agents.report_agent import report_agent_node


def _base_state() -> dict:
    return {
        "messages": [],
        "intent_classification": None,
        "active_loop": None,
        "loop_history": [],
        "user_profile": None,
        "game_matrix": None,
        "report_draft": None,
        "research_topic": "计算机专业就业情况",
        "search_queries": [],
        "web_research_results": [],
        "knowledge_gaps": [],
        "research_loop_count": 1,
        "research_report": "# 深度调研报告\n\n## 核心结论\n该专业就业面较广。\n\n## 风险\n需核查官方培养方案。",
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


def test_report_agent_supports_research_only_branch() -> None:
    result = report_agent_node(_base_state())
    assert result["report_draft"] is not None
    assert "深度调研报告" in result["report_draft"].full_markdown
    assert result["agent_messages"][0].metadata["report_mode"] == "research_only"


if __name__ == "__main__":
    test_report_agent_supports_research_only_branch()
    print("report agent research-only smoke tests passed")

"""Deep Research Subgraph 构建器"""
from langgraph.graph import StateGraph, START, END

from models.research_state import DeepResearchState
from subgraphs.deep_research import (
    plan_research,
    execute_research,
    reflect_research,
    synthesize_report,
    should_continue_research,
)


def create_deep_research_subgraph() -> StateGraph:
    """
    创建 Deep Research Subgraph

    流程：Plan -> Execute -> Reflect -> [Continue | Synthesize]
                  ↑__________________________|
    """
    builder = StateGraph(DeepResearchState)

    # 添加节点
    builder.add_node("plan", plan_research)
    builder.add_node("execute", execute_research)
    builder.add_node("reflect", reflect_research)
    builder.add_node("synthesize", synthesize_report)

    # 设置入口
    builder.add_edge(START, "plan")

    # Plan -> Execute
    builder.add_edge("plan", "execute")

    # Execute -> Reflect
    builder.add_edge("execute", "reflect")

    # Reflect -> [Plan | Synthesize]（循环或终止）
    builder.add_conditional_edges(
        "reflect",
        should_continue_research,
        {
            "plan": "plan",        # 信息不足，继续循环
            "synthesize": "synthesize"  # 信息充分，生成报告
        }
    )

    # Synthesize -> END
    builder.add_edge("synthesize", END)

    return builder.compile()


# 创建全局 Subgraph 实例
deep_research_subgraph = create_deep_research_subgraph()

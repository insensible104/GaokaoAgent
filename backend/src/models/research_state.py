"""Deep Research Subgraph 状态定义"""
from typing import TypedDict, Annotated, Optional, List
import operator


class DeepResearchState(TypedDict):
    """Deep Research Subgraph 状态"""

    # 输入
    research_topic: str  # 研究主题

    # Plan 阶段输出
    sub_questions: Annotated[list, operator.add]  # 子问题列表

    # Execute 阶段输出
    search_queries: Annotated[list, operator.add]  # 搜索查询历史
    search_results: Annotated[list, operator.add]  # 搜索结果
    research_evidence_cards: Annotated[list, operator.add]  # 结构化来源证据卡

    # Reflect 阶段输出
    is_sufficient: bool  # 信息是否充分
    knowledge_gaps: Annotated[list, operator.add]  # 知识缺口
    information_density: float  # 信息密度评分（0-1）

    # 循环控制
    research_loop_count: int  # 当前循环次数
    max_research_loops: int   # 最大循环次数

    # 最终输出
    research_report: Optional[str]  # 研究报告

    # 调试
    debug_logs: Annotated[list, operator.add]

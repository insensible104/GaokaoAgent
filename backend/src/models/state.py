"""LangGraph 状态定义"""
from typing import TypedDict, Annotated, Optional, List
from langgraph.graph import add_messages
import operator

from .user_profile import UserProfile
from .game_matrix import GameMatrix
from .report import ReportDraft
from .audit_result import AuditResult
from .agent_communication import AgentMessage, AgentMemoryEntry, DeliberationSummary
from .intent import IntentClassification, LoopType


def keep_latest(_left, right):
    """Use the latest non-empty scalar value when parallel graph branches write."""
    return right if right not in (None, "") else _left


class SupervisorState(TypedDict):
    """Supervisor 统一状态（双循环架构）"""
    messages: Annotated[list, add_messages]

    # === 元认知层（Meta-Router 输出）===
    intent_classification: Optional[IntentClassification]  # 意图分类结果
    active_loop: Optional[LoopType]  # 当前激活的循环类型
    loop_history: Annotated[list, operator.add]  # 循环执行历史

    # === 快思考循环（Fast Loop - Quant）===
    # Agent 1 输出
    user_profile: Optional[UserProfile]
    explicit_profile: Optional[dict]

    # Agent 2 输出
    game_matrix: Optional[GameMatrix]

    # Agent 3 输出（Quant 报告）
    report_draft: Optional[ReportDraft]

    # === 慢思考循环（Slow Loop - Research）===
    research_topic: Optional[str]  # 研究主题
    search_queries: Annotated[list, operator.add]  # 搜索查询历史
    web_research_results: Annotated[list, operator.add]  # 网络搜索结果
    research_evidence_cards: Annotated[list, operator.add]  # 结构化来源证据卡
    knowledge_gaps: Annotated[list, operator.add]  # 知识缺口（驱动迭代）
    research_loop_count: int  # 研究循环次数
    research_report: Optional[str]  # 研究报告

    # === 多模态循环（Multimodal Loop）===
    pdf_sources: Annotated[list, operator.add]  # PDF 文件路径
    vision_results: Annotated[list, operator.add]  # 视觉模型输出
    health_restrictions: Annotated[list, operator.add]  # 体检限制提取结果

    # === 审计层（Agent 4 输出）===
    audit_result: Optional[AuditResult]
    step_rewards: Annotated[list, operator.add]  # Step-Level 奖励记录
    reflection_history: Annotated[list, operator.add]  # Reflexion 批评历史
    orchestration_trace: Annotated[list, operator.add]  # Supervisor policy trajectory
    next_action: Optional[str]  # Next action chosen by supervisor policy
    orchestration_reward: Optional[float]  # Terminal reward proxy for offline RL
    orchestration_reward_components: Optional[dict]  # Auditable reward terms for trajectory learning
    agent_messages: Annotated[list, operator.add]  # Public protocol messages among agents
    agent_memories: Annotated[list, operator.add]  # Scoped private memories
    deliberation_summaries: Annotated[list, operator.add]  # Aggregated multi-agent votes
    protocol_violations: Annotated[list, operator.add]  # Communication contract violations
    recommended_next_action: Optional[str]  # Deliberation output for supervisor policy

    # === 控制流 ===
    current_agent: Annotated[str, keep_latest]  # 当前活跃的 Agent
    retry_count: int    # 回退重试次数
    human_approved: bool  # 人工是否已确认
    max_loops: int  # 最大循环次数（防止无限循环）

    # === 调试信息 ===
    debug_logs: Annotated[list, operator.add]

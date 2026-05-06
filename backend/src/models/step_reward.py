"""Step-Level Reward 模型定义"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ToolCallType(str, Enum):
    """工具调用类型"""
    QUANT_ENGINE = "quant_engine"  # 量化引擎
    SEARCH_TOOL = "search_tool"    # 网络搜索
    PDF_PARSER = "pdf_parser"      # PDF 解析
    VISION_ANALYZER = "vision_analyzer"  # Vision 分析
    LLM_CALL = "llm_call"         # LLM 调用


class RewardLevel(str, Enum):
    """奖励等级"""
    HIGHLY_POSITIVE = "highly_positive"  # +1.0
    POSITIVE = "positive"                # +0.5
    NEUTRAL = "neutral"                  # 0.0
    NEGATIVE = "negative"                # -0.5
    HIGHLY_NEGATIVE = "highly_negative"  # -1.0


class StepReward(BaseModel):
    """单步奖励记录"""
    step_id: int = Field(description="步骤编号")
    agent_name: str = Field(description="执行的 Agent")
    tool_call_type: ToolCallType = Field(description="工具调用类型")
    query: str = Field(description="查询内容")
    result_summary: str = Field(description="结果摘要")

    # 评估结果
    reward_level: RewardLevel = Field(description="奖励等级")
    reward_value: float = Field(description="奖励数值（-1.0 到 1.0）")
    reasoning: str = Field(description="奖励原因（可解释性）")

    # 检查项
    is_result_empty: bool = Field(description="结果是否为空")
    is_tool_appropriate: bool = Field(description="工具选择是否合适")
    is_result_relevant: bool = Field(description="结果是否与问题相关")
    token_efficiency: float = Field(
        ge=0.0, le=1.0,
        description="Token 效率评分（0-1）"
    )


class RewardRules:
    """奖励规则定义（可配置）"""

    # 规则 1：结果为空 -> 强烈负奖励
    EMPTY_RESULT_PENALTY = -1.0

    # 规则 2：工具不匹配 -> 负奖励
    INAPPROPRIATE_TOOL_PENALTY = -0.8

    # 规则 3：结果不相关 -> 负奖励
    IRRELEVANT_RESULT_PENALTY = -0.5

    # 规则 4：Token 效率低 -> 轻微负奖励
    LOW_EFFICIENCY_PENALTY = -0.3

    # 规则 5：完美执行 -> 正奖励
    PERFECT_EXECUTION_REWARD = 1.0

    # 规则 6：有效但不完美 -> 中等奖励
    GOOD_EXECUTION_REWARD = 0.5

    @staticmethod
    def evaluate_step(
        tool_call_type: ToolCallType,
        query: str,
        result: Any,
        user_query: str
    ) -> Dict:
        """
        评估单步执行的质量

        Args:
            tool_call_type: 工具类型
            query: 工具查询内容
            result: 工具返回结果
            user_query: 用户原始问题

        Returns:
            {
                'reward_value': float,
                'reasoning': str,
                'is_result_empty': bool,
                'is_tool_appropriate': bool,
                'is_result_relevant': bool,
                'token_efficiency': float
            }
        """
        # 检查 1：结果是否为空
        is_result_empty = False
        if result is None or result == "" or (isinstance(result, (list, dict)) and len(result) == 0):
            is_result_empty = True

        # 检查 2：工具选择是否合适
        is_tool_appropriate = RewardRules._check_tool_appropriateness(
            tool_call_type, query, user_query
        )

        # 检查 3：结果是否相关
        is_result_relevant = RewardRules._check_result_relevance(
            result, user_query
        )

        # 检查 4：Token 效率
        token_efficiency = RewardRules._calculate_token_efficiency(
            tool_call_type, query, result
        )

        # 计算奖励值
        reward_value = 0.0
        reasoning_parts = []

        if is_result_empty:
            reward_value = RewardRules.EMPTY_RESULT_PENALTY
            reasoning_parts.append("结果为空，无效调用")
        elif not is_tool_appropriate:
            reward_value = RewardRules.INAPPROPRIATE_TOOL_PENALTY
            reasoning_parts.append("工具选择不当")
        elif not is_result_relevant:
            reward_value = RewardRules.IRRELEVANT_RESULT_PENALTY
            reasoning_parts.append("结果与问题不相关")
        elif token_efficiency < 0.5:
            reward_value = RewardRules.LOW_EFFICIENCY_PENALTY
            reasoning_parts.append(f"Token 效率低 ({token_efficiency:.2f})")
        else:
            # 根据效率给正奖励
            if token_efficiency > 0.9:
                reward_value = RewardRules.PERFECT_EXECUTION_REWARD
                reasoning_parts.append("完美执行")
            else:
                reward_value = RewardRules.GOOD_EXECUTION_REWARD
                reasoning_parts.append("有效执行")

        return {
            'reward_value': reward_value,
            'reasoning': "; ".join(reasoning_parts) if reasoning_parts else "正常执行",
            'is_result_empty': is_result_empty,
            'is_tool_appropriate': is_tool_appropriate,
            'is_result_relevant': is_result_relevant,
            'token_efficiency': token_efficiency
        }

    @staticmethod
    def _check_tool_appropriateness(
        tool_call_type: ToolCallType,
        query: str,
        user_query: str
    ) -> bool:
        """
        检查工具选择是否合适

        反例：
        - 用 quant_engine 查"清华大学地址" -> 不合适
        - 用 search_tool 查"录取概率" -> 不合适（应该用 quant_engine）
        """
        # 定义工具-任务映射
        quant_keywords = ["概率", "位次", "分数", "录取", "冲稳保", "排名"]
        search_keywords = ["地址", "电话", "官网", "介绍", "评价", "口碑"]
        pdf_keywords = ["章程", "体检", "限制", "规则", "单科"]

        query_lower = query.lower()
        user_query_lower = user_query.lower()
        combined = query_lower + " " + user_query_lower

        if tool_call_type == ToolCallType.QUANT_ENGINE:
            # 如果查询包含 search_keywords，说明用错了工具
            for keyword in search_keywords:
                if keyword in combined:
                    return False
            return True

        elif tool_call_type == ToolCallType.SEARCH_TOOL:
            # 如果查询包含 quant_keywords，说明应该用量化引擎
            for keyword in quant_keywords:
                if keyword in combined:
                    return False
            return True

        elif tool_call_type == ToolCallType.PDF_PARSER:
            # PDF 查询应该包含特定关键词
            for keyword in pdf_keywords:
                if keyword in combined:
                    return True
            return False

        # 默认认为合适
        return True

    @staticmethod
    def _check_result_relevance(result: Any, user_query: str) -> bool:
        """
        检查结果是否与用户问题相关

        简单实现：检查结果中是否包含用户查询的关键词
        """
        if not result:
            return False

        result_str = str(result).lower()
        user_query_lower = user_query.lower()

        # 提取用户查询中的关键词（简单分词）
        keywords = user_query_lower.split()

        # 检查是否有关键词出现在结果中
        match_count = sum(1 for kw in keywords if kw in result_str and len(kw) > 2)

        # 如果至少有 30% 的关键词匹配，认为相关
        return match_count >= len(keywords) * 0.3

    @staticmethod
    def _calculate_token_efficiency(
        tool_call_type: ToolCallType,
        query: str,
        result: Any
    ) -> float:
        """
        计算 Token 效率

        效率 = 有用信息量 / 消耗的 token

        简化版本：根据工具类型和结果大小估算
        """
        if not result:
            return 0.0

        result_size = len(str(result))

        # 根据工具类型设定期望的结果大小范围
        if tool_call_type == ToolCallType.QUANT_ENGINE:
            # 量化引擎应该返回简洁的数据
            expected_range = (100, 1000)
        elif tool_call_type == ToolCallType.SEARCH_TOOL:
            # 搜索工具可能返回较长结果
            expected_range = (500, 3000)
        elif tool_call_type == ToolCallType.PDF_PARSER:
            # PDF 解析应该只返回相关段落
            expected_range = (300, 2000)
        else:
            expected_range = (100, 1000)

        # 如果结果大小在期望范围内，效率高
        if expected_range[0] <= result_size <= expected_range[1]:
            return 1.0
        elif result_size < expected_range[0]:
            # 结果太少，可能信息不足
            return 0.7
        else:
            # 结果太多，可能没有精准定位
            overflow_ratio = result_size / expected_range[1]
            return max(0.3, 1.0 / overflow_ratio)


# === 便捷函数 ===
def create_step_reward(
    step_id: int,
    agent_name: str,
    tool_call_type: ToolCallType,
    query: str,
    result: Any,
    user_query: str
) -> StepReward:
    """
    创建步骤奖励记录

    Args:
        step_id: 步骤编号
        agent_name: Agent 名称
        tool_call_type: 工具类型
        query: 查询内容
        result: 结果
        user_query: 用户原始问题

    Returns:
        StepReward 对象
    """
    # 评估执行质量
    evaluation = RewardRules.evaluate_step(
        tool_call_type, query, result, user_query
    )

    # 确定奖励等级
    reward_value = evaluation['reward_value']
    if reward_value >= 0.8:
        reward_level = RewardLevel.HIGHLY_POSITIVE
    elif reward_value >= 0.3:
        reward_level = RewardLevel.POSITIVE
    elif reward_value >= -0.3:
        reward_level = RewardLevel.NEUTRAL
    elif reward_value >= -0.7:
        reward_level = RewardLevel.NEGATIVE
    else:
        reward_level = RewardLevel.HIGHLY_NEGATIVE

    # 生成结果摘要
    result_summary = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)

    return StepReward(
        step_id=step_id,
        agent_name=agent_name,
        tool_call_type=tool_call_type,
        query=query,
        result_summary=result_summary,
        reward_level=reward_level,
        reward_value=reward_value,
        reasoning=evaluation['reasoning'],
        is_result_empty=evaluation['is_result_empty'],
        is_tool_appropriate=evaluation['is_tool_appropriate'],
        is_result_relevant=evaluation['is_result_relevant'],
        token_efficiency=evaluation['token_efficiency']
    )

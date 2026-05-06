"""强化学习环境定义

定义志愿填报的RL环境，包括：
1. State（状态空间）：用户画像、历史数据
2. Action（动作空间）：Agent的输出（候选志愿、审核建议、报告）
3. Reward（奖励函数）：基于回测结果的综合评分
4. Environment（环境模拟器）：模拟志愿填报流程
"""

from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

# 导入现有模块
from engines.backtest_framework import run_backtest_for_row
from engines.quant_metrics import VolunteerOption, compute_all_metrics


# ============================================
# State（状态空间）
# ============================================

class VolunteerState(BaseModel):
    """志愿填报环境状态"""

    # 用户画像
    user_rank: int = Field(description="用户位次")
    category: str = Field(description="科类（physics/history）")
    preferences: List[str] = Field(
        default_factory=list,
        description="专业偏好（如['计算机', '软件工程']）"
    )
    blacklist: List[str] = Field(
        default_factory=list,
        description="专业黑名单"
    )

    # 历史数据
    historical_data: Dict = Field(
        default_factory=dict,
        description="历史录取数据（DataFrame序列化）"
    )

    # 约束条件
    budget: int = Field(default=45, description="志愿配额")
    year: int = Field(description="目标年份（用于回测）")

    # 环境元信息
    episode_id: int = Field(default=0, description="Episode编号")
    step: int = Field(default=0, description="当前步骤")


# ============================================
# Action（动作空间）
# ============================================

class Candidate(BaseModel):
    """单个候选志愿"""
    school_name: str
    major_name: str
    major_group_code: Optional[str] = None
    predicted_prob: float = Field(ge=0.0, le=1.0, description="预测录取概率")
    strategy_tag: str = Field(description="冲/稳/保")
    volunteer_index: int = Field(description="志愿序号 1-45")


class GameAgentAction(BaseModel):
    """Game Agent 的动作（生成候选志愿）"""
    candidates: List[Candidate] = Field(
        description="45个候选志愿"
    )
    reasoning: str = Field(default="", description="生成理由")


class CriticAgentAction(BaseModel):
    """Critic Agent 的动作（审核并修订）"""
    approval: bool = Field(description="是否通过审核")
    issues: List[str] = Field(
        default_factory=list,
        description="发现的问题"
    )
    revised_candidates: List[Candidate] = Field(
        default_factory=list,
        description="修订后的候选志愿"
    )
    reasoning: str = Field(default="", description="审核理由")


class ReportAgentAction(BaseModel):
    """Report Agent 的动作（生成报告）"""
    report_title: str = Field(default="GaokaoAgent 志愿填报建议书")
    executive_summary: str = Field(description="执行摘要")
    strategy_analysis: str = Field(description="策略分析")
    risk_warnings: List[str] = Field(default_factory=list, description="风险警示")
    reasoning: str = Field(default="", description="生成理由")


# ============================================
# Reward（奖励函数）
# ============================================

class ActualOutcome(BaseModel):
    """真实录取结果（环境反馈）"""
    admitted: bool = Field(description="是否被录取")
    admitted_school: Optional[str] = Field(default=None)
    admitted_major: Optional[str] = Field(default=None)
    admitted_index: Optional[int] = Field(
        default=None,
        description="被录取的志愿序号（1-45）"
    )
    actual_min_rank: int = Field(description="实际录取最低位次")


class RewardComponents(BaseModel):
    """奖励组成部分"""
    admission_reward: float = Field(description="录取成功奖励")
    utilization_reward: float = Field(description="位次利用奖励")
    risk_penalty: float = Field(description="风险惩罚")
    diversity_bonus: float = Field(description="多样性奖励")
    total_reward: float = Field(description="总奖励")


def calculate_reward(
    predicted_candidates: List[Candidate],
    actual_outcome: ActualOutcome,
    user_rank: int
) -> RewardComponents:
    """
    计算Episode的总奖励

    奖励组件：
    1. 录取成功奖励（40%）：是否被录取
    2. 位次利用奖励（30%）：遗憾值
    3. 风险惩罚（20%）：滑档风险
    4. 多样性奖励（10%）：志愿多样性

    Returns:
        RewardComponents 对象
    """
    # ============ 1. 录取成功奖励 ============
    if actual_outcome.admitted:
        admission_reward = 1.0

        # 额外奖励：录取到靠前的志愿
        if actual_outcome.admitted_index is not None:
            rank_bonus = (45 - actual_outcome.admitted_index) / 45
            admission_reward += rank_bonus * 0.5

        # 冲刺志愿录取 -> 额外奖励
        admitted_candidate = next(
            (c for c in predicted_candidates if c.volunteer_index == actual_outcome.admitted_index),
            None
        )
        if admitted_candidate and admitted_candidate.strategy_tag == 'rush':
            admission_reward += 0.3  # 冲刺成功奖励

    else:
        # 滑档 -> 严重惩罚
        admission_reward = -2.0

    # ============ 2. 位次利用奖励 ============
    # 转换为VolunteerOption格式
    volunteer_options = [
        VolunteerOption(
            school_name=c.school_name,
            major_name=c.major_name,
            admission_prob=c.predicted_prob,
            min_rank_pred=int(user_rank / (c.predicted_prob + 0.01)),  # 粗略估计
            hist_min_rank=int(user_rank / (c.predicted_prob + 0.01)),
            hist_max_rank=None,
            volunteer_index=c.volunteer_index
        )
        for c in predicted_candidates
    ]

    # 计算量化指标
    metrics = compute_all_metrics(volunteer_options, user_rank)

    # 遗憾值越小越好
    regret_value = metrics.regret_value
    utilization_reward = 1.0 - min(regret_value / 1000.0, 1.0)  # 归一化到[0,1]

    # ============ 3. 风险惩罚 ============
    slip_risk = metrics.slip_risk_rate
    risk_penalty = -slip_risk * 2.0  # 滑档风险越高，惩罚越大

    # ============ 4. 多样性奖励 ============
    # 鼓励学校多样性（避免全部选同一学校）
    unique_schools = len(set(c.school_name for c in predicted_candidates))
    diversity_bonus = (unique_schools / 45) * 0.5  # 归一化

    # ============ 总奖励（加权求和）============
    total_reward = (
        0.4 * admission_reward +
        0.3 * utilization_reward +
        0.2 * risk_penalty +
        0.1 * diversity_bonus
    )

    return RewardComponents(
        admission_reward=admission_reward,
        utilization_reward=utilization_reward,
        risk_penalty=risk_penalty,
        diversity_bonus=diversity_bonus,
        total_reward=total_reward
    )


# ============================================
# Environment（环境模拟器）
# ============================================

class VolunteerEnvironment:
    """
    志愿填报RL环境

    模拟真实的志愿填报流程：
    1. 给定用户画像（state）
    2. Agent生成志愿方案（action）
    3. 使用历史数据回测，计算reward
    """

    def __init__(self, historical_data: Dict[int, pd.DataFrame]):
        """
        Args:
            historical_data: {year: DataFrame} 历史录取数据
        """
        self.historical_data = historical_data
        self.current_state: Optional[VolunteerState] = None

    def reset(self, user_rank: int, category: str, year: int) -> VolunteerState:
        """
        重置环境，开始新的Episode

        Args:
            user_rank: 用户位次
            category: 科类
            year: 目标年份（用于回测）

        Returns:
            初始状态
        """
        self.current_state = VolunteerState(
            user_rank=user_rank,
            category=category,
            preferences=[],  # 可以从用户输入获取
            year=year
        )

        return self.current_state

    def step(
        self,
        action: List[Candidate]
    ) -> Tuple[VolunteerState, float, bool, Dict]:
        """
        执行一个动作，返回新状态、奖励、是否结束、额外信息

        Args:
            action: Agent的动作（候选志愿列表）

        Returns:
            (next_state, reward, done, info)
        """
        if self.current_state is None:
            raise ValueError("环境未初始化，请先调用 reset()")

        # ========== 模拟录取结果 ==========
        # 使用历史数据回测
        actual_outcome = self._simulate_admission(action)

        # ========== 计算奖励 ==========
        reward_components = calculate_reward(
            predicted_candidates=action,
            actual_outcome=actual_outcome,
            user_rank=self.current_state.user_rank
        )

        # ========== 更新状态 ==========
        self.current_state.step += 1

        # ========== 判断是否结束 ==========
        done = True  # 志愿填报是单步任务，执行完即结束

        # ========== 额外信息 ==========
        info = {
            'actual_outcome': actual_outcome,
            'reward_components': reward_components,
            'metrics': {}  # 可以添加更多统计信息
        }

        return self.current_state, reward_components.total_reward, done, info

    def _simulate_admission(self, candidates: List[Candidate]) -> ActualOutcome:
        """
        模拟录取结果（使用历史数据回测）

        Args:
            candidates: 候选志愿列表

        Returns:
            ActualOutcome 对象
        """
        year = self.current_state.year
        user_rank = self.current_state.user_rank

        # 获取该年份的历史数据
        if year not in self.historical_data:
            # 如果没有该年数据，随机模拟
            return ActualOutcome(
                admitted=False,
                actual_min_rank=user_rank
            )

        year_data = self.historical_data[year]

        # 按志愿顺序检查录取
        for candidate in sorted(candidates, key=lambda c: c.volunteer_index):
            # 查找该学校专业的实际录取位次
            school_data = year_data[
                (year_data['院校名称'] == candidate.school_name) &
                (year_data['专业/类'] == candidate.major_name)
            ]

            if school_data.empty:
                continue

            # 获取实际最低位次
            actual_min_rank = school_data['最低分\r\n平均排位'].iloc[0]
            if pd.isna(actual_min_rank):
                actual_min_rank = school_data['最低排位'].iloc[0] if '最低排位' in school_data.columns else None

            if actual_min_rank is None or pd.isna(actual_min_rank):
                continue

            actual_min_rank = int(float(actual_min_rank))

            # 判断是否录取（用户位次 <= 实际最低位次）
            if user_rank <= actual_min_rank:
                return ActualOutcome(
                    admitted=True,
                    admitted_school=candidate.school_name,
                    admitted_major=candidate.major_name,
                    admitted_index=candidate.volunteer_index,
                    actual_min_rank=actual_min_rank
                )

        # 所有志愿都未录取 -> 滑档
        return ActualOutcome(
            admitted=False,
            actual_min_rank=user_rank
        )


# ============================================
# 测试代码
# ============================================

if __name__ == "__main__":
    print("=== RL环境定义测试 ===\n")

    # 构造测试数据
    test_candidates = [
        Candidate(
            school_name="清华大学",
            major_name="计算机科学与技术",
            predicted_prob=0.3,
            strategy_tag="rush",
            volunteer_index=1
        ),
        Candidate(
            school_name="北京大学",
            major_name="软件工程",
            predicted_prob=0.6,
            strategy_tag="target",
            volunteer_index=2
        ),
        Candidate(
            school_name="浙江大学",
            major_name="计算机",
            predicted_prob=0.9,
            strategy_tag="safe",
            volunteer_index=3
        )
    ]

    # 测试奖励函数
    actual_outcome = ActualOutcome(
        admitted=True,
        admitted_school="北京大学",
        admitted_major="软件工程",
        admitted_index=2,
        actual_min_rank=1000
    )

    reward_components = calculate_reward(
        predicted_candidates=test_candidates,
        actual_outcome=actual_outcome,
        user_rank=1050
    )

    print("奖励组件测试:")
    print(f"  录取成功奖励: {reward_components.admission_reward:.3f}")
    print(f"  位次利用奖励: {reward_components.utilization_reward:.3f}")
    print(f"  风险惩罚: {reward_components.risk_penalty:.3f}")
    print(f"  多样性奖励: {reward_components.diversity_bonus:.3f}")
    print(f"  总奖励: {reward_components.total_reward:.3f}")
    print()

    # 测试环境
    print("环境模拟器测试:")
    print("  [INFO] 环境定义完成，等待历史数据加载")
    print("  [INFO] 可以与回测框架集成，使用真实2024年数据")
    print()

    print("测试完成！")


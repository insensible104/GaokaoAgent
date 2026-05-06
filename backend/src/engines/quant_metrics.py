"""量化指标计算模块

实现三大核心指标：
1. 志愿遗憾值（Regret Value）：失去的机会成本
2. 滑档风险率（Slip Risk Rate）：所有志愿都失败的概率
3. 位次利用深度（Rank Utilization Depth）：位次使用效率
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class VolunteerOption(BaseModel):
    """单个志愿选项"""
    school_name: str = Field(description="学校名称")
    major_name: str = Field(description="专业名称")
    admission_prob: float = Field(ge=0.0, le=1.0, description="录取概率")
    min_rank_pred: int = Field(description="预测最低位次")
    hist_min_rank: int = Field(description="历史最低位次")
    hist_max_rank: Optional[int] = Field(default=None, description="历史最高位次")
    volunteer_index: int = Field(description="志愿序号（1-45）")


class QuantMetrics(BaseModel):
    """量化指标结果"""

    # 1. 志愿遗憾值
    regret_value: float = Field(
        description="志愿遗憾值（位次差）"
    )
    regret_explanation: str = Field(
        description="遗憾值解释（哪个志愿被浪费）"
    )

    # 2. 滑档风险率
    slip_risk_rate: float = Field(
        ge=0.0, le=1.0,
        description="滑档风险率（所有志愿都失败的概率）"
    )
    slip_risk_level: str = Field(
        description="风险等级: LOW/MEDIUM/HIGH/CRITICAL"
    )

    # 3. 位次利用深度
    avg_rank_utilization: float = Field(
        ge=0.0, le=1.0,
        description="平均位次利用深度（0=浪费，1=充分利用）"
    )
    utilization_level: str = Field(
        description="利用等级: POOR/FAIR/GOOD/EXCELLENT"
    )

    # 详细分析
    top_regret_volunteers: List[Dict] = Field(
        default_factory=list,
        description="遗憾值最高的前3个志愿"
    )
    weakest_volunteers: List[Dict] = Field(
        default_factory=list,
        description="最薄弱的志愿（概率最低）"
    )


def calculate_regret_value(
    volunteers: List[VolunteerOption],
    user_rank: int
) -> Dict:
    """
    计算志愿遗憾值

    定义：如果用户被录取到第N个志愿，而本可以被录取到第M个志愿（M<N），
         那么遗憾值 = min_rank[M] - min_rank[N]

    计算逻辑：
    1. 找到用户最可能被录取的志愿（prob > 0.5 的第一个）
    2. 计算该志愿与理想志愿的位次差

    Args:
        volunteers: 志愿列表（按顺序排列）
        user_rank: 用户位次

    Returns:
        {
            'regret_value': float,
            'regret_explanation': str,
            'top_regret_volunteers': List[Dict]
        }
    """
    if not volunteers:
        return {
            'regret_value': 0.0,
            'regret_explanation': '无志愿数据',
            'top_regret_volunteers': []
        }

    # 找到第一个录取概率 > 50% 的志愿（预期录取志愿）
    expected_admitted_idx = None
    for i, vol in enumerate(volunteers):
        if vol.admission_prob > 0.5:
            expected_admitted_idx = i
            break

    if expected_admitted_idx is None:
        # 所有志愿概率都 <= 50%，风险极高
        return {
            'regret_value': 0.0,
            'regret_explanation': '警告：所有志愿录取概率均 ≤ 50%，滑档风险极高',
            'top_regret_volunteers': []
        }

    # 计算遗憾值：理想志愿（第0个）vs 预期录取志愿
    ideal_rank = volunteers[0].min_rank_pred
    expected_rank = volunteers[expected_admitted_idx].min_rank_pred
    regret_value = ideal_rank - expected_rank

    # 遗憾值不能为负（位次越小越好，如果 ideal < expected，说明首选更好）
    final_regret_value = max(0, regret_value)

    # 生成解释
    if expected_admitted_idx == 0:
        explanation = f"[OK] 预期被第1志愿录取（{volunteers[0].school_name}），无遗憾"
    else:
        if final_regret_value > 0:
            explanation = (
                f"[WARN] 预期被第{expected_admitted_idx + 1}志愿录取"
                f"（{volunteers[expected_admitted_idx].school_name}），"
                f"而非首选志愿（{volunteers[0].school_name}），"
                f"遗憾值 = {final_regret_value:.0f} 位"
            )
        else:
            # 如果首选志愿更好但录取概率低，这是合理的冲刺策略
            explanation = (
                f"[INFO] 预期被第{expected_admitted_idx + 1}志愿录取"
                f"（{volunteers[expected_admitted_idx].school_name}），"
                f"首选志愿（{volunteers[0].school_name}）为冲刺志愿，遗憾值 = 0 位"
            )

    # 找出遗憾值最高的前3个志愿
    top_regrets = []
    for i in range(1, min(len(volunteers), 4)):
        vol = volunteers[i]
        regret = ideal_rank - vol.min_rank_pred
        if regret > 0:  # 只统计正遗憾值
            top_regrets.append({
                'volunteer_index': vol.volunteer_index,
                'school_name': vol.school_name,
                'major_name': vol.major_name,
                'regret_value': regret,
                'admission_prob': vol.admission_prob
            })

    # 按遗憾值排序
    top_regrets = sorted(top_regrets, key=lambda x: x['regret_value'], reverse=True)[:3]

    return {
        'regret_value': final_regret_value,
        'regret_explanation': explanation,
        'top_regret_volunteers': top_regrets
    }


def calculate_slip_risk_rate(
    volunteers: List[VolunteerOption]
) -> Dict:
    """
    计算滑档风险率

    定义：所有志愿都无法录取的概率

    假设各志愿独立，则：
    P(全部滑档) = ∏(1 - P_i)

    风险等级：
    - LOW: < 5%
    - MEDIUM: 5% - 15%
    - HIGH: 15% - 30%
    - CRITICAL: >= 30%

    Args:
        volunteers: 志愿列表

    Returns:
        {
            'slip_risk_rate': float,
            'slip_risk_level': str,
            'weakest_volunteers': List[Dict]
        }
    """
    if not volunteers:
        return {
            'slip_risk_rate': 1.0,
            'slip_risk_level': 'CRITICAL',
            'weakest_volunteers': []
        }

    # 计算滑档概率（假设各志愿独立）
    slip_prob = 1.0
    for vol in volunteers:
        fail_prob = 1 - vol.admission_prob
        slip_prob *= fail_prob

    # 确定风险等级
    if slip_prob < 0.05:
        risk_level = 'LOW'
    elif slip_prob < 0.15:
        risk_level = 'MEDIUM'
    elif slip_prob < 0.30:
        risk_level = 'HIGH'
    else:
        risk_level = 'CRITICAL'

    # 找出最薄弱的3个志愿（录取概率最低）
    weakest = sorted(volunteers, key=lambda v: v.admission_prob)[:3]
    weakest_list = [
        {
            'volunteer_index': vol.volunteer_index,
            'school_name': vol.school_name,
            'major_name': vol.major_name,
            'admission_prob': vol.admission_prob,
            'min_rank_pred': vol.min_rank_pred
        }
        for vol in weakest
    ]

    return {
        'slip_risk_rate': slip_prob,
        'slip_risk_level': risk_level,
        'weakest_volunteers': weakest_list
    }


def calculate_rank_utilization(
    volunteers: List[VolunteerOption],
    user_rank: int
) -> Dict:
    """
    计算位次利用深度

    定义：用户位次在该专业历史录取位次区间的利用程度

    公式：
    utilization = (user_rank - hist_max_rank) / (hist_min_rank - hist_max_rank)

    解释：
    - 0.0: 完全浪费位次（user_rank 远优于 hist_max_rank，可以冲击更好学校）
    - 0.5: 中等利用（位次在历史区间中部）
    - 1.0: 充分利用（压线录取，hist_min_rank）

    利用等级：
    - POOR: < 0.3（浪费位次）
    - FAIR: 0.3 - 0.6（中等利用）
    - GOOD: 0.6 - 0.85（良好利用）
    - EXCELLENT: >= 0.85（充分利用，接近压线）

    Args:
        volunteers: 志愿列表
        user_rank: 用户位次

    Returns:
        {
            'avg_rank_utilization': float,
            'utilization_level': str,
            'volunteers_detail': List[Dict]
        }
    """
    if not volunteers:
        return {
            'avg_rank_utilization': 0.0,
            'utilization_level': 'POOR',
            'volunteers_detail': []
        }

    utilizations = []
    details = []

    for vol in volunteers:
        # 如果没有 hist_max_rank，使用 hist_min_rank + 2000 作为估计
        if vol.hist_max_rank is None or vol.hist_max_rank <= 0:
            hist_max_rank = vol.hist_min_rank + 2000
        else:
            hist_max_rank = vol.hist_max_rank

        hist_min_rank = vol.hist_min_rank

        # 计算利用度
        if hist_max_rank == hist_min_rank:
            # 历史数据只有一年或波动极小
            utilization = 0.5  # 默认中等利用
        else:
            utilization = (user_rank - hist_max_rank) / (hist_min_rank - hist_max_rank)
            utilization = np.clip(utilization, 0.0, 1.0)  # 限制在 [0, 1]

        utilizations.append(utilization)
        details.append({
            'volunteer_index': vol.volunteer_index,
            'school_name': vol.school_name,
            'major_name': vol.major_name,
            'utilization': utilization,
            'user_rank': user_rank,
            'hist_min_rank': hist_min_rank,
            'hist_max_rank': hist_max_rank
        })

    # 计算平均利用深度
    avg_utilization = np.mean(utilizations)

    # 确定利用等级
    if avg_utilization < 0.3:
        utilization_level = 'POOR'
    elif avg_utilization < 0.6:
        utilization_level = 'FAIR'
    elif avg_utilization < 0.85:
        utilization_level = 'GOOD'
    else:
        utilization_level = 'EXCELLENT'

    return {
        'avg_rank_utilization': avg_utilization,
        'utilization_level': utilization_level,
        'volunteers_detail': details
    }


def compute_all_metrics(
    volunteers: List[VolunteerOption],
    user_rank: int
) -> QuantMetrics:
    """
    计算所有量化指标（一站式接口）

    Args:
        volunteers: 志愿列表（按顺序排列）
        user_rank: 用户位次

    Returns:
        QuantMetrics 对象
    """
    # 1. 志愿遗憾值
    regret_result = calculate_regret_value(volunteers, user_rank)

    # 2. 滑档风险率
    slip_result = calculate_slip_risk_rate(volunteers)

    # 3. 位次利用深度
    utilization_result = calculate_rank_utilization(volunteers, user_rank)

    return QuantMetrics(
        regret_value=regret_result['regret_value'],
        regret_explanation=regret_result['regret_explanation'],
        slip_risk_rate=slip_result['slip_risk_rate'],
        slip_risk_level=slip_result['slip_risk_level'],
        avg_rank_utilization=utilization_result['avg_rank_utilization'],
        utilization_level=utilization_result['utilization_level'],
        top_regret_volunteers=regret_result['top_regret_volunteers'],
        weakest_volunteers=slip_result['weakest_volunteers']
    )


# === 快速测试函数 ===
if __name__ == "__main__":
    # 构造测试数据
    test_volunteers = [
        VolunteerOption(
            school_name="清华大学",
            major_name="计算机科学与技术",
            admission_prob=0.3,
            min_rank_pred=500,
            hist_min_rank=500,
            hist_max_rank=300,
            volunteer_index=1
        ),
        VolunteerOption(
            school_name="北京大学",
            major_name="软件工程",
            admission_prob=0.6,
            min_rank_pred=800,
            hist_min_rank=800,
            hist_max_rank=600,
            volunteer_index=2
        ),
        VolunteerOption(
            school_name="浙江大学",
            major_name="计算机",
            admission_prob=0.85,
            min_rank_pred=1200,
            hist_min_rank=1200,
            hist_max_rank=1000,
            volunteer_index=3
        )
    ]

    user_rank = 1000

    metrics = compute_all_metrics(test_volunteers, user_rank)

    print("=== 量化指标测试结果 ===")
    print(f"1. 志愿遗憾值: {metrics.regret_value:.0f} 位")
    print(f"   解释: {metrics.regret_explanation}")
    print(f"\n2. 滑档风险率: {metrics.slip_risk_rate:.2%}")
    print(f"   风险等级: {metrics.slip_risk_level}")
    print(f"\n3. 位次利用深度: {metrics.avg_rank_utilization:.2f}")
    print(f"   利用等级: {metrics.utilization_level}")
    print("\n测试完成！")

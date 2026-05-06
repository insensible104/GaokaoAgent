"""蒙特卡洛仿真引擎

真正的蒙特卡洛模拟，通过多次采样估计录取概率，而不是简单的正态分布 CDF。

核心思想：
1. 从历史位次分布中采样 N 次（默认 10,000 次）
2. 每次采样模拟一个可能的"今年录取位次"
3. 比较用户位次与采样位次，统计录取次数
4. 录取概率 = 录取次数 / 总采样次数
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from scipy.stats import norm, skewnorm


class MonteCarloResult(BaseModel):
    """蒙特卡洛模拟结果"""

    # 基础概率
    admission_prob: float = Field(
        ge=0.0, le=1.0,
        description="录取概率（蒙特卡洛估计）"
    )

    # 预测位次
    min_rank_pred: int = Field(description="预测最低位次（中位数）")
    min_rank_mean: float = Field(description="预测位次均值")

    # 置信区间（基于采样分位数）
    ci_lower: int = Field(description="95% 置信区间下界")
    ci_upper: int = Field(description="95% 置信区间上界")
    ci_90_lower: int = Field(description="90% 置信区间下界")
    ci_90_upper: int = Field(description="90% 置信区间上界")

    # 分布特征
    volatility_std: float = Field(description="波动标准差（调整后）")
    raw_std: float = Field(description="原始标准差（未惩罚）")
    z_score: float = Field(description="Z-score（相对位次优势，基于raw_std）")
    skewness: float = Field(description="偏度（分布对称性）")

    # 模拟元数据
    n_simulations: int = Field(description="模拟次数")
    sample_size: int = Field(description="样本大小（招生人数）")

    # 可视化数据（可选）
    histogram_data: Optional[Dict] = Field(
        default=None,
        description="直方图数据 {bins: [], counts: []}"
    )


def monte_carlo_admission_probability(
    user_rank: int,
    hist_data: pd.DataFrame,
    n_simulations: int = 10000,
    quota_change_rate: float = 0.0,
    sentiment_modifier: float = 0.0,
    penalty_factor: float = 2.0,
    random_seed: Optional[int] = None
) -> MonteCarloResult:
    """
    蒙特卡洛法计算录取概率

    Args:
        user_rank: 用户位次
        hist_data: 历史数据 DataFrame（包含 'min_rank', 'quota' 等列）
        n_simulations: 模拟次数（默认 10,000）
        quota_change_rate: 招生计划变化率（-0.2 表示减少 20%）
        sentiment_modifier: 舆情修正系数（-200 表示位次向下调整 200 位）
        penalty_factor: 小样本惩罚系数
        random_seed: 随机种子（用于复现）

    Returns:
        MonteCarloResult 对象
    """
    if hist_data.empty:
        raise ValueError("历史数据为空，无法进行蒙特卡洛模拟")

    # 设置随机种子
    if random_seed is not None:
        np.random.seed(random_seed)

    # 1. 计算基准位次和标准差
    recent_data = hist_data.tail(3)
    ranks = recent_data['min_rank'].values

    # 加权平均（越近的年份权重越高）
    weights = np.array([0.2, 0.3, 0.5])[-len(ranks):]
    weights = weights / weights.sum()  # 归一化
    base_rank = np.average(ranks, weights=weights)

    # 波动性估计：使用MAD（中位数绝对偏差）代替标准差，对异常值更鲁棒
    median_rank = hist_data['min_rank'].median()
    mad = (hist_data['min_rank'] - median_rank).abs().median()

    # 将MAD转换为标准差等价值
    std = mad * 1.4826 if mad > 0 else base_rank * 0.05

    if pd.isna(std) or std == 0:
        std = base_rank * 0.05  # 默认 5% 波动

    # 2. 小样本惩罚
    latest_quota = recent_data['quota'].iloc[-1] if 'quota' in recent_data.columns else 10
    N = max(latest_quota, 1)
    penalty = penalty_factor / np.sqrt(N)
    adjusted_std = std * (1 + penalty)

    # 3. 考虑招生计划变化（quota_change_rate）
    # 招生计划增加 -> 录取位次下降（min_rank 增大）
    # 招生计划减少 -> 录取位次上升（min_rank 减小）
    quota_adjustment = base_rank * quota_change_rate
    adjusted_base_rank = base_rank + quota_adjustment

    # 4. 考虑舆情修正（sentiment_modifier）
    # 正面舆情 -> 位次下降（min_rank 减小，更难录取）
    # 负面舆情 -> 位次上升（min_rank 增大，更容易录取）
    final_base_rank = adjusted_base_rank + sentiment_modifier

    # 5. 开始蒙特卡洛模拟
    # 假设今年录取位次服从正态分布（可扩展为偏态分布）
    simulated_ranks = np.random.normal(
        loc=final_base_rank,
        scale=adjusted_std,
        size=n_simulations
    )

    # 限制模拟结果在合理范围内（位次最小为 1）
    simulated_ranks = np.maximum(simulated_ranks, 1)

    # 6. 统计录取次数
    # 位次越小越好，所以 user_rank <= simulated_rank 表示录取
    admitted_count = np.sum(user_rank <= simulated_ranks)
    admission_prob = admitted_count / n_simulations

    # 7. 计算分位数（置信区间）
    ci_lower = int(np.percentile(simulated_ranks, 2.5))   # 95% CI 下界
    ci_upper = int(np.percentile(simulated_ranks, 97.5))  # 95% CI 上界
    ci_90_lower = int(np.percentile(simulated_ranks, 5))   # 90% CI 下界
    ci_90_upper = int(np.percentile(simulated_ranks, 95))  # 90% CI 上界

    min_rank_pred = int(np.median(simulated_ranks))  # 中位数
    min_rank_mean = float(np.mean(simulated_ranks))  # 均值

    # 8. 计算分布特征
    volatility_std = float(np.std(simulated_ranks))
    skewness = float(_calculate_skewness(simulated_ranks))

    # 9. 计算Z-score（使用原始std，不受惩罚系数影响）
    # Z-score = (学校位次 - 用户位次) / 原始标准差
    # 表示用户比学校历史位次好多少个标准差（客观优势）
    z_score = (base_rank - user_rank) / std if std > 0 else 0

    # 10. 生成直方图数据（用于可视化）
    hist_counts, hist_bins = np.histogram(simulated_ranks, bins=50)
    histogram_data = {
        'bins': hist_bins.tolist(),
        'counts': hist_counts.tolist(),
        'user_rank': user_rank
    }

    return MonteCarloResult(
        admission_prob=admission_prob,
        min_rank_pred=min_rank_pred,
        min_rank_mean=min_rank_mean,
        ci_lower=max(1, ci_lower),
        ci_upper=ci_upper,
        ci_90_lower=max(1, ci_90_lower),
        ci_90_upper=ci_90_upper,
        volatility_std=volatility_std,
        raw_std=float(std),  # 原始标准差（用于Z-score计算）
        z_score=float(z_score),  # 相对位次优势（基于raw_std）
        skewness=skewness,
        n_simulations=n_simulations,
        sample_size=int(N),
        histogram_data=histogram_data
    )


def monte_carlo_with_skewed_distribution(
    user_rank: int,
    hist_data: pd.DataFrame,
    n_simulations: int = 10000,
    quota_change_rate: float = 0.0,
    sentiment_modifier: float = 0.0,
    penalty_factor: float = 2.0,
    skewness_param: float = 0.0,
    random_seed: Optional[int] = None
) -> MonteCarloResult:
    """
    蒙特卡洛法计算录取概率（支持偏态分布）

    当历史数据表现出明显的偏态特征时（如热门专业位次波动大），
    使用偏态正态分布（Skewed Normal Distribution）更准确。

    Args:
        user_rank: 用户位次
        hist_data: 历史数据 DataFrame
        n_simulations: 模拟次数
        quota_change_rate: 招生计划变化率
        sentiment_modifier: 舆情修正系数
        penalty_factor: 小样本惩罚系数
        skewness_param: 偏度参数（alpha）
            - alpha = 0: 正态分布
            - alpha > 0: 右偏（长尾在右侧）
            - alpha < 0: 左偏（长尾在左侧）
        random_seed: 随机种子

    Returns:
        MonteCarloResult 对象
    """
    if hist_data.empty:
        raise ValueError("历史数据为空")

    if random_seed is not None:
        np.random.seed(random_seed)

    # 1. 计算基准参数（与正态分布版本相同）
    recent_data = hist_data.tail(3)
    ranks = recent_data['min_rank'].values
    weights = np.array([0.2, 0.3, 0.5])[-len(ranks):]
    weights = weights / weights.sum()
    base_rank = np.average(ranks, weights=weights)

    std = hist_data['min_rank'].std()
    if pd.isna(std) or std == 0:
        std = base_rank * 0.05

    latest_quota = recent_data['quota'].iloc[-1] if 'quota' in recent_data.columns else 10
    N = max(latest_quota, 1)
    penalty = penalty_factor / np.sqrt(N)
    adjusted_std = std * (1 + penalty)

    # 2. 应用修正
    quota_adjustment = base_rank * quota_change_rate
    adjusted_base_rank = base_rank + quota_adjustment
    final_base_rank = adjusted_base_rank + sentiment_modifier

    # 3. 使用偏态正态分布采样
    simulated_ranks = skewnorm.rvs(
        a=skewness_param,  # 偏度参数
        loc=final_base_rank,  # 位置参数（均值）
        scale=adjusted_std,   # 尺度参数（标准差）
        size=n_simulations
    )

    simulated_ranks = np.maximum(simulated_ranks, 1)

    # 4. 统计结果（与正态分布版本相同）
    admitted_count = np.sum(user_rank <= simulated_ranks)
    admission_prob = admitted_count / n_simulations

    ci_lower = int(np.percentile(simulated_ranks, 2.5))
    ci_upper = int(np.percentile(simulated_ranks, 97.5))
    ci_90_lower = int(np.percentile(simulated_ranks, 5))
    ci_90_upper = int(np.percentile(simulated_ranks, 95))

    min_rank_pred = int(np.median(simulated_ranks))
    min_rank_mean = float(np.mean(simulated_ranks))

    volatility_std = float(np.std(simulated_ranks))
    skewness = float(_calculate_skewness(simulated_ranks))

    hist_counts, hist_bins = np.histogram(simulated_ranks, bins=50)
    histogram_data = {
        'bins': hist_bins.tolist(),
        'counts': hist_counts.tolist(),
        'user_rank': user_rank
    }

    return MonteCarloResult(
        admission_prob=admission_prob,
        min_rank_pred=min_rank_pred,
        min_rank_mean=min_rank_mean,
        ci_lower=max(1, ci_lower),
        ci_upper=ci_upper,
        ci_90_lower=max(1, ci_90_lower),
        ci_90_upper=ci_90_upper,
        volatility_std=volatility_std,
        skewness=skewness,
        n_simulations=n_simulations,
        sample_size=int(N),
        histogram_data=histogram_data
    )


def _calculate_skewness(data: np.ndarray) -> float:
    """
    计算偏度（Skewness）

    偏度衡量分布的对称性：
    - skewness = 0: 对称分布（如正态分布）
    - skewness > 0: 右偏（长尾在右侧）
    - skewness < 0: 左偏（长尾在左侧）

    Args:
        data: 数据数组

    Returns:
        偏度值
    """
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 0.0

    # 三阶中心矩 / 标准差^3
    skewness = np.mean(((data - mean) / std) ** 3)
    return skewness


def batch_monte_carlo(
    user_rank: int,
    candidates: List[Dict],
    n_simulations: int = 10000,
    quota_change_rate: float = 0.0,
    sentiment_modifiers: Optional[Dict[str, float]] = None
) -> List[Dict]:
    """
    批量蒙特卡洛模拟（用于 45 个志愿）

    Args:
        user_rank: 用户位次
        candidates: 候选志愿列表，每个元素包含：
            {
                'school_code': str,
                'major_code': str,
                'hist_data': pd.DataFrame
            }
        n_simulations: 模拟次数
        quota_change_rate: 全局招生计划变化率
        sentiment_modifiers: 舆情修正字典（可选）
            {
                'school_code_major_code': modifier_value
            }

    Returns:
        List[Dict]，每个元素包含原始信息 + 蒙特卡洛结果
    """
    results = []

    for candidate in candidates:
        school_code = candidate.get('school_code', '')
        major_code = candidate.get('major_code', '')
        hist_data = candidate.get('hist_data')

        if hist_data is None or hist_data.empty:
            continue

        # 获取该志愿的舆情修正值
        key = f"{school_code}_{major_code}"
        sentiment_modifier = 0.0
        if sentiment_modifiers and key in sentiment_modifiers:
            sentiment_modifier = sentiment_modifiers[key]

        # 运行蒙特卡洛模拟
        try:
            mc_result = monte_carlo_admission_probability(
                user_rank=user_rank,
                hist_data=hist_data,
                n_simulations=n_simulations,
                quota_change_rate=quota_change_rate,
                sentiment_modifier=sentiment_modifier
            )

            results.append({
                **candidate,  # 保留原始信息
                'mc_result': mc_result.dict()  # 添加蒙特卡洛结果
            })

        except Exception as e:
            print(f"[WARN] 蒙特卡洛模拟失败: {school_code} {major_code} - {e}")
            continue

    return results


# === 测试代码 ===
if __name__ == "__main__":
    # 构造测试数据
    test_hist_data = pd.DataFrame({
        'year': [2022, 2023, 2024],
        'min_rank': [1000, 1050, 1020],
        'quota': [50, 50, 48]
    })

    user_rank = 1100

    print("=== 蒙特卡洛仿真测试 ===\n")

    # 测试 1：标准蒙特卡洛（正态分布）
    print("测试 1：标准蒙特卡洛模拟（正态分布）")
    result1 = monte_carlo_admission_probability(
        user_rank=user_rank,
        hist_data=test_hist_data,
        n_simulations=10000,
        random_seed=42
    )
    print(f"录取概率: {result1.admission_prob:.2%}")
    print(f"预测位次（中位数）: {result1.min_rank_pred}")
    print(f"95% 置信区间: [{result1.ci_lower}, {result1.ci_upper}]")
    print(f"标准差: {result1.volatility_std:.1f}")
    print(f"偏度: {result1.skewness:.3f}")
    print()

    # 测试 2：考虑招生计划变化
    print("测试 2：招生计划减少 20%")
    result2 = monte_carlo_admission_probability(
        user_rank=user_rank,
        hist_data=test_hist_data,
        quota_change_rate=-0.2,  # 减少 20%
        n_simulations=10000,
        random_seed=42
    )
    print(f"录取概率: {result2.admission_prob:.2%}")
    print(f"预测位次: {result2.min_rank_pred}")
    print()

    # 测试 3：考虑舆情修正
    print("测试 3：负面舆情（位次上升 100 位）")
    result3 = monte_carlo_admission_probability(
        user_rank=user_rank,
        hist_data=test_hist_data,
        sentiment_modifier=100,  # 位次上升 100 位（更容易录取）
        n_simulations=10000,
        random_seed=42
    )
    print(f"录取概率: {result3.admission_prob:.2%}")
    print(f"预测位次: {result3.min_rank_pred}")
    print()

    # 测试 4：偏态分布
    print("测试 4：偏态分布（右偏，alpha=2）")
    result4 = monte_carlo_with_skewed_distribution(
        user_rank=user_rank,
        hist_data=test_hist_data,
        skewness_param=2.0,  # 右偏
        n_simulations=10000,
        random_seed=42
    )
    print(f"录取概率: {result4.admission_prob:.2%}")
    print(f"预测位次: {result4.min_rank_pred}")
    print(f"偏度: {result4.skewness:.3f}")
    print()

    print("测试完成！")

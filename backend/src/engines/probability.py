"""录取概率计算模块（增强版：分层惩罚 + AI推理）"""
import pandas as pd
import numpy as np
from scipy.stats import norm
from typing import Dict, Optional


def get_adaptive_penalty_factor(quota: int) -> float:
    """
    根据招生规模自适应调整惩罚系数（分层惩罚策略）

    核心思想：
    - 省外顶尖985（招生20-50人）：样本小但历史稳定，适度惩罚
    - 省外中等985/211（招生50-200人）：中等规模，中等惩罚
    - 省内985或大规模招生（200+人）：样本大，轻度惩罚

    Args:
        quota: 招生人数（专业组总招生人数）

    Returns:
        penalty_factor: 动态惩罚系数
    """
    if quota < 30:
        # 超小样本（省外顶尖985，如清北、华五在广东招生）
        # 虽然样本小，但这些学校历史数据非常稳定，不需要过度惩罚
        return 0.8
    elif quota < 50:
        # 小样本（省外C9、华东五校等）
        return 1.0
    elif quota < 100:
        # 中小样本（省外中等985）
        return 1.2
    elif quota < 300:
        # 中等样本（省外211或省内小专业组）
        return 1.3
    elif quota < 1000:
        # 大样本（省内985大专业组）
        return 1.4
    else:
        # 超大样本（省内985全校汇总）
        return 1.5


def calculate_admission_probability(
    user_rank: int,
    hist_data: pd.DataFrame,
    penalty_factor: Optional[float] = None
) -> Dict:
    """
    计算录取概率（核心算法 - 增强版）

    新增特性：
    - 自适应分层惩罚：根据招生规模动态调整penalty_factor
    - 如果不传入penalty_factor，系统会根据招生人数自动选择最优值

    Args:
        user_rank: 用户位次
        hist_data: 历史数据 DataFrame
        penalty_factor: 小样本惩罚系数（可选，不传则自动计算）

    Returns:
        {
            'prob': 0.65,
            'min_rank_pred': 12000,
            'ci_lower': 11500,
            'ci_upper': 12500,
            'sample_size': 50,
            'penalty_factor_used': 1.2  # 新增：记录实际使用的惩罚系数
        }
    """
    if hist_data.empty:
        return None

    # 1. 计算基准位次（3年加权平均，越近的年份权重越高）
    weights = [0.2, 0.3, 0.5]  # 最多3年数据
    recent_data = hist_data.tail(3)
    ranks = recent_data['min_rank'].values
    used_weights = weights[-len(ranks):]

    base_rank = np.average(ranks, weights=used_weights)

    # 2. 自适应小样本惩罚系数（核心创新）
    latest_quota = recent_data['quota'].iloc[-1] if 'quota' in recent_data.columns else 10
    N = max(latest_quota, 1)  # 避免除以0

    # 如果未传入penalty_factor，使用自适应分层惩罚
    if penalty_factor is None:
        penalty_factor = get_adaptive_penalty_factor(N)

    penalty = penalty_factor / np.sqrt(N)

    # 3. 波动性估计：使用MAD（中位数绝对偏差）代替标准差，对异常值更鲁棒
    # MAD对"大小年"效应（某年爆冷）不敏感，能准确反映学校真实定位
    # 例如：某学校历史位次 [18000, 19000, 17500, 42000]，std会被42000严重拉大
    #      但MAD基于中位数，不受单年异常影响，能正确识别该校实际在18000档
    median_rank = hist_data['min_rank'].median()
    mad = (hist_data['min_rank'] - median_rank).abs().median()

    # 将MAD转换为标准差等价值（在正态分布下，MAD * 1.4826 ≈ std）
    raw_std = mad * 1.4826 if mad > 0 else base_rank * 0.05

    # 如果MAD为0（所有年份位次完全相同），使用base_rank的5%作为默认波动
    if raw_std == 0 or pd.isna(raw_std):
        raw_std = base_rank * 0.05

    # 分离：原始std用于Z-score，调整后std用于概率计算
    adjusted_std = raw_std * (1 + penalty)

    # 4. 正态分布假设下计算概率
    # 核心逻辑：假设学校的最低位次服从 N(base_rank, adjusted_std)
    # 录取条件：user_rank <= 学校最低位次（位次越小越好）
    # 录取概率 = P(学校最低位次 >= user_rank)
    #          = P(X >= user_rank | X ~ N(base_rank, adjusted_std))
    #          = 1 - P(X < user_rank)
    #          = 1 - norm.cdf(user_rank, loc=base_rank, scale=adjusted_std)

    # 修复：统一使用base_rank为中心的正态分布（不再分支）
    prob = 1 - norm.cdf(user_rank, loc=base_rank, scale=adjusted_std)

    # 等价写法（更清晰）:
    # prob = norm.sf(user_rank, loc=base_rank, scale=adjusted_std)
    # sf = survival function = 1 - cdf

    # 5. 置信区间（95%）
    ci_lower = int(base_rank - 1.96 * adjusted_std)
    ci_upper = int(base_rank + 1.96 * adjusted_std)

    # 6. 计算Z-score（相对位次优势）- 使用原始std，不受惩罚系数影响
    # Z-score = (学校位次 - 用户位次) / 原始标准差
    # 表示用户位次比学校好多少个标准差（客观测量）
    # 关键：这里必须用raw_std，因为Z-score衡量的是客观优势，不应被主观惩罚因子扭曲
    z_score = (base_rank - user_rank) / raw_std if raw_std > 0 else 0

    return {
        'prob': float(np.clip(prob, 0, 1)),  # 确保在[0,1]范围内
        'min_rank_pred': int(base_rank),
        'ci_lower': max(1, ci_lower),  # 位次最小为1
        'ci_upper': ci_upper,
        'sample_size': int(N),
        'raw_std': float(raw_std),  # 原始标准差（用于Z-score客观测量）
        'volatility_std': float(adjusted_std),  # 调整后标准差（用于概率保守估计）
        'penalty_factor_used': float(penalty_factor),  # 记录实际使用的惩罚系数
        'z_score': float(z_score)  # 相对位次优势（基于raw_std的客观测量）
    }


def classify_strategy_tag(prob: float, z_score: Optional[float] = None) -> str:
    """
    根据相对位次优势分类策略标签（AI智能分类）

    核心思想：关注相对位次优势（Z-score），而非绝对概率
    - Z-score = (学校位次 - 用户位次) / 标准差
    - 表示用户比学校历史位次好多少个标准差

    分类标准（基于统计学原理）：
    - Z >= 2.0: 保底 (位次优势是波动的2倍，对应95%+置信度)
    - Z 在 1.0-2.0: 稳妥 (1倍标准差优势，对应84%-95%置信度)
    - Z < 1.0: 冲刺 (位次优势小于波动，风险较高)

    优势：
    1. 自适应：不同学校波动不同，Z-score自动适应
    2. 合理性：2σ原则是统计学通用标准
    3. 体现智能：即使概率计算因惩罚偏低，Z-score仍能识别真实优势

    Args:
        prob: 录取概率（作为参考，优先使用z_score）
        z_score: 相对位次优势（标准差倍数），如提供则优先使用

    Returns:
        'rush' | 'target' | 'safe'
    """
    # 优先使用Z-score分类（体现Agent智能）
    if z_score is not None:
        if z_score >= 2.0:
            return 'safe'     # 2σ优势 = 保底
        elif z_score >= 1.0:
            return 'target'   # 1-2σ = 稳妥
        else:
            return 'rush'     # <1σ = 冲刺

    # Fallback: 使用概率分类（兼容旧代码）
    if prob < 0.5:
        return 'rush'
    elif prob < 0.6:
        return 'target'
    else:
        return 'safe'

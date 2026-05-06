"""量化信号模块（恐惧指数、波动率）"""
import pandas as pd
import numpy as np
from typing import Tuple


def calculate_fear_index(hist_data: pd.DataFrame) -> float:
    """
    恐惧指数（识别大小年）

    公式：F_idx = (最新年位次 - 历史均值) / 标准差

    解读：
    - F < -1.5：超卖（市场错杀），捡漏机会
    - -1.5 < F < 1.5：正常波动
    - F > 1.5：超买（追高风险）

    Args:
        hist_data: 历史数据 DataFrame

    Returns:
        恐惧指数（float）
    """
    if len(hist_data) < 2:
        return 0.0

    ranks = hist_data['min_rank'].values
    mean = ranks.mean()
    std = ranks.std()

    if std == 0 or pd.isna(std):
        return 0.0

    latest = ranks[-1]
    f_idx = (latest - mean) / std

    return float(np.clip(f_idx, -3, 3))  # 限制在 [-3, 3] 范围


def calculate_volatility(hist_data: pd.DataFrame) -> Tuple[str, float]:
    """
    计算波动率等级

    Args:
        hist_data: 历史数据 DataFrame

    Returns:
        (VolatilityLevel, 波动率数值)
    """
    if len(hist_data) < 2:
        return 'medium', 0.0

    ranks = hist_data['min_rank'].values
    mean = ranks.mean()

    # 变异系数（标准差/均值）
    cv = ranks.std() / mean if mean > 0 else 0

    # 分类
    if cv < 0.05:
        level = 'low'
    elif cv < 0.15:
        level = 'medium'
    else:
        level = 'high'

    return level, float(cv)


def detect_trend(hist_data: pd.DataFrame) -> str:
    """
    检测趋势（上升/下降/平稳）

    Args:
        hist_data: 历史数据 DataFrame

    Returns:
        'rising' | 'falling' | 'stable'
    """
    if len(hist_data) < 2:
        return 'stable'

    ranks = hist_data['min_rank'].values

    # 简单线性回归斜率
    years = np.arange(len(ranks))
    slope = np.polyfit(years, ranks, 1)[0]

    if slope > 500:
        return 'rising'  # 位次上升（竞争变弱）
    elif slope < -500:
        return 'falling'  # 位次下降（竞争加剧）
    else:
        return 'stable'

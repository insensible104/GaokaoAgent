"""博弈空间降维模块

在志愿填报的庞大搜索空间中（45个志愿×6个专业=270个选择），
通过智能采样和聚类，将空间降维到可管理的规模。

核心技术：
1. 局部竞争密度采样（Competition Density Sampling）
2. 分层采样（冲稳保策略）
3. K-means 聚类降维

应用场景：
- 从上万个候选专业中筛选出 100-200 个高质量候选
- 避免信息过载，提升用户决策效率
- 聚焦用户位次附近的竞争热点
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class CompetitionDensity(BaseModel):
    """竞争密度指标"""
    rank_range: Tuple[int, int] = Field(description="位次区间 (min, max)")
    density_score: float = Field(
        description="竞争密度得分（单位位次的志愿数量）"
    )
    candidate_count: int = Field(description="该区间内的候选数量")


class DimensionReductionResult(BaseModel):
    """降维结果"""
    selected_candidates: List[Dict] = Field(
        default_factory=list,
        description="筛选后的候选志愿"
    )

    # 统计信息
    original_size: int = Field(description="原始候选数量")
    reduced_size: int = Field(description="降维后数量")
    reduction_ratio: float = Field(description="降维比例")

    # 分布统计
    rush_count: int = Field(default=0, description="冲刺类数量")
    target_count: int = Field(default=0, description="稳妥类数量")
    safe_count: int = Field(default=0, description="保底类数量")

    # 竞争密度分析
    competition_densities: List[CompetitionDensity] = Field(
        default_factory=list,
        description="各区间的竞争密度"
    )


def calculate_competition_density(
    candidates: pd.DataFrame,
    rank_col: str = 'min_rank',
    bin_width: int = 1000
) -> List[CompetitionDensity]:
    """
    计算竞争密度

    定义：在某个位次区间内，单位位次的志愿数量

    公式：
    density = candidate_count / bin_width

    Args:
        candidates: 候选志愿 DataFrame
        rank_col: 位次列名
        bin_width: 位次区间宽度（默认 1000 位）

    Returns:
        竞争密度列表
    """
    if candidates.empty or rank_col not in candidates.columns:
        return []

    # 去除缺失值
    valid_candidates = candidates[candidates[rank_col].notna()].copy()

    if valid_candidates.empty:
        return []

    # 计算位次范围
    min_rank = int(valid_candidates[rank_col].min())
    max_rank = int(valid_candidates[rank_col].max())

    # 分桶
    bins = range(min_rank, max_rank + bin_width, bin_width)
    valid_candidates['rank_bin'] = pd.cut(
        valid_candidates[rank_col],
        bins=bins,
        labels=False
    )

    # 统计每个桶的候选数量
    bin_counts = valid_candidates.groupby('rank_bin').size()

    # 生成竞争密度
    densities = []
    for bin_idx, count in bin_counts.items():
        if pd.isna(bin_idx):
            continue

        bin_idx = int(bin_idx)
        rank_start = min_rank + bin_idx * bin_width
        rank_end = rank_start + bin_width

        density_score = count / bin_width

        densities.append(CompetitionDensity(
            rank_range=(rank_start, rank_end),
            density_score=density_score,
            candidate_count=count
        ))

    # 按密度降序排序
    densities.sort(key=lambda x: x.density_score, reverse=True)

    return densities


def local_competition_sampling(
    candidates: pd.DataFrame,
    user_rank: int,
    rank_col: str = 'min_rank',
    sample_window: int = 5000,
    top_k: int = 100
) -> pd.DataFrame:
    """
    局部竞争密度采样

    策略：
    1. 在用户位次附近 [user_rank - sample_window, user_rank + sample_window] 采样
    2. 按竞争密度降序排序
    3. 取前 top_k 个

    Args:
        candidates: 候选志愿 DataFrame
        user_rank: 用户位次
        rank_col: 位次列名
        sample_window: 采样窗口（默认 ±5000 位）
        top_k: 采样数量

    Returns:
        采样后的 DataFrame
    """
    if candidates.empty or rank_col not in candidates.columns:
        return pd.DataFrame()

    # 筛选局部窗口
    local_mask = (
        (candidates[rank_col] >= user_rank - sample_window) &
        (candidates[rank_col] <= user_rank + sample_window)
    )

    local_candidates = candidates[local_mask].copy()

    if local_candidates.empty:
        # 如果窗口内没有候选，返回最接近的前 top_k 个
        local_candidates = candidates.copy()

    # 计算每个候选与用户位次的距离
    local_candidates['rank_distance'] = abs(
        local_candidates[rank_col] - user_rank
    )

    # 按距离排序（距离越小，竞争越激烈）
    local_candidates = local_candidates.sort_values('rank_distance')

    # 取前 top_k 个
    sampled = local_candidates.head(top_k)

    return sampled


def stratified_sampling(
    candidates: pd.DataFrame,
    user_rank: int,
    rank_col: str = 'min_rank',
    rush_count: int = 15,
    target_count: int = 15,
    safe_count: int = 15
) -> pd.DataFrame:
    """
    分层采样（按冲稳保策略）

    策略：
    - 冲刺类：min_rank < user_rank，按接近度采样
    - 稳妥类：min_rank ≈ user_rank（±10%），按概率采样
    - 保底类：min_rank > user_rank，按安全边际采样

    Args:
        candidates: 候选志愿 DataFrame
        user_rank: 用户位次
        rank_col: 位次列名
        rush_count: 冲刺类采样数量
        target_count: 稳妥类采样数量
        safe_count: 保底类采样数量

    Returns:
        分层采样后的 DataFrame
    """
    if candidates.empty or rank_col not in candidates.columns:
        return pd.DataFrame()

    # 分层
    rush_mask = candidates[rank_col] < user_rank * 0.9  # 位次更小=更好的学校
    target_mask = (
        (candidates[rank_col] >= user_rank * 0.9) &
        (candidates[rank_col] <= user_rank * 1.1)
    )
    safe_mask = candidates[rank_col] > user_rank * 1.1

    rush_candidates = candidates[rush_mask].copy()
    target_candidates = candidates[target_mask].copy()
    safe_candidates = candidates[safe_mask].copy()

    # 采样策略
    sampled_parts = []

    # 冲刺类：选择最接近 user_rank 的前 N 个
    if not rush_candidates.empty:
        rush_candidates['distance'] = abs(rush_candidates[rank_col] - user_rank)
        rush_sampled = rush_candidates.nsmallest(rush_count, 'distance')
        sampled_parts.append(rush_sampled)

    # 稳妥类：随机采样
    if not target_candidates.empty:
        target_sampled = target_candidates.sample(
            n=min(target_count, len(target_candidates)),
            random_state=42
        )
        sampled_parts.append(target_sampled)

    # 保底类：选择位次最大（最安全）的前 N 个
    if not safe_candidates.empty:
        safe_sampled = safe_candidates.nlargest(safe_count, rank_col)
        sampled_parts.append(safe_sampled)

    # 合并
    if not sampled_parts:
        return pd.DataFrame()

    result = pd.concat(sampled_parts, ignore_index=True)
    return result


def kmeans_clustering_reduction(
    candidates: pd.DataFrame,
    feature_cols: List[str],
    n_clusters: int = 50,
    random_state: int = 42
) -> pd.DataFrame:
    """
    K-means 聚类降维

    策略：
    1. 使用关键特征（如 min_rank, admission_prob, adjustment_risk）进行聚类
    2. 每个聚类选择最代表性的样本（距离聚类中心最近）
    3. 返回 n_clusters 个代表性样本

    Args:
        candidates: 候选志愿 DataFrame
        feature_cols: 用于聚类的特征列
        n_clusters: 聚类数量（即降维后的样本数）
        random_state: 随机种子

    Returns:
        聚类后的代表性样本 DataFrame
    """
    if candidates.empty:
        return pd.DataFrame()

    # 检查特征列是否存在
    valid_feature_cols = [col for col in feature_cols if col in candidates.columns]

    if not valid_feature_cols:
        # 如果没有特征列，随机采样
        return candidates.sample(n=min(n_clusters, len(candidates)), random_state=random_state)

    # 提取特征
    features = candidates[valid_feature_cols].copy()

    # 处理缺失值
    features = features.fillna(features.mean())

    # 如果样本数少于聚类数，直接返回全部
    if len(features) <= n_clusters:
        return candidates

    # 标准化
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    # K-means 聚类
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    cluster_labels = kmeans.fit_predict(features_scaled)

    # 为每个聚类选择最代表性的样本（距离聚类中心最近）
    candidates = candidates.copy()
    candidates['cluster'] = cluster_labels

    representative_indices = []
    for cluster_id in range(n_clusters):
        cluster_mask = candidates['cluster'] == cluster_id
        cluster_data = features_scaled[cluster_mask]

        if len(cluster_data) == 0:
            continue

        # 计算每个样本到聚类中心的距离
        center = kmeans.cluster_centers_[cluster_id]
        distances = np.linalg.norm(cluster_data - center, axis=1)

        # 选择距离最小的样本
        closest_idx = np.argmin(distances)
        original_idx = candidates[cluster_mask].index[closest_idx]
        representative_indices.append(original_idx)

    # 返回代表性样本
    result = candidates.loc[representative_indices].copy()
    result = result.drop(columns=['cluster'])

    return result


def reduce_game_space(
    candidates: pd.DataFrame,
    user_rank: int,
    rank_col: str = 'min_rank',
    target_size: int = 100,
    strategy: str = 'hybrid'
) -> DimensionReductionResult:
    """
    博弈空间降维（一站式接口）

    策略选项：
    - 'local': 局部竞争密度采样
    - 'stratified': 分层采样（冲稳保）
    - 'clustering': K-means 聚类降维
    - 'hybrid': 混合策略（推荐）

    Args:
        candidates: 候选志愿 DataFrame
        user_rank: 用户位次
        rank_col: 位次列名
        target_size: 目标降维后的大小
        strategy: 降维策略

    Returns:
        DimensionReductionResult 对象
    """
    original_size = len(candidates)

    if candidates.empty:
        return DimensionReductionResult(
            original_size=0,
            reduced_size=0,
            reduction_ratio=0.0
        )

    # 计算竞争密度
    competition_densities = calculate_competition_density(
        candidates, rank_col, bin_width=1000
    )

    # 选择降维策略
    if strategy == 'local':
        # 局部采样
        reduced = local_competition_sampling(
            candidates, user_rank, rank_col, sample_window=5000, top_k=target_size
        )

    elif strategy == 'stratified':
        # 分层采样
        per_layer = target_size // 3
        reduced = stratified_sampling(
            candidates, user_rank, rank_col,
            rush_count=per_layer,
            target_count=per_layer,
            safe_count=per_layer
        )

    elif strategy == 'clustering':
        # 聚类降维
        feature_cols = [rank_col, 'admission_prob', 'adjustment_risk']
        reduced = kmeans_clustering_reduction(
            candidates, feature_cols, n_clusters=target_size
        )

    elif strategy == 'hybrid':
        # 混合策略（推荐）：先分层，再聚类
        # 1. 分层采样（保留 3 * target_size）
        per_layer = target_size
        stratified_result = stratified_sampling(
            candidates, user_rank, rank_col,
            rush_count=per_layer,
            target_count=per_layer,
            safe_count=per_layer
        )

        # 2. 对分层结果进行聚类降维
        feature_cols = [rank_col]
        if 'admission_prob' in stratified_result.columns:
            feature_cols.append('admission_prob')

        reduced = kmeans_clustering_reduction(
            stratified_result, feature_cols, n_clusters=target_size
        )

    else:
        raise ValueError(f"未知策略: {strategy}")

    # 统计分布
    rush_count = 0
    target_count = 0
    safe_count = 0

    if rank_col in reduced.columns:
        rush_count = int((reduced[rank_col] < user_rank * 0.9).sum())
        target_count = int((
            (reduced[rank_col] >= user_rank * 0.9) &
            (reduced[rank_col] <= user_rank * 1.1)
        ).sum())
        safe_count = int((reduced[rank_col] > user_rank * 1.1).sum())

    reduced_size = len(reduced)
    reduction_ratio = (1 - reduced_size / original_size) if original_size > 0 else 0.0

    return DimensionReductionResult(
        selected_candidates=reduced.to_dict('records'),
        original_size=original_size,
        reduced_size=reduced_size,
        reduction_ratio=reduction_ratio,
        rush_count=rush_count,
        target_count=target_count,
        safe_count=safe_count,
        competition_densities=competition_densities[:10]  # 只保留前10个密度最高的区间
    )


# === 测试代码 ===
if __name__ == "__main__":
    print("=== 博弈空间降维测试 ===\n")

    # 生成模拟数据（1000个候选志愿）
    np.random.seed(42)
    n_candidates = 1000
    user_rank = 10000

    mock_data = pd.DataFrame({
        'school_name': [f'学校{i}' for i in range(n_candidates)],
        'major_name': [f'专业{i}' for i in range(n_candidates)],
        'min_rank': np.random.randint(5000, 50000, n_candidates),
        'admission_prob': np.random.uniform(0.1, 0.95, n_candidates),
        'adjustment_risk': np.random.uniform(0.0, 0.5, n_candidates)
    })

    print(f"原始候选数量: {len(mock_data)}")
    print(f"用户位次: {user_rank}")
    print()

    # 测试不同策略
    strategies = ['local', 'stratified', 'clustering', 'hybrid']

    for strategy in strategies:
        print(f"=== 策略: {strategy.upper()} ===")
        result = reduce_game_space(
            candidates=mock_data,
            user_rank=user_rank,
            rank_col='min_rank',
            target_size=100,
            strategy=strategy
        )

        print(f"降维后数量: {result.reduced_size}")
        print(f"降维比例: {result.reduction_ratio:.1%}")
        print(f"冲刺类: {result.rush_count}，稳妥类: {result.target_count}，保底类: {result.safe_count}")
        print()

    # 竞争密度分析
    print("=== 竞争密度分析（Top 5）===")
    hybrid_result = reduce_game_space(
        mock_data, user_rank, target_size=100, strategy='hybrid'
    )

    for i, density in enumerate(hybrid_result.competition_densities[:5], 1):
        print(f"{i}. 位次区间 [{density.rank_range[0]}, {density.rank_range[1]}]")
        print(f"   密度得分: {density.density_score:.4f}，候选数量: {density.candidate_count}")

    print("\n测试完成！")

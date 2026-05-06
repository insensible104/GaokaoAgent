"""离线回测框架

使用历史数据（2021-2024）验证预测算法的准确性。

核心流程：
1. 加载多年历史数据
2. 对于目标年份（如2024），使用前N年数据预测
3. 对比预测结果与实际录取结果
4. 计算误差指标（MAE, RMSE, 准确率等）

应用场景：
- 验证概率计算算法准确性
- 优化模型参数（如小样本惩罚系数）
- 评估蒙特卡洛模拟效果
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from engines.probability import calculate_admission_probability
from engines.monte_carlo_sim import monte_carlo_admission_probability


class BacktestMetrics(BaseModel):
    """回测指标"""

    # 位次预测误差
    mae_rank: float = Field(description="位次预测平均绝对误差（MAE）")
    rmse_rank: float = Field(description="位次预测均方根误差（RMSE）")
    max_error_rank: float = Field(description="位次预测最大误差")

    # 概率校准误差
    calibration_error: float = Field(
        description="概率校准误差（预测概率 vs 实际录取率）"
    )

    # 准确率（分类指标）
    accuracy_rush: float = Field(
        description="冲刺类志愿预测准确率（预测prob<0.6 且实际能录取）"
    )
    accuracy_target: float = Field(
        description="稳妥类志愿预测准确率（预测prob 0.6-0.9）"
    )
    accuracy_safe: float = Field(
        description="保底类志愿预测准确率（预测prob>=0.9 且实际能录取）"
    )

    # 样本统计
    total_samples: int = Field(description="总样本数")
    valid_predictions: int = Field(description="有效预测数（数据完整）")


class BacktestResult(BaseModel):
    """单次回测结果"""
    school_name: str
    major_name: Optional[str] = None
    major_group_code: Optional[str] = None

    # 预测值
    predicted_rank: int
    predicted_prob: float

    # 实际值
    actual_rank: int

    # 误差
    rank_error: float = Field(description="位次预测误差（predicted - actual）")
    abs_rank_error: float = Field(description="位次预测绝对误差")


def load_historical_data(
    data_dir: str,
    years: List[int],
    category: str = 'physics'
) -> Dict[int, pd.DataFrame]:
    """
    加载多年历史数据

    Args:
        data_dir: 数据目录路径
        years: 年份列表（如 [2021, 2022, 2023, 2024]）
        category: 科类（physics/history）

    Returns:
        {year: DataFrame} 字典
    """
    data_dir = Path(data_dir)
    historical_data = {}

    for year in years:
        file_path = data_dir / f"{year}_{category}.csv"

        if not file_path.exists():
            print(f"[WARN] 数据文件不存在: {file_path}")
            continue

        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            historical_data[year] = df
            print(f"[OK] 加载 {year} 年数据: {len(df)} 条记录")

        except Exception as e:
            print(f"[ERROR] 加载 {year} 年数据失败: {e}")
            continue

    return historical_data


def prepare_backtest_dataset(
    historical_data: Dict[int, pd.DataFrame],
    test_year: int,
    training_years: int = 3
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    准备回测数据集

    Args:
        historical_data: {year: DataFrame} 历史数据
        test_year: 测试年份（如 2024）
        training_years: 训练年份数量（默认 3 年）

    Returns:
        (training_data, test_data) 元组
    """
    if test_year not in historical_data:
        raise ValueError(f"测试年份 {test_year} 数据不存在")

    # 测试集：目标年份的数据
    test_data = historical_data[test_year].copy()

    # 训练集：前N年的数据
    training_years_list = [
        year for year in range(test_year - training_years, test_year)
        if year in historical_data
    ]

    if not training_years_list:
        raise ValueError(f"训练数据不足（需要 {test_year - training_years} 到 {test_year - 1} 年）")

    # 合并训练数据
    training_dfs = [historical_data[year] for year in training_years_list]
    training_data = pd.concat(training_dfs, ignore_index=True)

    print(f"[Backtest] 训练集: {training_years_list} 年，共 {len(training_data)} 条")
    print(f"[Backtest] 测试集: {test_year} 年，共 {len(test_data)} 条")

    return training_data, test_data


def run_backtest_for_row(
    row: pd.Series,
    training_data: pd.DataFrame,
    use_monte_carlo: bool = False,
    user_rank_percentile: float = 0.5
) -> Optional[BacktestResult]:
    """
    对单个学校专业进行回测

    Args:
        row: 测试集中的一行数据（包含实际 min_rank）
        training_data: 训练集数据
        use_monte_carlo: 是否使用蒙特卡洛模拟
        user_rank_percentile: 模拟用户位次（相对于该专业 min_rank 的百分位）

    Returns:
        BacktestResult 对象，如果数据不足则返回 None
    """
    school_name = row.get('school_name')
    if not school_name:
        school_name = row.get('院校名称', '')

    major_name = row.get('major_name')
    if not major_name:
        major_name = row.get('专业名称')
    if not major_name:
        major_name = row.get('专业/类')

    major_group_code = row.get('major_group_code')
    if not major_group_code:
        major_group_code = row.get('专业组代码')
    if not major_group_code:
        major_group_code = row.get('专业组')

    # 实际录取位次（处理列名中的换行符）
    actual_rank = row.get('min_rank')
    if pd.isna(actual_rank) or actual_rank is None:
        actual_rank = row.get('最低排位')
    if pd.isna(actual_rank) or actual_rank is None:
        actual_rank = row.get('最低分\r\n平均排位')
    if pd.isna(actual_rank) or actual_rank is None:
        actual_rank = row.get('最低分平均排位')

    if pd.isna(actual_rank) or actual_rank is None:
        return None

    actual_rank = int(float(actual_rank))

    # 从训练集中提取该学校专业的历史数据
    # 处理中文列名（可能包含换行符）
    possible_school_cols = ['school_name', '院校名称']
    possible_major_cols = ['major_name', '专业名称', '专业/类']
    possible_rank_cols = ['min_rank', '最低排位', '最低分\r\n平均排位', '最低分平均排位']
    possible_quota_cols = ['quota', '计划数', '录取\r\n人数', '录取人数']

    # 找到实际存在的列名
    school_col = next((col for col in possible_school_cols if col in training_data.columns), None)
    major_col = next((col for col in possible_major_cols if col in training_data.columns), None)
    rank_col = next((col for col in possible_rank_cols if col in training_data.columns), None)
    quota_col = next((col for col in possible_quota_cols if col in training_data.columns), None)

    if not school_col or not major_col or not rank_col:
        return None

    # 筛选历史数据
    if major_name:
        hist_mask = (
            (training_data[school_col] == school_name) &
            (training_data[major_col] == major_name)
        )
    else:
        hist_mask = (training_data[school_col] == school_name)

    hist_data = training_data[hist_mask].copy()

    if hist_data.empty:
        return None

    # 标准化列名
    rename_dict = {rank_col: 'min_rank'}
    if quota_col:
        rename_dict[quota_col] = 'quota'

    hist_data = hist_data.rename(columns=rename_dict)

    # 如果缺少 quota 列，添加默认值
    if 'quota' not in hist_data.columns:
        hist_data['quota'] = 10  # 默认招生计划10人

    # 模拟用户位次（假设用户位次略差于历史最低位次）
    user_rank = int(actual_rank * (1 + user_rank_percentile * 0.1))

    # 预测
    try:
        if use_monte_carlo:
            # 使用蒙特卡洛模拟
            mc_result = monte_carlo_admission_probability(
                user_rank=user_rank,
                hist_data=hist_data,
                n_simulations=5000,  # 回测时减少模拟次数以加速
                random_seed=42
            )
            predicted_rank = mc_result.min_rank_pred
            predicted_prob = mc_result.admission_prob

        else:
            # 使用正态分布 CDF
            prob_result = calculate_admission_probability(
                user_rank=user_rank,
                hist_data=hist_data,
                penalty_factor=2.0
            )

            if prob_result is None:
                return None

            predicted_rank = prob_result['min_rank_pred']
            predicted_prob = prob_result['prob']

    except Exception as e:
        print(f"[WARN] 预测失败: {school_name} {major_name} - {e}")
        return None

    # 计算误差
    rank_error = predicted_rank - actual_rank
    abs_rank_error = abs(rank_error)

    return BacktestResult(
        school_name=school_name,
        major_name=major_name,
        major_group_code=str(major_group_code) if major_group_code else None,
        predicted_rank=predicted_rank,
        predicted_prob=predicted_prob,
        actual_rank=actual_rank,
        rank_error=rank_error,
        abs_rank_error=abs_rank_error
    )


def compute_backtest_metrics(
    results: List[BacktestResult]
) -> BacktestMetrics:
    """
    计算回测指标

    Args:
        results: 回测结果列表

    Returns:
        BacktestMetrics 对象
    """
    if not results:
        return BacktestMetrics(
            mae_rank=0.0,
            rmse_rank=0.0,
            max_error_rank=0.0,
            calibration_error=0.0,
            accuracy_rush=0.0,
            accuracy_target=0.0,
            accuracy_safe=0.0,
            total_samples=0,
            valid_predictions=0
        )

    # 位次预测误差
    abs_errors = [r.abs_rank_error for r in results]
    mae_rank = np.mean(abs_errors)
    rmse_rank = np.sqrt(np.mean([e**2 for e in abs_errors]))
    max_error_rank = np.max(abs_errors)

    # 概率校准误差（简化版：平均预测概率 vs 实际录取率）
    # 实际录取率 = 预测 prob > 0.5 且实际能录取的比例
    predicted_probs = [r.predicted_prob for r in results]
    avg_predicted_prob = np.mean(predicted_probs)

    # 假设用户位次略差于预测位次，计算实际录取率
    # 这里简化为：预测位次 <= 实际位次 则视为能录取
    actual_admission_rate = sum(
        1 for r in results if r.predicted_rank >= r.actual_rank
    ) / len(results)

    calibration_error = abs(avg_predicted_prob - actual_admission_rate)

    # 准确率（分策略类型）
    rush_results = [r for r in results if r.predicted_prob < 0.6]
    target_results = [r for r in results if 0.6 <= r.predicted_prob < 0.9]
    safe_results = [r for r in results if r.predicted_prob >= 0.9]

    def calculate_accuracy(subset):
        if not subset:
            return 0.0
        # 简化：如果预测位次在实际位次 ±10% 范围内，视为准确
        accurate = sum(
            1 for r in subset
            if abs(r.rank_error) <= r.actual_rank * 0.1
        )
        return accurate / len(subset)

    accuracy_rush = calculate_accuracy(rush_results)
    accuracy_target = calculate_accuracy(target_results)
    accuracy_safe = calculate_accuracy(safe_results)

    return BacktestMetrics(
        mae_rank=mae_rank,
        rmse_rank=rmse_rank,
        max_error_rank=max_error_rank,
        calibration_error=calibration_error,
        accuracy_rush=accuracy_rush,
        accuracy_target=accuracy_target,
        accuracy_safe=accuracy_safe,
        total_samples=len(results),
        valid_predictions=len(results)
    )


def run_full_backtest(
    data_dir: str = "backend/data",
    test_year: int = 2024,
    category: str = 'physics',
    use_monte_carlo: bool = False,
    sample_size: Optional[int] = None
) -> Tuple[List[BacktestResult], BacktestMetrics]:
    """
    运行完整回测

    Args:
        data_dir: 数据目录
        test_year: 测试年份
        category: 科类（physics/history）
        use_monte_carlo: 是否使用蒙特卡洛模拟
        sample_size: 采样大小（None 表示使用全部数据）

    Returns:
        (results, metrics) 元组
    """
    print(f"=== 开始离线回测 ===")
    print(f"测试年份: {test_year}")
    print(f"预测方法: {'蒙特卡洛模拟' if use_monte_carlo else '正态分布CDF'}")
    print()

    # 1. 加载历史数据
    years = [2021, 2022, 2023, 2024]
    historical_data = load_historical_data(data_dir, years, category)

    # 2. 准备数据集
    training_data, test_data = prepare_backtest_dataset(
        historical_data, test_year, training_years=3
    )

    # 3. 采样（如果指定）
    if sample_size and len(test_data) > sample_size:
        test_data = test_data.sample(n=sample_size, random_state=42)
        print(f"[Backtest] 采样测试集: {sample_size} 条")

    # 4. 运行回测
    results = []
    for idx, row in test_data.iterrows():
        result = run_backtest_for_row(
            row, training_data, use_monte_carlo, user_rank_percentile=0.5
        )
        if result:
            results.append(result)

        # 进度显示
        if (idx + 1) % 100 == 0:
            print(f"[Backtest] 已处理: {idx + 1}/{len(test_data)}")

    print(f"\n[Backtest] 完成！有效预测: {len(results)}/{len(test_data)}")

    # 5. 计算指标
    metrics = compute_backtest_metrics(results)

    return results, metrics


# === 测试代码 ===
if __name__ == "__main__":
    print("=== 离线回测框架测试 ===\n")

    # 检查数据文件是否存在
    data_dir = Path("backend/data")
    if not data_dir.exists():
        data_dir = Path("data")  # 如果从 backend 目录运行

    required_files = [
        "2021_physics.csv",
        "2022_physics.csv",
        "2023_physics.csv",
        "2024_physics.csv"
    ]

    missing_files = [f for f in required_files if not (data_dir / f).exists()]

    if missing_files:
        print("[ERROR] 缺少必要的数据文件:")
        for f in missing_files:
            print(f"  - {f}")
        print("\n请确保 backend/data 目录中包含 2021-2024 年的历史数据")
        exit(1)

    # 运行小样本回测
    print("运行小样本回测（100条）...\n")
    results, metrics = run_full_backtest(
        data_dir=str(data_dir),
        test_year=2024,
        category='physics',
        use_monte_carlo=False,
        sample_size=100
    )

    # 显示结果
    print("\n=== 回测指标 ===")
    print(f"有效预测数: {metrics.valid_predictions} / {metrics.total_samples}")
    print(f"\n位次预测误差:")
    print(f"  MAE (平均绝对误差): {metrics.mae_rank:.1f} 位")
    print(f"  RMSE (均方根误差): {metrics.rmse_rank:.1f} 位")
    print(f"  最大误差: {metrics.max_error_rank:.1f} 位")
    print(f"\n概率校准误差: {metrics.calibration_error:.2%}")
    print(f"\n策略准确率（±10%范围内）:")
    print(f"  冲刺类: {metrics.accuracy_rush:.2%}")
    print(f"  稳妥类: {metrics.accuracy_target:.2%}")
    print(f"  保底类: {metrics.accuracy_safe:.2%}")

    # 显示部分详细结果
    print("\n=== 前5个回测样本 ===")
    for i, r in enumerate(results[:5], 1):
        print(f"{i}. {r.school_name} - {r.major_name or '(专业组)'}")
        print(f"   预测位次: {r.predicted_rank}，实际位次: {r.actual_rank}")
        print(f"   误差: {r.rank_error:+.0f} 位，预测概率: {r.predicted_prob:.2%}")
        print()

    print("测试完成！")

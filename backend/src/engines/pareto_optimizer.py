"""帕累托前沿优化模块

在志愿填报的多目标优化问题中，找出帕累托最优解集（Pareto Frontier）。

核心概念：
- 帕累托支配（Pareto Dominance）：解A支配解B，当且仅当A在所有目标上都不差于B，且至少在一个目标上严格优于B
- 帕累托前沿（Pareto Frontier）：所有非支配解的集合

应用场景：
1. 识别"被支配"的志愿（存在严格更优的选择）
2. 可视化"冲稳保"策略的权衡曲线
3. 提供多样化的志愿组合方案
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field


class Objective(BaseModel):
    """目标函数定义"""
    name: str = Field(description="目标名称（如'录取概率'）")
    key: str = Field(description="数据字段名（如'admission_prob'）")
    maximize: bool = Field(description="是否最大化（True）或最小化（False）")
    weight: float = Field(
        default=1.0, ge=0.0,
        description="目标权重（用于加权评分）"
    )


class ParetoSolution(BaseModel):
    """帕累托解"""
    volunteer_index: int = Field(description="志愿索引")
    school_name: str = Field(description="学校名称")
    major_name: Optional[str] = Field(default=None, description="专业名称")

    # 目标值
    objectives: Dict[str, float] = Field(
        default_factory=dict,
        description="目标值字典（如 {'admission_prob': 0.8, 'rank': 1000}）"
    )

    # 帕累托排名
    pareto_rank: int = Field(
        description="帕累托排名（1=前沿，2=第二层，...）"
    )

    # 支配关系
    dominated_by_count: int = Field(
        default=0,
        description="被多少个解支配"
    )
    dominates_count: int = Field(
        default=0,
        description="支配多少个解"
    )


class ParetoFrontierResult(BaseModel):
    """帕累托前沿分析结果"""

    # 帕累托前沿（第一层非支配解）
    pareto_frontier: List[ParetoSolution] = Field(
        default_factory=list,
        description="帕累托前沿解集"
    )

    # 所有解（按帕累托排名分层）
    all_solutions: List[ParetoSolution] = Field(
        default_factory=list,
        description="所有解（包含多层）"
    )

    # 被支配的解（建议删除）
    dominated_solutions: List[ParetoSolution] = Field(
        default_factory=list,
        description="被支配的解（存在严格更优的选择）"
    )

    # 统计信息
    frontier_size: int = Field(description="前沿大小")
    dominated_size: int = Field(description="被支配解数量")
    total_solutions: int = Field(description="总解数量")


def is_dominated(
    solution_a: Dict[str, float],
    solution_b: Dict[str, float],
    objectives: List[Objective]
) -> bool:
    """
    判断解A是否被解B支配

    支配条件：
    - B在所有目标上都不差于A
    - B至少在一个目标上严格优于A

    Args:
        solution_a: 解A的目标值
        solution_b: 解B的目标值
        objectives: 目标函数列表

    Returns:
        True 表示 A 被 B 支配
    """
    at_least_one_better = False
    all_not_worse = True

    for obj in objectives:
        key = obj.key
        value_a = solution_a.get(key, 0.0)
        value_b = solution_b.get(key, 0.0)

        if obj.maximize:
            # 最大化目标：value_b > value_a 表示 B 更好
            if value_b > value_a:
                at_least_one_better = True
            elif value_b < value_a:
                all_not_worse = False
                break
        else:
            # 最小化目标：value_b < value_a 表示 B 更好
            if value_b < value_a:
                at_least_one_better = True
            elif value_b > value_a:
                all_not_worse = False
                break

    return all_not_worse and at_least_one_better


def compute_pareto_frontier(
    candidates: List[Dict],
    objectives: List[Objective],
    max_rank: int = 3
) -> ParetoFrontierResult:
    """
    计算帕累托前沿（非支配排序算法）

    使用 NSGA-II 中的 Fast Non-Dominated Sorting 算法

    Args:
        candidates: 候选志愿列表，每个元素是字典，包含目标值
        objectives: 目标函数列表
        max_rank: 最大排名（超过此排名的解不返回）

    Returns:
        ParetoFrontierResult 对象
    """
    if not candidates:
        return ParetoFrontierResult(
            frontier_size=0,
            dominated_size=0,
            total_solutions=0
        )

    n = len(candidates)

    # 初始化支配关系
    dominated_by = [[] for _ in range(n)]  # dominated_by[i] = 支配解i的解列表
    dominates = [[] for _ in range(n)]     # dominates[i] = 解i支配的解列表
    dominated_count = [0] * n              # dominated_count[i] = 支配解i的解数量

    # 提取目标值
    objectives_values = []
    for candidate in candidates:
        obj_dict = {}
        for obj in objectives:
            obj_dict[obj.key] = candidate.get(obj.key, 0.0)
        objectives_values.append(obj_dict)

    # 第一步：计算支配关系
    for i in range(n):
        for j in range(n):
            if i == j:
                continue

            if is_dominated(objectives_values[i], objectives_values[j], objectives):
                # 解i被解j支配
                dominated_by[i].append(j)
                dominates[j].append(i)
                dominated_count[i] += 1

    # 第二步：非支配排序
    fronts = [[]]  # fronts[0] = 第一层（帕累托前沿），fronts[1] = 第二层，...
    for i in range(n):
        if dominated_count[i] == 0:
            # 没有被任何解支配，属于第一层
            fronts[0].append(i)

    # 构建后续层
    current_rank = 0
    while fronts[current_rank] and current_rank < max_rank - 1:
        next_front = []
        for i in fronts[current_rank]:
            # 对于第i个解支配的所有解
            for j in dominates[i]:
                dominated_count[j] -= 1
                if dominated_count[j] == 0:
                    # 解j不再被当前层的解支配，加入下一层
                    next_front.append(j)

        if next_front:
            fronts.append(next_front)
            current_rank += 1
        else:
            break

    # 第三步：构建结果
    all_solutions = []
    pareto_frontier_solutions = []
    dominated_solutions = []

    for rank, front in enumerate(fronts, start=1):
        for idx in front:
            candidate = candidates[idx]

            solution = ParetoSolution(
                volunteer_index=candidate.get('volunteer_index', idx),
                school_name=candidate.get('school_name', ''),
                major_name=candidate.get('major_name'),
                objectives=objectives_values[idx],
                pareto_rank=rank,
                dominated_by_count=len(dominated_by[idx]),
                dominates_count=len(dominates[idx])
            )

            all_solutions.append(solution)

            if rank == 1:
                pareto_frontier_solutions.append(solution)
            elif rank > 1:
                dominated_solutions.append(solution)

    return ParetoFrontierResult(
        pareto_frontier=pareto_frontier_solutions,
        all_solutions=all_solutions,
        dominated_solutions=dominated_solutions,
        frontier_size=len(pareto_frontier_solutions),
        dominated_size=len(dominated_solutions),
        total_solutions=len(all_solutions)
    )


def recommend_from_pareto_frontier(
    pareto_result: ParetoFrontierResult,
    objectives: List[Objective],
    target_count: int = 30
) -> List[ParetoSolution]:
    """
    从帕累托前沿中推荐志愿

    策略：
    1. 优先选择帕累托前沿（rank=1）的解
    2. 如果前沿解不足，选择第二层（rank=2）的解
    3. 在同一层内，按加权评分排序

    Args:
        pareto_result: 帕累托前沿分析结果
        objectives: 目标函数列表
        target_count: 目标推荐数量

    Returns:
        推荐的志愿列表
    """
    if not pareto_result.all_solutions:
        return []

    # 计算加权评分
    def calculate_weighted_score(solution: ParetoSolution) -> float:
        score = 0.0
        for obj in objectives:
            value = solution.objectives.get(obj.key, 0.0)
            if obj.maximize:
                score += value * obj.weight
            else:
                # 最小化目标：转换为最大化（1 / value）
                # 避免除零，添加一个小常数
                score += (1.0 / (value + 1e-6)) * obj.weight
        return score

    # 按帕累托排名和加权评分排序
    solutions_with_scores = [
        (solution, calculate_weighted_score(solution))
        for solution in pareto_result.all_solutions
    ]

    # 先按 pareto_rank 升序，再按 weighted_score 降序
    solutions_with_scores.sort(key=lambda x: (x[0].pareto_rank, -x[1]))

    # 取前 target_count 个
    recommended = [sol for sol, score in solutions_with_scores[:target_count]]

    return recommended


def visualize_pareto_frontier_2d(
    pareto_result: ParetoFrontierResult,
    obj1_key: str,
    obj2_key: str,
    obj1_name: str = "Objective 1",
    obj2_name: str = "Objective 2"
) -> Dict:
    """
    生成二维帕累托前沿可视化数据

    Args:
        pareto_result: 帕累托前沿分析结果
        obj1_key: 第一个目标的字段名
        obj2_key: 第二个目标的字段名
        obj1_name: 第一个目标的显示名称
        obj2_name: 第二个目标的显示名称

    Returns:
        可视化数据字典（用于前端绘图）
    """
    frontier_points = []
    dominated_points = []

    for solution in pareto_result.pareto_frontier:
        x = solution.objectives.get(obj1_key, 0.0)
        y = solution.objectives.get(obj2_key, 0.0)
        frontier_points.append({
            'x': x,
            'y': y,
            'label': f"{solution.school_name} {solution.major_name or ''}".strip(),
            'rank': solution.pareto_rank
        })

    for solution in pareto_result.dominated_solutions:
        x = solution.objectives.get(obj1_key, 0.0)
        y = solution.objectives.get(obj2_key, 0.0)
        dominated_points.append({
            'x': x,
            'y': y,
            'label': f"{solution.school_name} {solution.major_name or ''}".strip(),
            'rank': solution.pareto_rank
        })

    return {
        'obj1_name': obj1_name,
        'obj2_name': obj2_name,
        'frontier_points': frontier_points,
        'dominated_points': dominated_points
    }


# === 测试代码 ===
if __name__ == "__main__":
    # 构造测试数据（模拟志愿填报场景）
    test_candidates = [
        {
            'volunteer_index': 1,
            'school_name': '清华大学',
            'major_name': '计算机科学与技术',
            'admission_prob': 0.3,  # 低概率
            'rank': 500,  # 高质量（位次小）
            'adjustment_risk': 0.1  # 低调剂风险
        },
        {
            'volunteer_index': 2,
            'school_name': '北京大学',
            'major_name': '软件工程',
            'admission_prob': 0.6,  # 中等概率
            'rank': 800,  # 中等质量
            'adjustment_risk': 0.2
        },
        {
            'volunteer_index': 3,
            'school_name': '浙江大学',
            'major_name': '计算机',
            'admission_prob': 0.85,  # 高概率
            'rank': 1200,  # 较低质量
            'adjustment_risk': 0.15
        },
        {
            'volunteer_index': 4,
            'school_name': 'XX大学',
            'major_name': '计算机',
            'admission_prob': 0.5,  # 中等概率
            'rank': 1500,  # 低质量
            'adjustment_risk': 0.5  # 高调剂风险
        },
        {
            'volunteer_index': 5,
            'school_name': 'YY大学',
            'major_name': '计算机',
            'admission_prob': 0.95,  # 极高概率
            'rank': 2000,  # 很低质量
            'adjustment_risk': 0.05
        }
    ]

    # 定义目标函数
    objectives = [
        Objective(name='录取概率', key='admission_prob', maximize=True, weight=1.0),
        Objective(name='学校排名', key='rank', maximize=False, weight=2.0),  # 学校质量权重更高
        Objective(name='调剂风险', key='adjustment_risk', maximize=False, weight=0.5)
    ]

    print("=== 帕累托前沿优化测试 ===\n")

    # 计算帕累托前沿
    result = compute_pareto_frontier(
        candidates=test_candidates,
        objectives=objectives,
        max_rank=3
    )

    print(f"总志愿数: {result.total_solutions}")
    print(f"帕累托前沿大小: {result.frontier_size}")
    print(f"被支配解数量: {result.dominated_size}")
    print()

    # 显示帕累托前沿
    print("=== 帕累托前沿（非支配解）===")
    for i, sol in enumerate(result.pareto_frontier, 1):
        print(f"{i}. {sol.school_name} - {sol.major_name}")
        print(f"   录取概率: {sol.objectives['admission_prob']:.2f}")
        print(f"   学校排名: {sol.objectives['rank']}")
        print(f"   调剂风险: {sol.objectives['adjustment_risk']:.2f}")
        print(f"   支配 {sol.dominates_count} 个解")
        print()

    # 显示被支配的解
    if result.dominated_solutions:
        print("=== 被支配的解（建议删除）===")
        for i, sol in enumerate(result.dominated_solutions, 1):
            print(f"{i}. {sol.school_name} - {sol.major_name}")
            print(f"   录取概率: {sol.objectives['admission_prob']:.2f}")
            print(f"   学校排名: {sol.objectives['rank']}")
            print(f"   被 {sol.dominated_by_count} 个解支配")
            print(f"   帕累托排名: {sol.pareto_rank}")
            print()

    # 推荐志愿
    print("=== 推荐志愿（按帕累托排名+加权评分）===")
    recommendations = recommend_from_pareto_frontier(
        pareto_result=result,
        objectives=objectives,
        target_count=3
    )

    for i, sol in enumerate(recommendations, 1):
        print(f"{i}. {sol.school_name} - {sol.major_name} (Rank {sol.pareto_rank})")

    print("\n测试完成！")

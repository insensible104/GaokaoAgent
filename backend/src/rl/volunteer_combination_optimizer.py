"""志愿组合优化器

使用整数线性规划（Integer Linear Programming）从N个推荐中选择最优的10个志愿

问题建模：
- 决策变量：x_i ∈ {0, 1}, i=1..N（是否选择第i个推荐）
- 目标函数：maximize Σ utility_i * x_i
- 约束条件：
  1. Σ x_i = 10（正好选10个）
  2. Σ x_i * is_rush_i ∈ [2, 4]（2-4个冲刺）
  3. Σ x_i * is_target_i ∈ [4, 6]（4-6个稳妥）
  4. Σ x_i * is_safe_i ∈ [1, 3]（1-3个保底）
  5. 多样性约束（避免过度集中）

方法：
- 使用scipy.optimize.milp（Mixed Integer Linear Programming）
- 生成多种风格的组合（激进/平衡/保守）
"""

import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from dataclasses import dataclass


class VolunteerCandidate(BaseModel):
    """志愿候选（推荐池中的一个专业组）"""
    index: int = Field(description="索引")
    school_name: str = Field(description="学校名称")
    major_group: str = Field(description="专业组代码")
    major_list: List[str] = Field(default_factory=list, description="包含的专业")

    # 核心指标
    admission_prob: float = Field(ge=0.0, le=1.0, description="录取概率")
    major_satisfaction: float = Field(ge=0.0, le=1.0, description="专业满意度")
    school_tier_score: float = Field(ge=0.0, le=1.0, description="学校层次分数")
    comprehensive_score: float = Field(ge=0.0, le=1.0, description="综合评分")
    adjustment_risk: float = Field(ge=0.0, le=1.0, description="调剂风险")

    # 策略类型
    strategy_type: str = Field(description="策略类型: rush/target/safe")

    # 地域
    city: Optional[str] = Field(None, description="城市")


@dataclass
class CombinationStyle:
    """组合风格配置"""
    name: str
    description: str
    objective_weights: Dict[str, float]  # 目标函数权重
    rush_range: Tuple[int, int]  # 冲刺数量范围
    target_range: Tuple[int, int]  # 稳妥数量范围
    safe_range: Tuple[int, int]  # 保底数量范围


class VolunteerCombination(BaseModel):
    """志愿组合（最终的10个志愿）"""
    style_name: str = Field(description="风格名称")
    style_description: str = Field(description="风格说明")
    volunteers: List[VolunteerCandidate] = Field(description="选中的10个志愿")

    # 统计信息
    total_utility: float = Field(description="总效用")
    avg_admission_prob: float = Field(description="平均录取概率")
    avg_major_satisfaction: float = Field(description="平均专业满意度")
    rush_count: int = Field(description="冲刺数量")
    target_count: int = Field(description="稳妥数量")
    safe_count: int = Field(description="保底数量")

    # 风险评估
    admission_guarantee: float = Field(ge=0.0, le=1.0, description="录取保障度")
    major_guarantee: float = Field(ge=0.0, le=1.0, description="专业保障度")


class VolunteerCombinationOptimizer:
    """
    志愿组合优化器

    从N个推荐中选择最优的10个志愿组合
    """

    def __init__(self):
        """初始化优化器"""
        # 预定义的组合风格
        self.styles = {
            "optimal": CombinationStyle(
                name="最优方案（推荐）",
                description="综合平衡学校层次、专业满意度和录取概率",
                objective_weights={
                    "comprehensive": 0.50,
                    "admission_prob": 0.30,
                    "major_satisfaction": 0.20
                },
                rush_range=(2, 4),
                target_range=(4, 6),
                safe_range=(2, 3)
            ),

            "aggressive": CombinationStyle(
                name="激进方案",
                description="冲刺更好的学校，接受一定调剂风险",
                objective_weights={
                    "school_tier": 0.60,
                    "admission_prob": 0.20,
                    "major_satisfaction": 0.20
                },
                rush_range=(4, 5),
                target_range=(4, 5),
                safe_range=(1, 2)
            ),

            "conservative": CombinationStyle(
                name="保守方案（专业优先）",
                description="确保录取到满意的专业，降低滑档风险",
                objective_weights={
                    "major_satisfaction": 0.50,
                    "admission_prob": 0.30,
                    "comprehensive": 0.20
                },
                rush_range=(1, 2),
                target_range=(5, 6),
                safe_range=(3, 4)
            ),

            "balanced_school": CombinationStyle(
                name="学校优先方案",
                description="重点关注学校层次，专业可适当妥协",
                objective_weights={
                    "school_tier": 0.50,
                    "comprehensive": 0.30,
                    "admission_prob": 0.20
                },
                rush_range=(3, 4),
                target_range=(4, 5),
                safe_range=(2, 3)
            )
        }

    def optimize_combinations(
        self,
        candidates: List[VolunteerCandidate],
        user_preferences: Optional[Dict[str, float]] = None,
        num_combinations: int = 4
    ) -> List[VolunteerCombination]:
        """
        生成多种风格的志愿组合

        Args:
            candidates: 候选推荐列表（N个）
            user_preferences: 用户偏好权重（可选）
            num_combinations: 生成的组合数量

        Returns:
            志愿组合列表
        """
        combinations = []

        # 为每种风格生成一个组合
        for style_key in ["optimal", "aggressive", "conservative", "balanced_school"]:
            if len(combinations) >= num_combinations:
                break

            style = self.styles[style_key]

            try:
                combination = self._solve_ilp(candidates, style, user_preferences)
                if combination:
                    combinations.append(combination)
            except Exception as e:
                print(f"[WARN] 优化风格'{style.name}'失败: {e}")
                continue

        return combinations

    def _solve_ilp(
        self,
        candidates: List[VolunteerCandidate],
        style: CombinationStyle,
        user_preferences: Optional[Dict[str, float]] = None
    ) -> Optional[VolunteerCombination]:
        """
        使用整数线性规划求解最优组合

        Args:
            candidates: 候选列表
            style: 组合风格
            user_preferences: 用户偏好

        Returns:
            志愿组合
        """
        n = len(candidates)

        if n < 10:
            print(f"[ERROR] 候选数量不足10个（当前{n}个）")
            return None

        # === 构建目标函数 ===
        objective_weights = style.objective_weights

        # 如果用户提供了偏好，覆盖默认权重
        if user_preferences:
            objective_weights = {**objective_weights, **user_preferences}

        # 计算每个候选的效用
        utilities = []
        for c in candidates:
            utility = (
                objective_weights.get("comprehensive", 0.0) * c.comprehensive_score +
                objective_weights.get("admission_prob", 0.0) * c.admission_prob +
                objective_weights.get("major_satisfaction", 0.0) * c.major_satisfaction +
                objective_weights.get("school_tier", 0.0) * c.school_tier_score
            )
            utilities.append(utility)

        # 目标函数系数（取负，因为scipy默认是最小化）
        c_obj = -np.array(utilities)

        # === 构建约束 ===
        A_constraints = []
        b_lower = []
        b_upper = []

        # 约束1：正好选10个
        A_constraints.append(np.ones(n))
        b_lower.append(10)
        b_upper.append(10)

        # 约束2：冲刺数量
        rush_mask = np.array([
            1 if c.strategy_type == "rush" else 0
            for c in candidates
        ])
        if rush_mask.sum() > 0:
            A_constraints.append(rush_mask)
            b_lower.append(style.rush_range[0])
            b_upper.append(style.rush_range[1])

        # 约束3：稳妥数量
        target_mask = np.array([
            1 if c.strategy_type == "target" else 0
            for c in candidates
        ])
        if target_mask.sum() > 0:
            A_constraints.append(target_mask)
            b_lower.append(style.target_range[0])
            b_upper.append(style.target_range[1])

        # 约束4：保底数量
        safe_mask = np.array([
            1 if c.strategy_type == "safe" else 0
            for c in candidates
        ])
        if safe_mask.sum() > 0:
            A_constraints.append(safe_mask)
            b_lower.append(style.safe_range[0])
            b_upper.append(style.safe_range[1])

        # 约束5：多样性约束（每个城市最多3个）
        city_counts = {}
        for c in candidates:
            if c.city:
                city_counts[c.city] = city_counts.get(c.city, 0) + 1

        for city, count in city_counts.items():
            if count >= 3:  # 只对>=3个候选的城市添加约束
                city_mask = np.array([
                    1 if c.city == city else 0
                    for c in candidates
                ])
                A_constraints.append(city_mask)
                b_lower.append(0)
                b_upper.append(3)  # 最多3个

        # 合并约束
        A = np.array(A_constraints)
        constraints = LinearConstraint(A, b_lower, b_upper)

        # 变量界：0 <= x_i <= 1
        bounds = Bounds(lb=0, ub=1)

        # 整数约束
        integrality = np.ones(n, dtype=int)

        # === 求解 ===
        result = milp(
            c=c_obj,
            constraints=constraints,
            bounds=bounds,
            integrality=integrality
        )

        if not result.success:
            print(f"[WARN] 整数规划求解失败: {result.message}")
            return None

        # === 提取解 ===
        selected_indices = np.where(result.x > 0.5)[0]

        if len(selected_indices) != 10:
            print(f"[WARN] 选中的数量不等于10: {len(selected_indices)}")
            return None

        selected_volunteers = [candidates[i] for i in selected_indices]

        # === 计算统计信息 ===
        total_utility = -result.fun  # 取负（因为目标函数是负的）
        avg_admission_prob = np.mean([v.admission_prob for v in selected_volunteers])
        avg_major_satisfaction = np.mean([v.major_satisfaction for v in selected_volunteers])

        rush_count = sum(1 for v in selected_volunteers if v.strategy_type == "rush")
        target_count = sum(1 for v in selected_volunteers if v.strategy_type == "target")
        safe_count = sum(1 for v in selected_volunteers if v.strategy_type == "safe")

        # 录取保障度：至少有一个高概率志愿
        max_admission_prob = max([v.admission_prob for v in selected_volunteers])
        admission_guarantee = max_admission_prob

        # 专业保障度：平均专业满意度
        major_guarantee = avg_major_satisfaction

        return VolunteerCombination(
            style_name=style.name,
            style_description=style.description,
            volunteers=selected_volunteers,
            total_utility=total_utility,
            avg_admission_prob=avg_admission_prob,
            avg_major_satisfaction=avg_major_satisfaction,
            rush_count=rush_count,
            target_count=target_count,
            safe_count=safe_count,
            admission_guarantee=admission_guarantee,
            major_guarantee=major_guarantee
        )


# === 测试代码 ===
if __name__ == "__main__":
    print("=== 志愿组合优化器测试 ===\n")

    # 生成模拟候选（30个）
    candidates = []

    for i in range(30):
        strategy = "rush" if i < 10 else ("target" if i < 20 else "safe")

        candidates.append(VolunteerCandidate(
            index=i,
            school_name=f"大学{i+1}",
            major_group=f"物理0{i+1}组",
            major_list=["计算机", "软件工程"],
            admission_prob=0.3 + i * 0.025,
            major_satisfaction=0.5 + np.random.rand() * 0.5,
            school_tier_score=(30 - i) / 30.0,
            comprehensive_score=0.9 - i * 0.025,
            adjustment_risk=0.1 + np.random.rand() * 0.3,
            strategy_type=strategy,
            city=["广州", "深圳", "珠海", "佛山"][i % 4]
        ))

    print(f"候选数量: {len(candidates)}")
    print()

    # 创建优化器
    optimizer = VolunteerCombinationOptimizer()

    # 生成组合
    print("生成最优组合...\n")
    combinations = optimizer.optimize_combinations(
        candidates=candidates,
        num_combinations=4
    )

    # 显示结果
    for i, combo in enumerate(combinations, 1):
        print(f"{'='*60}")
        print(f"组合{i}: {combo.style_name}")
        print(f"{'='*60}")
        print(f"说明: {combo.style_description}")
        print(f"\n组合统计:")
        print(f"  总效用: {combo.total_utility:.4f}")
        print(f"  平均录取概率: {combo.avg_admission_prob:.1%}")
        print(f"  平均专业满意度: {combo.avg_major_satisfaction:.1%}")
        print(f"  志愿配比: 冲{combo.rush_count} + 稳{combo.target_count} + 保{combo.safe_count}")
        print(f"  录取保障度: {combo.admission_guarantee:.1%}")
        print(f"  专业保障度: {combo.major_guarantee:.1%}")

        print(f"\n选中的志愿:")
        for j, vol in enumerate(combo.volunteers, 1):
            print(f"  {j}. {vol.school_name} {vol.major_group}")
            print(f"     策略: {vol.strategy_type} | 录取概率: {vol.admission_prob:.1%} | 满意度: {vol.major_satisfaction:.1%}")

        print()

    print("测试完成！")

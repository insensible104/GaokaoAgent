"""两阶段推荐架构

完整的志愿推荐流程，整合所有核心模块：

阶段0（预处理）：
├─ 排位梯度策略：动态确定候选池大小
├─ 量化引擎：搜索候选专业组
├─ 蒙特卡洛模拟：估计录取概率
└─ 帕累托筛选：过滤被支配方案

阶段1（GRPO推荐生成）：
├─ 策略网络：从候选池选N个推荐
├─ 专业分配预测：预测会被分配到哪个专业
└─ 综合评分：计算每个推荐的质量

阶段2（组合优化）：
├─ 整数规划：从N个推荐选10个志愿
├─ 多风格组合：生成激进/平衡/保守方案
└─ 蒙特卡洛验证：模拟最终录取结果
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np

# 导入各模块
from rl.rank_gradient_strategy import RankGradientStrategy
from rl.grpo_recommendation_policy import (
    GRPORecommendationPolicy,
    UserFeatures,
    CandidateFeatures
)
from rl.volunteer_combination_optimizer import (
    VolunteerCombinationOptimizer,
    VolunteerCandidate,
    VolunteerCombination
)
from engines.major_assignment_predictor import (
    MajorAssignmentPredictor
)
from engines.pareto_optimizer import compute_pareto_frontier, Objective
from engines.monte_carlo_sim import monte_carlo_admission_probability


class TwoStageRecommendationEngine:
    """
    两阶段推荐引擎
    """

    def __init__(
        self,
        grpo_model_path: Optional[str] = None,
        data_dir: str = "data",
        device: str = 'cpu'
    ):
        """
        Args:
            grpo_model_path: GRPO策略模型路径（如果已训练）
            data_dir: 数据目录
            device: 计算设备
        """
        # 排位梯度策略
        self.gradient_strategy = RankGradientStrategy()

        # GRPO策略（如果提供了模型路径）
        self.grpo_policy = None
        if grpo_model_path and Path(grpo_model_path).exists():
            self.grpo_policy = GRPORecommendationPolicy(
                model_path=grpo_model_path,
                device=device
            )

        # 组合优化器
        self.combination_optimizer = VolunteerCombinationOptimizer()

        # 专业分配预测器
        self.major_predictor = MajorAssignmentPredictor(data_dir=data_dir)

    def recommend_full_pipeline(
        self,
        user_rank: int,
        user_risk_tolerance: float = 0.5,
        user_major_priority: float = 0.5,
        user_major_preferences: Optional[List[str]] = None,
        candidate_pool_raw: List[Dict] = None,  # 来自game_agent的原始候选池
        use_grpo: bool = True,
        num_final_combinations: int = 4
    ) -> Dict:
        """
        完整推荐流程

        Args:
            user_rank: 用户位次
            user_risk_tolerance: 风险偏好 (0=保守, 1=激进)
            user_major_priority: 专业优先度 (0=学校优先, 1=专业优先)
            user_major_preferences: 用户专业偏好
            candidate_pool_raw: 原始候选池（来自game_agent）
            use_grpo: 是否使用GRPO（如果为False，使用传统方法）
            num_final_combinations: 生成的最终组合数量

        Returns:
            {
                "recommendations_pool": List[VolunteerCandidate],  # 阶段1：N个推荐
                "final_combinations": List[VolunteerCombination],  # 阶段2：多组10个志愿
                "statistics": Dict  # 统计信息
            }
        """
        print("\n" + "="*70)
        print("两阶段推荐引擎 - 完整流程")
        print("="*70)

        # === 阶段0：预处理 ===
        print("\n[阶段0] 预处理...")
        config = self.gradient_strategy.get_config(user_rank)
        print(f"  排位梯度: {config.description}")
        print(f"  候选池目标: {config.candidate_pool_size}个")
        print(f"  推荐目标: {config.recommend_count}个")

        if not candidate_pool_raw:
            raise ValueError("需要提供候选池（candidate_pool_raw）")

        # 转换候选池格式
        candidates_features = self._convert_candidates_to_features(
            candidate_pool_raw,
            user_rank
        )

        print(f"  候选池大小: {len(candidates_features)}个")

        # === 阶段1：GRPO推荐生成（或传统方法）===
        if use_grpo and self.grpo_policy:
            print(f"\n[阶段1] GRPO推荐生成...")
            recommendations = self._stage1_grpo(
                user_rank=user_rank,
                user_risk_tolerance=user_risk_tolerance,
                user_major_priority=user_major_priority,
                candidates=candidates_features,
                n_recommendations=config.recommend_count
            )
        else:
            print(f"\n[阶段1] 传统推荐生成（帕累托+评分排序）...")
            recommendations = self._stage1_traditional(
                candidates=candidates_features,
                n_recommendations=config.recommend_count
            )

        print(f"  生成推荐: {len(recommendations)}个")

        # 转换为VolunteerCandidate格式
        volunteer_candidates = self._convert_to_volunteer_candidates(
            recommendations,
            candidate_pool_raw
        )

        # === 阶段2：组合优化 ===
        print(f"\n[阶段2] 组合优化（整数规划）...")
        user_preferences = {
            "major_satisfaction": user_major_priority,
            "school_tier": 1 - user_major_priority,
            "admission_prob": 0.3
        }

        final_combinations = self.combination_optimizer.optimize_combinations(
            candidates=volunteer_candidates,
            user_preferences=user_preferences,
            num_combinations=num_final_combinations
        )

        print(f"  生成组合: {len(final_combinations)}种")

        # === 统计信息 ===
        statistics = {
            "user_rank": user_rank,
            "gradient_config": {
                "description": config.description,
                "candidate_pool_size": config.candidate_pool_size,
                "recommend_count": config.recommend_count
            },
            "stage1_count": len(recommendations),
            "stage2_combinations": len(final_combinations),
            "method": "GRPO" if (use_grpo and self.grpo_policy) else "Traditional"
        }

        print("\n" + "="*70)
        print("推荐完成！")
        print("="*70)

        return {
            "recommendations_pool": volunteer_candidates,
            "final_combinations": final_combinations,
            "statistics": statistics
        }

    def _stage1_grpo(
        self,
        user_rank: int,
        user_risk_tolerance: float,
        user_major_priority: float,
        candidates: List[CandidateFeatures],
        n_recommendations: int
    ) -> List[CandidateFeatures]:
        """阶段1：使用GRPO生成推荐"""
        user_features = UserFeatures(
            rank=user_rank,
            rank_normalized=user_rank / 100000,
            risk_tolerance=user_risk_tolerance,
            major_priority=user_major_priority
        )

        recommendation = self.grpo_policy.generate_recommendations(
            user_features=user_features,
            candidate_pool=candidates,
            n_recommendations=n_recommendations,
            temperature=1.0,
            deterministic=False
        )

        return recommendation.selected_candidates

    def _stage1_traditional(
        self,
        candidates: List[CandidateFeatures],
        n_recommendations: int
    ) -> List[CandidateFeatures]:
        """阶段1：使用传统方法（帕累托+评分）"""
        # 转换为字典格式
        candidates_dict = []
        for i, c in enumerate(candidates):
            candidates_dict.append({
                'index': i,
                'admission_prob': c.admission_prob,
                'comprehensive_score': c.comprehensive_score,
                'adjustment_risk': c.adjustment_risk,
                'original': c
            })

        # 帕累托筛选
        objectives = [
            Objective(name='录取概率', key='admission_prob', maximize=True, weight=1.0),
            Objective(name='综合评分', key='comprehensive_score', maximize=True, weight=2.0),
            Objective(name='调剂风险', key='adjustment_risk', maximize=False, weight=0.5)
        ]

        pareto_result = compute_pareto_frontier(
            candidates=candidates_dict,
            objectives=objectives,
            max_rank=2
        )

        # 提取帕累托前沿
        pareto_indices = [sol.volunteer_index for sol in pareto_result.pareto_frontier]
        pareto_candidates = [candidates[i] for i in pareto_indices]

        # 按综合评分排序，取top-N
        sorted_candidates = sorted(
            pareto_candidates,
            key=lambda c: c.comprehensive_score,
            reverse=True
        )

        return sorted_candidates[:n_recommendations]

    def _convert_candidates_to_features(
        self,
        candidate_pool_raw: List[Dict],
        user_rank: int
    ) -> List[CandidateFeatures]:
        """将原始候选转换为特征向量"""
        features_list = []

        for c in candidate_pool_raw:
            # 归一化位次差
            rank_diff = c.get('min_rank_pred', user_rank) - user_rank
            rank_diff_normalized = np.clip(rank_diff / 10000, -1.0, 1.0)

            features = CandidateFeatures(
                school_tier=c.get('school_tier', 3),
                admission_prob=c.get('admission_prob', 0.5),
                major_satisfaction=c.get('major_satisfaction', 0.5),
                adjustment_risk=c.get('adjustment_risk', 0.3),
                rank_diff_normalized=rank_diff_normalized,
                comprehensive_score=c.get('comprehensive_score', 0.5)
            )
            features_list.append(features)

        return features_list

    def _convert_to_volunteer_candidates(
        self,
        recommendations: List[CandidateFeatures],
        candidate_pool_raw: List[Dict]
    ) -> List[VolunteerCandidate]:
        """将推荐转换为VolunteerCandidate格式"""
        volunteers = []

        for i, rec in enumerate(recommendations):
            # 找到对应的原始候选
            raw = candidate_pool_raw[i] if i < len(candidate_pool_raw) else {}

            # 确定策略类型
            if rec.admission_prob < 0.5:
                strategy_type = "rush"
            elif rec.admission_prob < 0.85:
                strategy_type = "target"
            else:
                strategy_type = "safe"

            volunteer = VolunteerCandidate(
                index=i,
                school_name=raw.get('school_name', f'学校{i+1}'),
                major_group=raw.get('major_group_code', f'专业组{i+1}'),
                major_list=raw.get('major_list', []),
                admission_prob=rec.admission_prob,
                major_satisfaction=rec.major_satisfaction,
                school_tier_score=(6 - rec.school_tier) / 5.0,
                comprehensive_score=rec.comprehensive_score,
                adjustment_risk=rec.adjustment_risk,
                strategy_type=strategy_type,
                city=raw.get('city')
            )
            volunteers.append(volunteer)

        return volunteers


# === 测试代码 ===
if __name__ == "__main__":
    print("=== 两阶段推荐引擎测试 ===\n")

    # 模拟候选池（来自game_agent）
    mock_candidates = []
    for i in range(50):
        mock_candidates.append({
            'school_name': f'大学{i+1}',
            'major_group_code': f'物理0{i+1}组',
            'major_list': ['计算机', '软件工程'],
            'school_tier': min(5, 1 + i // 10),
            'admission_prob': 0.95 - i * 0.015,
            'major_satisfaction': 0.5 + np.random.rand() * 0.5,
            'adjustment_risk': 0.1 + np.random.rand() * 0.3,
            'comprehensive_score': 0.9 - i * 0.015,
            'min_rank_pred': 10000 + i * 200,
            'city': ['广州', '深圳', '珠海', '佛山'][i % 4]
        })

    # 创建引擎（不使用GRPO模型，用传统方法）
    engine = TwoStageRecommendationEngine(
        grpo_model_path=None,
        data_dir="data"
    )

    # 运行完整流程
    result = engine.recommend_full_pipeline(
        user_rank=12000,
        user_risk_tolerance=0.6,
        user_major_priority=0.8,
        user_major_preferences=["计算机", "软件工程"],
        candidate_pool_raw=mock_candidates,
        use_grpo=False,  # 使用传统方法
        num_final_combinations=3
    )

    # 显示结果
    print(f"\n推荐池大小: {len(result['recommendations_pool'])}")
    print(f"最终组合数: {len(result['final_combinations'])}")

    for i, combo in enumerate(result['final_combinations'], 1):
        print(f"\n组合{i}: {combo.style_name}")
        print(f"  志愿配比: 冲{combo.rush_count} + 稳{combo.target_count} + 保{combo.safe_count}")
        print(f"  平均录取概率: {combo.avg_admission_prob:.1%}")
        print(f"  平均专业满意度: {combo.avg_major_satisfaction:.1%}")

    print("\n测试完成！")

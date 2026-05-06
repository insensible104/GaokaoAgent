"""GRPO推荐训练器

使用Group Relative Policy Optimization训练志愿推荐策略

算法流程：
1. 对于每个训练样本，生成K组不同的推荐方案
2. 评估每组方案的质量（模拟用户选择+蒙特卡洛验证）
3. 计算相对优势（advantages）
4. 使用policy gradient更新策略网络
5. 优势高的方案被增强，优势低的被削弱
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from tqdm import tqdm
import json
from pydantic import BaseModel

from rl.grpo_recommendation_policy import (
    GRPOPolicyNetwork,
    UserFeatures,
    CandidateFeatures,
    GRPORecommendation
)


class TrainingCase(BaseModel):
    """训练样本"""
    user_features: UserFeatures
    candidate_pool: List[CandidateFeatures]
    ground_truth_admitted: Optional[str] = None  # 真实录取结果（如果有）


class GRPOTrainer:
    """
    GRPO推荐训练器
    """

    def __init__(
        self,
        learning_rate: float = 1e-4,
        device: str = 'cpu',
        checkpoint_dir: str = "rl_checkpoints"
    ):
        """
        Args:
            learning_rate: 学习率
            device: 计算设备
            checkpoint_dir: 检查点保存目录
        """
        self.device = device
        self.policy = GRPOPolicyNetwork().to(device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=learning_rate)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 训练统计
        self.episode_rewards = []
        self.episode_best_scores = []
        self.episode_worst_scores = []

    def train_episode(
        self,
        case: TrainingCase,
        n_groups: int = 4,
        n_recommendations: int = 30,
        temperature: float = 1.0
    ) -> Tuple[float, Dict]:
        """
        训练一个episode

        Args:
            case: 训练样本
            n_groups: 生成的推荐组数量（默认4组）
            n_recommendations: 每组推荐的数量（默认30个）
            temperature: 采样温度

        Returns:
            (best_score, info)
        """
        user_vec = torch.FloatTensor(
            case.user_features.to_vector()
        ).unsqueeze(0).to(self.device)

        candidate_vecs = torch.FloatTensor(
            np.array([c.to_vector() for c in case.candidate_pool])
        ).unsqueeze(0).to(self.device)

        # === 步骤1：生成K组推荐 ===
        recommendations_group = []
        log_probs_group = []

        for k in range(n_groups):
            # 每次使用不同的温度增加多样性
            temp = temperature * (1.0 + k * 0.2)

            selected_indices, log_probs = self.policy.select_top_k(
                user_vec,
                candidate_vecs,
                k=n_recommendations,
                temperature=temp,
                deterministic=False
            )

            recommendations_group.append(selected_indices[0])  # [n_recommendations]
            log_probs_group.append(log_probs[0])  # [n_recommendations]

        # === 步骤2：评估每组推荐的质量 ===
        scores = []
        for indices in recommendations_group:
            selected_candidates = [
                case.candidate_pool[i.item()] for i in indices
            ]

            score = self._evaluate_recommendations(
                selected_candidates,
                case.user_features
            )
            scores.append(score)

        scores = np.array(scores)

        # === 步骤3：计算相对优势 ===
        # Advantage = score - mean(scores)
        # 正值表示比平均好，负值表示比平均差
        advantages = scores - scores.mean()

        # === 步骤4：GRPO更新 ===
        self.policy.train()
        policy_loss = 0

        for k in range(n_groups):
            # 计算该组的总log概率
            log_prob_sum = log_probs_group[k].sum()

            # Policy gradient: -log_prob * advantage
            # 优势高 → 负loss → 增强该策略
            # 优势低 → 正loss → 削弱该策略
            policy_loss -= log_prob_sum * advantages[k]

        # 平均loss
        policy_loss = policy_loss / n_groups

        # 反向传播
        self.optimizer.zero_grad()
        policy_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy.parameters(), max_norm=1.0)
        self.optimizer.step()

        # === 统计 ===
        best_score = scores.max()
        worst_score = scores.min()
        mean_score = scores.mean()

        return best_score, {
            'mean_score': mean_score,
            'best_score': best_score,
            'worst_score': worst_score,
            'score_std': scores.std(),
            'policy_loss': policy_loss.item()
        }

    def _evaluate_recommendations(
        self,
        recommendations: List[CandidateFeatures],
        user_features: UserFeatures
    ) -> float:
        """
        评估推荐质量

        模拟：用户从推荐中选择10个，计算期望效用

        Args:
            recommendations: 推荐列表（30个）
            user_features: 用户特征

        Returns:
            质量评分（0-1）
        """
        # === 模拟用户选择10个志愿 ===
        # 简化版：用户会选择综合评分最高的10个
        # （实际应该用组合优化器，但这里为了训练速度用简化版）

        # 按不同策略类型分层选择
        rush_candidates = [
            c for c in recommendations
            if c.admission_prob < 0.5
        ]
        target_candidates = [
            c for c in recommendations
            if 0.5 <= c.admission_prob < 0.85
        ]
        safe_candidates = [
            c for c in recommendations
            if c.admission_prob >= 0.85
        ]

        # 从每层选择
        selected = []

        # 选2-3个冲刺
        rush_sorted = sorted(
            rush_candidates,
            key=lambda c: c.comprehensive_score,
            reverse=True
        )
        selected.extend(rush_sorted[:3])

        # 选4-5个稳妥
        target_sorted = sorted(
            target_candidates,
            key=lambda c: c.comprehensive_score,
            reverse=True
        )
        selected.extend(target_sorted[:5])

        # 选2个保底
        safe_sorted = sorted(
            safe_candidates,
            key=lambda c: c.comprehensive_score,
            reverse=True
        )
        selected.extend(safe_sorted[:2])

        # 确保正好10个
        selected = selected[:10]

        if len(selected) < 10:
            # 不足10个，从所有推荐中补充
            remaining = [c for c in recommendations if c not in selected]
            remaining_sorted = sorted(
                remaining,
                key=lambda c: c.comprehensive_score,
                reverse=True
            )
            selected.extend(remaining_sorted[:10 - len(selected)])

        # First-hit expected utility: later rows only matter if all earlier rows miss.
        survival_before = 1.0
        expected_utility = 0.0
        expected_tail_risk = 0.0

        for rank, candidate in enumerate(selected, 1):
            admission_prob = max(0.0, min(1.0, candidate.admission_prob))
            first_hit_prob = survival_before * admission_prob
            school_tier_score = (6 - candidate.school_tier) / 5.0
            rank_utilization = (11 - rank) / 10.0
            utility_if_admitted = (
                0.5 * candidate.major_satisfaction
                + 0.3 * school_tier_score
                + 0.2 * rank_utilization
            )
            utility_after_tail_risk = utility_if_admitted * (1 - candidate.adjustment_risk)

            expected_utility += first_hit_prob * utility_after_tail_risk
            expected_tail_risk += first_hit_prob * candidate.adjustment_risk
            survival_before *= 1 - admission_prob

        expected_admission_prob = 1 - survival_before
        sliding_risk = 1 - expected_admission_prob
        total_utility = expected_utility - 0.35 * expected_tail_risk - 0.6 * sliding_risk

        has_safe = any(c.admission_prob >= 0.9 for c in selected)
        if not has_safe:
            total_utility *= 0.7
        avg_satisfaction = np.mean([c.major_satisfaction for c in selected])
        if avg_satisfaction < 0.5:
            total_utility *= 0.8

        return float(max(-1.0, min(1.0, total_utility)))

        # === 计算期望效用 ===
        # 模拟录取结果：按平行志愿规则，依次投档
        total_utility = 0.0

        for rank, candidate in enumerate(selected, 1):
            # 该志愿录取的概率
            admission_prob = candidate.admission_prob

            # 如果录取，效用 = 专业满意度 × 学校层次 × 志愿利用率
            school_tier_score = (6 - candidate.school_tier) / 5.0
            rank_utilization = (11 - rank) / 10.0  # 第1志愿=1.0，第10志愿=0.1

            utility_if_admitted = (
                0.5 * candidate.major_satisfaction +
                0.3 * school_tier_score +
                0.2 * rank_utilization
            )

            # 期望效用 = 录取概率 × 效用
            total_utility += admission_prob * utility_if_admitted

            # 如果这个志愿录取了，后面的志愿不考虑
            # （这里简化处理：只考虑最可能录取的志愿）
            if admission_prob > 0.7:
                break

        # 惩罚：如果没有保底志愿（所有录取概率都<0.9），降低评分
        has_safe = any(c.admission_prob >= 0.9 for c in selected)
        if not has_safe:
            total_utility *= 0.7  # 惩罚30%

        # 惩罚：如果专业满意度都很低
        avg_satisfaction = np.mean([c.major_satisfaction for c in selected])
        if avg_satisfaction < 0.5:
            total_utility *= 0.8  # 惩罚20%

        return total_utility

    def train(
        self,
        training_cases: List[TrainingCase],
        n_episodes: int = 1000,
        n_groups: int = 4,
        temperature_start: float = 1.5,
        temperature_end: float = 0.8,
        save_interval: int = 100,
        print_interval: int = 10
    ):
        """
        训练主循环

        Args:
            training_cases: 训练样本列表
            n_episodes: 训练轮数
            n_groups: 每个episode生成的推荐组数
            temperature_start: 初始温度
            temperature_end: 最终温度
            save_interval: 保存间隔
            print_interval: 打印间隔
        """
        print("=" * 60)
        print("GRPO推荐策略训练")
        print("=" * 60)
        print(f"训练样本数: {len(training_cases)}")
        print(f"训练轮数: {n_episodes}")
        print(f"每轮生成: {n_groups}组推荐")
        print(f"学习率: {self.optimizer.param_groups[0]['lr']}")
        print()

        for episode in tqdm(range(n_episodes), desc="Training"):
            # 线性衰减温度
            temperature = temperature_start + (temperature_end - temperature_start) * (
                episode / n_episodes
            )

            # 随机选择一个训练样本
            case = training_cases[np.random.randint(len(training_cases))]

            # 训练一个episode
            best_score, info = self.train_episode(
                case,
                n_groups=n_groups,
                temperature=temperature
            )

            # 记录
            self.episode_rewards.append(best_score)
            self.episode_best_scores.append(info['best_score'])
            self.episode_worst_scores.append(info['worst_score'])

            # 打印进度
            if (episode + 1) % print_interval == 0:
                avg_best = np.mean(self.episode_best_scores[-print_interval:])
                avg_mean = np.mean(self.episode_rewards[-print_interval:])
                avg_worst = np.mean(self.episode_worst_scores[-print_interval:])

                print(f"\nEpisode {episode + 1}/{n_episodes}")
                print(f"  温度: {temperature:.3f}")
                print(f"  最佳组: {avg_best:.4f}")
                print(f"  平均: {avg_mean:.4f}")
                print(f"  最差组: {avg_worst:.4f}")
                print(f"  差距: {avg_best - avg_worst:.4f}")

            # 定期保存
            if (episode + 1) % save_interval == 0:
                self.save_checkpoint(f"grpo_checkpoint_ep{episode + 1}.pt")

        # 训练完成
        print("\n" + "=" * 60)
        print("训练完成！")
        print("=" * 60)
        self._print_summary()

        # 保存最终模型
        self.save_checkpoint("grpo_final_policy.pt")

    def _print_summary(self):
        """打印训练总结"""
        print(f"\n训练统计:")
        print(f"  平均最佳: {np.mean(self.episode_best_scores):.4f}")
        print(f"  最高分: {max(self.episode_best_scores):.4f}")

        # 最近100轮
        if len(self.episode_best_scores) >= 100:
            print(f"\n最近100轮:")
            print(f"  平均最佳: {np.mean(self.episode_best_scores[-100:]):.4f}")
            print(f"  平均平均: {np.mean(self.episode_rewards[-100:]):.4f}")
            print(f"  平均最差: {np.mean(self.episode_worst_scores[-100:]):.4f}")

    def save_checkpoint(self, filename: str):
        """保存检查点"""
        filepath = self.checkpoint_dir / filename

        checkpoint = {
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'episode_rewards': self.episode_rewards,
            'episode_best_scores': self.episode_best_scores,
            'episode_worst_scores': self.episode_worst_scores
        }

        torch.save(checkpoint, filepath)
        print(f"[Save] 检查点已保存: {filepath}")

    def load_checkpoint(self, filename: str):
        """加载检查点"""
        filepath = self.checkpoint_dir / filename

        checkpoint = torch.load(filepath, map_location=self.device)

        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.episode_rewards = checkpoint.get('episode_rewards', [])
        self.episode_best_scores = checkpoint.get('episode_best_scores', [])
        self.episode_worst_scores = checkpoint.get('episode_worst_scores', [])

        print(f"[Load] 检查点已加载: {filepath}")


# === 测试代码 ===
if __name__ == "__main__":
    from pydantic import BaseModel

    print("=== GRPO训练器测试 ===\n")

    # 生成模拟训练数据
    def generate_mock_training_cases(n: int = 10) -> List[TrainingCase]:
        """生成模拟训练样本"""
        cases = []

        for i in range(n):
            user_rank = np.random.randint(10000, 50000)
            user = UserFeatures(
                rank=user_rank,
                rank_normalized=user_rank / 100000,
                risk_tolerance=np.random.rand(),
                major_priority=np.random.rand()
            )

            # 生成候选池（100个）
            candidates = []
            for j in range(100):
                candidates.append(CandidateFeatures(
                    school_tier=min(5, 1 + j // 20),
                    admission_prob=0.95 - j * 0.007,
                    major_satisfaction=0.4 + np.random.rand() * 0.6,
                    adjustment_risk=0.1 + np.random.rand() * 0.4,
                    rank_diff_normalized=j / 100.0,
                    comprehensive_score=0.9 - j * 0.008
                ))

            cases.append(TrainingCase(
                user_features=user,
                candidate_pool=candidates
            ))

        return cases

    # 生成训练数据
    print("生成模拟训练数据...")
    training_cases = generate_mock_training_cases(n=20)
    print(f"生成了 {len(training_cases)} 个训练样本\n")

    # 创建训练器
    trainer = GRPOTrainer(learning_rate=1e-3, device='cpu')

    # 快速训练测试（50轮）
    print("开始快速训练测试（50轮）...\n")
    trainer.train(
        training_cases=training_cases,
        n_episodes=50,
        n_groups=4,
        temperature_start=1.5,
        temperature_end=1.0,
        print_interval=10,
        save_interval=50
    )

    print("\n测试完成！")
    print("完整训练命令:")
    print("  trainer.train(training_cases, n_episodes=1000)")

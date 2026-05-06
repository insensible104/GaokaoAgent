"""Prompt RL 训练器 - Mock 版本

用于演示训练流程，不需要真实LLM
适合快速测试和调试
"""

import json
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple

from rl.learnable_prompt import LearnablePrompt
from rl.environment import Candidate


class MockPromptRLTrainer:
    """
    Mock版本的Prompt RL训练器

    模拟LLM生成，快速演示训练流程
    """

    def __init__(self):
        self.learnable_prompt = LearnablePrompt()
        self.episode_rewards = []
        self.episode_metrics = []

    def _mock_llm_generation(
        self,
        user_rank: int,
        preferences: List[str]
    ) -> List[Candidate]:
        """
        模拟LLM生成候选志愿

        生成规则：
        - 冲刺：rank * 0.7 - rank * 0.9
        - 稳妥：rank * 0.9 - rank * 1.1
        - 保底：rank * 1.1 - rank * 1.5
        """
        candidates = []

        # 获取当前参数
        params = self.learnable_prompt.params
        rush_count = int(45 * params.rush_ratio)
        target_count = int(45 * params.target_ratio)
        safe_count = 45 - rush_count - target_count

        # 模拟学校列表
        schools = [
            "清华大学", "北京大学", "浙江大学", "上海交通大学", "复旦大学",
            "中国科学技术大学", "南京大学", "哈尔滨工业大学", "西安交通大学",
            "中山大学", "华中科技大学", "武汉大学", "同济大学", "东南大学",
            "北京航空航天大学", "电子科技大学", "西北工业大学", "天津大学",
            "南开大学", "北京理工大学", "华南理工大学", "中南大学"
        ]

        majors = preferences if preferences else ["计算机科学与技术", "软件工程"]

        idx = 1

        # 生成冲刺志愿
        for i in range(rush_count):
            school = schools[i % len(schools)]
            major = majors[i % len(majors)]
            prob = np.random.uniform(0.2, params.rush_prob_threshold)

            candidates.append(Candidate(
                volunteer_index=idx,
                school_name=school,
                major_name=major,
                predicted_prob=prob,
                strategy_tag="rush"
            ))
            idx += 1

        # 生成稳妥志愿
        for i in range(target_count):
            school = schools[(rush_count + i) % len(schools)]
            major = majors[i % len(majors)]
            prob = np.random.uniform(params.target_prob_min, params.target_prob_max)

            candidates.append(Candidate(
                volunteer_index=idx,
                school_name=school,
                major_name=major,
                predicted_prob=prob,
                strategy_tag="target"
            ))
            idx += 1

        # 生成保底志愿
        for i in range(safe_count):
            school = schools[(rush_count + target_count + i) % len(schools)]
            major = majors[i % len(majors)]
            prob = np.random.uniform(params.safe_prob_threshold, 0.98)

            candidates.append(Candidate(
                volunteer_index=idx,
                school_name=school,
                major_name=major,
                predicted_prob=prob,
                strategy_tag="safe"
            ))
            idx += 1

        return candidates

    def _mock_reward(self, candidates: List[Candidate], user_rank: int) -> float:
        """
        模拟计算reward

        规则：
        - 有高概率保底志愿：+0.5
        - 有合理的冲刺志愿：+0.3
        - 志愿多样性：+0.2
        """
        reward = 0.0

        # 检查保底志愿
        safe_candidates = [c for c in candidates if c.strategy_tag == "safe"]
        if safe_candidates:
            avg_safe_prob = np.mean([c.predicted_prob for c in safe_candidates])
            if avg_safe_prob > 0.9:
                reward += 0.5

        # 检查冲刺志愿
        rush_candidates = [c for c in candidates if c.strategy_tag == "rush"]
        if rush_candidates and len(rush_candidates) >= 10:
            reward += 0.3

        # 检查多样性
        unique_schools = len(set(c.school_name for c in candidates))
        diversity_score = unique_schools / len(candidates)
        reward += diversity_score * 0.2

        # 添加随机噪声
        reward += np.random.randn() * 0.1

        return reward

    def train_episode(
        self,
        user_rank: int,
        preferences: List[str]
    ) -> Tuple[float, Dict]:
        """训练一个Episode"""

        print(f"\n[Episode] 位次{user_rank}，偏好{preferences}")
        print("  生成候选中（Mock）...")

        # Mock LLM生成
        time.sleep(0.1)  # 模拟生成时间
        candidates = self._mock_llm_generation(user_rank, preferences)

        print(f"  生成 {len(candidates)} 个候选")
        print(f"    冲刺: {sum(1 for c in candidates if c.strategy_tag == 'rush')}")
        print(f"    稳妥: {sum(1 for c in candidates if c.strategy_tag == 'target')}")
        print(f"    保底: {sum(1 for c in candidates if c.strategy_tag == 'safe')}")

        # Mock计算reward
        reward = self._mock_reward(candidates, user_rank)
        print(f"  Reward: {reward:.3f}")

        metrics = {
            'num_candidates': len(candidates),
            'reward': reward
        }

        return reward, metrics

    def train(
        self,
        num_episodes: int = 10,
        learning_rate: float = 0.05
    ):
        """训练主循环"""

        print("=" * 60)
        print("Prompt RL 训练（Mock模式）")
        print("=" * 60)
        print(f"训练轮数: {num_episodes}")
        print(f"学习率: {learning_rate}")
        print()

        for episode in range(num_episodes):
            print(f"\n{'='*60}")
            print(f"Episode {episode + 1}/{num_episodes}")
            print(f"{'='*60}")

            # 随机生成用户案例
            user_rank = np.random.randint(5000, 50000)
            preferences = ["计算机", "软件工程"]

            # 训练
            reward, metrics = self.train_episode(user_rank, preferences)

            # 更新参数
            self.learnable_prompt.update_params(reward, learning_rate)

            # 记录
            self.episode_rewards.append(reward)
            self.episode_metrics.append(metrics)

            # 显示当前参数
            params = self.learnable_prompt.params
            print(f"\n  当前参数:")
            print(f"    冲{params.rush_ratio:.2f}/稳{params.target_ratio:.2f}/保{params.safe_ratio:.2f}")
            print(f"    风险偏好: {params.risk_tolerance:.2f}")

        # 训练完成
        print("\n" + "=" * 60)
        print("训练完成！")
        print("=" * 60)
        self._print_summary()

        # 保存
        self.save_checkpoint()

    def _print_summary(self):
        """打印训练总结"""
        print(f"\n训练统计:")
        print(f"  平均Reward: {np.mean(self.episode_rewards):.3f}")
        print(f"  最佳Reward: {max(self.episode_rewards):.3f}")
        print(f"  最差Reward: {min(self.episode_rewards):.3f}")

        # 绘制reward曲线（简单文本版）
        print(f"\nReward曲线:")
        for i, r in enumerate(self.episode_rewards):
            bar_length = int((r + 1) * 20)  # 归一化到0-40
            bar = "█" * max(0, bar_length)
            print(f"  Ep{i+1:2d}: {bar} {r:.3f}")

        if self.learnable_prompt.best_params:
            print(f"\n最佳参数:")
            bp = self.learnable_prompt.best_params
            print(f"  冲{bp.rush_ratio:.2f}/稳{bp.target_ratio:.2f}/保{bp.safe_ratio:.2f}")
            print(f"  风险偏好: {bp.risk_tolerance:.2f}")
            print(f"  多样性: {bp.diversity_weight:.2f}")

    def save_checkpoint(self):
        """保存训练结果"""
        save_dir = Path("rl_checkpoints")
        save_dir.mkdir(parents=True, exist_ok=True)

        # 保存参数
        filepath = save_dir / "mock_checkpoint.json"
        self.learnable_prompt.save(str(filepath))

        # 保存统计
        stats_file = save_dir / "mock_stats.json"
        with open(stats_file, 'w') as f:
            json.dump({
                'episode_rewards': self.episode_rewards,
                'episode_metrics': self.episode_metrics
            }, f, indent=2)

        print(f"\n[Save] 结果已保存到 {save_dir}")


# ============================================
# 快速测试
# ============================================

if __name__ == "__main__":
    print("=== Mock Prompt RL 训练器 ===\n")

    trainer = MockPromptRLTrainer()
    trainer.train(num_episodes=10, learning_rate=0.05)

    print("\n测试完成！")

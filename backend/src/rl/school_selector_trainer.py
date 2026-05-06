"""学校选择RL训练器

使用策略梯度算法（REINFORCE）训练学校选择策略网络

训练流程：
1. 从候选池采样（200个学校）
2. 策略网络选择45个学校
3. 环境回测，计算reward
4. 使用策略梯度更新网络
5. 重复训练
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Dict, Tuple
from pathlib import Path
import json
from tqdm import tqdm

from rl.school_selection_env import (
    SchoolSelectionEnv,
    PolicyNetwork,
    UserContext,
    SchoolFeatures,
    SchoolSelectionAction
)


class SchoolSelectorTrainer:
    """
    学校选择RL训练器

    算法：REINFORCE（策略梯度）
    """

    def __init__(
        self,
        historical_data: Dict,
        learning_rate: float = 1e-4,
        gamma: float = 0.99,
        device: str = 'cpu'
    ):
        """
        Args:
            historical_data: 历史录取数据
            learning_rate: 学习率
            gamma: 折扣因子
            device: 计算设备
        """
        self.env = SchoolSelectionEnv(historical_data)
        self.policy = PolicyNetwork().to(device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=learning_rate)
        self.gamma = gamma
        self.device = device

        # 训练统计
        self.episode_rewards = []
        self.episode_success_rate = []

    def compute_returns(self, rewards: List[float]) -> List[float]:
        """
        计算折扣回报

        Args:
            rewards: 奖励序列

        Returns:
            折扣回报序列
        """
        returns = []
        R = 0
        for r in reversed(rewards):
            R = r + self.gamma * R
            returns.insert(0, R)

        # 标准化
        returns = torch.tensor(returns, dtype=torch.float32)
        returns = (returns - returns.mean()) / (returns.std() + 1e-8)

        return returns.tolist()

    def train_episode(
        self,
        user_context: UserContext,
        candidate_pool: List[SchoolFeatures],
        temperature: float = 1.0,
        epsilon: float = 0.1
    ) -> Tuple[float, Dict]:
        """
        训练一个episode

        Args:
            user_context: 用户上下文
            candidate_pool: 候选池 (200个)
            temperature: 温度参数
            epsilon: 探索率

        Returns:
            (total_reward, info)
        """
        # 重置环境
        state = self.env.reset(user_context, candidate_pool)

        # 提取特征
        user_vec = user_context.to_vector()
        school_vecs = np.array([s.to_vector() for s in candidate_pool])

        # 转为tensor
        user_tensor = torch.FloatTensor(user_vec).unsqueeze(0).to(self.device)
        school_tensor = torch.FloatTensor(school_vecs).unsqueeze(0).to(self.device)

        # 选择45个学校
        self.policy.train()
        logits = self.policy(user_tensor, school_tensor).squeeze(0)  # [200]

        # 策略梯度：记录log概率
        log_probs = []
        rewards = []
        selected_indices = []

        probs = torch.softmax(logits / temperature, dim=0)

        # 依次选择45个学校
        remaining_mask = torch.ones(len(candidate_pool), dtype=torch.bool)

        for step in range(45):
            # ε-greedy探索
            if np.random.rand() < epsilon:
                # 随机选择（从未选过的）
                available = torch.where(remaining_mask)[0]
                action_idx = np.random.choice(available.cpu().numpy())
            else:
                # 根据概率采样
                masked_probs = probs.clone()
                masked_probs[~remaining_mask] = 0
                masked_probs = masked_probs / masked_probs.sum()

                # 采样
                dist = torch.distributions.Categorical(masked_probs)
                action_idx = dist.sample().item()

                # 记录log概率
                log_probs.append(dist.log_prob(torch.tensor(action_idx)))

            # 标记已选
            remaining_mask[action_idx] = False
            selected_indices.append(action_idx)

            # 环境step
            action = SchoolSelectionAction(school_index=action_idx)
            state, reward, done, info = self.env.step(action)
            rewards.append(reward)

            if done:
                break

        # 计算折扣回报
        returns = self.compute_returns(rewards)

        # 策略梯度更新
        policy_loss = []
        for log_prob, R in zip(log_probs, returns):
            policy_loss.append(-log_prob * R)

        if policy_loss:
            loss = torch.stack(policy_loss).sum()

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy.parameters(), max_norm=1.0)
            self.optimizer.step()

        # 统计
        total_reward = sum(rewards)
        success = info.get('admitted', False)

        return total_reward, {
            'success': success,
            'admitted_school': info.get('admitted_school'),
            'admitted_index': info.get('admitted_index'),
            'selected_schools': info.get('selected_schools', [])[:10]  # 前10个
        }

    def train(
        self,
        n_episodes: int = 1000,
        temperature: float = 1.0,
        epsilon_start: float = 0.3,
        epsilon_end: float = 0.05,
        save_interval: int = 100,
        print_interval: int = 10
    ):
        """
        训练主循环

        Args:
            n_episodes: 训练轮数
            temperature: 温度参数
            epsilon_start: 初始探索率
            epsilon_end: 最终探索率
            save_interval: 保存间隔
            print_interval: 打印间隔
        """
        print("=" * 60)
        print("开始学校选择RL训练")
        print("=" * 60)
        print(f"训练轮数: {n_episodes}")
        print(f"学习率: {self.optimizer.param_groups[0]['lr']}")
        print(f"温度: {temperature}")
        print(f"探索率: {epsilon_start} -> {epsilon_end}")
        print()

        for episode in tqdm(range(n_episodes), desc="Training"):
            # 线性衰减探索率
            epsilon = epsilon_start + (epsilon_end - epsilon_start) * (episode / n_episodes)

            # 采样用户画像和候选池
            user_context, candidate_pool = self._sample_case()

            # 训练一个episode
            total_reward, info = self.train_episode(
                user_context, candidate_pool,
                temperature=temperature,
                epsilon=epsilon
            )

            # 记录
            self.episode_rewards.append(total_reward)
            self.episode_success_rate.append(1.0 if info['success'] else 0.0)

            # 打印进度
            if (episode + 1) % print_interval == 0:
                avg_reward = np.mean(self.episode_rewards[-print_interval:])
                avg_success = np.mean(self.episode_success_rate[-print_interval:])
                print(f"\nEpisode {episode+1}/{n_episodes}")
                print(f"  平均Reward: {avg_reward:.3f}")
                print(f"  录取率: {avg_success*100:.1f}%")
                print(f"  探索率: {epsilon:.3f}")

                if info['success']:
                    print(f"  录取: {info['admitted_school']} (第{info['admitted_index']}志愿)")

            # 定期保存
            if (episode + 1) % save_interval == 0:
                self.save_checkpoint(f"checkpoint_ep{episode+1}.pt")

        # 训练完成
        print("\n" + "=" * 60)
        print("训练完成！")
        print("=" * 60)
        self._print_summary()

        # 保存最终模型
        self.save_checkpoint("final_model.pt")

    def _sample_case(self) -> Tuple[UserContext, List[SchoolFeatures]]:
        """
        采样一个训练案例

        Returns:
            (user_context, candidate_pool)
        """
        # 随机用户画像
        user_rank = np.random.randint(5000, 50000)
        user_context = UserContext(
            user_rank=user_rank,
            rank_normalized=user_rank / 100000,
            category="physics",
            risk_tolerance=np.random.rand(),
            school_priority=np.random.rand(),
            major_priority=1 - np.random.rand(),
            major_preferences=["计算机", "软件工程"]
        )

        # 随机候选池（模拟）
        candidate_pool = []
        base_rank = user_rank - 5000

        for i in range(200):
            rank_offset = i * 50
            admission_prob = 1.0 / (1.0 + np.exp((rank_offset - 2500) / 500))  # sigmoid

            school = SchoolFeatures(
                school_name=f"大学{i+1}",
                major_group="计算机类",
                min_rank_hist=base_rank + rank_offset,
                admission_prob=admission_prob,
                rank_volatility=0.1 + np.random.rand() * 0.2,
                quota=30 + i // 2,
                major_match_score=0.5 + np.random.rand() * 0.5,
                school_tier=min(4, 1 + i // 50),
                location_score=0.5 + np.random.rand() * 0.5,
                employment_rate=0.75 + np.random.rand() * 0.25,
                avg_salary=0.6 + np.random.rand() * 0.4,
                postgrad_rate=0.2 + np.random.rand() * 0.3,
                strategy_tag=0 if admission_prob < 0.6 else (1 if admission_prob < 0.85 else 2)
            )
            candidate_pool.append(school)

        return user_context, candidate_pool

    def _print_summary(self):
        """打印训练总结"""
        print(f"\n训练统计:")
        print(f"  平均Reward: {np.mean(self.episode_rewards):.3f}")
        print(f"  最佳Reward: {max(self.episode_rewards):.3f}")
        print(f"  最差Reward: {min(self.episode_rewards):.3f}")
        print(f"  平均录取率: {np.mean(self.episode_success_rate)*100:.1f}%")

        # 最近100轮
        if len(self.episode_rewards) >= 100:
            print(f"\n最近100轮:")
            print(f"  平均Reward: {np.mean(self.episode_rewards[-100:]):.3f}")
            print(f"  录取率: {np.mean(self.episode_success_rate[-100:])*100:.1f}%")

    def save_checkpoint(self, filename: str):
        """保存检查点"""
        save_dir = Path("rl_checkpoints")
        save_dir.mkdir(parents=True, exist_ok=True)

        filepath = save_dir / filename

        checkpoint = {
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'episode_rewards': self.episode_rewards,
            'episode_success_rate': self.episode_success_rate
        }

        torch.save(checkpoint, filepath)
        print(f"[Save] 检查点已保存: {filepath}")

    def load_checkpoint(self, filename: str):
        """加载检查点"""
        filepath = Path("rl_checkpoints") / filename

        checkpoint = torch.load(filepath, map_location=self.device)

        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.episode_rewards = checkpoint.get('episode_rewards', [])
        self.episode_success_rate = checkpoint.get('episode_success_rate', [])

        print(f"[Load] 检查点已加载: {filepath}")


# ============================================
# 测试代码
# ============================================

if __name__ == "__main__":
    print("=== 学校选择RL训练器测试 ===\n")

    # 创建训练器
    print("初始化训练器...")
    trainer = SchoolSelectorTrainer(
        historical_data={},
        learning_rate=1e-3
    )

    # 快速测试（10轮）
    print("\n开始快速测试（10轮）...")
    trainer.train(
        n_episodes=10,
        temperature=1.0,
        epsilon_start=0.3,
        epsilon_end=0.1,
        print_interval=5,
        save_interval=10
    )

    print("\n测试完成！")
    print("\n完整训练命令:")
    print("  trainer.train(n_episodes=1000, temperature=1.0)")

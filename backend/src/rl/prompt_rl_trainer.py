"""Prompt RL 训练器

支持：
1. 本地 ollama 模型（开发测试）
2. 云端 API（GPT-4/Claude，生产部署）
3. 灵活切换，无需修改代码
"""

import os
import json
import time
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np

# 导入自定义模块
from rl.learnable_prompt import LearnablePrompt, PromptParameters
from rl.environment import (
    Candidate, VolunteerEnvironment,
    calculate_reward, ActualOutcome
)
from utils.llm_factory import get_llm


class PromptRLTrainer:
    """
    Prompt RL 训练器

    训练流程：
    1. 用当前prompt参数生成候选志愿
    2. 使用历史数据回测，计算reward
    3. 根据reward更新prompt参数
    4. 重复直到收敛
    """

    def __init__(
        self,
        model_name: str = "local",  # "local" 或 "gpt-4" 或 "claude"
        data_dir: str = "backend/data"
    ):
        """
        Args:
            model_name: 模型选择
                - "local": 使用本地ollama（qwen2.5:7b）
                - "gpt-4": 使用GPT-4 API
                - "claude": 使用Claude API
            data_dir: 历史数据目录
        """
        self.model_name = model_name
        self.data_dir = Path(data_dir)

        # 初始化LLM
        print(f"[Init] 初始化模型: {model_name}")
        if model_name == "local":
            os.environ['LLM_PROVIDER'] = 'local'
            self.llm = get_llm(temperature=0.7)
            print("  使用本地 Ollama 模型")
        elif model_name == "gpt-4":
            os.environ['LLM_PROVIDER'] = 'cloud'
            os.environ['QWEN_MODEL'] = 'gpt-4'  # 假设配置了OpenAI
            self.llm = get_llm(temperature=0.7)
            print("  使用 GPT-4 API")
        else:
            # Claude 或其他
            self.llm = get_llm(temperature=0.7)
            print(f"  使用 {model_name} API")

        # 初始化可学习prompt
        self.learnable_prompt = LearnablePrompt()

        # 加载历史数据
        self.env = None
        self._load_historical_data()

        # 训练统计
        self.episode_rewards = []
        self.episode_metrics = []

    def _load_historical_data(self):
        """加载历史录取数据"""
        print("[Init] 加载历史数据...")

        historical_data = {}
        for year in [2021, 2022, 2023, 2024]:
            file_path = self.data_dir / f"{year}_physics.csv"
            if file_path.exists():
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                historical_data[year] = df
                print(f"  [OK] {year}: {len(df)} 条记录")

        if not historical_data:
            print("  [WARN] 未找到历史数据，将使用模拟数据")
            self.env = None
        else:
            self.env = VolunteerEnvironment(historical_data)
            print(f"  [OK] 环境初始化完成")

    def _parse_llm_output(self, llm_response: str) -> List[Candidate]:
        """
        解析LLM输出，提取候选志愿

        Args:
            llm_response: LLM的原始输出

        Returns:
            Candidate列表
        """
        try:
            # 尝试解析JSON
            # 查找JSON代码块
            if "```json" in llm_response:
                start = llm_response.find("```json") + 7
                end = llm_response.find("```", start)
                json_str = llm_response[start:end].strip()
            elif "```" in llm_response:
                start = llm_response.find("```") + 3
                end = llm_response.find("```", start)
                json_str = llm_response[start:end].strip()
            else:
                json_str = llm_response.strip()

            # 解析JSON
            data = json.loads(json_str)

            # 转换为Candidate对象
            candidates = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                candidate = Candidate(
                    volunteer_index=item.get('volunteer_index', len(candidates) + 1),
                    school_name=item.get('school_name', '未知学校'),
                    major_name=item.get('major_name', '未知专业'),
                    predicted_prob=item.get('predicted_prob', 0.5),
                    strategy_tag=item.get('strategy_tag', 'target')
                )
                candidates.append(candidate)

            return candidates[:45]  # 最多45个

        except Exception as e:
            print(f"[ERROR] 解析LLM输出失败: {e}")
            print(f"  原始输出: {llm_response[:200]}...")
            return []

    def train_episode(
        self,
        user_rank: int,
        category: str,
        preferences: List[str],
        year: int = 2024,
        num_samples: int = 1,  # TTS: 生成多个样本
        temperature: float = 0.7  # TTS: 控制多样性
    ) -> Tuple[float, Dict]:
        """
        训练一个Episode (支持 Test Time Scaling)

        Args:
            user_rank: 用户位次
            category: 科类
            preferences: 专业偏好
            year: 测试年份
            num_samples: TTS采样数量（>1时启用TTS）
            temperature: 生成温度（影响多样性）

        Returns:
            (best_reward, metrics)
        """
        print(f"\n[Episode] 位次{user_rank}，{category}，偏好{preferences}")

        if num_samples > 1:
            print(f"  [TTS] 启用Test Time Scaling，生成{num_samples}个候选方案")

        # 1. 生成prompt
        prompt = self.learnable_prompt.generate_prompt(
            user_rank=user_rank,
            category=category,
            preferences=preferences
        )

        # TTS: 生成多个候选方案，选择最优
        all_samples = []
        total_generation_time = 0

        for sample_idx in range(num_samples):
            if num_samples > 1:
                print(f"  [TTS] 生成方案 {sample_idx + 1}/{num_samples}...")
            else:
                print("  生成候选中...")

            # 2. LLM生成候选志愿
            start_time = time.time()
            try:
                llm_response = self.llm.invoke(prompt).content
            except Exception as e:
                print(f"  [ERROR] LLM调用失败: {e}")
                continue  # 跳过失败的样本

            generation_time = time.time() - start_time
            total_generation_time += generation_time

            # 3. 解析输出
            candidates = self._parse_llm_output(llm_response)

            if not candidates:
                print(f"  [WARN] 方案{sample_idx + 1}未能解析出候选")
                continue

            if num_samples == 1:
                print(f"  生成耗时: {generation_time:.1f}秒")
                print(f"  成功生成 {len(candidates)} 个候选")

            # 4. 环境模拟（回测）
            if self.env:
                self.env.reset(user_rank, category, year)
                _, reward, done, info = self.env.step(candidates)

                actual_outcome = info.get('actual_outcome')
                reward_components = info.get('reward_components')

            else:
                # 模拟reward（无历史数据时）
                reward = np.random.randn() * 0.5
                actual_outcome = None
                reward_components = None

            # 记录样本
            all_samples.append({
                'sample_idx': sample_idx,
                'candidates': candidates,
                'reward': reward,
                'generation_time': generation_time,
                'actual_outcome': actual_outcome,
                'reward_components': reward_components
            })

            if num_samples == 1:
                # 单样本模式：直接输出
                admitted = actual_outcome.admitted if actual_outcome else False
                print(f"  回测结果: {'录取' if admitted else '滑档'}")
                if actual_outcome and actual_outcome.admitted:
                    print(f"    录取学校: {actual_outcome.admitted_school}")
                    print(f"    志愿序号: 第{actual_outcome.admitted_index}志愿")
                print(f"  Reward: {reward:.3f}")

        # TTS: 没有成功生成任何样本
        if not all_samples:
            print("  [ERROR] 所有样本生成失败")
            return -2.0, {}

        # TTS: 选择reward最高的样本
        best_sample = max(all_samples, key=lambda x: x['reward'])
        best_reward = best_sample['reward']
        best_idx = best_sample['sample_idx']

        # TTS统计信息
        if num_samples > 1:
            rewards = [s['reward'] for s in all_samples]
            print(f"\n  [TTS] 总耗时: {total_generation_time:.1f}秒")
            print(f"  [TTS] 所有方案Reward: {[f'{r:.3f}' for r in rewards]}")
            print(f"  [TTS] 最佳方案: #{best_idx + 1}, Reward={best_reward:.3f}")
            print(f"  [TTS] Reward范围: [{min(rewards):.3f}, {max(rewards):.3f}]")
            print(f"  [TTS] Reward提升: {best_reward - np.mean(rewards):.3f} (vs平均)")

            actual_outcome = best_sample['actual_outcome']
            if actual_outcome:
                print(f"  回测结果: {'录取' if actual_outcome.admitted else '滑档'}")
                if actual_outcome.admitted:
                    print(f"    录取学校: {actual_outcome.admitted_school}")
                    print(f"    志愿序号: 第{actual_outcome.admitted_index}志愿")

        # 5. 统计指标
        metrics = {
            'num_candidates': len(best_sample['candidates']),
            'generation_time': total_generation_time,
            'admitted': best_sample['actual_outcome'].admitted if best_sample['actual_outcome'] else False,
            'reward': best_reward,
            'num_samples': num_samples,  # TTS采样数
            'all_rewards': [s['reward'] for s in all_samples],  # 所有样本的reward
            'reward_improvement': best_reward - np.mean([s['reward'] for s in all_samples]) if len(all_samples) > 1 else 0.0
        }

        return best_reward, metrics

    def train(
        self,
        num_episodes: int = 20,
        learning_rate: float = 0.05,
        save_interval: int = 5,
        num_samples: int = 1,  # TTS: 每个episode的采样数量
        temperature: float = 0.7  # TTS: 生成温度
    ):
        """
        训练主循环 (支持 Test Time Scaling)

        Args:
            num_episodes: 训练轮数
            learning_rate: 学习率
            save_interval: 保存间隔
            num_samples: TTS采样数量（>1时启用TTS）
            temperature: 生成温度
        """
        print("=" * 60)
        print("开始 Prompt RL 训练")
        print("=" * 60)
        print(f"模型: {self.model_name}")
        print(f"训练轮数: {num_episodes}")
        print(f"学习率: {learning_rate}")
        if num_samples > 1:
            print(f"[TTS] Test Time Scaling: 每episode生成{num_samples}个样本")
            print(f"[TTS] 预计总LLM调用: {num_episodes * num_samples}次")
        print()

        # TTS统计
        tts_improvements = []

        # 训练循环
        for episode in range(num_episodes):
            print(f"\n{'='*60}")
            print(f"Episode {episode + 1}/{num_episodes}")
            print(f"{'='*60}")

            # 从历史数据采样一个案例
            user_rank, category, preferences, year = self._sample_case()

            # 训练一个episode (支持TTS)
            reward, metrics = self.train_episode(
                user_rank=user_rank,
                category=category,
                preferences=preferences,
                year=year,
                num_samples=num_samples,  # TTS参数
                temperature=temperature
            )

            # 记录TTS改进
            if num_samples > 1 and 'reward_improvement' in metrics:
                tts_improvements.append(metrics['reward_improvement'])

            # 更新prompt参数
            self.learnable_prompt.update_params(reward, learning_rate)

            # 记录
            self.episode_rewards.append(reward)
            self.episode_metrics.append(metrics)

            # 显示当前参数
            params = self.learnable_prompt.params
            print(f"\n  当前参数:")
            print(f"    冲{params.rush_ratio:.2f}/稳{params.target_ratio:.2f}/保{params.safe_ratio:.2f}")
            print(f"    风险偏好: {params.risk_tolerance:.2f}")

            # 定期保存
            if (episode + 1) % save_interval == 0:
                self.save_checkpoint(f"checkpoint_ep{episode+1}.json")

        # 训练完成
        print("\n" + "=" * 60)
        print("训练完成！")
        print("=" * 60)
        self._print_summary()

        # TTS统计
        if tts_improvements:
            print(f"\n[TTS] Test Time Scaling 统计:")
            print(f"  平均Reward提升: {np.mean(tts_improvements):.3f}")
            print(f"  最大提升: {max(tts_improvements):.3f}")
            print(f"  提升率: {np.mean([1 if x > 0 else 0 for x in tts_improvements])*100:.1f}%")

        # 保存最终参数
        self.save_checkpoint("final_checkpoint.json")

    def _sample_case(self) -> Tuple[int, str, List[str], int]:
        """从历史数据采样一个测试案例"""
        # 随机生成用户画像
        user_rank = np.random.randint(5000, 50000)
        category = "physics"
        preferences = ["计算机", "软件工程", "人工智能"][:np.random.randint(1, 4)]
        year = 2024

        return user_rank, category, preferences, year

    def _print_summary(self):
        """打印训练总结"""
        print(f"\n训练统计:")
        print(f"  平均Reward: {np.mean(self.episode_rewards):.3f}")
        print(f"  最佳Reward: {max(self.episode_rewards):.3f}")
        print(f"  最差Reward: {min(self.episode_rewards):.3f}")

        if self.learnable_prompt.best_params:
            print(f"\n最佳参数:")
            bp = self.learnable_prompt.best_params
            print(f"  冲{bp.rush_ratio:.2f}/稳{bp.target_ratio:.2f}/保{bp.safe_ratio:.2f}")
            print(f"  风险偏好: {bp.risk_tolerance:.2f}")

    def save_checkpoint(self, filename: str):
        """保存训练检查点"""
        save_dir = Path("rl_checkpoints")
        save_dir.mkdir(parents=True, exist_ok=True)

        filepath = save_dir / filename

        # 保存prompt参数
        self.learnable_prompt.save(str(filepath))

        # 保存训练统计
        stats_file = filepath.with_suffix('.stats.json')
        with open(stats_file, 'w') as f:
            json.dump({
                'episode_rewards': self.episode_rewards,
                'episode_metrics': self.episode_metrics
            }, f, indent=2)

        print(f"[Save] 检查点已保存: {filepath}")


# ============================================
# 测试代码
# ============================================

if __name__ == "__main__":
    print("=== Prompt RL 训练器 ===\n")

    # 创建训练器（使用本地ollama）
    trainer = PromptRLTrainer(model_name="local")

    # 运行完整训练（20个episodes）
    print("\n开始完整训练（20 episodes）...\n")
    trainer.train(num_episodes=20, learning_rate=0.05)

    print("\n训练完成！")

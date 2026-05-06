"""可学习的Prompt模板

核心思想：
- Prompt本身有"参数"（如冲稳保比例、风险偏好）
- 通过RL训练，自动学习最优参数
- 模型本身不变，只优化prompt

示例：
  初始：冲0.33/稳0.33/保0.34
  训练后：冲0.25/稳0.40/保0.35（学习到的最优策略）
"""

import numpy as np
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import json


class PromptParameters(BaseModel):
    """Prompt的可学习参数"""

    # 策略比例（核心参数）
    rush_ratio: float = Field(
        default=0.33, ge=0.0, le=1.0,
        description="冲刺志愿比例"
    )
    target_ratio: float = Field(
        default=0.33, ge=0.0, le=1.0,
        description="稳妥志愿比例"
    )
    safe_ratio: float = Field(
        default=0.34, ge=0.0, le=1.0,
        description="保底志愿比例"
    )

    # 概率阈值
    rush_prob_threshold: float = Field(
        default=0.6, ge=0.0, le=1.0,
        description="冲刺志愿概率上限"
    )
    target_prob_min: float = Field(
        default=0.6, ge=0.0, le=1.0,
        description="稳妥志愿概率下限"
    )
    target_prob_max: float = Field(
        default=0.85, ge=0.0, le=1.0,
        description="稳妥志愿概率上限"
    )
    safe_prob_threshold: float = Field(
        default=0.85, ge=0.0, le=1.0,
        description="保底志愿概率下限"
    )

    # 高级策略参数
    risk_tolerance: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="风险偏好（0=保守，1=激进）"
    )
    diversity_weight: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="学校多样性权重"
    )
    prestige_weight: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description="学校声望权重"
    )

    def normalize_ratios(self):
        """归一化比例，确保总和=1"""
        total = self.rush_ratio + self.target_ratio + self.safe_ratio
        if total > 0:
            self.rush_ratio /= total
            self.target_ratio /= total
            self.safe_ratio /= total


class LearnablePrompt:
    """
    可学习的Prompt生成器

    功能：
    1. 根据参数生成结构化prompt
    2. 支持参数更新（RL训练）
    3. 保存/加载学习到的参数
    """

    def __init__(self, initial_params: Optional[PromptParameters] = None):
        """
        Args:
            initial_params: 初始参数（可选）
        """
        self.params = initial_params or PromptParameters()
        self.params.normalize_ratios()

        # 训练历史
        self.training_history = []
        self.best_params = None
        self.best_reward = float('-inf')

    def generate_prompt(
        self,
        user_rank: int,
        category: str,
        preferences: List[str],
        historical_context: Optional[str] = None
    ) -> str:
        """
        生成结构化prompt

        Args:
            user_rank: 用户位次
            category: 科类
            preferences: 专业偏好
            historical_context: 历史成功案例（可选）

        Returns:
            完整的prompt字符串
        """
        # 计算每类志愿数量
        total_slots = 45
        rush_count = int(total_slots * self.params.rush_ratio)
        target_count = int(total_slots * self.params.target_ratio)
        safe_count = total_slots - rush_count - target_count  # 确保总和=45

        # 构造prompt
        prompt = f"""你是一位资深的高考志愿填报专家。请为用户生成45个志愿推荐。

## 用户信息
- 位次：{user_rank}
- 科类：{category}
- 专业偏好：{', '.join(preferences) if preferences else '无特殊偏好'}

## 推荐策略
请严格按照以下比例和标准生成推荐：

### 1. 冲刺志愿（{rush_count}个）
- 目标：冲击名校，允许一定风险
- 录取概率要求：{int(self.params.rush_prob_threshold*100)}%以下
- 选择原则：学校排名优先，专业可适当妥协

### 2. 稳妥志愿（{target_count}个）
- 目标：平衡质量与安全性
- 录取概率要求：{int(self.params.target_prob_min*100)}%-{int(self.params.target_prob_max*100)}%
- 选择原则：学校与专业并重

### 3. 保底志愿（{safe_count}个）
- 目标：确保录取，避免滑档
- 录取概率要求：{int(self.params.safe_prob_threshold*100)}%以上
- 选择原则：录取概率优先

## 重要考虑因素
- 风险偏好：{'激进（偏向冲击名校）' if self.params.risk_tolerance > 0.6 else '保守（偏向安全录取）' if self.params.risk_tolerance < 0.4 else '平衡'}
- 学校多样性：{'高度重视（避免过度集中）' if self.params.diversity_weight > 0.5 else '适度考虑'}
- 学校声望：{'重点考虑（优先985/211）' if self.params.prestige_weight > 0.6 else '均衡考虑'}
"""

        # 添加历史成功案例（In-Context Learning）
        if historical_context:
            prompt += f"\n## 参考案例\n{historical_context}\n"

        # 输出格式要求
        prompt += """
## 输出格式
请以JSON格式输出，每个志愿包含以下字段：
```json
[
  {
    "volunteer_index": 1,
    "school_name": "学校名称",
    "major_name": "专业名称",
    "strategy_tag": "rush/target/safe",
    "predicted_prob": 0.45,
    "reasoning": "简短理由"
  },
  ...
]
```

现在请开始生成45个志愿推荐。
"""

        return prompt

    def update_params(
        self,
        reward: float,
        learning_rate: float = 0.01,
        method: str = "gradient_ascent"
    ):
        """
        更新参数（基于reward）

        Args:
            reward: 当前episode的奖励
            learning_rate: 学习率
            method: 更新方法（gradient_ascent/random_search）
        """
        # 记录历史
        self.training_history.append({
            'params': self.params.dict(),
            'reward': reward
        })

        # 更新最佳参数
        if reward > self.best_reward:
            self.best_reward = reward
            self.best_params = self.params.copy()
            print(f"[RL] 发现更好参数！Reward: {reward:.3f}")

        if method == "gradient_ascent":
            # 梯度上升（简化版）
            # 根据reward正负，调整参数
            if reward > 0:
                # 正奖励：强化当前策略
                # 增加效果好的部分
                pass  # 保持当前参数
            else:
                # 负奖励：探索新策略
                self._explore_params(learning_rate)

        elif method == "random_search":
            # 随机搜索
            self._explore_params(learning_rate * 2)

    def _explore_params(self, epsilon: float):
        """探索新参数（加入随机扰动）"""
        # 扰动冲稳保比例
        noise = np.random.randn(3) * epsilon
        self.params.rush_ratio = np.clip(self.params.rush_ratio + noise[0], 0.15, 0.5)
        self.params.target_ratio = np.clip(self.params.target_ratio + noise[1], 0.20, 0.5)
        self.params.safe_ratio = 1.0 - self.params.rush_ratio - self.params.target_ratio
        self.params.safe_ratio = np.clip(self.params.safe_ratio, 0.20, 0.5)

        # 归一化
        self.params.normalize_ratios()

        # 扰动其他参数
        self.params.risk_tolerance = np.clip(
            self.params.risk_tolerance + np.random.randn() * epsilon,
            0.0, 1.0
        )
        self.params.diversity_weight = np.clip(
            self.params.diversity_weight + np.random.randn() * epsilon,
            0.0, 1.0
        )

    def save(self, filepath: str):
        """保存学习到的参数"""
        save_data = {
            'params': self.params.dict(),
            'best_params': self.best_params.dict() if self.best_params else None,
            'best_reward': self.best_reward,
            'training_history': self.training_history
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        print(f"[Save] 参数已保存到 {filepath}")

    def load(self, filepath: str):
        """加载已学习的参数"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.params = PromptParameters(**data['params'])
        if data.get('best_params'):
            self.best_params = PromptParameters(**data['best_params'])
        self.best_reward = data.get('best_reward', float('-inf'))
        self.training_history = data.get('training_history', [])

        print(f"[Load] 参数已从 {filepath} 加载")
        print(f"  最佳Reward: {self.best_reward:.3f}")


# ============================================
# 测试代码
# ============================================

if __name__ == "__main__":
    print("=== 可学习Prompt测试 ===\n")

    # 创建learnable prompt
    learnable_prompt = LearnablePrompt()

    print("初始参数:")
    print(f"  冲刺比例: {learnable_prompt.params.rush_ratio:.2f}")
    print(f"  稳妥比例: {learnable_prompt.params.target_ratio:.2f}")
    print(f"  保底比例: {learnable_prompt.params.safe_ratio:.2f}")
    print(f"  风险偏好: {learnable_prompt.params.risk_tolerance:.2f}")
    print()

    # 生成prompt
    test_prompt = learnable_prompt.generate_prompt(
        user_rank=10000,
        category="physics",
        preferences=["计算机", "软件工程"]
    )

    print("生成的Prompt（前500字符）:")
    print(test_prompt[:500])
    print("...\n")

    # 模拟训练
    print("模拟RL训练:")
    for episode in range(5):
        # 模拟reward
        reward = np.random.randn() * 0.5

        # 更新参数
        learnable_prompt.update_params(reward, learning_rate=0.05)

        print(f"  Episode {episode+1}: Reward={reward:.3f}, "
              f"冲{learnable_prompt.params.rush_ratio:.2f}/"
              f"稳{learnable_prompt.params.target_ratio:.2f}/"
              f"保{learnable_prompt.params.safe_ratio:.2f}")

    print(f"\n最佳Reward: {learnable_prompt.best_reward:.3f}")

    # 保存参数
    learnable_prompt.save("learned_prompt_params.json")

    print("\n测试完成！")

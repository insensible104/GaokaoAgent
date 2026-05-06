"""强化学习学校选择环境

真正的RL推荐系统：
- State: 用户画像 + 候选池特征
- Action: 从候选池中选择学校
- Reward: 基于回测的录取结果
- Policy: 策略网络输出选择概率

核心改进：
1. RL直接选择学校，而非仅调整比例参数
2. 学习"哪些学校组合"效果好
3. 考虑学校间的协同效应
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field
import torch
import torch.nn as nn


# ============================================
# 学校特征编码
# ============================================

class SchoolFeatures(BaseModel):
    """学校特征向量"""
    school_name: str
    major_group: str

    # 核心特征
    min_rank_hist: float          # 历史最低位次（归一化）
    admission_prob: float         # 预测录取概率 (0-1)
    rank_volatility: float        # 位次波动度 (0-1)
    quota: int                    # 招生人数

    # 匹配特征
    major_match_score: float      # 专业匹配度 (0-1)
    school_tier: int              # 学校档次 (1=985, 2=211, 3=双一流, 4=普通)
    location_score: float         # 地域匹配度 (0-1)

    # 质量特征
    employment_rate: float        # 就业率 (0-1)
    avg_salary: float             # 平均薪资（归一化）
    postgrad_rate: float          # 深造率 (0-1)

    # 策略特征
    strategy_tag: int             # 冲/稳/保 (0/1/2)

    def to_vector(self) -> np.ndarray:
        """转换为特征向量 (10维)"""
        return np.array([
            self.min_rank_hist,
            self.admission_prob,
            self.rank_volatility,
            self.quota / 100.0,           # 归一化
            self.major_match_score,
            (4 - self.school_tier) / 3.0, # 归一化
            self.location_score,
            self.employment_rate,
            self.avg_salary,
            self.postgrad_rate
        ], dtype=np.float32)


class UserContext(BaseModel):
    """用户上下文特征"""
    user_rank: int
    rank_normalized: float        # 位次归一化 (0-1)
    category: str                 # 物理/历史

    # 偏好
    risk_tolerance: float         # 风险偏好 (0-1)
    school_priority: float        # 学校优先度 (0-1)
    major_priority: float         # 专业优先度 (0-1)
    location_preference: List[str] = []
    major_preferences: List[str] = []

    def to_vector(self) -> np.ndarray:
        """转换为特征向量 (5维)"""
        return np.array([
            self.rank_normalized,
            self.risk_tolerance,
            self.school_priority,
            self.major_priority,
            1.0 if self.category == "physics" else 0.0
        ], dtype=np.float32)


# ============================================
# RL环境：学校选择
# ============================================

class SchoolSelectionState(BaseModel):
    """RL状态"""
    user_context: UserContext
    candidate_pool: List[SchoolFeatures]      # 200个候选
    selected_schools: List[int] = []          # 已选学校的索引
    step: int = 0

    class Config:
        arbitrary_types_allowed = True


class SchoolSelectionAction(BaseModel):
    """RL动作：选择一个学校"""
    school_index: int = Field(description="选择的学校索引 (0-199)")
    confidence: float = Field(default=1.0, description="选择置信度")


class SchoolSelectionReward(BaseModel):
    """奖励组件"""
    # 核心奖励
    admission_reward: float = Field(description="录取奖励 (0/1)")
    rank_utilization: float = Field(description="位次利用率 (0-1)")

    # 额外奖励
    admitted_rank_bonus: float = Field(description="录取志愿序号奖励")
    strategy_balance: float = Field(description="策略平衡奖励")
    diversity_bonus: float = Field(description="学校多样性奖励")
    preference_match: float = Field(description="偏好匹配奖励")

    # 惩罚
    slip_penalty: float = Field(description="滑档惩罚")
    redundancy_penalty: float = Field(description="冗余惩罚")

    total: float = Field(description="总奖励")

    @staticmethod
    def calculate(
        admitted: bool,
        admitted_index: Optional[int],
        selected_schools: List[SchoolFeatures],
        user_context: UserContext,
        user_rank: int
    ) -> 'SchoolSelectionReward':
        """计算奖励"""

        # 1. 录取奖励 (权重40%)
        if admitted:
            admission_reward = 1.0
            # 录取到靠前志愿额外奖励
            admitted_rank_bonus = (45 - admitted_index) / 45.0 if admitted_index else 0.0
        else:
            admission_reward = 0.0
            admitted_rank_bonus = 0.0

        # 2. 位次利用率 (权重30%)
        if admitted and selected_schools:
            admitted_school = selected_schools[admitted_index - 1]
            rank_diff = abs(user_rank - admitted_school.min_rank_hist)
            rank_utilization = max(0, 1.0 - rank_diff / 5000.0)  # 5000位次内为满分
        else:
            rank_utilization = 0.0

        # 3. 策略平衡 (权重10%)
        if selected_schools:
            rush_count = sum(1 for s in selected_schools if s.strategy_tag == 0)
            target_count = sum(1 for s in selected_schools if s.strategy_tag == 1)
            safe_count = sum(1 for s in selected_schools if s.strategy_tag == 2)

            # 理想比例: 25%冲 / 40%稳 / 35%保
            ideal_rush = 11
            ideal_target = 18
            ideal_safe = 16

            balance_score = 1.0 - (
                abs(rush_count - ideal_rush) / 11 +
                abs(target_count - ideal_target) / 18 +
                abs(safe_count - ideal_safe) / 16
            ) / 3
            strategy_balance = max(0, balance_score)
        else:
            strategy_balance = 0.0

        # 4. 学校多样性 (权重10%)
        if selected_schools:
            unique_schools = len(set(s.school_name for s in selected_schools))
            diversity_bonus = unique_schools / len(selected_schools)
        else:
            diversity_bonus = 0.0

        # 5. 偏好匹配 (权重10%)
        if selected_schools:
            match_scores = [s.major_match_score for s in selected_schools]
            preference_match = np.mean(match_scores)
        else:
            preference_match = 0.0

        # 惩罚项
        slip_penalty = -2.0 if not admitted else 0.0  # 滑档严重惩罚

        # 冗余惩罚（选了太多同一学校）
        if selected_schools:
            school_counts = {}
            for s in selected_schools:
                school_counts[s.school_name] = school_counts.get(s.school_name, 0) + 1
            max_redundancy = max(school_counts.values())
            redundancy_penalty = -0.1 * (max_redundancy - 1) if max_redundancy > 3 else 0.0
        else:
            redundancy_penalty = 0.0

        # 总奖励（加权求和）
        total = (
            0.40 * admission_reward +
            0.30 * rank_utilization +
            0.10 * strategy_balance +
            0.10 * diversity_bonus +
            0.10 * preference_match +
            0.05 * admitted_rank_bonus +
            slip_penalty +
            redundancy_penalty
        )

        return SchoolSelectionReward(
            admission_reward=admission_reward,
            rank_utilization=rank_utilization,
            admitted_rank_bonus=admitted_rank_bonus,
            strategy_balance=strategy_balance,
            diversity_bonus=diversity_bonus,
            preference_match=preference_match,
            slip_penalty=slip_penalty,
            redundancy_penalty=redundancy_penalty,
            total=total
        )


class SchoolSelectionEnv:
    """
    学校选择RL环境

    工作流程：
    1. reset(): 初始化候选池（200个学校）
    2. step(action): 从候选池选择一个学校
    3. 重复45次，选出45个学校
    4. 使用历史数据回测，计算reward
    """

    def __init__(self, historical_data: Dict[int, pd.DataFrame]):
        """
        Args:
            historical_data: {year: DataFrame} 历史录取数据
        """
        self.historical_data = historical_data
        self.state: Optional[SchoolSelectionState] = None

    def reset(
        self,
        user_context: UserContext,
        candidate_pool: List[SchoolFeatures]
    ) -> SchoolSelectionState:
        """
        重置环境

        Args:
            user_context: 用户上下文
            candidate_pool: 候选学校池 (200个)

        Returns:
            初始状态
        """
        self.state = SchoolSelectionState(
            user_context=user_context,
            candidate_pool=candidate_pool,
            selected_schools=[],
            step=0
        )
        return self.state

    def step(
        self,
        action: SchoolSelectionAction
    ) -> Tuple[SchoolSelectionState, float, bool, Dict]:
        """
        执行动作：选择一个学校

        Args:
            action: 选择的学校索引

        Returns:
            (next_state, reward, done, info)
        """
        if self.state is None:
            raise ValueError("环境未初始化，请先调用reset()")

        # 执行动作：将学校加入选择列表
        school_idx = action.school_index

        if school_idx in self.state.selected_schools:
            # 重复选择，给予惩罚
            reward = -0.5
            done = False
            info = {'error': 'duplicate_selection'}
            return self.state, reward, done, info

        self.state.selected_schools.append(school_idx)
        self.state.step += 1

        # 判断是否完成（选够45个）
        done = len(self.state.selected_schools) >= 45

        if done:
            # 完成选择，计算最终奖励
            reward, info = self._evaluate_selection()
        else:
            # 未完成，给予中间奖励
            reward = 0.0
            info = {}

        return self.state, reward, done, info

    def _evaluate_selection(self) -> Tuple[float, Dict]:
        """
        评估选择结果（使用历史数据回测）

        Returns:
            (reward, info)
        """
        selected_indices = self.state.selected_schools
        selected_schools = [
            self.state.candidate_pool[i]
            for i in selected_indices
        ]

        # 使用历史数据回测
        year = 2024  # 默认测试年份
        user_rank = self.state.user_context.user_rank

        # 模拟录取（按志愿顺序检查）
        admitted = False
        admitted_index = None
        admitted_school = None

        for idx, school in enumerate(selected_schools, 1):
            # 检查是否被录取（用户位次 <= 历史最低位次）
            if user_rank <= school.min_rank_hist:
                admitted = True
                admitted_index = idx
                admitted_school = school
                break

        # 计算奖励
        reward_obj = SchoolSelectionReward.calculate(
            admitted=admitted,
            admitted_index=admitted_index,
            selected_schools=selected_schools,
            user_context=self.state.user_context,
            user_rank=user_rank
        )

        info = {
            'admitted': admitted,
            'admitted_index': admitted_index,
            'admitted_school': admitted_school.school_name if admitted_school else None,
            'reward_breakdown': reward_obj.dict(),
            'selected_schools': [s.school_name for s in selected_schools]
        }

        return reward_obj.total, info


# ============================================
# 策略网络
# ============================================

class PolicyNetwork(nn.Module):
    """
    策略网络：输出每个候选学校的选择概率

    架构：
    - 输入：用户特征(5) + 学校特征(10) = 15维
    - 隐藏层：128 -> 64 -> 32
    - 输出：1维（该学校的logit）
    """

    def __init__(self, user_dim=5, school_dim=10, hidden_dims=[128, 64, 32]):
        super().__init__()

        self.user_dim = user_dim
        self.school_dim = school_dim

        # 用户编码器
        self.user_encoder = nn.Sequential(
            nn.Linear(user_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 32)
        )

        # 学校编码器
        self.school_encoder = nn.Sequential(
            nn.Linear(school_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32)
        )

        # 融合层
        self.fusion = nn.Sequential(
            nn.Linear(64, hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dims[0], hidden_dims[1]),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dims[1], hidden_dims[2]),
            nn.ReLU(),
            nn.Linear(hidden_dims[2], 1)  # 输出logit
        )

    def forward(
        self,
        user_features: torch.Tensor,    # [batch, user_dim]
        school_features: torch.Tensor   # [batch, n_schools, school_dim]
    ) -> torch.Tensor:
        """
        前向传播

        Args:
            user_features: 用户特征 [batch, 5]
            school_features: 候选学校特征 [batch, 200, 10]

        Returns:
            logits: 每个学校的选择logit [batch, 200]
        """
        batch_size = user_features.shape[0]
        n_schools = school_features.shape[1]

        # 编码用户特征
        user_embed = self.user_encoder(user_features)  # [batch, 32]

        # 扩展用户特征到每个学校
        user_embed = user_embed.unsqueeze(1).expand(-1, n_schools, -1)  # [batch, 200, 32]

        # 编码学校特征
        school_embed = self.school_encoder(
            school_features.view(-1, self.school_dim)
        )  # [batch*200, 32]
        school_embed = school_embed.view(batch_size, n_schools, -1)  # [batch, 200, 32]

        # 融合
        combined = torch.cat([user_embed, school_embed], dim=-1)  # [batch, 200, 64]
        logits = self.fusion(combined.view(-1, 64))  # [batch*200, 1]
        logits = logits.view(batch_size, n_schools)  # [batch, 200]

        return logits

    def select_schools(
        self,
        user_features: np.ndarray,
        school_features: np.ndarray,
        n_select: int = 45,
        temperature: float = 1.0,
        epsilon: float = 0.1
    ) -> List[int]:
        """
        选择学校（推理阶段）

        Args:
            user_features: 用户特征 [5]
            school_features: 候选学校特征 [200, 10]
            n_select: 选择数量
            temperature: 温度参数（控制随机性）
            epsilon: 探索率

        Returns:
            选择的学校索引列表 [45]
        """
        self.eval()
        with torch.no_grad():
            # 转换为tensor
            user_tensor = torch.FloatTensor(user_features).unsqueeze(0)  # [1, 5]
            school_tensor = torch.FloatTensor(school_features).unsqueeze(0)  # [1, 200, 10]

            # 前向传播
            logits = self.forward(user_tensor, school_tensor)  # [1, 200]
            logits = logits.squeeze(0)  # [200]

            # 温度采样
            probs = torch.softmax(logits / temperature, dim=0)  # [200]
            probs = probs.numpy()

            # ε-greedy探索
            if np.random.rand() < epsilon:
                # 随机选择
                selected = np.random.choice(len(probs), size=n_select, replace=False)
            else:
                # 根据概率采样（无放回）
                selected = []
                remaining = list(range(len(probs)))
                remaining_probs = probs.copy()

                for _ in range(n_select):
                    # 归一化剩余概率
                    remaining_probs_norm = remaining_probs / remaining_probs.sum()

                    # 采样
                    idx = np.random.choice(len(remaining), p=remaining_probs_norm)
                    selected.append(remaining[idx])

                    # 移除已选
                    remaining.pop(idx)
                    remaining_probs = np.delete(remaining_probs, idx)

            return selected


# ============================================
# 测试代码
# ============================================

if __name__ == "__main__":
    print("=== 学校选择RL环境测试 ===\n")

    # 创建测试数据
    print("1. 创建用户上下文...")
    user_context = UserContext(
        user_rank=10000,
        rank_normalized=10000 / 100000,
        category="physics",
        risk_tolerance=0.5,
        school_priority=0.6,
        major_priority=0.4,
        major_preferences=["计算机", "软件工程"]
    )
    print(f"   用户位次: {user_context.user_rank}")
    print(f"   风险偏好: {user_context.risk_tolerance}")

    # 创建候选池（模拟）
    print("\n2. 创建候选池...")
    candidate_pool = []
    for i in range(200):
        school = SchoolFeatures(
            school_name=f"大学{i+1}",
            major_group="计算机类",
            min_rank_hist=8000 + i * 100,
            admission_prob=0.3 + (i / 200) * 0.6,
            rank_volatility=0.1 + np.random.rand() * 0.3,
            quota=30 + i,
            major_match_score=0.5 + np.random.rand() * 0.5,
            school_tier=1 + (i // 50),
            location_score=0.5 + np.random.rand() * 0.5,
            employment_rate=0.8 + np.random.rand() * 0.2,
            avg_salary=0.6 + np.random.rand() * 0.4,
            postgrad_rate=0.2 + np.random.rand() * 0.3,
            strategy_tag=0 if i < 66 else (1 if i < 132 else 2)
        )
        candidate_pool.append(school)
    print(f"   候选池大小: {len(candidate_pool)}")

    # 创建环境
    print("\n3. 创建RL环境...")
    env = SchoolSelectionEnv(historical_data={})
    state = env.reset(user_context, candidate_pool)
    print("   环境初始化完成")

    # 测试策略网络
    print("\n4. 测试策略网络...")
    policy = PolicyNetwork()
    print(f"   网络参数量: {sum(p.numel() for p in policy.parameters()):,}")

    # 提取特征
    user_vec = user_context.to_vector()
    school_vecs = np.array([s.to_vector() for s in candidate_pool])

    print(f"   用户特征维度: {user_vec.shape}")
    print(f"   学校特征维度: {school_vecs.shape}")

    # 选择学校
    selected_indices = policy.select_schools(
        user_vec, school_vecs, n_select=45, temperature=1.0
    )
    print(f"   选择了 {len(selected_indices)} 个学校")
    print(f"   前5个: {selected_indices[:5]}")

    # 测试环境step
    print("\n5. 测试环境交互...")
    for i, idx in enumerate(selected_indices[:5], 1):
        action = SchoolSelectionAction(school_index=idx)
        state, reward, done, info = env.step(action)
        print(f"   Step {i}: 选择学校{idx}, reward={reward:.3f}, done={done}")

    print("\n测试完成！")
    print("\n下一步:")
    print("  1. 实现训练器 (school_selector_trainer.py)")
    print("  2. 集成到Game Agent")
    print("  3. 使用真实历史数据训练")

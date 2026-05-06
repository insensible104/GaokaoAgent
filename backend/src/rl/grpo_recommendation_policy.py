"""GRPO推荐策略网络

使用Group Relative Policy Optimization训练推荐策略，
生成高质量的志愿推荐候选池

核心思想：
1. 策略网络学习从候选池中选择N个推荐
2. GRPO通过相对比较学习（不需要绝对的reward）
3. 在一组推荐方案中，选择最好的作为正样本
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field


class UserFeatures(BaseModel):
    """用户特征（输入）"""
    rank: int = Field(description="用户位次")
    rank_normalized: float = Field(description="归一化位次 (0-1)")
    risk_tolerance: float = Field(ge=0.0, le=1.0, description="风险偏好 (0=保守, 1=激进)")
    major_priority: float = Field(ge=0.0, le=1.0, description="专业优先度 (0=学校优先, 1=专业优先)")

    def to_vector(self) -> np.ndarray:
        """转换为向量"""
        return np.array([
            self.rank_normalized,
            self.risk_tolerance,
            self.major_priority
        ], dtype=np.float32)


class CandidateFeatures(BaseModel):
    """候选专业组特征（每个候选的特征向量）"""
    school_tier: int = Field(ge=1, le=5, description="学校层次 (1=985, 5=民办)")
    admission_prob: float = Field(ge=0.0, le=1.0, description="录取概率")
    major_satisfaction: float = Field(ge=0.0, le=1.0, description="专业满意度")
    adjustment_risk: float = Field(ge=0.0, le=1.0, description="调剂风险")
    rank_diff_normalized: float = Field(description="位次差（归一化）")
    comprehensive_score: float = Field(ge=0.0, le=1.0, description="综合评分")

    def to_vector(self) -> np.ndarray:
        """转换为向量"""
        return np.array([
            (6 - self.school_tier) / 5.0,  # 转换为越大越好
            self.admission_prob,
            self.major_satisfaction,
            1 - self.adjustment_risk,  # 转换为越大越好
            self.rank_diff_normalized,
            self.comprehensive_score
        ], dtype=np.float32)


class GRPOPolicyNetwork(nn.Module):
    """
    GRPO策略网络

    输入：用户特征 (3维) + 候选池特征 (N×6维)
    输出：每个候选被选中的logits (N维)

    架构：
    1. User Encoder：编码用户特征
    2. Candidate Encoder：编码每个候选特征
    3. Attention：用户特征attend到候选特征
    4. Output：输出选择logits
    """

    def __init__(
        self,
        user_dim: int = 3,
        candidate_dim: int = 6,
        hidden_dim: int = 128,
        num_heads: int = 4
    ):
        super().__init__()

        self.user_dim = user_dim
        self.candidate_dim = candidate_dim
        self.hidden_dim = hidden_dim

        # User Encoder
        self.user_encoder = nn.Sequential(
            nn.Linear(user_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )

        # Candidate Encoder
        self.candidate_encoder = nn.Sequential(
            nn.Linear(candidate_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )

        # Multi-head Attention
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=num_heads,
            batch_first=True
        )

        # Output Layer
        self.output = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)  # 输出单个logit
        )

    def forward(
        self,
        user_features: torch.Tensor,  # [batch_size, user_dim]
        candidate_features: torch.Tensor  # [batch_size, n_candidates, candidate_dim]
    ) -> torch.Tensor:
        """
        前向传播

        Args:
            user_features: 用户特征 [batch_size, 3]
            candidate_features: 候选特征 [batch_size, n_candidates, 6]

        Returns:
            logits [batch_size, n_candidates]
        """
        batch_size = user_features.shape[0]
        n_candidates = candidate_features.shape[1]

        # 编码用户特征
        user_embed = self.user_encoder(user_features)  # [batch, hidden]
        user_embed = user_embed.unsqueeze(1)  # [batch, 1, hidden]

        # 编码候选特征
        candidate_embed = self.candidate_encoder(
            candidate_features.view(-1, self.candidate_dim)
        )  # [batch * n_candidates, hidden]
        candidate_embed = candidate_embed.view(
            batch_size, n_candidates, self.hidden_dim
        )  # [batch, n_candidates, hidden]

        # Attention：用户特征作为query，候选特征作为key/value
        attn_output, _ = self.attention(
            query=user_embed.expand(-1, n_candidates, -1),  # [batch, n_candidates, hidden]
            key=candidate_embed,
            value=candidate_embed
        )  # [batch, n_candidates, hidden]

        # 输出logits
        logits = self.output(attn_output).squeeze(-1)  # [batch, n_candidates]

        return logits

    def select_top_k(
        self,
        user_features: torch.Tensor,
        candidate_features: torch.Tensor,
        k: int,
        temperature: float = 1.0,
        deterministic: bool = False
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        从候选中选择top-k个

        Args:
            user_features: 用户特征 [batch, 3]
            candidate_features: 候选特征 [batch, n_candidates, 6]
            k: 选择数量
            temperature: 温度参数（越大越随机）
            deterministic: 是否确定性选择（True=选择概率最高的k个）

        Returns:
            selected_indices: 选中的索引 [batch, k]
            log_probs: 对应的log概率 [batch, k]
        """
        logits = self.forward(user_features, candidate_features)  # [batch, n_candidates]
        logits = logits / temperature

        if deterministic:
            # 确定性：选择概率最高的k个
            selected_indices = torch.topk(logits, k, dim=1).indices
            probs = F.softmax(logits, dim=1)
            log_probs = torch.log(probs.gather(1, selected_indices) + 1e-8)
        else:
            # 随机：根据概率采样k个（不放回）
            probs = F.softmax(logits, dim=1)

            # 使用Gumbel-Top-k采样
            batch_size = logits.shape[0]
            selected_indices = []
            log_probs_list = []

            for b in range(batch_size):
                # 对每个batch单独采样
                batch_probs = probs[b]

                # 采样k个（不放回）
                sampled = torch.multinomial(batch_probs, k, replacement=False)
                selected_indices.append(sampled)

                # 计算log概率
                sampled_log_probs = torch.log(batch_probs[sampled] + 1e-8)
                log_probs_list.append(sampled_log_probs)

            selected_indices = torch.stack(selected_indices)
            log_probs = torch.stack(log_probs_list)

        return selected_indices, log_probs


class GRPORecommendation:
    """GRPO推荐结果"""

    def __init__(
        self,
        selected_indices: List[int],
        selected_candidates: List[Dict],
        log_probs: List[float],
        total_log_prob: float
    ):
        self.selected_indices = selected_indices
        self.selected_candidates = selected_candidates
        self.log_probs = log_probs
        self.total_log_prob = total_log_prob


class GRPORecommendationPolicy:
    """
    GRPO推荐策略（推理接口）

    用于生成推荐（从训练好的策略网络）
    """

    def __init__(self, model_path: Optional[str] = None, device: str = 'cpu'):
        """
        Args:
            model_path: 模型权重路径
            device: 计算设备
        """
        self.device = device
        self.policy = GRPOPolicyNetwork().to(device)

        if model_path:
            self.load(model_path)

        self.policy.eval()

    def generate_recommendations(
        self,
        user_features: UserFeatures,
        candidate_pool: List[CandidateFeatures],
        n_recommendations: int = 30,
        temperature: float = 1.0,
        deterministic: bool = False
    ) -> GRPORecommendation:
        """
        生成推荐

        Args:
            user_features: 用户特征
            candidate_pool: 候选池
            n_recommendations: 推荐数量
            temperature: 温度参数
            deterministic: 是否确定性选择

        Returns:
            GRPORecommendation对象
        """
        # 转换为tensor
        user_vec = torch.FloatTensor(user_features.to_vector()).unsqueeze(0).to(self.device)

        candidate_vecs = torch.FloatTensor(
            np.array([c.to_vector() for c in candidate_pool])
        ).unsqueeze(0).to(self.device)

        # 选择top-k
        with torch.no_grad():
            selected_indices, log_probs = self.policy.select_top_k(
                user_vec,
                candidate_vecs,
                k=n_recommendations,
                temperature=temperature,
                deterministic=deterministic
            )

        selected_indices = selected_indices[0].cpu().numpy().tolist()
        log_probs = log_probs[0].cpu().numpy().tolist()

        # 提取选中的候选
        selected_candidates = [candidate_pool[i] for i in selected_indices]

        return GRPORecommendation(
            selected_indices=selected_indices,
            selected_candidates=selected_candidates,
            log_probs=log_probs,
            total_log_prob=sum(log_probs)
        )

    def save(self, path: str):
        """保存模型"""
        torch.save(self.policy.state_dict(), path)
        print(f"[Save] 模型已保存: {path}")

    def load(self, path: str):
        """加载模型"""
        self.policy.load_state_dict(torch.load(path, map_location=self.device))
        print(f"[Load] 模型已加载: {path}")


# === 测试代码 ===
if __name__ == "__main__":
    print("=== GRPO策略网络测试 ===\n")

    # 创建模拟数据
    user = UserFeatures(
        rank=12000,
        rank_normalized=0.12,
        risk_tolerance=0.6,
        major_priority=0.8
    )

    # 模拟候选池（100个候选）
    candidates = []
    for i in range(100):
        candidates.append(CandidateFeatures(
            school_tier=min(5, 1 + i // 20),
            admission_prob=0.95 - i * 0.005,
            major_satisfaction=0.5 + np.random.rand() * 0.5,
            adjustment_risk=0.1 + np.random.rand() * 0.3,
            rank_diff_normalized=i / 100.0,
            comprehensive_score=0.9 - i * 0.008
        ))

    # 创建策略
    policy = GRPORecommendationPolicy(device='cpu')

    # 生成推荐
    print("生成30个推荐...")
    recommendation = policy.generate_recommendations(
        user_features=user,
        candidate_pool=candidates,
        n_recommendations=30,
        temperature=1.0,
        deterministic=False
    )

    print(f"\n选中的索引: {recommendation.selected_indices[:10]}...")
    print(f"总log概率: {recommendation.total_log_prob:.4f}")

    print("\n前5个推荐:")
    for i, (idx, candidate) in enumerate(zip(
        recommendation.selected_indices[:5],
        recommendation.selected_candidates[:5]
    ), 1):
        print(f"{i}. 候选#{idx}")
        print(f"   学校层次: {candidate.school_tier}")
        print(f"   录取概率: {candidate.admission_prob:.2%}")
        print(f"   专业满意度: {candidate.major_satisfaction:.2%}")

    print("\n测试完成！")

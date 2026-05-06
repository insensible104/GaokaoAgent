"""排位梯度分层策略

根据考生排位，动态确定候选池大小和搜索范围

核心思想：
- 高分考生（前5000）：学校选择少（50个），但都是名校，竞争激烈
- 中分考生（20000）：学校选择多（200个），需要精细化匹配
- 低分考生（80000+）：学校选择广（300个），但层次分散
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class RankGradientConfig:
    """排位梯度配置"""
    rank_range: Tuple[int, int]  # 排位范围 (min, max)
    candidate_pool_size: int     # 候选池大小
    rush_range: Tuple[int, int]  # 冲刺位次范围（相对用户位次的偏移）
    target_range: Tuple[int, int]  # 稳妥位次范围
    safe_range: Tuple[int, int]    # 保底位次范围
    description: str             # 描述

    # 推荐配置
    recommend_count: int         # 推荐数量
    rush_ratio: float           # 冲刺比例
    target_ratio: float         # 稳妥比例
    safe_ratio: float           # 保底比例


class RankGradientStrategy:
    """
    排位梯度策略

    根据考生排位，自动配置候选池大小和搜索策略
    """

    def __init__(self):
        """
        定义不同排位梯度的策略配置
        """
        self.configs = [
            # ===== 顶尖层（前5000）=====
            RankGradientConfig(
                rank_range=(1, 5000),
                candidate_pool_size=50,
                rush_range=(-3000, -1000),    # 冲刺：往前1000-3000名
                target_range=(-1000, 1000),   # 稳妥：上下1000名
                safe_range=(1000, 3000),      # 保底：往后1000-3000名
                description="顶尖层：主要竞争C9+华五+顶尖985",
                recommend_count=20,
                rush_ratio=0.30,
                target_ratio=0.50,
                safe_ratio=0.20
            ),

            # ===== 优秀层（5000-15000）=====
            RankGradientConfig(
                rank_range=(5000, 15000),
                candidate_pool_size=2000,  # 修复：从80增加到2000，确保能捕获全部搜索范围的学校（40000-50000）
                rush_range=(-5000, -2000),
                target_range=(-2000, 2000),
                safe_range=(2000, 10000),  # 修复：从5000扩大到10000，确保能找到保底院校
                description="优秀层：985/211 + 重点一本",
                recommend_count=30,
                rush_ratio=0.30,
                target_ratio=0.50,
                safe_ratio=0.20
            ),

            # ===== 良好层（15000-30000）=====
            RankGradientConfig(
                rank_range=(15000, 30000),
                candidate_pool_size=150,
                rush_range=(-8000, -3000),
                target_range=(-3000, 3000),
                safe_range=(3000, 8000),
                description="良好层：211 + 重点一本 + 省重点",
                recommend_count=35,
                rush_ratio=0.25,
                target_ratio=0.50,
                safe_ratio=0.25
            ),

            # ===== 中等层（30000-60000）=====
            RankGradientConfig(
                rank_range=(30000, 60000),
                candidate_pool_size=200,
                rush_range=(-10000, -4000),
                target_range=(-4000, 4000),
                safe_range=(4000, 10000),
                description="中等层：一本为主 + 好的二本",
                recommend_count=40,
                rush_ratio=0.25,
                target_ratio=0.50,
                safe_ratio=0.25
            ),

            # ===== 普通层（60000-100000）=====
            RankGradientConfig(
                rank_range=(60000, 100000),
                candidate_pool_size=250,
                rush_range=(-15000, -5000),
                target_range=(-5000, 5000),
                safe_range=(5000, 15000),
                description="普通层：一本二本混合",
                recommend_count=45,
                rush_ratio=0.20,
                target_ratio=0.50,
                safe_ratio=0.30
            ),

            # ===== 基础层（100000+）=====
            RankGradientConfig(
                rank_range=(100000, 300000),
                candidate_pool_size=300,
                rush_range=(-20000, -8000),
                target_range=(-8000, 8000),
                safe_range=(8000, 25000),
                description="基础层：二本为主 + 专科",
                recommend_count=50,
                rush_ratio=0.20,
                target_ratio=0.45,
                safe_ratio=0.35
            )
        ]

    def get_config(self, user_rank: int) -> RankGradientConfig:
        """
        根据用户排位获取对应的策略配置

        Args:
            user_rank: 用户排位 (e.g., 12000)

        Returns:
            对应的策略配置
        """
        for config in self.configs:
            if config.rank_range[0] <= user_rank < config.rank_range[1]:
                return config

        # 默认返回最后一个（兜底）
        return self.configs[-1]

    def calculate_search_range(
        self,
        user_rank: int
    ) -> Dict[str, Tuple[int, int]]:
        """
        计算搜索范围

        Args:
            user_rank: 用户排位

        Returns:
            {
                "rush": (8000, 10000),    # 冲刺区间：位次8000-10000
                "target": (10000, 14000), # 稳妥区间：位次10000-14000
                "safe": (14000, 17000)    # 保底区间：位次14000-17000
            }
        """
        config = self.get_config(user_rank)

        rush_min = max(1, user_rank + config.rush_range[0])
        rush_max = max(1, user_rank + config.rush_range[1])

        target_min = max(1, user_rank + config.target_range[0])
        target_max = user_rank + config.target_range[1]

        safe_min = user_rank + config.safe_range[0]
        safe_max = user_rank + config.safe_range[1]

        return {
            "rush": (rush_min, rush_max),
            "target": (target_min, target_max),
            "safe": (safe_min, safe_max)
        }

    def get_recommended_volunteer_count(
        self,
        user_rank: int,
        user_preference: str = "balanced"
    ) -> Dict[str, int]:
        """
        获取推荐的志愿数量配置

        Args:
            user_rank: 用户排位
            user_preference: 用户偏好类型
                - "aggressive": 激进型（多冲刺）
                - "balanced": 平衡型（默认）
                - "conservative": 保守型（多保底）

        Returns:
            {
                "total": 30,     # 总推荐数
                "rush": 9,       # 冲刺数量
                "target": 15,    # 稳妥数量
                "safe": 6        # 保底数量
            }
        """
        config = self.get_config(user_rank)
        total = config.recommend_count

        # 根据用户偏好调整比例
        if user_preference == "aggressive":
            rush_ratio = min(0.40, config.rush_ratio + 0.10)
            safe_ratio = max(0.10, config.safe_ratio - 0.10)
            target_ratio = 1 - rush_ratio - safe_ratio
        elif user_preference == "conservative":
            rush_ratio = max(0.15, config.rush_ratio - 0.10)
            safe_ratio = min(0.45, config.safe_ratio + 0.15)
            target_ratio = 1 - rush_ratio - safe_ratio
        else:  # balanced
            rush_ratio = config.rush_ratio
            target_ratio = config.target_ratio
            safe_ratio = config.safe_ratio

        rush_count = int(total * rush_ratio)
        target_count = int(total * target_ratio)
        safe_count = total - rush_count - target_count

        return {
            "total": total,
            "rush": rush_count,
            "target": target_count,
            "safe": safe_count
        }

    def explain_strategy(self, user_rank: int) -> str:
        """
        解释当前排位的策略

        Args:
            user_rank: 用户排位

        Returns:
            策略说明文本
        """
        config = self.get_config(user_rank)
        search_range = self.calculate_search_range(user_rank)
        volunteer_count = self.get_recommended_volunteer_count(user_rank)

        explanation = f"""
【排位梯度分析】

您的排位: {user_rank}
所属层次: {config.description}

【候选池配置】
- 候选池大小: {config.candidate_pool_size}个专业组
- 推荐数量: {config.recommend_count}个

【搜索范围】
- 冲刺区间: 位次 {search_range['rush'][0]:,} - {search_range['rush'][1]:,}
  （比您排位靠前 {user_rank - search_range['rush'][0]:,} - {user_rank - search_range['rush'][1]:,} 名）

- 稳妥区间: 位次 {search_range['target'][0]:,} - {search_range['target'][1]:,}
  （上下浮动范围）

- 保底区间: 位次 {search_range['safe'][0]:,} - {search_range['safe'][1]:,}
  （比您排位靠后 {search_range['safe'][0] - user_rank:,} - {search_range['safe'][1] - user_rank:,} 名）

【推荐志愿配比】
- 冲刺志愿: {volunteer_count['rush']}个 ({config.rush_ratio*100:.0f}%)
- 稳妥志愿: {volunteer_count['target']}个 ({config.target_ratio*100:.0f}%)
- 保底志愿: {volunteer_count['safe']}个 ({config.safe_ratio*100:.0f}%)

【策略说明】
{self._get_strategy_advice(user_rank, config)}
        """

        return explanation.strip()

    def _get_strategy_advice(
        self,
        user_rank: int,
        config: RankGradientConfig
    ) -> str:
        """生成针对性的策略建议"""
        if user_rank < 5000:
            return """
顶尖考生策略：
1. 候选池较小，因为可选的顶尖学校有限
2. 每个志愿都很关键，需要精细匹配
3. 建议重点关注专业方向，名校之间差异不大
4. 注意专业组内部结构，避免被调剂到不喜欢的专业
"""
        elif user_rank < 30000:
            return """
优良层考生策略：
1. 候选池适中，选择面较广
2. 可以在985/211和专业之间做平衡
3. 建议冲刺985的同时，保底211
4. 注意地域因素，同层次学校地域差异大
"""
        elif user_rank < 60000:
            return """
中等层考生策略：
1. 候选池较大，需要精细筛选
2. 一本和好二本是主要选择
3. 建议专业优先，学校层次其次
4. 注意就业率和深造率，这个分段差异明显
"""
        else:
            return """
普通层考生策略：
1. 候选池最大，选择面广但需要谨慎
2. 建议确保录取，避免滑档
3. 关注专业实用性和就业前景
4. 保底志愿比例适当增加
"""


# ============================================
# 测试代码
# ============================================

if __name__ == "__main__":
    print("=== 排位梯度策略测试 ===\n")

    strategy = RankGradientStrategy()

    # 测试不同排位
    test_ranks = [3000, 12000, 25000, 50000, 120000]

    for rank in test_ranks:
        print(f"\n{'='*60}")
        print(strategy.explain_strategy(rank))
        print(f"{'='*60}\n")

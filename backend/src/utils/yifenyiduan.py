"""
一分一段表管理器
用于分数-位次转换和验证
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict
import numpy as np


class YiFenYiDuanManager:
    """一分一段表管理器"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化一分一段表管理器

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.data: Dict[Tuple[int, str], pd.DataFrame] = {}
        self._load_all_data()

    def _load_all_data(self):
        """加载所有一分一段表数据"""
        print("[INFO] 正在加载一分一段表...")

        # 加载2021-2025年的物理类和历史类数据
        for year in range(2021, 2026):
            for category in ['物理', '历史']:
                file_path = self.data_dir / f"{year}_{category}_yifenyiduan.csv"

                if file_path.exists():
                    try:
                        df = pd.read_csv(file_path, encoding='utf-8-sig')
                        # 确保数据按分数降序排列
                        df = df.sort_values('score', ascending=False).reset_index(drop=True)
                        self.data[(year, category)] = df
                        print(f"[OK] 加载: {year}年{category}类 ({len(df)} 条记录)")
                    except Exception as e:
                        print(f"[WARN] 加载失败 {file_path}: {e}")
                else:
                    print(f"[WARN] 文件不存在: {file_path}")

        if not self.data:
            print("[WARN] 未加载任何一分一段表数据！")

    def score_to_rank(
        self,
        score: float,
        category: str,
        year: Optional[int] = None
    ) -> Optional[int]:
        """
        分数转位次（使用最近年份的数据或指定年份）

        Args:
            score: 分数
            category: 类别（物理/历史）
            year: 年份（可选，默认使用最新可用年份）

        Returns:
            位次（如果找不到则返回None）
        """
        # 标准化类别名称
        category = self._normalize_category(category)

        # 如果没有指定年份，使用最新可用年份
        if year is None:
            available_years = sorted([y for y, c in self.data.keys() if c == category], reverse=True)
            if not available_years:
                return None
            year = available_years[0]

        # 获取对应的一分一段表
        df = self.data.get((year, category))
        if df is None:
            return None

        # 查找分数对应的位次
        matched = df[df['score'] == score]
        if not matched.empty:
            return int(matched.iloc[0]['rank'])

        # 如果精确分数不存在，进行插值估算
        # 找到最接近的两个分数
        higher = df[df['score'] > score]
        lower = df[df['score'] < score]

        if higher.empty and lower.empty:
            return None
        elif higher.empty:
            # 分数高于最高分，返回最好位次
            return int(df.iloc[0]['rank'])
        elif lower.empty:
            # 分数低于最低分，返回最差位次
            return int(df.iloc[-1]['rank'])
        else:
            # 线性插值
            score_high = higher.iloc[-1]['score']
            rank_high = higher.iloc[-1]['rank']
            score_low = lower.iloc[0]['score']
            rank_low = lower.iloc[0]['rank']

            # 插值计算
            rank = rank_high + (score - score_high) / (score_low - score_high) * (rank_low - rank_high)
            return int(rank)

    def rank_to_score(
        self,
        rank: int,
        category: str,
        year: Optional[int] = None
    ) -> Optional[int]:
        """
        位次转分数（使用最近年份的数据或指定年份）

        Args:
            rank: 位次
            category: 类别（物理/历史）
            year: 年份（可选，默认使用最新可用年份）

        Returns:
            分数（如果找不到则返回None）
        """
        # 标准化类别名称
        category = self._normalize_category(category)

        # 如果没有指定年份，使用最新可用年份
        if year is None:
            available_years = sorted([y for y, c in self.data.keys() if c == category], reverse=True)
            if not available_years:
                return None
            year = available_years[0]

        # 获取对应的一分一段表
        df = self.data.get((year, category))
        if df is None:
            return None

        # 查找位次对应的分数（找到最接近的位次）
        df['rank_diff'] = abs(df['rank'] - rank)
        closest = df.loc[df['rank_diff'].idxmin()]

        return int(closest['score'])

    def validate_score_rank_match(
        self,
        score: float,
        rank: int,
        category: str,
        tolerance: int = 500
    ) -> Tuple[bool, Optional[str]]:
        """
        验证分数和位次是否匹配

        Args:
            score: 用户输入的分数
            rank: 用户输入的位次
            category: 类别（物理/历史）
            tolerance: 位次容差（允许的位次偏差）

        Returns:
            (是否匹配, 错误信息)
        """
        # 标准化类别名称
        category = self._normalize_category(category)

        # 使用最新年份数据验证
        predicted_rank = self.score_to_rank(score, category)

        if predicted_rank is None:
            return False, f"无法根据{category}类一分一段表验证分数{score}"

        # 检查位次偏差
        rank_diff = abs(predicted_rank - rank)

        if rank_diff <= tolerance:
            return True, None
        else:
            # 根据位次反推正确的分数
            correct_score = self.rank_to_score(rank, category)
            return False, (
                f"分数与位次不匹配！\n"
                f"您的位次 {rank} 对应的分数约为 {correct_score} 分\n"
                f"您输入的分数 {score} 对应的位次约为 {predicted_rank}\n"
                f"请确认您的分数是否正确"
            )

    def get_available_years(self, category: str) -> list:
        """获取某类别可用的年份列表"""
        category = self._normalize_category(category)
        years = sorted([y for y, c in self.data.keys() if c == category])
        return years

    def _normalize_category(self, category: str) -> str:
        """标准化类别名称"""
        if '物' in category or 'physics' in category.lower():
            return '物理'
        elif '历' in category or '史' in category or 'history' in category.lower():
            return '历史'
        else:
            return category

    def get_score_range(self, category: str, year: Optional[int] = None) -> Tuple[int, int]:
        """
        获取某年份某类别的分数范围

        Returns:
            (最低分, 最高分)
        """
        category = self._normalize_category(category)

        if year is None:
            available_years = sorted([y for y, c in self.data.keys() if c == category], reverse=True)
            if not available_years:
                return (0, 750)
            year = available_years[0]

        df = self.data.get((year, category))
        if df is None:
            return (0, 750)

        return (int(df['score'].min()), int(df['score'].max()))

    def get_rank_range(self, category: str, year: Optional[int] = None) -> Tuple[int, int]:
        """
        获取某年份某类别的位次范围

        Returns:
            (最好位次, 最差位次)
        """
        category = self._normalize_category(category)

        if year is None:
            available_years = sorted([y for y, c in self.data.keys() if c == category], reverse=True)
            if not available_years:
                return (1, 500000)
            year = available_years[0]

        df = self.data.get((year, category))
        if df is None:
            return (1, 500000)

        return (int(df['rank'].min()), int(df['rank'].max()))

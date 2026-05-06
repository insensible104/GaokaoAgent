"""高考量化引擎 - 核心数学模块"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple  # 修复问题4：添加Tuple导入
import glob
from functools import lru_cache  # 修复P2：添加LRU缓存优化性能


class GaokaoQuantEngine:
    """高考量化引擎（全内存计算）"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化引擎，加载所有历史数据到内存

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.df: Optional[pd.DataFrame] = None
        self.available_years: List[int] = []  # 可用的数据年份
        self._load_data()
        self._detect_available_years()

    def _load_data(self):
        """加载所有 CSV 数据到内存"""
        print("[INFO] 正在加载历史数据...")

        # 查找历史录取 CSV 文件。招生计划和一分一段表由专门 loader 处理，
        # 不混入历史录取表，避免字段映射后被误删或污染统计。
        csv_files = [
            file
            for file in glob.glob(str(self.data_dir / "*.csv"))
            if "enrollment" not in Path(file).name
            and "yifenyiduan" not in Path(file).name
            and "一分一段" not in Path(file).name
        ]

        if not csv_files:
            raise FileNotFoundError(f"在 {self.data_dir} 目录下未找到任何 CSV 文件")

        # 读取并合并所有文件
        dfs = []
        for file in csv_files:
            try:
                # 优先尝试 UTF-8，失败则尝试 GBK（Windows 常用）
                try:
                    df = pd.read_csv(file, encoding='utf-8-sig')
                except UnicodeDecodeError:
                    df = pd.read_csv(file, encoding='gbk')

                # 立即清洗列名，避免合并时列名不一致
                df.columns = df.columns.str.strip().str.replace('\r\n', '').str.replace('\n', '').str.replace('\r', '')

                dfs.append(df)
                print(f"[OK] 加载: {Path(file).name} ({len(df)} 行)")
            except Exception as e:
                print(f"[WARN] 跳过文件 {file}: {e}")

        if not dfs:
            raise ValueError("没有成功加载任何数据文件")

        self.df = pd.concat(dfs, ignore_index=True)

        # 数据清洗
        self._clean_data()

        print(f"[OK] 数据加载完成！总计 {len(self.df)} 行记录")

    def _clean_data(self):
        """数据清洗和标准化"""
        # 列名已在加载时清洗，这里不需要再处理

        # 关键字段映射（兼容不同格式）
        column_mapping = {
            '院校名称': 'school',
            '院校代码': 'school_code',  # 添加院校代码映射
            '代码': 'school_code',
            '专业/类': 'major',
            '最低分平均排位': 'min_rank',
            '录取人数': 'quota',
            '专业组': 'major_group',
            '年份': 'year',
            '选科': 'subject_requirement'
        }

        for old, new in column_mapping.items():
            if old in self.df.columns:
                self.df[new] = self.df[old]

        # 确保关键字段为数值类型
        numeric_cols = ['min_rank', 'quota', 'year']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # 删除缺失关键数据的行
        self.df.dropna(subset=['school', 'major', 'min_rank'], inplace=True)

        # 填充专业组缺失值
        if 'major_group' in self.df.columns:
            self.df['major_group'] = self.df['major_group'].fillna('未分组')

    def _detect_available_years(self):
        """检测数据中可用的年份"""
        if self.df is not None and 'year' in self.df.columns:
            self.available_years = sorted(self.df['year'].dropna().unique().astype(int).tolist())
            print(f"[INFO] 检测到可用数据年份: {self.available_years}")
        else:
            print("[WARN] 数据中没有year字段，无法检测年份")
            self.available_years = []

    def get_historical_years(self, num_years: int = 4, target_year: Optional[int] = None) -> List[int]:
        """
        动态获取历史年份列表

        Args:
            num_years: 需要的历史年份数量（默认4年）
            target_year: 目标预测年份（可选，默认为最新年份+1）

        Returns:
            历史年份列表

        例如：
        - 如果可用数据是[2021,2022,2023,2024,2025]，target_year=2026
        - 返回[2022,2023,2024,2025]（最近4年）
        """
        if not self.available_years:
            print("[WARN] 没有可用年份数据，使用默认年份[2021,2022,2023,2024]")
            return [2021, 2022, 2023, 2024]

        # 如果没有指定target_year，使用最新年份+1
        if target_year is None:
            target_year = max(self.available_years) + 1

        # 从target_year往前推num_years年，并过滤出实际存在的年份
        potential_years = list(range(target_year - num_years, target_year))
        historical_years = [y for y in potential_years if y in self.available_years]

        # 如果过滤后不足num_years，尽可能使用所有可用年份
        if len(historical_years) < num_years:
            historical_years = self.available_years[-num_years:]  # 使用最近的N年

        print(f"[INFO] 使用历史年份: {historical_years} (预测 {target_year} 年)")
        return historical_years

    def get_school_major_history(
        self,
        school: str,
        major: str,
        years: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        获取某院校专业的历史数据

        Args:
            school: 院校名称
            major: 专业名称
            years: 年份列表（可选）

        Returns:
            历史数据 DataFrame
        """
        # 使用缓存方法（将list转为tuple）
        years_tuple = tuple(years) if years else None
        return self._get_school_major_history_cached(school, major, years_tuple)

    @lru_cache(maxsize=1000)
    def _get_school_major_history_cached(
        self,
        school: str,
        major: str,
        years_tuple: Optional[Tuple[int, ...]]
    ) -> pd.DataFrame:
        """
        内部缓存方法：获取某院校专业的历史数据

        修复P2-3: 添加LRU缓存避免重复查询
        """
        query = (self.df['school'] == school) & (self.df['major'] == major)

        if years_tuple:
            query &= self.df['year'].isin(years_tuple)

        return self.df[query].sort_values('year')

    def get_major_group_history(
        self,
        school: str,
        major_group: str,
        years: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        获取某院校专业组的历史数据（用于概率计算）

        Args:
            school: 院校名称
            major_group: 专业组代码
            years: 年份列表（可选，默认使用最近4年）

        Returns:
            历史数据 DataFrame（包含min_rank和quota字段）
        """
        # 如果没有指定years，使用最近4年
        if years is None:
            years = self.get_historical_years(num_years=4)

        # 使用缓存方法（将list转为tuple）
        years_tuple = tuple(years)
        return self._get_major_group_history_cached(school, major_group, years_tuple)

    @lru_cache(maxsize=1000)
    def _get_major_group_history_cached(
        self,
        school: str,
        major_group: str,
        years_tuple: Tuple[int, ...]
    ) -> pd.DataFrame:
        """
        内部缓存方法：获取某院校专业组的历史数据

        修复P2-3: 添加LRU缓存避免重复查询（game_agent.py调用200次）
        """
        query = (self.df['school'] == school) & (self.df['major_group'] == major_group)
        query &= self.df['year'].isin(years_tuple)

        return self.df[query].sort_values('year')

    def _calculate_adaptive_range(
        self,
        user_rank: int,
        subject_group: str,
        target_count: int,
        df_grouped: pd.DataFrame
    ) -> Tuple[int, int]:  # 修复问题4：使用Tuple而不是tuple
        """
        自适应动态滑动窗口算法：根据数据密度计算搜索范围

        策略：
        1. 从初始小范围开始搜索
        2. 逐步扩大窗口直到找到足够的候选
        3. 顶尖段和普通段使用不同的扩张策略
        4. 设置最大范围避免推荐质量下降

        Args:
            user_rank: 用户位次
            subject_group: 选科组合
            target_count: 目标候选数量
            df_grouped: 已聚合的专业组数据

        Returns:
            (rush_range, safe_range) 冲刺和保底范围
        """
        # 按位次段设置初始范围和扩张步长
        # 核心原则：位次越高，学校断档越明显，范围应该越小
        # 位次越低，需要看更大范围（考虑冲学校/保专业的权衡）
        if user_rank <= 1000:
            # 超顶尖段（清北、港科广直博）：极小范围
            initial_rush = 300
            initial_safe = 1000
            expand_step = 300
            max_rush = 2000
            max_safe = 3000
        elif user_rank <= 5000:
            # 顶尖段（华东五校、C9）：小范围
            initial_rush = 800
            initial_safe = 2000
            expand_step = 500
            max_rush = 3000
            max_safe = 8000
        elif user_rank <= 15000:
            # 985段（中上985 + 特色985）：应该有大量冲刺空间
            # 修复：大幅增加冲刺范围，让中等分数段也能看到顶尖985
            # 位次7889的学生应该能冲刺位次1000-4000的华东五校
            initial_rush = 7000  # 增加到7000，确保能搜到顶尖985
            initial_safe = 15000  # 修复：进一步增加保底范围（12000→15000），确保找到真正保底
            expand_step = 5000    # 修复：加快扩张速度（2000→5000）
            max_rush = 20000  # 最大冲刺范围20000
            max_safe = 60000  # 修复：大幅增加最大保底范围（35000→60000），rank 7999最大搜到67999
        elif user_rank <= 30000:
            # 211段（中等211 + 双一流）：中等范围
            # 物理30000名 → 应该看到60000-70000名
            initial_rush = 5000
            initial_safe = 15000
            expand_step = 2000
            max_rush = 15000
            max_safe = 40000  # 30000 + 40000 = 70000
        elif user_rank <= 60000:
            # 双一流/一本段：较大范围
            initial_rush = 8000
            initial_safe = 25000
            expand_step = 3000
            max_rush = 20000
            max_safe = 50000
        else:
            # 普通一本/二本段：最大范围
            initial_rush = 10000
            initial_safe = 30000
            expand_step = 5000
            max_rush = 25000
            max_safe = 60000

        # 滑动窗口：逐步扩大范围直到找到足够的候选
        rush_range = initial_rush
        safe_range = initial_safe
        iteration = 0
        max_iterations = 15  # 修复：增加到15次，确保能达到max_safe=60000（需要9次迭代）

        while iteration < max_iterations:
            # 计算当前窗口范围
            min_rank_search = max(1, user_rank - rush_range)
            max_rank_search = user_rank + safe_range

            # 在当前窗口内筛选候选
            candidates = df_grouped[
                (df_grouped['min_rank'] >= min_rank_search) &
                (df_grouped['min_rank'] <= max_rank_search)
            ]

            candidate_count = len(candidates)

            # 判断是否找到足够的候选
            # 修复：确保safe_range至少达到max_safe的80%，才停止扩张
            # 这样可以确保搜索到真正的保底学校（如rank 7999需要搜到40000-50000的学校）
            min_safe_range_required = max(initial_safe * 2, int(max_safe * 0.8))

            if candidate_count >= target_count and safe_range >= min_safe_range_required:
                print(f"[OK] 找到足够候选 ({candidate_count} >= {target_count})，停止扩张")
                break
            elif candidate_count >= target_count * 0.7 and safe_range >= min_safe_range_required:
                # 如果接近目标（≥70%），也可以接受
                print(f"[OK] 候选数接近目标 ({candidate_count} ≈ {target_count})，停止扩张")
                break
            else:
                # 继续扩张
                if rush_range < max_rush:
                    rush_range = min(rush_range + expand_step, max_rush)
                if safe_range < max_safe:
                    safe_range = min(safe_range + expand_step, max_safe)
                iteration += 1

                # 如果已达最大范围，停止
                if rush_range >= max_rush and safe_range >= max_safe:
                    print(f"[WARN] 已达最大范围限制，停止扩张")
                    break

        return rush_range, safe_range

    def search_major_groups(
        self,
        user_rank: int,
        subject_group: str,
        target_count: int = 100
    ) -> pd.DataFrame:
        """
        按专业组搜索符合用户位次范围的院校（基于历史数据预测）

        自适应动态滑动窗口策略：
        - 根据实际数据密度动态调整搜索范围
        - 确保找到足够的候选（target_count个专业组）
        - 避免范围过大导致推荐质量下降

        Args:
            user_rank: 用户位次
            subject_group: 选科组合（物理/历史）
            target_count: 目标返回的专业组数量

        Returns:
            符合条件的专业组列表（聚合后）
        """
        # 动态获取历史年份（让系统根据可用数据自动判断）
        # 例如：如果有2021-2025数据，自动使用2022-2025预测2026
        historical_years = self.get_historical_years(num_years=4)
        df_historical = self.df[self.df['year'].isin(historical_years)].copy()

        # 筛选选科要求
        if 'subject_requirement' in df_historical.columns:
            # 广东新高考：物理类用"物"，历史类用"历"（不是"史"）
            subject_abbr = subject_group.replace('物理', '物').replace('历史', '历')
            df_historical = df_historical[
                df_historical['subject_requirement'].str.contains(
                    subject_abbr,
                    na=False,
                    case=False
                )
            ]

        # 按 (学校 + 专业组) 聚合
        # 如果有school_code字段，在聚合时保留它（取第一个值）
        if 'school_code' in df_historical.columns:
            grouped = df_historical.groupby(['school', 'major_group']).agg({
                'min_rank': 'median',  # 历史中位数最低位次（对爆冷年份不敏感）
                'major': lambda x: list(x.unique()),  # 该专业组包含的所有专业
                'quota': 'sum',  # 该专业组的总招生人数
                'school_code': 'first'  # 保留院校代码（同一学校代码相同）
            }).reset_index()
        else:
            # 如果没有school_code，聚合后生成默认值（使用学校名称作为代码）
            grouped = df_historical.groupby(['school', 'major_group']).agg({
                'min_rank': 'median',  # 历史中位数最低位次（对爆冷年份不敏感）
                'major': lambda x: list(x.unique()),
                'quota': 'sum'
            }).reset_index()
            grouped['school_code'] = grouped['school']  # 默认使用学校名称作为代码

        # 计算每个专业组包含的专业数量
        grouped['major_count'] = grouped['major'].apply(len)

        # 动态滑动窗口算法：基于数据密度自适应调整范围
        rush_range, safe_range = self._calculate_adaptive_range(
            user_rank,
            subject_group,
            target_count,
            grouped  # 传入已聚合的数据
        )

        print(f"[INFO] 位次 {user_rank} → 自适应范围：冲刺±{rush_range}, 保底±{safe_range}")

        # 位次范围筛选（非对称：冲刺向上，保底向下）
        min_rank_search = max(1, user_rank - rush_range)
        max_rank_search = user_rank + safe_range

        df_result = grouped[
            (grouped['min_rank'] >= min_rank_search) &
            (grouped['min_rank'] <= max_rank_search)
        ].copy()

        # 按位次排序
        df_result = df_result.sort_values('min_rank')

        # 如果结果过多，取前 target_count 个
        if len(df_result) > target_count:
            df_result = df_result.head(target_count)

        print(f"[INFO] 搜索范围: {min_rank_search}-{max_rank_search}位次，找到{len(df_result)}个专业组")

        return df_result

    def search_schools(
        self,
        user_rank: int,
        subject_group: str,
        rank_range: int = 5000
    ) -> pd.DataFrame:
        """
        搜索符合用户位次范围的院校专业（旧方法，保留兼容性）

        Args:
            user_rank: 用户位次
            subject_group: 选科组合（物理/历史）
            rank_range: 位次搜索范围（±）

        Returns:
            符合条件的院校专业列表
        """
        # 筛选最新年份数据
        latest_year = self.df['year'].max()
        df_latest = self.df[self.df['year'] == latest_year].copy()

        # 筛选选科要求（兼容完整名称和缩写）
        if 'subject_requirement' in df_latest.columns:
            # 广东新高考：物理类用"物"，历史类用"历"（不是"史"）
            subject_abbr = subject_group.replace('物理', '物').replace('历史', '历')
            df_latest = df_latest[
                df_latest['subject_requirement'].str.contains(
                    subject_abbr,
                    na=False,
                    case=False
                )
            ]

        # 位次范围筛选
        df_result = df_latest[
            (df_latest['min_rank'] >= user_rank - rank_range) &
            (df_latest['min_rank'] <= user_rank + rank_range)
        ].copy()

        return df_result.sort_values('min_rank')

    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        return {
            'total_records': len(self.df),
            'schools_count': self.df['school'].nunique(),
            'majors_count': self.df['major'].nunique(),
            'years': sorted(self.df['year'].unique().tolist()),
            'latest_year': int(self.df['year'].max())
        }

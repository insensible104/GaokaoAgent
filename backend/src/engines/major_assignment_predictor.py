"""专业分配预测模块

基于专业级别的历史录取线，预测考生进入专业组后会被分配到哪个专业

核心原理：
- 广东新高考按专业组投档，但专业组内的专业分数线不同
- 热门专业（如计算机）的最低位次接近专业组投档线
- 冷门专业（如哲学）的最低位次远高于专业组投档线
- 考生被分配到哪个专业，取决于其位次在专业组内的相对位置

示例：
  中山大学物理01组投档线：位次8000
  - 计算机科学：最低位次8000（热门，卡线进）
  - 数学类：最低位次9000
  - 物理类：最低位次10000
  - 哲学：最低位次15000（冷门，调剂去向）

  用户位次12000：
  → 能进专业组（12000 > 8000），但只能去"物理类"或"哲学"
  → 预测分配：哲学（最可能的调剂专业）
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from pathlib import Path


class MajorInfo(BaseModel):
    """专业信息"""
    major_name: str = Field(description="专业名称")
    min_rank_2024: Optional[int] = Field(None, description="2024年最低位次")
    min_rank_2023: Optional[int] = Field(None, description="2023年最低位次")
    min_rank_2022: Optional[int] = Field(None, description="2022年最低位次")
    min_rank_2021: Optional[int] = Field(None, description="2021年最低位次")
    mean_min_rank: float = Field(description="历史平均最低位次")
    std_min_rank: float = Field(description="位次标准差（波动性）")
    quota: int = Field(default=30, description="招生计划数")


class MajorGroupStructure(BaseModel):
    """专业组内部结构"""
    school_name: str = Field(description="学校名称")
    major_group_code: str = Field(description="专业组代码")
    group_min_rank: int = Field(description="专业组投档线（最低位次）")
    majors: List[MajorInfo] = Field(default_factory=list, description="包含的专业列表")
    total_quota: int = Field(default=0, description="专业组总招生计划")


class MajorAssignmentPrediction(BaseModel):
    """专业分配预测结果"""
    predicted_major: str = Field(description="预测会被分配到的专业")
    confidence: float = Field(ge=0.0, le=1.0, description="预测置信度")
    rank_gap: int = Field(description="用户位次 - 专业最低位次")
    safety_level: str = Field(description="安全等级: guaranteed/safe/moderate/risky")

    # 专业满意度
    user_satisfaction: float = Field(
        ge=0.0, le=1.0,
        description="用户对该专业的满意度"
    )

    # 备选专业
    alternative_majors: List[Dict] = Field(
        default_factory=list,
        description="可能的其他专业 [{'name': xx, 'probability': 0.2}]"
    )

    # 调剂风险
    adjustment_risk: float = Field(
        ge=0.0, le=1.0,
        description="被调剂到不想要专业的风险"
    )


class MajorAssignmentPredictor:
    """
    专业分配预测器

    使用专业级别的历史录取数据，预测考生会被分配到哪个专业
    """

    def __init__(self, data_dir: str = "data"):
        """
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.major_data_cache = {}  # 缓存专业组数据

    def load_major_group_structure(
        self,
        school_name: str,
        major_group_code: str,
        subject_group: str = "物理类"
    ) -> Optional[MajorGroupStructure]:
        """
        加载专业组的内部结构（包含的专业及其录取线）

        Args:
            school_name: 学校名称
            major_group_code: 专业组代码
            subject_group: 科类（物理类/历史类）

        Returns:
            专业组结构，如果数据不存在返回None
        """
        cache_key = f"{school_name}_{major_group_code}_{subject_group}"

        # 检查缓存
        if cache_key in self.major_data_cache:
            return self.major_data_cache[cache_key]

        # 读取多年数据
        years = [2024, 2023, 2022, 2021]
        subject_suffix = "physics" if subject_group == "物理类" else "history"

        all_majors_data = []

        for year in years:
            file_path = self.data_dir / f"{year}_{subject_suffix}.csv"
            if not file_path.exists():
                continue

            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')

                # 筛选该学校和专业组的数据
                mask = (
                    (df['院校名称'] == school_name) &
                    (df['专业组'] == major_group_code)
                )
                group_df = df[mask].copy()

                if group_df.empty:
                    continue

                # 提取专业信息
                for _, row in group_df.iterrows():
                    major_name = row['专业/类']
                    min_rank = row.get('最低分\n平均排位', row.get('最低排位'))

                    if pd.isna(min_rank):
                        continue

                    all_majors_data.append({
                        'year': year,
                        'major_name': major_name,
                        'min_rank': int(min_rank),
                        'quota': int(row.get('录取\n人数', row.get('录取人数', 30)))
                    })

            except Exception as e:
                print(f"[WARN] 读取{year}年数据失败: {e}")
                continue

        if not all_majors_data:
            return None

        # 汇总专业数据
        majors_df = pd.DataFrame(all_majors_data)

        majors_list = []
        total_quota = 0

        for major_name in majors_df['major_name'].unique():
            major_df = majors_df[majors_df['major_name'] == major_name]

            # 提取各年的最低位次
            ranks_by_year = {}
            for year in years:
                year_data = major_df[major_df['year'] == year]
                if not year_data.empty:
                    ranks_by_year[year] = int(year_data.iloc[0]['min_rank'])

            if not ranks_by_year:
                continue

            # 计算均值和标准差
            ranks_values = list(ranks_by_year.values())
            mean_rank = np.mean(ranks_values)
            std_rank = np.std(ranks_values) if len(ranks_values) > 1 else mean_rank * 0.05

            # 招生计划（使用最近年份的）
            quota = int(major_df.iloc[0]['quota'])
            total_quota += quota

            major_info = MajorInfo(
                major_name=major_name,
                min_rank_2024=ranks_by_year.get(2024),
                min_rank_2023=ranks_by_year.get(2023),
                min_rank_2022=ranks_by_year.get(2022),
                min_rank_2021=ranks_by_year.get(2021),
                mean_min_rank=mean_rank,
                std_min_rank=std_rank,
                quota=quota
            )

            majors_list.append(major_info)

        if not majors_list:
            return None

        # 专业组投档线 = 所有专业中最低的位次（热门专业）
        group_min_rank = int(min([m.mean_min_rank for m in majors_list]))

        structure = MajorGroupStructure(
            school_name=school_name,
            major_group_code=major_group_code,
            group_min_rank=group_min_rank,
            majors=sorted(majors_list, key=lambda m: m.mean_min_rank),  # 按热度排序
            total_quota=total_quota
        )

        # 缓存
        self.major_data_cache[cache_key] = structure

        return structure

    def predict_major_assignment(
        self,
        user_rank: int,
        major_group_structure: MajorGroupStructure,
        user_major_preferences: Optional[List[str]] = None
    ) -> MajorAssignmentPrediction:
        """
        预测用户会被分配到哪个专业

        策略：
        1. 找到用户位次能达到的最好专业（位次 >= 专业最低位次）
        2. 如果所有专业都够不到，返回最冷门专业（调剂）
        3. 计算用户对该专业的满意度

        Args:
            user_rank: 用户位次
            major_group_structure: 专业组结构
            user_major_preferences: 用户专业偏好列表（如 ["计算机", "软件工程"]）

        Returns:
            专业分配预测结果
        """
        majors = major_group_structure.majors

        if not majors:
            raise ValueError("专业组没有包含任何专业")

        # === 步骤1：找到用户位次能达到的最好专业 ===
        predicted_major = None
        rank_gap = None

        for major in majors:
            gap = user_rank - major.mean_min_rank

            if gap >= 0:  # 用户位次 >= 专业最低位次，能进这个专业
                predicted_major = major
                rank_gap = gap
                break

        # 如果所有专业都够不到，返回最冷门的（调剂）
        if predicted_major is None:
            predicted_major = majors[-1]  # 最后一个（最冷门）
            rank_gap = user_rank - predicted_major.mean_min_rank

        # === 步骤2：计算置信度 ===
        # 基于rank_gap和专业波动性
        if rank_gap >= predicted_major.std_min_rank * 2:
            confidence = 0.95  # 非常安全
            safety_level = "guaranteed"
        elif rank_gap >= predicted_major.std_min_rank:
            confidence = 0.85
            safety_level = "safe"
        elif rank_gap >= 0:
            confidence = 0.70
            safety_level = "moderate"
        else:
            confidence = 0.60  # 边缘情况
            safety_level = "risky"

        # === 步骤3：计算用户满意度 ===
        user_satisfaction = self._calculate_satisfaction(
            predicted_major.major_name,
            user_major_preferences or []
        )

        # === 步骤4：计算备选专业 ===
        alternative_majors = []
        for i, major in enumerate(majors):
            if major.major_name == predicted_major.major_name:
                continue

            # 估计被分配到该专业的概率
            gap = user_rank - major.mean_min_rank
            if gap < -major.std_min_rank * 2:
                prob = 0.0  # 基本不可能
            elif gap < 0:
                prob = 0.05  # 很小概率
            else:
                prob = 0.10  # 有可能

            if prob > 0:
                alternative_majors.append({
                    'name': major.major_name,
                    'probability': prob
                })

        # === 步骤5：计算调剂风险 ===
        # 被调剂到不想要专业的风险
        if user_major_preferences:
            # 目标专业数量
            target_count = sum(
                1 for m in majors
                if self._calculate_satisfaction(m.major_name, user_major_preferences) >= 0.8
            )
            target_ratio = target_count / len(majors)

            # 如果预测专业不是目标专业，风险高
            if user_satisfaction < 0.8:
                adjustment_risk = 0.8 * (1 - target_ratio)
            else:
                adjustment_risk = 0.2 * (1 - target_ratio)
        else:
            adjustment_risk = 0.3  # 默认中等风险

        return MajorAssignmentPrediction(
            predicted_major=predicted_major.major_name,
            confidence=confidence,
            rank_gap=rank_gap,
            safety_level=safety_level,
            user_satisfaction=user_satisfaction,
            alternative_majors=alternative_majors[:3],  # 最多3个备选
            adjustment_risk=adjustment_risk
        )

    def _calculate_satisfaction(
        self,
        major_name: str,
        user_preferences: List[str]
    ) -> float:
        """
        计算用户对专业的满意度

        Args:
            major_name: 专业名称
            user_preferences: 用户偏好列表

        Returns:
            满意度 (0.0 - 1.0)
        """
        if not user_preferences:
            return 0.5  # 默认中性

        # 精确匹配
        for pref in user_preferences:
            if pref in major_name or major_name in pref:
                return 1.0  # 完美匹配

        # 部分匹配（基于关键词）
        tech_keywords = ['计算机', '软件', '人工智能', '数据科学', '电子信息', '自动化']
        science_keywords = ['数学', '物理', '化学', '统计']
        business_keywords = ['经济', '金融', '管理', '会计']
        liberal_keywords = ['文学', '历史', '哲学', '法学']

        user_is_tech = any(kw in ''.join(user_preferences) for kw in tech_keywords)
        major_is_tech = any(kw in major_name for kw in tech_keywords)

        if user_is_tech and major_is_tech:
            return 0.7  # 同类别，较满意

        user_is_science = any(kw in ''.join(user_preferences) for kw in science_keywords)
        major_is_science = any(kw in major_name for kw in science_keywords)

        if user_is_science and major_is_science:
            return 0.6

        # 如果用户想要理工科，但专业是文科，满意度低
        if user_is_tech and any(kw in major_name for kw in liberal_keywords):
            return 0.2

        return 0.4  # 默认较低满意度


# === 测试代码 ===
if __name__ == "__main__":
    print("=== 专业分配预测器测试 ===\n")

    predictor = MajorAssignmentPredictor(data_dir="data")

    # 测试案例
    test_cases = [
        {
            "school": "中山大学",
            "group": "201",
            "user_rank": 10000,
            "preferences": ["计算机", "软件工程"]
        },
        {
            "school": "华南理工大学",
            "group": "202",
            "user_rank": 15000,
            "preferences": ["计算机"]
        }
    ]

    for case in test_cases:
        print(f"\n{'='*60}")
        print(f"学校: {case['school']}")
        print(f"专业组: {case['group']}")
        print(f"用户位次: {case['user_rank']}")
        print(f"偏好专业: {case['preferences']}")
        print(f"{'='*60}\n")

        # 加载专业组结构
        structure = predictor.load_major_group_structure(
            school_name=case["school"],
            major_group_code=case["group"],
            subject_group="物理类"
        )

        if not structure:
            print("[ERROR] 未找到专业组数据\n")
            continue

        print(f"专业组投档线: {structure.group_min_rank}")
        print(f"包含 {len(structure.majors)} 个专业:")
        for i, major in enumerate(structure.majors[:5], 1):
            print(f"  {i}. {major.major_name} - 最低位次{major.mean_min_rank:.0f}")

        # 预测专业分配
        prediction = predictor.predict_major_assignment(
            user_rank=case["user_rank"],
            major_group_structure=structure,
            user_major_preferences=case["preferences"]
        )

        print(f"\n【预测结果】")
        print(f"预测专业: {prediction.predicted_major}")
        print(f"置信度: {prediction.confidence:.1%}")
        print(f"位次差: {prediction.rank_gap}")
        print(f"安全等级: {prediction.safety_level}")
        print(f"用户满意度: {prediction.user_satisfaction:.1%}")
        print(f"调剂风险: {prediction.adjustment_risk:.1%}")

        if prediction.alternative_majors:
            print(f"\n备选专业:")
            for alt in prediction.alternative_majors:
                print(f"  - {alt['name']} (概率{alt['probability']:.0%})")

    print("\n测试完成！")

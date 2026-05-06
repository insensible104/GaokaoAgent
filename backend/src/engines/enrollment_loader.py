"""2025年招生计划加载器"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional


class EnrollmentPlanLoader:
    """加载2025年招生计划数据"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化加载器

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.enrollment_data: Optional[pd.DataFrame] = None
        self._load_enrollment_plan()

    @staticmethod
    def _normalize_code(value) -> str:
        """把 Excel/CSV 中的代码统一成无小数点字符串。"""
        if pd.isna(value):
            return ""
        text = str(value).strip()
        if text.endswith(".0"):
            text = text[:-2]
        return text

    def _load_enrollment_plan(self):
        """加载2025年招生计划"""
        print("[INFO] 加载2025年招生计划...")

        # 尝试加载完整数据
        full_file = self.data_dir / "2025_enrollment_full.csv"
        if not full_file.exists():
            print("[WARN] 未找到2025年招生计划文件，跳过加载")
            return

        try:
            self.enrollment_data = pd.read_csv(full_file, encoding='utf-8-sig')
            print(f"[OK] 加载2025年招生计划：{len(self.enrollment_data)} 条记录")

            # 数据清洗
            self._clean_data()
        except Exception as e:
            print(f"[ERROR] 加载2025年招生计划失败: {e}")
            self.enrollment_data = None

    def _clean_data(self):
        """清洗招生计划数据"""
        if self.enrollment_data is None:
            return

        # 确保关键字段存在且类型正确
        numeric_cols = [
            '计划招数',
            '学制',
            '学费',
            '2024_最低分',
            '2024_最低位次',
            '2023_最低分',
            '2023_最低位次',
            '2022_最低分',
            '2022_最低位次',
            '2021_最低分',
            '2021_最低位次',
        ]
        for col in numeric_cols:
            if col in self.enrollment_data.columns:
                self.enrollment_data[col] = pd.to_numeric(
                    self.enrollment_data[col], errors='coerce'
                )

        # 删除关键信息缺失的行
        self.enrollment_data.dropna(
            subset=['院校名称', '科类', '专业名称'],
            inplace=True
        )

        self.enrollment_data['school_code'] = self.enrollment_data['院校代码'].apply(self._normalize_code)
        self.enrollment_data['school_name'] = self.enrollment_data['院校名称'].astype(str).str.strip()
        self.enrollment_data['major_group_code'] = self.enrollment_data['专业组代码'].apply(self._normalize_code)
        self.enrollment_data['major_code'] = self.enrollment_data['专业序号'].apply(self._normalize_code)
        self.enrollment_data['major_name'] = self.enrollment_data['专业名称'].astype(str).str.strip()
        self.enrollment_data['subject_group'] = self.enrollment_data['科类'].astype(str).str.strip()

    def _filter_group(
        self,
        school_name: Optional[str] = None,
        major_group_code: Optional[str | int] = None,
        category: Optional[str] = None,
        school_code: Optional[str | int] = None,
    ) -> pd.DataFrame:
        """按学校、科类和专业组筛选招生计划。"""
        if self.enrollment_data is None:
            return pd.DataFrame()

        query = pd.Series(True, index=self.enrollment_data.index)
        if school_code is not None and self._normalize_code(school_code):
            query &= self.enrollment_data['school_code'] == self._normalize_code(school_code)
        elif school_name:
            query &= self.enrollment_data['school_name'] == str(school_name).strip()

        if major_group_code is not None and self._normalize_code(major_group_code):
            query &= self.enrollment_data['major_group_code'] == self._normalize_code(major_group_code)

        if category:
            category_text = str(category).strip()
            query &= self.enrollment_data['subject_group'].str.contains(
                category_text,
                na=False,
                regex=False,
            )

        return self.enrollment_data[query].copy()

    def get_major_group_options(
        self,
        school_name: Optional[str] = None,
        major_group_code: Optional[str | int] = None,
        category: Optional[str] = None,
        school_code: Optional[str | int] = None,
    ) -> List[Dict]:
        """获取某个院校专业组内的全部专业选项。"""
        group_data = self._filter_group(
            school_name=school_name,
            school_code=school_code,
            major_group_code=major_group_code,
            category=category,
        )

        if group_data.empty:
            return []

        if '专业序号' in group_data.columns:
            group_data = group_data.sort_values('专业序号')

        records = []
        for _, row in group_data.iterrows():
            records.append({
                'school_code': row.get('school_code', ''),
                'school_name': row.get('school_name', ''),
                'major_group_code': row.get('major_group_code', ''),
                'major_code': row.get('major_code', ''),
                'major_name': row.get('major_name', ''),
                'subject_requirement': row.get('选科要求'),
                'plan_quota': None if pd.isna(row.get('计划招数')) else int(row.get('计划招数')),
                'tuition': None if pd.isna(row.get('学费')) else float(row.get('学费')),
                'remarks': row.get('专业备注'),
                'historical_min_scores': {
                    year: None if pd.isna(row.get(f'{year}_最低分')) else float(row.get(f'{year}_最低分'))
                    for year in [2021, 2022, 2023, 2024]
                },
                'historical_min_ranks': {
                    year: None if pd.isna(row.get(f'{year}_最低位次')) else int(row.get(f'{year}_最低位次'))
                    for year in [2021, 2022, 2023, 2024]
                },
            })

        return records

    def get_major_group_info(
        self,
        school_name: str,
        major_group_code: int,
        category: str
    ) -> Optional[Dict]:
        """
        获取指定专业组的2025年招生信息

        Args:
            school_name: 院校名称
            major_group_code: 专业组代码
            category: 科类（物理/历史）

        Returns:
            专业组信息字典，如果不存在则返回None
        """
        if self.enrollment_data is None:
            return None

        group_data = self._filter_group(
            school_name=school_name,
            major_group_code=major_group_code,
            category=category,
        )

        if group_data.empty:
            return None

        # 聚合该专业组的信息
        return {
            '院校名称': school_name,
            '专业组代码': major_group_code,
            '科类': category,
            '批次': group_data['批次'].iloc[0] if '批次' in group_data.columns else None,
            '选科要求': group_data['选科要求'].iloc[0] if '选科要求' in group_data.columns else None,
            '专业列表': group_data['专业名称'].tolist(),
            '专业数量': len(group_data),
            '2025计划招数': int(group_data['计划招数'].sum()) if '计划招数' in group_data.columns else None,
            '学费范围': (
                int(group_data['学费'].min()),
                int(group_data['学费'].max())
            ) if '学费' in group_data.columns and group_data['学费'].notna().any() else None,
        }

    def get_school_major_groups(
        self,
        school_name: str,
        category: str
    ) -> pd.DataFrame:
        """
        获取某院校某科类的所有专业组

        Args:
            school_name: 院校名称
            category: 科类（物理/历史）

        Returns:
            专业组列表DataFrame
        """
        if self.enrollment_data is None:
            return pd.DataFrame()

        query = (
            (self.enrollment_data['院校名称'] == school_name) &
            (self.enrollment_data['科类'] == category)
        )

        school_data = self.enrollment_data[query]

        if school_data.empty:
            return pd.DataFrame()

        # 按专业组聚合
        grouped = school_data.groupby('专业组代码').agg({
            '专业名称': lambda x: list(x),
            '计划招数': 'sum',
            '选科要求': 'first',
            '批次': 'first'
        }).reset_index()

        grouped['专业数量'] = grouped['专业名称'].apply(len)
        grouped['院校名称'] = school_name
        grouped['科类'] = category

        return grouped

    def get_statistics(self) -> Dict:
        """获取招生计划统计信息"""
        if self.enrollment_data is None:
            return {'error': '未加载招生计划数据'}

        return {
            'total_records': len(self.enrollment_data),
            'schools_count': self.enrollment_data['院校名称'].nunique(),
            'major_groups_count': self.enrollment_data.groupby(
                ['院校名称', '专业组代码']
            ).ngroups,
            'physics_count': len(self.enrollment_data[self.enrollment_data['科类'] == '物理']),
            'history_count': len(self.enrollment_data[self.enrollment_data['科类'] == '历史']),
            'total_quota': int(self.enrollment_data['计划招数'].sum()) if '计划招数' in self.enrollment_data.columns else 0
        }

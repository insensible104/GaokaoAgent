"""处理2025年招生计划Excel文件
将多层嵌套表格转换为系统可用的格式
"""
import pandas as pd
import numpy as np
from pathlib import Path


def process_enrollment_plan(input_file: str, output_dir: str = "data"):
    """
    处理广东省2025年夏季高考专家版Excel文件

    表格结构：
    - 列1-14: 2025年招生计划
    - 列15-23: 2024年历史数据
    - 列24-26: 2023年历史数据
    - 列27-29: 2022年历史数据
    - 列30-32: 2021年历史数据

    Args:
        input_file: Excel文件路径
        output_dir: 输出目录
    """
    print(f"[INFO] 读取文件: {input_file}")

    # 读取Excel，跳过前2行标题
    df = pd.read_excel(input_file, sheet_name='专家版', skiprows=2)

    print(f"[INFO] 原始数据: {len(df)} 行 x {len(df.columns)} 列")

    # 列名映射（根据实际位置）
    col_mapping = {
        # 2025年招生计划 (0-13)
        0: '院校代码',
        1: '院校名称',
        2: '批次',
        3: '招生备注',
        4: '科类',
        5: '专业组代码',
        6: '专业序号',
        7: '专业名称',
        8: '专业备注',
        9: '语种要求',
        10: '选科要求',
        11: '计划招数',
        12: '学制',
        13: '学费',
        # 2024年历史数据 (14-22)
        17: '2024_最低分',
        18: '2024_最低位次',
        # 2023年历史数据 (23-25)
        24: '2023_最低分',
        25: '2023_最低位次',
        # 2022年历史数据 (26-28)
        27: '2022_最低分',
        28: '2022_最低位次',
        # 2021年历史数据 (29-31)
        30: '2021_最低分',
        31: '2021_最低位次',
    }

    # 创建新的DataFrame，只保留需要的列
    data_dict = {}
    for idx, new_name in col_mapping.items():
        if idx < len(df.columns):
            data_dict[new_name] = df.iloc[:, idx]

    df_clean = pd.DataFrame(data_dict)

    # 数据清洗
    print("[INFO] 数据清洗中...")

    # 1. 删除空行
    df_clean = df_clean.dropna(subset=['院校代码', '院校名称', '专业名称'])

    # 2. 规范科类字段
    df_clean['科类'] = df_clean['科类'].str.strip()
    df_clean = df_clean[df_clean['科类'].isin(['物理', '历史'])]

    # 3. 转换数值字段
    numeric_cols = ['院校代码', '专业组代码', '专业序号', '计划招数', '学制', '学费',
                    '2024_最低分', '2024_最低位次', '2023_最低分', '2023_最低位次',
                    '2022_最低分', '2022_最低位次', '2021_最低分', '2021_最低位次']

    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    # 4. 填充缺失的历史数据为NaN（保持原样）
    # 不做填充，保留原始的NaN值表示该年份无数据

    print(f"[OK] 清洗后数据: {len(df_clean)} 行")

    # 统计信息
    print("\n=== 数据统计 ===")
    print(f"院校数量: {df_clean['院校名称'].nunique()}")
    print(f"专业组数量: {df_clean.groupby(['院校代码', '专业组代码']).ngroups}")
    print(f"科类分布:")
    print(df_clean['科类'].value_counts())

    # 按科类分别保存（用于系统快速查询）
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    for category in ['物理', '历史']:
        df_category = df_clean[df_clean['科类'] == category]
        filename = f"2025_enrollment_{category}.csv"
        filepath = output_path / filename
        df_category.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"[OK] 保存: {filepath} ({len(df_category)} 行)")

    # 同时保存完整数据
    full_filepath = output_path / "2025_enrollment_full.csv"
    df_clean.to_csv(full_filepath, index=False, encoding='utf-8-sig')
    print(f"[OK] 保存: {full_filepath} ({len(df_clean)} 行)")

    return df_clean


def analyze_major_groups(df: pd.DataFrame):
    """分析专业组结构"""
    print("\n=== 专业组分析 ===")

    # 按专业组聚合
    grouped = df.groupby(['院校代码', '院校名称', '科类', '专业组代码']).agg({
        '专业名称': lambda x: list(x),  # 该专业组包含的所有专业
        '计划招数': 'sum',  # 总招生人数
        '2024_最低位次': 'mean',  # 2024年平均最低位次
        '2023_最低位次': 'mean',  # 2023年平均最低位次
        '2022_最低位次': 'mean',  # 2022年平均最低位次
        '2021_最低位次': 'mean',  # 2021年平均最低位次
    }).reset_index()

    grouped['专业数量'] = grouped['专业名称'].apply(len)

    print(f"专业组总数: {len(grouped)}")
    print(f"平均每组专业数: {grouped['专业数量'].mean():.1f}")
    print(f"最多专业的专业组: {grouped['专业数量'].max()}个专业")

    # 示例：查看物理类专业组
    print("\n物理类专业组示例（前5个）:")
    physics_groups = grouped[grouped['科类'] == '物理'].head(5)
    for _, row in physics_groups.iterrows():
        print(f"  {row['院校名称']} - 专业组{row['专业组代码']} - {row['专业数量']}个专业")
        print(f"    2024年均位次: {row['2024_最低位次']:.0f if pd.notna(row['2024_最低位次']) else 'N/A'}")

    return grouped


if __name__ == "__main__":
    # 处理Excel文件
    input_file = "../广东省2025年夏季高考专家版.xlsx"

    try:
        df = process_enrollment_plan(input_file)
        groups = analyze_major_groups(df)
        print("\n[SUCCESS] 处理完成！")
    except Exception as e:
        print(f"[ERROR] 处理失败: {e}")
        import traceback
        traceback.print_exc()

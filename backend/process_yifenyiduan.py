"""
处理广东省一分一段表数据
提取2021-2025年的物理类和历史类数据
"""
import pandas as pd

def process_yifenyiduan():
    file_path = '../2011-2025广东高考一分一段表.xlsx'

    # 读取Excel文件
    print("[INFO] 正在读取Excel文件...")
    df = pd.read_excel(file_path, sheet_name=0)

    # 重命名列（根据观察到的结构）
    df.columns = ['key_id', 'score', 'count_per_segment', 'cumulative_count',
                  'cumulative_ratio', 'avg_rank', 'year', 'category', 'extra']

    # 删除第一行（列名行）
    df = df.iloc[1:].reset_index(drop=True)

    print(f"[INFO] 原始数据：{len(df)} 行")

    # 筛选年份：2021-2025
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df_filtered = df[(df['year'] >= 2021) & (df['year'] <= 2025)].copy()

    print(f"[INFO] 筛选2021-2025年：{len(df_filtered)} 行")

    # 筛选类别：2021年起广东新高考，理科→物理类，文科→历史类
    def classify_category(cat, year):
        if pd.isna(cat):
            return None
        cat_str = str(cat)

        # 2021年及以后：理科=物理类，文科=历史类
        if year >= 2021:
            if '理' in cat_str or '理科' in cat_str:
                return '物理'
            elif '文' in cat_str or '文科' in cat_str:
                return '历史'
        # 2020年及之前：保持原样（但我们只要2021-2025）
        else:
            if '理' in cat_str or '理科' in cat_str:
                return '理科'
            elif '文' in cat_str or '文科' in cat_str:
                return '文科'

        return None

    df_filtered['category_clean'] = df_filtered.apply(
        lambda row: classify_category(row['category'], row['year']), axis=1
    )
    df_filtered = df_filtered[df_filtered['category_clean'].notna()].copy()

    print(f"[INFO] 筛选物理/历史：{len(df_filtered)} 行")
    print(f"[INFO] 物理类：{len(df_filtered[df_filtered['category_clean']=='物理'])} 行")
    print(f"[INFO] 历史类：{len(df_filtered[df_filtered['category_clean']=='历史'])} 行")

    # 清理数据类型
    df_filtered['score'] = pd.to_numeric(df_filtered['score'], errors='coerce')
    df_filtered['count_per_segment'] = pd.to_numeric(df_filtered['count_per_segment'], errors='coerce')
    df_filtered['cumulative_count'] = pd.to_numeric(df_filtered['cumulative_count'], errors='coerce')
    df_filtered['avg_rank'] = pd.to_numeric(df_filtered['avg_rank'], errors='coerce')

    # 删除缺失值
    df_filtered = df_filtered.dropna(subset=['score', 'avg_rank'])

    # 选择需要的列
    df_final = df_filtered[['year', 'category_clean', 'score', 'count_per_segment',
                            'cumulative_count', 'avg_rank']].copy()
    df_final.columns = ['year', 'category', 'score', 'count', 'cumulative_count', 'rank']

    # 按年份和类别分组保存
    for year in range(2021, 2026):
        for category in ['物理', '历史']:
            df_subset = df_final[(df_final['year'] == year) & (df_final['category'] == category)]

            if len(df_subset) > 0:
                # 按分数降序排序
                df_subset = df_subset.sort_values('score', ascending=False)

                output_file = f'data/{year}_{category}_yifenyiduan.csv'
                df_subset.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f"[OK] 保存: {output_file} ({len(df_subset)} 行)")

    print("\n[OK] 处理完成！")

    # 统计摘要
    print("\n=== 数据摘要 ===")
    summary = df_final.groupby(['year', 'category']).agg({
        'score': ['min', 'max', 'count']
    }).reset_index()
    print(summary)

if __name__ == '__main__':
    process_yifenyiduan()

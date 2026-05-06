"""调剂模拟器（剩饭算法）"""
import pandas as pd
from typing import List, Dict, Optional


def simulate_adjustment(
    engine,  # GaokaoQuantEngine实例
    user_rank: int,
    school: str,
    major_group: str,
    blacklist: List[str]
) -> Dict:
    """
    调剂地狱模拟器（剩饭算法）

    逻辑：
    1. 找出同组所有专业
    2. 按历史位次排序
    3. 计算"最差会掉到哪里"
    4. 检查是否命中黑名单

    Args:
        engine: 量化引擎实例
        user_rank: 用户位次
        school: 院校名称
        major_group: 专业组代码
        blacklist: 黑名单专业关键词列表

    Returns:
        {
            'worst_case_major': '最差专业名',
            'is_blacklist_risk': True/False,
            'adjustment_prob': 0.3
        }
    """
    # 1. 查找同组所有专业
    latest_year = engine.df['year'].max()
    group_data = engine.df[
        (engine.df['school'] == school) &
        (engine.df['year'] == latest_year)
    ]

    # 如果有专业组信息，则按专业组筛选
    if 'major_group' in group_data.columns and major_group and major_group != '未分组':
        group_data = group_data[group_data['major_group'] == major_group]

    if group_data.empty:
        return {
            'worst_case_major': None,
            'is_blacklist_risk': False,
            'adjustment_prob': 0.0
        }

    # 2. 按历史位次排序（位次越大越容易进）
    sorted_majors = group_data.sort_values('min_rank', ascending=False)

    # 3. 找到第一个用户位次能进的专业（最差情况）
    worst_major = None
    for _, row in sorted_majors.iterrows():
        if user_rank <= row['min_rank'] * 1.2:  # 留20%余量
            worst_major = row['major']
            break

    # 如果没找到，取组内最低要求的专业
    if worst_major is None and len(sorted_majors) > 0:
        worst_major = sorted_majors.iloc[0]['major']

    # 4. 检查是否命中黑名单
    is_blacklist = False
    if worst_major and blacklist:
        for keyword in blacklist:
            if keyword in worst_major:
                is_blacklist = True
                break

    # 5. 估算调剂概率（简化版）
    # 实际应该基于历史调剂数据，这里用启发式规则
    total_majors = len(group_data)
    # 修复问题9：添加边界检查，防止除零
    if total_majors == 0:
        adjustment_prob = 0.0  # 没有专业数据，无法计算
    elif total_majors == 1:
        adjustment_prob = 0.0  # 只有一个专业，无调剂风险
    else:
        # 专业越多，调剂概率越高
        adjustment_prob = min(0.5, (total_majors - 1) / total_majors * 0.6)

    return {
        'worst_case_major': worst_major,
        'is_blacklist_risk': is_blacklist,
        'adjustment_prob': float(adjustment_prob)
    }


def check_major_blacklist(major: str, blacklist: List[str]) -> bool:
    """
    检查专业是否在黑名单中

    Args:
        major: 专业名称
        blacklist: 黑名单关键词列表

    Returns:
        是否命中黑名单
    """
    if not blacklist:
        return False

    for keyword in blacklist:
        if keyword.lower() in major.lower():
            return True

    return False

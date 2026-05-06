"""基于Deep Research的动态专业质量评估

核心思想：
1. 现有的专业质量评分（S/A/B/C/D）是静态的、基于经验的
2. 使用Deep Research进行多步调研，动态获取最新的专业评价
3. 结合历史录取位次数据，验证评分是否合理

使用场景：
- 当用户对某个专业质量有疑问时，启动Deep Research
- 定期更新专业质量数据库（如每年高考后）
- 对于新兴专业（如AI、大数据），动态查询最新就业情况
"""

from typing import Dict, List, Optional
import pandas as pd


async def research_major_quality(
    school_name: str,
    major_name: str,
    engine: 'GaokaoQuantEngine'
) -> Dict:
    """
    使用Deep Research调研专业质量

    调研维度：
    1. 就业数据：毕业生就业率、平均薪资、Top企业录用率
    2. 学科评估：教育部学科评估结果（A+/A/A-/B+等）
    3. 社会舆情：知乎、小红书、微博等平台对该专业的评价
    4. 历史位次：该专业历年录取位次变化（反映热度）

    Args:
        school_name: 学校名称
        major_name: 专业名称
        engine: 量化引擎（用于获取历史数据）

    Returns:
        {
            'employment_score': 就业评分（0-100）,
            'discipline_score': 学科评估分（0-100）,
            'sentiment_score': 舆情评分（0-100）,
            'rank_trend': 位次趋势（'rising'/'stable'/'declining'),
            '综合评分': 0-100,
            'research_sources': [搜索来源列表]
        }
    """
    # NOTE: 深度研究功能（Slow Loop集成）- 当前返回模拟数据
    # 完整实现需要调用 Deep Research Agent（见 subgraphs/deep_research.py）
    # 1. 构建研究问题
    research_queries = [
        f"{school_name}{major_name}就业情况",
        f"{school_name}{major_name}学科评估",
        f"{major_name}专业前景 知乎",
        f"{school_name}{major_name}毕业生薪资"
    ]

    # 2. 调用Tavily搜索（或Slow Loop）
    # research_results = await slow_loop_research(research_queries)

    # 3. 分析历史录取位次趋势
    rank_trend = await analyze_rank_trend(
        school_name, major_name, engine
    )

    # 暂时返回模拟数据
    return {
        'employment_score': 85.0,
        'discipline_score': 90.0,
        'sentiment_score': 80.0,
        'rank_trend': rank_trend,
        'comprehensive_score': 85.0,
        'research_sources': research_queries
    }


async def analyze_rank_trend(
    school_name: str,
    major_name: str,
    engine: 'GaokaoQuantEngine'
) -> str:
    """
    分析历年录取位次趋势（反映专业热度变化）

    Args:
        school_name: 学校名称
        major_name: 专业名称
        engine: 量化引擎

    Returns:
        'rising' | 'stable' | 'declining'
    """
    # 获取历史数据
    try:
        hist_data = engine.get_school_major_history(
            school=school_name,
            major=major_name
        )

        if hist_data.empty or len(hist_data) < 2:
            return 'stable'  # 数据不足，默认稳定

        # 计算位次变化趋势
        ranks = hist_data['min_rank'].values
        years = hist_data['year'].values

        # 简单线性趋势（最近3年）
        recent_ranks = ranks[-3:]
        if len(recent_ranks) < 2:
            return 'stable'

        # 计算趋势
        # 位次变小 = 录取分数线上升 = 专业热度上升
        avg_change = (recent_ranks[-1] - recent_ranks[0]) / len(recent_ranks)

        if avg_change < -500:  # 位次显著下降（热度上升）
            return 'rising'
        elif avg_change > 500:  # 位次显著上升（热度下降）
            return 'declining'
        else:
            return 'stable'

    except Exception as e:
        print(f"[WARN] 位次趋势分析失败: {e}")
        return 'stable'


def adjust_major_quality_by_research(
    base_quality_score: float,
    research_result: Dict
) -> float:
    """
    根据Deep Research结果调整专业质量评分

    Args:
        base_quality_score: 基础评分（来自静态数据库）
        research_result: Deep Research结果

    Returns:
        调整后的评分
    """
    # 1. 提取各维度评分
    employment = research_result.get('employment_score', 50)
    discipline = research_result.get('discipline_score', 50)
    sentiment = research_result.get('sentiment_score', 50)
    trend = research_result.get('rank_trend', 'stable')

    # 2. 加权计算动态评分
    dynamic_score = (
        employment * 0.4 +    # 就业占40%
        discipline * 0.3 +    # 学科评估占30%
        sentiment * 0.3       # 舆情占30%
    )

    # 3. 趋势修正
    trend_modifier = {
        'rising': 1.05,     # 热度上升，加5%
        'stable': 1.0,      # 稳定，不变
        'declining': 0.95   # 热度下降，减5%
    }
    dynamic_score *= trend_modifier.get(trend, 1.0)

    # 4. 与基础评分加权平均（70%基础 + 30%动态）
    # 避免完全依赖网络搜索，保持一定稳定性
    final_score = base_quality_score * 0.7 + dynamic_score * 0.3

    return min(100, max(0, final_score))


# === 集成到推荐流程 ===
async def calculate_comprehensive_score_with_research(
    school_name: str,
    major_name: str,
    preference: str,
    engine: 'GaokaoQuantEngine',
    enable_research: bool = False
) -> Dict:
    """
    计算综合评分（可选启用Deep Research）

    Args:
        school_name: 学校名称
        major_name: 专业名称
        preference: 用户偏好策略
        engine: 量化引擎
        enable_research: 是否启用Deep Research

    Returns:
        综合评分结果
    """
    from .school_major_scoring import calculate_comprehensive_score

    # 1. 使用静态数据库计算基础分
    base_result = calculate_comprehensive_score(
        school_name, major_name, preference
    )

    # 2. 如果启用Research，进行动态调整
    if enable_research:
        research_result = await research_major_quality(
            school_name, major_name, engine
        )

        # 调整专业质量评分
        adjusted_major_score = adjust_major_quality_by_research(
            base_result['major_quality_score'],
            research_result
        )

        # 重新计算综合分（使用调整后的专业评分）
        # NOTE: 当前使用简单替换，未来可考虑更复杂的加权融合
        base_result['major_quality_score'] = adjusted_major_score
        base_result['research_adjusted'] = True
        base_result['research_data'] = research_result

    return base_result


if __name__ == "__main__":
    print("=== Deep Research 专业质量评估系统 ===")
    print("\n功能说明：")
    print("1. 基于静态数据库的快速评分（当前已实现）")
    print("2. 基于Deep Research的动态评分（需集成Slow Loop）")
    print("3. 结合历史位次趋势的综合评分")
    print("\n使用场景：")
    print("- 快速推荐：使用静态评分（响应时间<1秒）")
    print("- 精细调研：启用Deep Research（响应时间10-30秒）")
    print("- 定期更新：每年高考后运行一次Deep Research，更新数据库")

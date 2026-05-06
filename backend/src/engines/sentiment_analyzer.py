"""Tavily 舆情位次修正模块

使用 Tavily Search API + LLM 情感分析，根据网络舆情修正录取位次预测。

核心逻辑：
1. 使用 Tavily 搜索学校/专业相关信息
2. LLM 分析舆情倾向（正面/负面/中性）
3. 计算情感得分（-1.0 到 1.0）
4. 转换为位次修正值（sentiment_modifier）

应用规则：
- 正面舆情（如排名上升、就业好）-> 位次下降（min_rank 减小）-> 更难录取
- 负面舆情（如丑闻、排名下跌）-> 位次上升（min_rank 增大）-> 更容易录取
- 中性舆情 -> 不修正
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults

from utils.llm_factory import get_llm


class SentimentScore(BaseModel):
    """情感分析结果"""
    sentiment: str = Field(
        description="情感倾向：positive / negative / neutral"
    )
    score: float = Field(
        ge=-1.0, le=1.0,
        description="情感得分（-1.0 = 极度负面，0.0 = 中性，1.0 = 极度正面）"
    )
    reasoning: str = Field(description="分析理由")
    key_factors: List[str] = Field(
        default_factory=list,
        description="关键因素（如'排名上升'、'就业率下降'等）"
    )


class SentimentModifierResult(BaseModel):
    """舆情修正结果"""
    school_name: str = Field(description="学校名称")
    major_name: Optional[str] = Field(default=None, description="专业名称")
    sentiment_score: float = Field(
        ge=-1.0, le=1.0,
        description="情感得分"
    )
    rank_modifier: float = Field(
        description="位次修正值（正数=位次上升=更容易录取，负数=位次下降=更难录取）"
    )
    explanation: str = Field(description="修正解释")
    search_results_summary: str = Field(description="搜索结果摘要")


# === Prompt Templates ===
SENTIMENT_ANALYSIS_PROMPT = """你是一个高考志愿填报领域的舆情分析专家。请分析以下搜索结果，判断网络舆情对该学校/专业的录取热度的影响。

## 分析目标
学校：{school_name}
专业：{major_name}

## 搜索结果
{search_results}

## 任务
分析上述搜索结果中的舆情倾向，判断该学校/专业的社会认可度和报考热度的变化趋势。

## 情感得分标准
- **+1.0（极度正面）**：
  - 学科评估等级大幅提升（如从 B+ 升至 A）
  - 排名大幅上升（如 QS/软科排名提升 50+ 位）
  - 重大利好消息（如获得国家重点实验室、大额科研经费）
  - 就业率/薪资水平显著提升

- **+0.5（正面）**：
  - 排名小幅上升（10-50 位）
  - 获得省级/校级荣誉
  - 媒体正面报道增加
  - 学科建设取得进展

- **0.0（中性）**：
  - 没有明显变化
  - 只有常规新闻（如招生简章、校园活动）
  - 正面和负面消息相互抵消

- **-0.5（负面）**：
  - 排名小幅下降
  - 负面新闻（如教学事故、学生投诉）
  - 就业率/认可度下降

- **-1.0（极度负面）**：
  - 学科评估等级大幅下降
  - 排名大幅下跌
  - 重大丑闻（如学术造假、招生舞弊）
  - 专业被撤销或停招

## 关键因素识别
请列出 2-4 个关键因素（如"软科排名上升 30 位"、"第五轮学科评估 A-"、"就业率下降 5%"）

## 注意事项
1. **区分时效性**：优先考虑 2024-2025 年的最新消息，历史消息权重较低
2. **区分信源可信度**：官方消息（教育部、学校官网）> 主流媒体 > 社交媒体
3. **量化优先**：具体数字（如排名、评级）比模糊评价（如"很好"）更重要
4. **综合判断**：不要只看单一消息，需要综合多个来源

现在请分析并给出情感得分。
"""


def search_school_sentiment(
    school_name: str,
    major_name: Optional[str] = None,
    max_results: int = 5
) -> List[Dict]:
    """
    使用 Tavily 搜索学校/专业相关舆情

    Args:
        school_name: 学校名称
        major_name: 专业名称（可选）
        max_results: 最大搜索结果数

    Returns:
        搜索结果列表
    """
    # 检查 Tavily API Key
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key or tavily_api_key == "your_tavily_api_key_here":
        print("[WARN] Tavily API Key 未配置，跳过舆情搜索")
        return []

    # 构造搜索查询
    if major_name:
        query = f"{school_name} {major_name} 2024 2025 排名 评价 就业 学科评估"
    else:
        query = f"{school_name} 2024 2025 排名 评价 认可度"

    try:
        search_tool = TavilySearchResults(max_results=max_results)
        results = search_tool.invoke(query)
        return results

    except Exception as e:
        print(f"[ERROR] Tavily 搜索失败: {e}")
        return []


def analyze_sentiment(
    school_name: str,
    search_results: List[Dict],
    major_name: Optional[str] = None
) -> SentimentScore:
    """
    使用 LLM 分析舆情

    Args:
        school_name: 学校名称
        search_results: Tavily 搜索结果
        major_name: 专业名称（可选）

    Returns:
        SentimentScore 对象
    """
    if not search_results:
        return SentimentScore(
            sentiment="neutral",
            score=0.0,
            reasoning="未找到相关搜索结果",
            key_factors=[]
        )

    # 格式化搜索结果
    formatted_results = ""
    for i, res in enumerate(search_results, 1):
        title = res.get('title', 'No title')
        content = res.get('content', 'No content')
        url = res.get('url', '')
        formatted_results += f"{i}. [{title}]({url})\n{content}\n\n"

    # 调用 LLM 进行情感分析
    llm = get_llm(temperature=0.3)
    structured_llm = llm.with_structured_output(SentimentScore)

    prompt = SENTIMENT_ANALYSIS_PROMPT.format(
        school_name=school_name,
        major_name=major_name or "（全校整体）",
        search_results=formatted_results
    )

    try:
        result: SentimentScore = structured_llm.invoke(prompt)
        return result

    except Exception as e:
        print(f"[ERROR] LLM 情感分析失败: {e}")
        # Fallback：返回中性结果
        return SentimentScore(
            sentiment="neutral",
            score=0.0,
            reasoning=f"分析失败: {e}",
            key_factors=[]
        )


def calculate_rank_modifier(
    sentiment_score: float,
    base_modifier: float = 200.0
) -> float:
    """
    根据情感得分计算位次修正值

    公式：
    rank_modifier = -sentiment_score * base_modifier

    解释：
    - sentiment_score = +1.0（极度正面）-> rank_modifier = -200（位次下降 200 位，更难录取）
    - sentiment_score = 0.0（中性）-> rank_modifier = 0（不修正）
    - sentiment_score = -1.0（极度负面）-> rank_modifier = +200（位次上升 200 位，更容易录取）

    Args:
        sentiment_score: 情感得分（-1.0 到 1.0）
        base_modifier: 基础修正幅度（默认 200 位）

    Returns:
        位次修正值（正数=位次上升=更容易，负数=位次下降=更难）
    """
    return -sentiment_score * base_modifier


def get_sentiment_modifier(
    school_name: str,
    major_name: Optional[str] = None,
    max_search_results: int = 5,
    base_modifier: float = 200.0
) -> SentimentModifierResult:
    """
    一站式舆情修正接口

    Args:
        school_name: 学校名称
        major_name: 专业名称（可选）
        max_search_results: 最大搜索结果数
        base_modifier: 基础修正幅度（默认 200 位）

    Returns:
        SentimentModifierResult 对象
    """
    print(f"[Sentiment] 开始分析舆情: {school_name} {major_name or ''}")

    # 1. 搜索舆情
    search_results = search_school_sentiment(
        school_name=school_name,
        major_name=major_name,
        max_results=max_search_results
    )

    if not search_results:
        print("[Sentiment] 未找到搜索结果，返回中性修正")
        return SentimentModifierResult(
            school_name=school_name,
            major_name=major_name,
            sentiment_score=0.0,
            rank_modifier=0.0,
            explanation="未找到相关舆情信息，不进行修正",
            search_results_summary="无搜索结果"
        )

    # 2. 分析情感
    sentiment = analyze_sentiment(
        school_name=school_name,
        search_results=search_results,
        major_name=major_name
    )

    # 3. 计算修正值
    rank_modifier = calculate_rank_modifier(
        sentiment_score=sentiment.score,
        base_modifier=base_modifier
    )

    # 4. 生成解释
    if sentiment.score > 0.3:
        explanation = (
            f"[正面舆情] {school_name} 近期表现优异，"
            f"预计报考热度上升，录取位次下降 {abs(rank_modifier):.0f} 位"
        )
    elif sentiment.score < -0.3:
        explanation = (
            f"[负面舆情] {school_name} 近期表现欠佳，"
            f"预计报考热度下降，录取位次上升 {abs(rank_modifier):.0f} 位"
        )
    else:
        explanation = f"[中性舆情] {school_name} 无明显舆情变化，不进行修正"

    # 5. 生成搜索结果摘要
    summary_parts = []
    for i, res in enumerate(search_results[:3], 1):
        title = res.get('title', '')
        summary_parts.append(f"{i}. {title}")
    search_results_summary = "\n".join(summary_parts)

    print(f"[Sentiment] 情感得分: {sentiment.score:.2f}")
    print(f"[Sentiment] 位次修正: {rank_modifier:+.0f} 位")

    return SentimentModifierResult(
        school_name=school_name,
        major_name=major_name,
        sentiment_score=sentiment.score,
        rank_modifier=rank_modifier,
        explanation=explanation,
        search_results_summary=search_results_summary
    )


def batch_get_sentiment_modifiers(
    candidates: List[Dict],
    max_search_results: int = 5,
    base_modifier: float = 200.0
) -> Dict[str, float]:
    """
    批量获取舆情修正值（用于 45 个志愿）

    Args:
        candidates: 候选志愿列表，每个元素包含：
            {
                'school_name': str,
                'major_name': str
            }
        max_search_results: 最大搜索结果数
        base_modifier: 基础修正幅度

    Returns:
        Dict[school_major_key, rank_modifier]
    """
    modifiers = {}

    for candidate in candidates:
        school_name = candidate.get('school_name', '')
        major_name = candidate.get('major_name', '')

        if not school_name:
            continue

        key = f"{school_name}_{major_name}"

        try:
            result = get_sentiment_modifier(
                school_name=school_name,
                major_name=major_name,
                max_search_results=max_search_results,
                base_modifier=base_modifier
            )
            modifiers[key] = result.rank_modifier

        except Exception as e:
            print(f"[WARN] 舆情分析失败: {school_name} {major_name} - {e}")
            modifiers[key] = 0.0  # Fallback

    return modifiers


# === 测试代码 ===
if __name__ == "__main__":
    import sys

    # 测试：中山大学计算机
    print("=== Tavily 舆情位次修正测试 ===\n")

    # 检查 Tavily API Key
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key or tavily_key == "your_tavily_api_key_here":
        print("[ERROR] 请先在 .env 文件中配置 TAVILY_API_KEY")
        print("获取 API Key: https://tavily.com/")
        sys.exit(1)

    # 测试 1：单个学校/专业
    print("测试 1：中山大学 计算机科学与技术")
    result = get_sentiment_modifier(
        school_name="中山大学",
        major_name="计算机科学与技术",
        max_search_results=5,
        base_modifier=200.0
    )

    print(f"\n情感得分: {result.sentiment_score:.2f}")
    print(f"位次修正: {result.rank_modifier:+.0f} 位")
    print(f"解释: {result.explanation}")
    print(f"\n搜索结果摘要:\n{result.search_results_summary}")
    print("\n" + "="*50 + "\n")

    # 测试 2：批量处理
    print("测试 2：批量处理（3 个志愿）")
    test_candidates = [
        {'school_name': '清华大学', 'major_name': '计算机科学与技术'},
        {'school_name': '北京大学', 'major_name': '软件工程'},
        {'school_name': '浙江大学', 'major_name': '人工智能'}
    ]

    modifiers = batch_get_sentiment_modifiers(
        candidates=test_candidates,
        max_search_results=3,
        base_modifier=150.0
    )

    print("\n批量修正结果:")
    for key, modifier in modifiers.items():
        print(f"  {key}: {modifier:+.0f} 位")

    print("\n测试完成！")

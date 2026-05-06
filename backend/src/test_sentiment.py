"""测试舆情分析模块（Mock 版本，不需要 Tavily API Key）"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engines.sentiment_analyzer import (
    calculate_rank_modifier,
    SentimentScore,
    analyze_sentiment
)


def test_calculate_rank_modifier():
    """测试位次修正值计算"""
    print("=== 测试位次修正值计算 ===\n")

    # 测试 1：极度正面舆情
    modifier1 = calculate_rank_modifier(sentiment_score=1.0, base_modifier=200.0)
    print(f"极度正面舆情（+1.0）: {modifier1:+.0f} 位（应为 -200）")
    assert modifier1 == -200.0

    # 测试 2：中性舆情
    modifier2 = calculate_rank_modifier(sentiment_score=0.0, base_modifier=200.0)
    print(f"中性舆情（0.0）: {modifier2:+.0f} 位（应为 0）")
    assert modifier2 == 0.0

    # 测试 3：极度负面舆情
    modifier3 = calculate_rank_modifier(sentiment_score=-1.0, base_modifier=200.0)
    print(f"极度负面舆情（-1.0）: {modifier3:+.0f} 位（应为 +200）")
    assert modifier3 == 200.0

    # 测试 4：轻微正面舆情
    modifier4 = calculate_rank_modifier(sentiment_score=0.5, base_modifier=200.0)
    print(f"轻微正面舆情（+0.5）: {modifier4:+.0f} 位（应为 -100）")
    assert modifier4 == -100.0

    print("\n所有测试通过！\n")


def test_sentiment_logic():
    """测试舆情分析逻辑（不调用 LLM）"""
    print("=== 测试舆情分析逻辑 ===\n")

    # Mock 搜索结果
    mock_positive_results = [
        {
            'title': '清华大学计算机学科评估 A+，全国第一',
            'content': '第五轮学科评估中，清华大学计算机科学与技术获得 A+ 评级',
            'url': 'https://example.com/1'
        },
        {
            'title': 'QS 排名上升，清华计算机全球前 10',
            'content': '2024 年 QS 计算机学科排名中，清华大学位列全球第 8 位',
            'url': 'https://example.com/2'
        }
    ]

    mock_negative_results = [
        {
            'title': 'XX 大学计算机专业就业率下降',
            'content': '2024 年 XX 大学计算机专业就业率同比下降 10%',
            'url': 'https://example.com/3'
        }
    ]

    print("Mock 正面舆情搜索结果:")
    for i, res in enumerate(mock_positive_results, 1):
        print(f"  {i}. {res['title']}")

    print("\nMock 负面舆情搜索结果:")
    for i, res in enumerate(mock_negative_results, 1):
        print(f"  {i}. {res['title']}")

    print("\n逻辑测试通过！\n")


if __name__ == "__main__":
    test_calculate_rank_modifier()
    test_sentiment_logic()

    print("=== 所有测试完成 ===")
    print("\n提示：如果要测试真实的 Tavily API 调用，")
    print("请在 backend/.env 中配置 TAVILY_API_KEY，")
    print("然后运行: uv run python src/engines/sentiment_analyzer.py")

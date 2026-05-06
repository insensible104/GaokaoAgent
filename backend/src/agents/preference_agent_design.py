"""Agent自主决策：学校-专业权衡系统集成方案

核心理念：
1. Agent应该主动询问用户偏好（而不是假设）
2. Agent应该基于用户需求自主决策
3. Agent应该解释推荐理由（为什么推荐清华材料而不是中国海洋计算机）
4. Agent应该处理冲突场景（如"冲学校"与"保专业"的矛盾）
"""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


# === 1. 扩展用户画像，添加学校-专业偏好 ===
class SchoolMajorPreference(str, Enum):
    """学校-专业权衡偏好"""
    PRIORITIZE_SCHOOL = "prioritize_school"   # 优先选择好学校（可接受冷门专业）
    BALANCED = "balanced"                     # 学校和专业兼顾
    PRIORITIZE_MAJOR = "prioritize_major"     # 优先选择好专业（可接受学校降档）
    UNKNOWN = "unknown"                       # 用户未明确（需要Agent询问）


class UserProfileExtended(BaseModel):
    """扩展的用户画像（添加学校-专业偏好）"""
    # ... 原有字段（score, rank, subject_group等）...

    # 新增：学校-专业权衡偏好
    school_major_preference: SchoolMajorPreference = SchoolMajorPreference.UNKNOWN

    # 新增：专业优先级（用户自己排序的专业重要性）
    major_priority_list: Optional[List[str]] = Field(
        default=None,
        description="用户专业优先级排序，如 ['计算机', '金融', '电子信息']"
    )

    # 新增：学校层级底线（用户可接受的最低学校档次）
    min_acceptable_school_tier: Optional[str] = Field(
        default=None,
        description="最低可接受的学校档次，如 'top985'"
    )


# === 2. Agent主动询问用户偏好（Profile Agent扩展）===
PREFERENCE_QUESTIONS = {
    "school_major_preference": {
        "question": "在填报志愿时，您更看重学校名气还是专业质量？",
        "options": [
            {
                "label": "优先选好学校（可以接受冷门专业）",
                "value": SchoolMajorPreference.PRIORITIZE_SCHOOL,
                "explanation": "例如：宁愿去清华学材料，也不去普通985学计算机"
            },
            {
                "label": "学校和专业兼顾（平衡型）",
                "value": SchoolMajorPreference.BALANCED,
                "explanation": "例如：会综合考虑学校档次和专业质量"
            },
            {
                "label": "优先选好专业（可以接受学校降档）",
                "value": SchoolMajorPreference.PRIORITIZE_MAJOR,
                "explanation": "例如：宁愿去普通211学计算机，也不去末流985学天坑专业"
            }
        ]
    },
    "min_school_tier": {
        "question": "您能接受的最低学校档次是？",
        "options": [
            {"label": "必须是985（含末流985）", "value": "low985"},
            {"label": "可以接受211（含双一流）", "value": "low211"},
            {"label": "只要是一本就行", "value": "normal_1st"},
            {"label": "没有限制", "value": "other"}
        ]
    }
}


# === 3. Game Agent决策逻辑（集成学校-专业评分）===
async def game_agent_with_preference(
    state: 'SupervisorState',
    engine: 'GaokaoQuantEngine'
) -> dict:
    """
    Game Agent节点（增强版）：考虑学校-专业权衡

    决策流程：
    1. 检查用户是否已设置偏好
    2. 如果未设置，返回消息要求Profile Agent询问
    3. 基于用户偏好，计算每个专业组的综合评分
    4. 按综合评分排序，推荐Top 30
    5. 生成推荐理由（解释为什么这样推荐）
    """
    from utils.school_major_scoring import calculate_comprehensive_score

    profile = state["user_profile"]
    if not profile:
        return {"error": "缺少用户画像"}

    # 1. 检查用户偏好
    preference = profile.school_major_preference
    if preference == SchoolMajorPreference.UNKNOWN:
        # Agent自主决策：需要先询问用户偏好
        return {
            "current_agent": "profile_agent",  # 回到Profile Agent询问
            "messages": [
                AIMessage(
                    content="在为您推荐专业前，我需要了解您的偏好：\\n\\n"
                            "您更看重学校名气还是专业质量？\\n"
                            "1. 优先选好学校（可以接受冷门专业）\\n"
                            "2. 学校和专业兼顾\\n"
                            "3. 优先选好专业（可以接受学校降档）"
                )
            ]
        }

    # 2. 搜索候选专业组
    major_groups = engine.search_major_groups(
        user_rank=profile.rank,
        subject_group=profile.subject_group,
        target_count=200
    )

    # 3. 为每个专业组计算综合评分
    scored_groups = []
    for _, group in major_groups.iterrows():
        school = group['school']
        major_list = group['major']  # List[str]

        # 对每个专业计算综合评分，取平均值
        major_scores = []
        for major in major_list[:6]:  # 最多6个专业
            score_result = calculate_comprehensive_score(
                school_name=school,
                major_name=major,
                preference=preference  # 使用用户偏好
            )
            major_scores.append(score_result['comprehensive_score'])

        # 该专业组的综合评分 = 各专业平均分
        avg_score = sum(major_scores) / len(major_scores) if major_scores else 0

        scored_groups.append({
            'school': school,
            'major_group': group['major_group'],
            'major_list': major_list,
            'comprehensive_score': avg_score,
            'admission_prob': 0.75,  # NOTE: 设计阶段占位符，实际由蒙特卡洛模拟计算（见game_agent.py）
        })

    # 4. 按综合评分排序（而不是仅按录取概率）
    # Agent自主决策：平衡录取概率和综合评分
    scored_groups.sort(
        key=lambda x: x['comprehensive_score'] * 0.6 + x['admission_prob'] * 0.4,
        reverse=True
    )

    # 5. 分类推荐（冲/稳/保）
    top_30 = scored_groups[:30]
    rush = [g for g in top_30 if g['admission_prob'] < 0.6][:10]
    target = [g for g in top_30 if 0.6 <= g['admission_prob'] < 0.9][:10]
    safe = [g for g in top_30 if g['admission_prob'] >= 0.9][:10]

    # 6. 生成推荐理由（Agent自主解释）
    explanation = generate_recommendation_explanation(
        preference=preference,
        rush_groups=rush,
        target_groups=target,
        safe_groups=safe
    )

    return {
        "game_matrix": create_game_matrix(rush + target + safe),
        "messages": [AIMessage(content=explanation)],
        "current_agent": "game_agent"
    }


def generate_recommendation_explanation(
    preference: SchoolMajorPreference,
    rush_groups: List[Dict],
    target_groups: List[Dict],
    safe_groups: List[Dict]
) -> str:
    """
    Agent自主生成推荐理由

    Args:
        preference: 用户偏好
        rush_groups: 冲刺组
        target_groups: 稳妥组
        safe_groups: 保底组

    Returns:
        推荐理由文本
    """
    if preference == SchoolMajorPreference.PRIORITIZE_SCHOOL:
        strategy_desc = "根据您'优先选好学校'的偏好，我为您优先推荐了名校的专业组，即使部分专业可能相对冷门，但学校平台优势明显。"
    elif preference == SchoolMajorPreference.PRIORITIZE_MAJOR:
        strategy_desc = "根据您'优先选好专业'的偏好，我为您优先推荐了热门专业（如计算机、金融），即使学校档次可能略低，但专业就业前景好。"
    else:
        strategy_desc = "根据您'学校专业兼顾'的偏好，我为您平衡推荐了学校档次和专业质量都不错的选项。"

    # 举例说明（拿最高分的冲刺组举例）
    if rush_groups:
        top_rush = rush_groups[0]
        example = f"\\n\\n例如，推荐的冲刺院校 {top_rush['school']}（综合评分 {top_rush['comprehensive_score']:.1f}），虽然录取概率约 {top_rush['admission_prob']:.0%}，但综合考虑学校平台和专业质量后，是值得冲刺的目标。"
    else:
        example = ""

    explanation = f"""
已为您生成30个专业组推荐（冲{len(rush_groups)} + 稳{len(target_groups)} + 保{len(safe_groups)}）

{strategy_desc}{example}

您可以查看详细的博弈矩阵，或告诉我调整偏好重新推荐。
"""
    return explanation.strip()


# === 4. 用户交互场景示例 ===
INTERACTION_SCENARIOS = '''
场景1：用户未明确偏好
User: "我是物理类考生，620分，位次12000，帮我推荐志愿"
Agent: "好的！在为您推荐前，我需要了解：您更看重学校名气还是专业质量？
        1. 优先选好学校（可以接受冷门专业，如清华材料）
        2. 学校和专业兼顾
        3. 优先选好专业（可以接受学校降档，如211的计算机）"
User: "我选2，兼顾"
Agent: "明白了！基于您的偏好，我会平衡推荐..."

场景2：用户对推荐有疑问
User: "为什么推荐清华材料而不是中国海洋计算机？"
Agent: "根据综合评分：
        - 清华材料：88分（学校100分×50% + 专业20分×50% + 平台加成28分）
        - 中国海洋计算机：87.5分（学校75分×50% + 专业100分×50%）

        虽然计算机专业质量更高，但清华的平台优势（保研率、就业背书、校友资源）
        使得即使是冷门专业，综合价值也略高。当然，如果您更看重专业，我可以调整
        推荐策略，为您推荐更多好专业的选择。"

场景3：用户要求调整
User: "能不能多推荐一些计算机相关的专业？"
Agent: "当然可以！我会调整策略，增加计算机相关专业的权重..."
[Agent自主决策：调整专业质量权重，重新排序]

场景4：冲突场景
User: "我想去985，但只想学计算机"
Agent: "我理解您的需求。但根据您的位次（12000），985的计算机录取概率较低（约30%）。
        我有两个建议方案：

        方案A（冲刺型）：多填报985的计算机（冲刺），同时配置211的计算机（保底）
        方案B（稳妥型）：选择985的电子信息、自动化等相关专业（录取概率70%+）

        您倾向于哪个方案？"
'''


if __name__ == "__main__":
    print("=== Agent自主决策：学校-专业权衡系统 ===\\n")
    print("核心功能：")
    print("1. ✅ 主动询问用户偏好（而不是假设）")
    print("2. ✅ 基于用户需求自主决策推荐策略")
    print("3. ✅ 解释推荐理由（透明化决策过程）")
    print("4. ✅ 处理冲突场景（如'只想去985学计算机'但位次不够）")
    print("\\n交互示例：")
    print(INTERACTION_SCENARIOS)

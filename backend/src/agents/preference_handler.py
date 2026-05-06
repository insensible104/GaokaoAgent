"""偏好选择处理节点"""
from langchain_core.messages import AIMessage, HumanMessage

from models.state import SupervisorState
from models.user_profile import SchoolMajorPreference
from utils.constants import PREFERENCE_MAP  # 修复：使用统一的常量定义


def handle_preference_response(state: SupervisorState) -> dict:
    """
    处理用户对学校-专业偏好问题的回复

    检测用户是否回复了1/2/3，并更新user_profile
    """
    profile = state.get("user_profile")

    # 如果已经设置了偏好，直接跳过
    if not profile or profile.school_major_preference != SchoolMajorPreference.UNKNOWN:
        return {}

    # 获取最新的用户消息
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_message = messages[-1]
    if not hasattr(last_message, 'type') or last_message.type != 'human':
        return {}

    user_response = last_message.content.strip()

    # 修复：使用统一的PREFERENCE_MAP替代局部定义
    # 查找匹配
    selected_preference = None
    for key, pref in PREFERENCE_MAP.items():
        if key in user_response:
            selected_preference = pref
            break

    if selected_preference:
        # 更新用户画像
        profile.school_major_preference = selected_preference

        preference_desc = {
            SchoolMajorPreference.PRIORITIZE_SCHOOL: "优先选好学校",
            SchoolMajorPreference.BALANCED: "学校和专业兼顾",
            SchoolMajorPreference.PRIORITIZE_MAJOR: "优先选好专业"
        }

        print(f"[OK] 用户选择了：{preference_desc[selected_preference]}")

        return {
            "user_profile": profile,
            "messages": [AIMessage(content=(
                f"✓ 已记录您的偏好：**{preference_desc[selected_preference]}**\n\n"
                f"正在为您生成推荐方案..."
            ))]
        }

    # 如果无法识别，提示用户重新选择
    return {
        "messages": [AIMessage(content=(
            "抱歉，我没有理解您的选择。请回复数字 **1**、**2** 或 **3**：\n\n"
            "1 - 优先选好学校\n"
            "2 - 学校和专业兼顾\n"
            "3 - 优先选好专业"
        ))]
    }

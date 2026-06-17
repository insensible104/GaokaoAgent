"""Agent 1: 画像挖掘智能体（简化版）"""
import os
import re
from langchain_core.messages import AIMessage, HumanMessage

from models.state import SupervisorState
from models.user_profile import HollandCode, UserProfile, RiskTolerance, SchoolMajorPreference
from prompts.profiling import profiling_system_prompt, profiling_user_prompt
from utils import get_llm
from utils.agent_bus import publish_agent_message, remember
from utils.validator import UserInputValidator
from utils.constants import PREFERENCE_MAP  # 修复：使用统一的常量定义


def _append_unique(values: list, item: str) -> None:
    if item and item not in values:
        values.append(item)


_PROFILE_FIELDS = (
    "score",
    "rank",
    "subject_group",
    "preferred_cities",
    "excluded_cities",
    "preferred_majors",
    "blacklist_majors",
    "risk_tolerance",
    "school_major_preference",
    "stated_misconceptions",
    "emotional_concerns",
    "family_pressure_points",
    "preference_assumptions",
    "preference_confidence",
    "major_cognition_risk",
    "regret_sensitivity",
    "medical_restrictions",
    "subject_scores",
    "holland_code",
    "riasec_top_codes",
    "career_assessment_mode",
    "career_assessment_status",
    "mbti_type",
    "mbti_source",
    "career_values",
)


def _has_profile_value(value) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def _mark_inferred_provenance(profile: UserProfile) -> UserProfile:
    for field_name in _PROFILE_FIELDS:
        if field_name not in profile.field_provenance and _has_profile_value(
            getattr(profile, field_name, None)
        ):
            profile.field_provenance[field_name] = "inferred"
    return profile


def merge_explicit_profile(
    inferred_profile: UserProfile,
    explicit_profile: dict | None,
) -> UserProfile:
    """Overlay user-stated fields while retaining inferred fields not explicitly supplied."""
    profile = _mark_inferred_provenance(inferred_profile.model_copy(deep=True))
    if not explicit_profile:
        return profile

    provenance_overrides = explicit_profile.get("_field_provenance", {})
    for field_name in _PROFILE_FIELDS:
        if field_name not in explicit_profile or explicit_profile[field_name] is None:
            continue
        value = explicit_profile[field_name]
        if field_name == "risk_tolerance":
            value = RiskTolerance(value)
        elif field_name == "school_major_preference":
            value = SchoolMajorPreference(value)
        elif field_name == "holland_code" and isinstance(value, dict):
            value = HollandCode(**value)
        elif isinstance(value, (list, dict)):
            value = value.copy()
        setattr(profile, field_name, value)
        profile.field_provenance[field_name] = provenance_overrides.get(
            field_name,
            "user_explicit",
        )
    return profile


def _enrich_behavioral_profile(profile: UserProfile, user_text: str) -> UserProfile:
    """Add deterministic behavioral signals when the LLM extraction is sparse."""
    text = user_text or ""
    preferred_blob = " ".join(profile.preferred_majors or [])
    blacklist_blob = " ".join(profile.blacklist_majors or [])

    if any(keyword in text for keyword in ["滑档", "退档", "保底", "稳一点"]):
        _append_unique(profile.emotional_concerns, "fear of sliding or failed admission")
        profile.regret_sensitivity = max(profile.regret_sensitivity, 0.7)

    if any(keyword in text for keyword in ["浪费分", "亏", "捡漏", "割韭菜", "后悔"]):
        _append_unique(profile.emotional_concerns, "fear of wasted rank, being exploited, or future regret")
        profile.regret_sensitivity = max(profile.regret_sensitivity, 0.75)

    if any(keyword in text for keyword in ["爸妈", "父母", "家里", "老师", "亲戚"]):
        _append_unique(profile.family_pressure_points, "family or advisor pressure may affect stated preference")
        profile.preference_confidence = min(profile.preference_confidence, 0.65)

    if any(keyword in preferred_blob + text for keyword in ["计算机", "人工智能", "AI", "金融", "法学", "临床"]):
        _append_unique(
            profile.preference_assumptions,
            "hot major preference may rely on employment narrative rather than verified curriculum fit",
        )
        profile.major_cognition_risk = max(profile.major_cognition_risk, 0.45)

    if blacklist_blob:
        _append_unique(
            profile.preference_assumptions,
            "blacklisted majors must be checked against mixed major-group tail assignment",
        )

    if profile.preferred_majors and not profile.preference_assumptions:
        _append_unique(
            profile.preference_assumptions,
            "major preference is explicit but the underlying tradeoff is not fully verified",
        )
        profile.preference_confidence = min(profile.preference_confidence, 0.75)

    return profile


def assess_recommendation_readiness(profile: UserProfile) -> dict:
    """Check whether a profile can safely enter the formal quant pipeline."""
    missing_fields = []
    has_score = profile.score is not None and profile.score > 0
    has_rank = profile.rank is not None and profile.rank > 0
    if not has_score and not has_rank:
        missing_fields.extend(["score", "rank"])
    if not str(profile.subject_group or "").strip():
        missing_fields.append("subject_group")
    return {
        "ready": not missing_fields,
        "missing_fields": missing_fields,
    }


def _labeled_value(text: str, labels: list[str]) -> str:
    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"(?:^|\n)\s*[-*]?\s*(?:{label_pattern})\s*[：:]\s*([^\n]+)",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def _split_text_list(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[，,、;；\s]+", value) if item.strip()]


def extract_profile_from_text(user_text: str) -> UserProfile:
    """Recover explicit user inputs when the LLM extractor is unavailable."""
    text = user_text or ""
    score_text = _labeled_value(text, ["高考总分", "总分", "分数"])
    rank_text = _labeled_value(text, ["全省位次", "位次", "排名"])
    subject_text = _labeled_value(text, ["选科组合", "选科"])

    score_match = re.search(r"\d+", score_text)
    rank_match = re.search(r"\d+", rank_text)
    if not score_match:
        score_match = re.search(r"(?:高考)?\s*(\d{3})\s*分", text)
    if not rank_match:
        rank_match = re.search(r"(?:位次|排名)\s*[：:]?\s*(\d{1,7})", text)

    subject_group = ""
    subject_source = subject_text or text
    if "物理" in subject_source:
        subject_group = "物理"
    elif "历史" in subject_source:
        subject_group = "历史"

    risk_text = _labeled_value(text, ["风险偏好"])
    if "保守" in risk_text or "conservative" in risk_text.lower():
        risk_tolerance = RiskTolerance.CONSERVATIVE
    elif "激进" in risk_text or "aggressive" in risk_text.lower():
        risk_tolerance = RiskTolerance.AGGRESSIVE
    else:
        risk_tolerance = RiskTolerance.BALANCED

    profile = UserProfile(
        score=int(score_match.group(1) if score_match.lastindex else score_match.group(0)) if score_match else None,
        rank=int(rank_match.group(1) if rank_match.lastindex else rank_match.group(0)) if rank_match else None,
        subject_group=subject_group,
        preferred_majors=_split_text_list(_labeled_value(text, ["偏好专业", "意向专业", "想学的专业"])),
        blacklist_majors=_split_text_list(_labeled_value(text, ["不想学的专业", "黑名单专业"])),
        preferred_cities=_split_text_list(_labeled_value(text, ["偏好城市", "偏好地区"])),
        risk_tolerance=risk_tolerance,
    )
    profile = _enrich_behavioral_profile(profile, text)
    readiness = assess_recommendation_readiness(profile)
    profile.recommendation_ready = readiness["ready"]
    profile.missing_critical_fields = readiness["missing_fields"]
    return profile


def profiling_agent_node(state: SupervisorState) -> dict:
    """
    Profiling Agent 节点（简化版）

    从用户消息中提取关键信息，构建 UserProfile
    包含分数-位次验证逻辑
    """
    print("[Agent 1] Profiling Agent 启动...")

    # === 步骤0：检查是否是用户回复偏好选择 ===
    existing_profile = state.get("user_profile")
    if existing_profile and existing_profile.school_major_preference == SchoolMajorPreference.UNKNOWN:
        # 用户可能在回复偏好问题，尝试解析
        messages = state.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'type') and last_msg.type == 'human':
                user_response = last_msg.content.strip()

                # 修复：使用统一的PREFERENCE_MAP替代局部定义
                for key, pref in PREFERENCE_MAP.items():
                    if key in user_response:
                        existing_profile.school_major_preference = pref
                        preference_desc = {
                            SchoolMajorPreference.PRIORITIZE_SCHOOL: "优先选好学校",
                            SchoolMajorPreference.BALANCED: "学校和专业兼顾",
                            SchoolMajorPreference.PRIORITIZE_MAJOR: "优先选好专业"
                        }
                        print(f"[OK] 用户选择了：{preference_desc[pref]}")
                        return {
                            "user_profile": existing_profile,
                            "current_agent": "profiling_agent",
                            "debug_logs": [f"[OK] 用户偏好已更新：{preference_desc[pref]}"],
                            "messages": [AIMessage(content=(
                                f"✓ 已记录您的偏好：**{preference_desc[pref]}**\n\n"
                                f"正在为您生成推荐方案..."
                            ))]
                        }

    print("[进度] 正在分析用户输入...")

    # 获取用户最初的消息（避免读到 Critic 回退时的消息）
    # 修复：始终读取第一条 HumanMessage，添加安全检查
    first_user_message = None

    # 检查messages是否为空
    if not state.get("messages"):
        raise ValueError("状态中没有消息，无法提取用户画像")

    for msg in state["messages"]:
        if hasattr(msg, 'type') and msg.type == 'human':
            first_user_message = msg
            break

    if not first_user_message:
        # Fallback: 读取第一条消息（已验证非空）
        first_user_message = state["messages"][0]

    user_text = first_user_message.content if hasattr(first_user_message, 'content') else str(first_user_message)

    # 使用 LLM 提取结构化信息
    print("[进度] 正在提取用户画像...")
    prompt = f"""你是数据提取专家，负责从用户输入中提取结构化信息。

用户输入：
{user_text}

请提取以下信息（必须返回有效的整数值）：
- score: 高考总分（整数，如 620；如果未提及则为 null）
- rank: 全省位次（整数，如 10000；如果未提及则为 null）
- subject_group: 选科组合（字符串，物理 或 历史）
- preferred_cities: 偏好城市（列表，如果未提及则为空列表 []）
- preferred_majors: 意向专业（列表，提取关键词如 ["计算机"]）
- blacklist_majors: 不想学的专业（列表，如果未提及则为空列表 []）
- risk_tolerance: 风险偏好（字符串，conservative/balanced/aggressive，默认 balanced）

重要提示：
1. 如果用户明确提到分数或位次，必须提取准确的数字
2. 如果用户没有提到某个字段，score和rank可以为null，其他字段使用默认值
3. 返回标准 JSON 格式

示例：
输入："我620分，位次10000，物理类，想学计算机"
输出：{{"score": 620, "rank": 10000, "subject_group": "物理", "preferred_majors": ["计算机"]}}

输入："我位次12000，选历史"
输出：{{"score": null, "rank": 12000, "subject_group": "历史"}}
"""

    prompt += """

Additional behavioral fields to extract:
- stated_misconceptions: possible wrong assumptions in the request.
- emotional_concerns: worries such as sliding, wasting rank, being exploited, or family conflict.
- family_pressure_points: family, teacher, or peer pressure signals.
- preference_assumptions: unverified assumptions behind school, major, city, or career choices.
- preference_confidence: float in [0,1]; lower when preference looks unstable or externally pressured.
- major_cognition_risk: float in [0,1]; higher when the user may misunderstand curriculum, career path, or mixed major groups.
- regret_sensitivity: float in [0,1]; higher when the user cares strongly about ex-post regret and justified envy.
"""

    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(UserProfile)
        profile = structured_llm.invoke(prompt)

        reasoning_process = []

        # 规范化选科组合：提取主选科（物理/历史）
        if profile.subject_group:
            if '物理' in profile.subject_group or '物' in profile.subject_group:
                profile.subject_group = '物理'
            elif '历史' in profile.subject_group or '历' in profile.subject_group or '史' in profile.subject_group:
                profile.subject_group = '历史'
            else:
                profile.subject_group = ''

        # 初始化验证器 - 智能检测数据目录
        print("[进度] 正在加载一分一段表验证数据...")
        profile = merge_explicit_profile(profile, state.get("explicit_profile"))
        profile = _enrich_behavioral_profile(profile, user_text)
        profile = _mark_inferred_provenance(profile)
        readiness = assess_recommendation_readiness(profile)
        profile.recommendation_ready = readiness["ready"]
        profile.missing_critical_fields = readiness["missing_fields"]
        if not readiness["ready"]:
            missing_text = "、".join(readiness["missing_fields"])
            return {
                "user_profile": profile,
                "current_agent": "profiling_agent",
                "debug_logs": [
                    f"[BLOCKED] Formal recommendation requires: {missing_text}",
                    "[BLOCKED] No synthetic score, rank, or subject group was inserted.",
                ],
                "messages": [AIMessage(content=(
                    "生成正式志愿推荐前，还需要补充真实的关键信息："
                    f"{missing_text}。系统不会使用典型分数或虚构位次替代。"
                ))],
            }

        from pathlib import Path
        import os

        # 获取当前工作目录
        cwd = Path.cwd()
        print(f"[DEBUG] 当前工作目录: {cwd}")

        # 优先检查相对于backend/的data目录
        if Path("data").exists():
            data_dir = "data"
            print(f"[DEBUG] 使用相对路径: data/")
        elif Path("../data").exists():
            data_dir = "../data"
            print(f"[DEBUG] 使用相对路径: ../data/")
        elif Path("backend/data").exists():
            data_dir = "backend/data"
            print(f"[DEBUG] 使用相对路径: backend/data/")
        else:
            # 使用绝对路径作为最后的备选
            abs_data_dir = cwd / "data"
            if not abs_data_dir.exists():
                abs_data_dir = cwd.parent / "data"
            data_dir = str(abs_data_dir)
            print(f"[DEBUG] 使用绝对路径: {data_dir}")

        validator = UserInputValidator(data_dir=data_dir)

        # 准备验证数据
        validation_data = {
            'score': profile.score,
            'rank': profile.rank,
            'subject_group': profile.subject_group
        }

        # 验证分数和位次
        is_valid, error_msg, corrected_data = validator.validate_user_input(validation_data)

        if not is_valid:
            # 验证失败，记录警告信息
            print(f"[WARN] 分数位次验证失败: {error_msg}")

            # 如果有位次信息，优先使用位次
            if profile.rank is not None and profile.rank > 0:
                # 根据位次推算正确的分数
                estimated_score = validator.yifenyiduan.rank_to_score(
                    profile.rank,
                    profile.subject_group
                )
                if estimated_score:
                    print(f"[INFO] 根据位次 {profile.rank} 推算分数：{estimated_score}")
                    profile.score = estimated_score
            elif profile.score is not None and profile.score > 0:
                # 只有分数，推算位次
                estimated_rank = validator.yifenyiduan.score_to_rank(
                    profile.score,
                    profile.subject_group
                )
                if estimated_rank:
                    print(f"[INFO] 根据分数 {profile.score} 推算位次：{estimated_rank}")
                    profile.rank = estimated_rank

            return {
                "user_profile": profile,
                "agent_messages": publish_agent_message(
                    sender="profiling_agent",
                    stage="profiling",
                    message_type="summary",
                    content=f"Profile corrected: score={profile.score}, rank={profile.rank}, subject_group={profile.subject_group}",
                    recipients=["game_agent", "deep_research"],
                    confidence=0.7,
                )["agent_messages"],
                "agent_memories": remember(
                    agent_name="profiling_agent",
                    stage="profiling",
                    note_type="correction",
                    content=f"Adjusted inconsistent score/rank to score={profile.score}, rank={profile.rank}",
                    importance=0.7,
                )["agent_memories"],
                "current_agent": "profiling_agent",
                "debug_logs": [
                    "[WARN] Profiling Agent: 分数位次不完全匹配，已自动修正",
                    f"[INFO] 最终数据 - 分数：{profile.score}，位次：{profile.rank}"
                ],
                "messages": [AIMessage(content=(
                    f"[WARN] 检测到分数与位次可能存在偏差\n\n"
                    f"已为您调整：\n"
                    f"- 位次：{profile.rank}\n"
                    f"- 分数：{profile.score}（根据{profile.subject_group}类一分一段表推算）\n"
                    f"- 选科：{profile.subject_group}\n\n"
                    f"正在进行量化分析..."
                ))]
            }
        else:
            # 验证通过，使用修正后的数据
            if corrected_data:
                profile.score = corrected_data.get('score', profile.score)
                profile.rank = corrected_data.get('rank', profile.rank)
                profile.subject_group = corrected_data.get('subject_group', profile.subject_group)

            print(f"[OK] 用户画像构建完成：分数 {profile.score}，位次 {profile.rank}，选科 {profile.subject_group}")

            # 构建返回消息（包含推理过程）
            message_parts = []

            # 如果有推理过程，先展示
            if reasoning_process:
                message_parts.append("## 🧠 AI 推理过程\n")
                for reasoning in reasoning_process:
                    message_parts.append(f"{reasoning}\n")
                message_parts.append("\n---\n\n")

            message_parts.append("## ✓ 用户画像已构建\n\n")
            message_parts.append(f"- **分数**：{profile.score} 分\n")
            message_parts.append(f"- **位次**：{profile.rank}\n")
            message_parts.append(f"- **选科**：{profile.subject_group}\n")

            if profile.preferred_majors:
                message_parts.append(f"- **意向专业**：{', '.join(profile.preferred_majors)}\n")
            if profile.preferred_cities:
                message_parts.append(f"- **偏好城市**：{', '.join(profile.preferred_cities)}\n")

            # 检查是否需要询问学校-专业偏好
            # 修复：默认使用BALANCED，不询问用户（减少交互步骤）
            if profile.school_major_preference == SchoolMajorPreference.UNKNOWN:
                print("[INFO] 检测到用户未设置学校-专业偏好，使用默认值: BALANCED")
                profile.school_major_preference = SchoolMajorPreference.BALANCED
                reasoning_process.append("🎯 **策略推理**：未指定偏好，使用平衡型策略（学校和专业兼顾）")

            message_parts.append(f"- **风险偏好**：{profile.risk_tolerance.value}\n")
            message_parts.append(f"- **志愿策略**：{profile.school_major_preference.value}\n\n")

            if reasoning_process:
                message_parts.append("💡 *基于您的需求，我已为您智能推理并构建了参考画像*\n\n")

            message_parts.append("正在进行量化分析...")

            return {
                "user_profile": profile,
                "agent_messages": publish_agent_message(
                    sender="profiling_agent",
                    stage="profiling",
                    message_type="summary",
                    content=f"Profile ready: score={profile.score}, rank={profile.rank}, subject_group={profile.subject_group}",
                    recipients=["game_agent", "deep_research"],
                    confidence=0.8,
                    metadata={
                        "has_major_pref": bool(profile.preferred_majors),
                        "has_city_pref": bool(profile.preferred_cities),
                    },
                )["agent_messages"],
                "agent_memories": remember(
                    agent_name="profiling_agent",
                    stage="profiling",
                    note_type="profile_summary",
                    content=f"Profile extracted with rank={profile.rank}, majors={profile.preferred_majors}, cities={profile.preferred_cities}",
                    importance=0.8,
                )["agent_memories"],
                "current_agent": "profiling_agent",
                "debug_logs": ["[OK] Profiling Agent: 画像构建完成"] + (["[REASONING] " + r for r in reasoning_process] if reasoning_process else []),
                "messages": [AIMessage(content=''.join(message_parts))]
            }

    except Exception as e:
        print(f"[WARN] Profiling Agent 失败: {e}")

        fallback_profile = extract_profile_from_text(user_text)
        fallback_profile = merge_explicit_profile(
            fallback_profile,
            state.get("explicit_profile"),
        )
        fallback_profile = _enrich_behavioral_profile(fallback_profile, user_text)
        fallback_profile = _mark_inferred_provenance(fallback_profile)
        readiness = assess_recommendation_readiness(fallback_profile)
        fallback_profile.recommendation_ready = readiness["ready"]
        fallback_profile.missing_critical_fields = readiness["missing_fields"]
        if not fallback_profile.recommendation_ready:
            missing_text = "、".join(fallback_profile.missing_critical_fields)
            return {
                "user_profile": fallback_profile,
                "current_agent": "profiling_agent",
                "debug_logs": [
                    f"[WARN] Profiling Agent LLM extraction failed: {e}",
                    f"[BLOCKED] Deterministic extraction still missing: {missing_text}",
                    "[BLOCKED] No default score, rank, or subject group was inserted.",
                ],
                "messages": [AIMessage(content=(
                    "画像提取服务暂不可用，且无法从输入中确认："
                    f"{missing_text}。请补充真实信息后重试。"
                ))],
            }

        return {
            "user_profile": fallback_profile,
            "agent_messages": publish_agent_message(
                sender="profiling_agent",
                stage="profiling",
                message_type="summary",
                content=(
                    "Profiling fallback recovered explicit user inputs: "
                    f"score={fallback_profile.score}, rank={fallback_profile.rank}, "
                    f"subject_group={fallback_profile.subject_group}."
                ),
                recipients=["game_agent"],
                confidence=0.75,
            )["agent_messages"],
            "current_agent": "profiling_agent",
            "debug_logs": [
                f"[WARN] Profiling Agent LLM extraction failed: {e}",
                "[OK] Profiling Agent recovered the explicit score, rank, and subject group without defaults.",
            ],
            "messages": [AIMessage(content="已从您提供的真实信息恢复画像，正在进行分析...")]
        }

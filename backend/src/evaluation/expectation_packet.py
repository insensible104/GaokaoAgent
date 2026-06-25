"""Expectation-management packet for Gaokao volunteer planning.

The packet is meant to be delivered before final recommendations. It records
known constraints, unresolved assumptions, risk boundaries, and sign-off items
so families understand what the plan can and cannot optimize.
"""

from __future__ import annotations

from typing import Any

from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


def _list_or_placeholder(values: list[str], placeholder: str = "未明确") -> str:
    return "、".join(str(value) for value in values if str(value).strip()) or placeholder


def _risk_label(profile: UserProfile) -> str:
    if profile.risk_tolerance == RiskTolerance.CONSERVATIVE:
        return "保守：优先降低滑档和尾部调剂风险，冲刺空间会被主动压缩。"
    if profile.risk_tolerance == RiskTolerance.AGGRESSIVE:
        return "激进：可接受更高不确定性以换取学校/专业上探空间。"
    return "平衡：在冲刺机会、稳妥录取和保底安全之间做组合权衡。"


def _school_major_label(profile: UserProfile) -> str:
    if profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_SCHOOL:
        return "学校优先：可接受一定专业让步，但必须确认冷门/尾部专业承受度。"
    if profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_MAJOR:
        return "专业优先：可接受学校层级下移，以提高目标专业和前排专业命中。"
    if profile.school_major_preference == SchoolMajorPreference.BALANCED:
        return "学校和专业兼顾：避免单一指标极端优化。"
    return "未明确：需要在推荐前确认学校与专业的优先级。"


def _confirmation_items(profile: UserProfile) -> list[dict[str, Any]]:
    items = [
        {
            "id": "rank_score_subject",
            "label": "分数、位次、选科已核对无误",
            "required": True,
            "status": "known" if profile.rank is not None and profile.score and profile.subject_group else "missing",
        },
        {
            "id": "region_boundary",
            "label": "地域边界已确认，包括是否接受省外、校区差异和城市优先级",
            "required": True,
            "status": "known" if profile.preferred_cities or profile.excluded_cities else "needs_confirmation",
        },
        {
            "id": "major_boundary",
            "label": "目标专业、可接受专业和绝对不接受专业已确认",
            "required": True,
            "status": "known" if profile.preferred_majors or profile.blacklist_majors else "needs_confirmation",
        },
        {
            "id": "school_major_tradeoff",
            "label": "学校优先还是专业优先已确认",
            "required": True,
            "status": "known"
            if profile.school_major_preference != SchoolMajorPreference.UNKNOWN
            else "needs_confirmation",
        },
        {
            "id": "adjustment_acceptance",
            "label": "服从调剂、尾部专业和专业组混搭风险已确认",
            "required": True,
            "status": "needs_confirmation",
        },
        {
            "id": "budget_pathway",
            "label": "民办、中外合作、高收费、异地校区和培养路径已确认",
            "required": True,
            "status": "needs_confirmation",
        },
        {
            "id": "official_review",
            "label": "最终填报前会复核考试院数据、招生章程和体检限制",
            "required": True,
            "status": "needs_confirmation",
        },
    ]
    if profile.medical_restrictions:
        items.append(
            {
                "id": "medical_restrictions",
                "label": "体检限制已逐项核对到专业章程",
                "required": True,
                "status": "needs_confirmation",
            }
        )
    return items


def _risk_disclosures(profile: UserProfile) -> list[str]:
    disclosures = [
        "录取概率是基于历史数据和当前模型的风险估计，不是录取承诺。",
        "平行志愿一旦前序专业组投档成功，后续志愿通常不再发挥实际录取作用。",
        "专业组内可能存在专业混搭，服从调剂可能进入非目标或低偏好专业。",
        "招生计划、选科要求、学费、校区和培养模式必须以官方招生章程为准。",
        "热门城市、热门专业和短视频/机构叙事可能造成群体拥挤，历史低位次不必然持续。",
    ]
    if profile.blacklist_majors:
        disclosures.append(
            f"黑名单专业（{_list_or_placeholder(profile.blacklist_majors)}）需要作为硬边界复核，不能只看院校层级。"
        )
    if profile.regret_sensitivity >= 0.7:
        disclosures.append("用户后悔敏感度较高，推荐时应降低高尾部风险和高解释成本方案。")
    if profile.major_cognition_risk >= 0.5:
        disclosures.append("专业认知风险较高，需要先解释专业学习内容、就业方向和专业组构成。")
    return disclosures


def _client_signoff_checklist(profile: UserProfile) -> list[dict[str, Any]]:
    checklist = [
        {
            "id": "constraint_freeze",
            "label": "已确认本次推荐依据的地域、专业、院校层级、费用和调剂边界；若后续边界变化，需要重新评估。",
            "required": True,
            "status": "pending_signature",
        },
        {
            "id": "adjustment_tail_risk",
            "label": "已理解服从调剂、专业组混搭、尾部专业和非目标专业录取风险。",
            "required": True,
            "status": "pending_signature",
        },
        {
            "id": "private_joint_fee_pathway",
            "label": "已确认是否接受民办、中外合作、高收费、异地校区和特殊培养路径。",
            "required": True,
            "status": "pending_signature",
        },
        {
            "id": "non_guarantee",
            "label": "已理解系统和顾问提供的是数据辅助、风险解释和方案建议，不承诺录取结果。",
            "required": True,
            "status": "pending_signature",
        },
        {
            "id": "official_final_review",
            "label": "已确认最终填报前必须复核考试院数据、招生章程、体检限制、学费和校区信息。",
            "required": True,
            "status": "pending_signature",
        },
    ]
    if profile.blacklist_majors:
        checklist.append(
            {
                "id": "blacklist_hard_boundary",
                "label": f"已确认黑名单专业（{_list_or_placeholder(profile.blacklist_majors)}）是硬边界。",
                "required": True,
                "status": "pending_signature",
            }
        )
    if profile.preferred_cities or profile.excluded_cities:
        checklist.append(
            {
                "id": "region_tradeoff",
                "label": "已理解地域边界越硬，可选院校、专业和保底空间可能越窄。",
                "required": True,
                "status": "pending_signature",
            }
        )
    return checklist


def build_expectation_packet(profile: UserProfile) -> dict[str, Any]:
    """Build a structured expectation-management packet from a user profile."""
    items = _confirmation_items(profile)
    missing_required = [item for item in items if item["required"] and item["status"] != "known"]
    status = "ready_for_recommendation" if not missing_required else "needs_confirmation"
    return {
        "status": status,
        "student_context": {
            "score": profile.score,
            "rank": profile.rank,
            "subject_group": profile.subject_group,
            "preferred_cities": profile.preferred_cities,
            "excluded_cities": profile.excluded_cities,
            "preferred_majors": profile.preferred_majors,
            "blacklist_majors": profile.blacklist_majors,
            "risk_tolerance": profile.risk_tolerance.value,
            "school_major_preference": profile.school_major_preference.value,
        },
        "preference_summary": {
            "risk_policy": _risk_label(profile),
            "school_major_policy": _school_major_label(profile),
            "preference_confidence": profile.preference_confidence,
            "major_cognition_risk": profile.major_cognition_risk,
            "regret_sensitivity": profile.regret_sensitivity,
        },
        "confirmation_items": items,
        "risk_disclosures": _risk_disclosures(profile),
        "client_signoff_checklist": _client_signoff_checklist(profile),
        "family_questions": [
            "是否接受省外？如果不接受，是否理解可选空间会明显变窄？",
            "是否接受民办、中外合作、高收费、异地校区或特殊培养路径？",
            "是否愿意为了学校层级接受非目标专业或尾部调剂？",
            "绝对不接受的专业、城市、学费和校区分别是什么？",
            "如果保底方案看起来不够漂亮，是否仍以避免滑档为优先？",
        ],
        "non_guarantee_clause": (
            "本系统提供数据辅助和风险解释，不承诺录取结果。最终志愿填报必须由考生和家长结合"
            "考试院官方数据、招生章程、体检限制和家庭约束自行确认。"
        ),
    }


def build_markdown_expectation_packet(packet: dict[str, Any]) -> str:
    """Render an expectation packet as Markdown for client delivery."""
    ctx = packet["student_context"]
    summary = packet["preference_summary"]
    lines = [
        "# 志愿填报预期确认单",
        "",
        f"状态：`{packet['status']}`",
        "",
        "## 一、已知学生画像",
        "",
        f"- 分数/位次/选科：{ctx['score']} 分，位次 {ctx.get('rank') or '未明确'}，{ctx['subject_group']}",
        f"- 偏好城市：{_list_or_placeholder(ctx.get('preferred_cities') or [])}",
        f"- 排除城市：{_list_or_placeholder(ctx.get('excluded_cities') or [])}",
        f"- 意向专业：{_list_or_placeholder(ctx.get('preferred_majors') or [])}",
        f"- 黑名单专业：{_list_or_placeholder(ctx.get('blacklist_majors') or [])}",
        f"- 风险偏好：{summary['risk_policy']}",
        f"- 学校/专业权衡：{summary['school_major_policy']}",
        "",
        "## 二、必须确认的限制条件",
        "",
    ]
    for item in packet["confirmation_items"]:
        marker = "[x]" if item["status"] == "known" else "[ ]"
        lines.append(f"- {marker} {item['label']}（{item['status']}）")

    lines.extend(["", "## 三、风险与边界说明", ""])
    for disclosure in packet["risk_disclosures"]:
        lines.append(f"- {disclosure}")

    lines.extend(["", "## 四、家长/学生需要回答的问题", ""])
    for idx, question in enumerate(packet["family_questions"], 1):
        lines.append(f"{idx}. {question}")

    lines.extend(
        [
            "",
            "## 五、非承诺与复核条款",
            "",
            packet["non_guarantee_clause"],
            "",
            "## 六、客户签收清单",
            "",
        ]
    )
    for item in packet.get("client_signoff_checklist", []) or []:
        lines.append(f"- [ ] {item['label']}（{item['status']}）")

    lines.extend(
        [
            "",
            "## 七、确认签字",
            "",
            "- 考生确认：__________ 日期：__________",
            "- 家长确认：__________ 日期：__________",
            "- 顾问复核：__________ 日期：__________",
        ]
    )
    return "\n".join(lines) + "\n"

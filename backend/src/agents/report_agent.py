"""Report generation agent with protocol-aware summaries and fallback output."""

from __future__ import annotations

from langchain_core.messages import AIMessage

from models.report import ReportDraft
from models.state import SupervisorState
from prompts.report import report_generation_prompt
from utils import get_llm
from utils.agent_bus import get_messages_for_stage, publish_agent_message, remember


FIRST_HIT_REPORT_INSTRUCTIONS = """

Additional first-hit constraints:
The Guangdong volunteer form is an ordered slate. Once an earlier major group is admitted, later rows no longer affect the actual admission result. Prefer explaining the key prefix instead of treating every row as equally consequential.

Definitions:
- group_admission_prob: standalone admission probability for the major group.
- survival_before_prob: probability that all previous rows fail.
- first_hit_prob: probability that this row becomes the actual first admitted result.
- cumulative_hit_prob: cumulative probability of at least one admission through this row.
- prefix_role: key_result / active_backup / safety_anchor / shadowed.
- score_band: rank-band policy that decides whether school, major, city, safety, or upside should dominate.
- pain_point_flags: user-facing anxieties such as sliding risk, wasted score, tail-major regret, city mismatch, and herding crowding.
- market_behavior_notes: parallel-volunteer game signals, including crowded obvious choices, small-quota lottery opportunities, and mixed-group bait risk.
- decision_evidence_cards: opportunity_thesis / student_fit / downside_guard cards that explain why others may miss it, why this student can take it, and what can go wrong.

The report must highlight high first_hit_prob rows, explain shadowed rows as backup only, and warn when a high first_hit_prob row also has high tail_assignment_risk.
Also explain why a row is ranked there through score_band, pain_point_flags, and market_behavior_notes instead of only restating admission probability.
When decision_evidence_cards are present, use them as the primary explanation spine for that recommendation.
"""


def _compact_tradeoff_note(row) -> str:
    score_band = getattr(row, "score_band", "")
    pain_flags = getattr(row, "pain_point_flags", []) or []
    market_notes = getattr(row, "market_behavior_notes", []) or []
    if not score_band and not pain_flags and not market_notes:
        return ""

    parts = []
    if score_band:
        parts.append(f"score_band={score_band}")
    if pain_flags:
        parts.append(f"pain_points={','.join(pain_flags[:3])}")
    if market_notes:
        parts.append(f"market_signals={';'.join(market_notes[:2])}")
    return " | " + " | ".join(parts)


def _compact_decision_evidence_note(row) -> str:
    """Format decision-grade evidence cards for the recommendation line."""
    cards = getattr(row, "market_evidence_cards", []) or []
    if not cards:
        return ""

    label_by_type = {
        "opportunity_thesis": "机会逻辑",
        "student_fit": "适配理由",
        "downside_guard": "风险边界",
    }
    selected = []
    for signal_type, label in label_by_type.items():
        card = next((item for item in cards if item.get("signal_type") == signal_type), None)
        if card and card.get("claim"):
            selected.append(f"{label}: {card['claim']}")
    return "；".join(selected)


def _compact_quant_note(row) -> str:
    band = getattr(row, "deterministic_risk_band", "")
    quant_score = getattr(row, "quant_score", 0.0)
    confidence = getattr(row, "data_confidence_score", 0.0)
    evidence = getattr(row, "quant_evidence", []) or []
    if not band and not evidence:
        return ""
    parts = []
    if band:
        parts.append(f"量化风险档={band}")
    if quant_score:
        parts.append(f"量化分={quant_score:.2f}")
    if confidence:
        parts.append(f"数据置信={confidence:.2f}")
    if evidence:
        parts.append(evidence[0])
    return "；".join(parts)


def _row_tradeoff_payload(row) -> dict:
    return {
        "score_band": getattr(row, "score_band", ""),
        "tradeoff_breakdown": getattr(row, "tradeoff_breakdown", {}) or {},
        "pain_point_flags": getattr(row, "pain_point_flags", []) or [],
        "market_behavior_notes": getattr(row, "market_behavior_notes", []) or [],
        "tradeoff_summary": getattr(row, "tradeoff_summary", ""),
    }


def _row_decision_evidence_payload(row) -> dict:
    cards = getattr(row, "market_evidence_cards", []) or []
    decision_types = {"opportunity_thesis", "student_fit", "downside_guard"}
    decision_cards = [
        card
        for card in cards
        if card.get("signal_type") in decision_types
    ]
    return {
        "arbitrage_score": getattr(row, "arbitrage_score", 0.0),
        "front_major_arbitrage_score": getattr(row, "front_major_arbitrage_score", 0.0),
        "market_discount_score": getattr(row, "market_discount_score", 0.0),
        "personal_acceptability": getattr(row, "personal_acceptability", 0.0),
        "sacrifice_cost": getattr(row, "sacrifice_cost", 0.0),
        "publicity_rebound_risk": getattr(row, "publicity_rebound_risk", 0.0),
        "segment_rebound_risk": getattr(row, "segment_rebound_risk", 0.0),
        "market_evidence_strength": getattr(row, "market_evidence_strength", 0.0),
        "decision_evidence_cards": decision_cards[:3],
    }


def _append_key_decision_evidence(draft: ReportDraft, matrix) -> ReportDraft:
    """Ensure key-prefix decision and quant evidence are visible in the delivered report."""
    volunteer_plan = getattr(matrix, "volunteer_plan", None)
    if not volunteer_plan:
        return draft

    existing_text = "\n".join(
        [
            draft.full_markdown or "",
            draft.executive_summary or "",
            draft.strategy_analysis or "",
            "\n".join(draft.school_recommendations or []),
            "\n".join(draft.risk_warnings or []),
        ]
    )
    required_types = {
        "opportunity_thesis": "机会逻辑",
        "student_fit": "适配理由",
        "downside_guard": "风险边界",
    }
    appended = []
    row_lookup = {
        (str(getattr(row, "school_code", "")), str(getattr(row, "major_group_code", ""))): row
        for row in getattr(matrix, "major_group_rows", []) or getattr(matrix, "rows", []) or []
    }
    for choice in volunteer_plan.choices:
        if not getattr(choice, "is_key_prefix", False):
            continue
        cards = getattr(choice, "market_evidence_cards", []) or []
        claims = []
        for signal_type, label in required_types.items():
            card = next((item for item in cards if item.get("signal_type") == signal_type), None)
            if card and card.get("claim"):
                claim = str(card["claim"])
                claims.append(f"{label}: {claim}")
        source_row = row_lookup.get(
            (str(getattr(choice, "school_code", "")), str(getattr(choice, "major_group_code", ""))),
            choice,
        )
        quant_note = _compact_quant_note(source_row)
        if quant_note:
            claims.append(f"量化校验: {quant_note}")
        if not claims:
            continue
        if any(claim[:40] in existing_text for claim in claims):
            continue
        appended.append(
            (
                f"关键志愿解释 - 第{choice.choice_index}志愿 {choice.school_name}"
                f"{choice.major_group_code}专业组："
                + "；".join(claims)
            )
        )

    if appended:
        draft.school_recommendations.extend(appended[:5])
        draft.generate_markdown()
    return draft


def _format_recommendation(row) -> str:
    major_info = getattr(row, "major_group_code", "") or getattr(row, "major_name", "")
    suggested = getattr(row, "suggested_major_choices", None) or getattr(row, "major_choices", None) or []
    suggested_names = [major.major_name for major in suggested[:6]]
    if not suggested_names and getattr(row, "major_list", None):
        suggested_names = row.major_list[:6]
    if not major_info and suggested_names:
        major_info = ", ".join(suggested_names[:3])
    adjustment_advice = getattr(getattr(row, "adjustment_advice", None), "value", "cautious")
    tail_risk = getattr(row, "tail_assignment_risk", getattr(row, "adjustment_risk", 0.0))
    admission_prob = getattr(row, "admission_prob", getattr(row, "group_admission_prob", 0.0))
    strategy_tag = getattr(getattr(row, "strategy_tag", None), "value", "target")
    choice_index = getattr(row, "choice_index", None)
    first_hit_prob = getattr(row, "first_hit_prob", 0.0)
    survival_before_prob = getattr(row, "survival_before_prob", 1.0)
    cumulative_hit_prob = getattr(row, "cumulative_hit_prob", 0.0)
    prefix_role = getattr(row, "prefix_role", "unclassified")
    tradeoff_note = _compact_tradeoff_note(row)
    if tradeoff_note:
        major_info = f"{major_info} [{tradeoff_note}]"
    evidence_note = _compact_decision_evidence_note(row)
    quant_note = _compact_quant_note(row)
    prefix = f"第{choice_index}志愿 " if choice_index else ""
    base = (
        f"{prefix}{row.school_name} {major_info} "
        f"(单点投档概率 {admission_prob:.1%}, 首命中概率 {first_hit_prob:.1%}, "
        f"前序失败概率 {survival_before_prob:.1%}, 累计命中 {cumulative_hit_prob:.1%}, "
        f"角色 {prefix_role}, 策略 {strategy_tag}, "
        f"专业1-6：{'、'.join(suggested_names[:6])}, "
        f"调剂建议 {adjustment_advice}, 尾部风险 {tail_risk:.0%})"
    ).strip()
    notes = [note for note in (quant_note, evidence_note) if note]
    return f"{base}；{'；'.join(notes)}" if notes else base
    return (
        f"{row.school_name} {major_info} "
        f"(录取概率 {row.admission_prob:.1%}, 策略 {row.strategy_tag.value}, "
        f"专业1-6：{'、'.join(suggested_names[:6])}, "
        f"调剂建议 {adjustment_advice}, 尾部风险 {tail_risk:.0%})"
    ).strip()


def _build_fallback_report(profile, matrix, data_source) -> ReportDraft:
    rush_rows = [row for row in data_source if row.strategy_tag.value == "rush"]
    target_rows = [row for row in data_source if row.strategy_tag.value == "target"]
    safe_rows = [row for row in data_source if row.strategy_tag.value == "safe"]
    volunteer_plan = getattr(matrix, "volunteer_plan", None)

    executive_summary = (
        f"系统为该用户生成了 {len(data_source)} 条候选推荐，"
        f"其中冲 {len(rush_rows)} 条、稳 {len(target_rows)} 条、保 {len(safe_rows)} 条。"
        f"当前位次 {profile.rank}，总分 {profile.score}，选科 {profile.subject_group}。"
    )
    strategy_analysis = (
        f"推荐组合的期望效用为 {matrix.expected_utility:.3f}，组合风险为 {matrix.portfolio_risk:.3f}。"
        f"{'当前组合较为均衡。' if matrix.is_balanced else '当前组合仍有进一步平衡冲稳保结构的空间。'}"
    )
    risk_warnings = []
    blacklist_rows = [row for row in data_source if row.is_blacklist_risk]
    if blacklist_rows:
        risk_warnings.append(f"{len(blacklist_rows)} 条推荐存在潜在调剂到非偏好专业的风险。")
    high_tail_rows = [
        row
        for row in data_source
        if getattr(row, "tail_assignment_risk", 0.0) >= 0.55
    ]
    if high_tail_rows:
        risk_warnings.append(f"{len(high_tail_rows)} 条推荐存在较高组内专业混搭或尾部调剂风险。")
    if volunteer_plan:
        key_high_tail = [
            choice
            for choice in volunteer_plan.choices
            if choice.is_key_prefix and choice.tail_assignment_risk >= 0.55
        ]
        if key_high_tail:
            risk_warnings.append(
                f"{len(key_high_tail)} 个关键前缀志愿存在高尾部调剂风险，需要优先复核。"
            )
        risk_warnings.append(
            f"本方案预计至少一次投档命中概率 {volunteer_plan.expected_admission_prob:.1%}，"
            f"关键前缀 {volunteer_plan.key_prefix_count} 行，"
            f"被前序选择遮蔽 {volunteer_plan.shadowed_choice_count} 行。"
        )
    if len(safe_rows) < 3:
        risk_warnings.append("保底志愿数量偏少，建议补充更稳妥的院校专业组。")
    if not risk_warnings:
        risk_warnings.append("当前未发现显著结构性风险，但仍建议人工复核招生章程。")

    recommendation_source = volunteer_plan.choices if volunteer_plan else data_source
    draft = ReportDraft(
        executive_summary=executive_summary,
        strategy_analysis=strategy_analysis,
        school_recommendations=[_format_recommendation(row) for row in recommendation_source[:8]],
        risk_warnings=risk_warnings,
        regret_value=float(abs(min((row.rank_diff for row in data_source), default=0))),
    )
    draft.generate_markdown()
    return draft


def _build_research_only_report(research_report: str, inbound_messages) -> ReportDraft:
    content_lines = [line.strip() for line in research_report.splitlines() if line.strip()]
    executive_summary = content_lines[0] if content_lines else "已完成深度调研，并整理出可供后续决策参考的研究结论。"
    strategy_analysis = (
        f"本次输出基于深度调研分支生成，当前不依赖量化志愿矩阵。"
        f"系统共接收到 {len(inbound_messages)} 条上游上下文消息，"
        "重点关注院校信息核验、政策约束和风险提示。"
    )
    recommendations = []
    for line in content_lines[:6]:
        if line.startswith("#"):
            continue
        if len(line) < 8:
            continue
        recommendations.append(line[:160])
    if not recommendations:
        recommendations.append("建议优先阅读调研报告中的核心结论、关键数据和风险提示，再决定是否进入量化推荐链。")

    risk_warnings = [
        "该报告主要基于调研信息生成，若要形成最终志愿表，仍建议结合分数、位次和招生计划做量化校验。",
        "若引用的是非官方来源信息，仍需人工复核院校官网或招生章程。",
    ]

    draft = ReportDraft(
        title="GaokaoAgent 深度调研结果摘要",
        executive_summary=executive_summary,
        strategy_analysis=strategy_analysis,
        school_recommendations=recommendations,
        risk_warnings=risk_warnings,
        regret_value=0.0,
    )
    draft.full_markdown = research_report
    return draft


def report_agent_node(state: SupervisorState) -> dict:
    """Generate a structured report from the game matrix and optional research context."""
    print("[Report Agent] generating recommendation report...")

    inbound_messages = get_messages_for_stage(
        state,
        stage="deep_research",
        recipients=["report_agent"],
    ) + get_messages_for_stage(
        state,
        stage="post_game_deliberation",
        recipients=["report_agent"],
    )

    profile = state.get("user_profile")
    matrix = state.get("game_matrix")
    research_report = state.get("research_report")
    if (not profile or not matrix) and research_report:
        draft = _build_research_only_report(research_report, inbound_messages)
        return {
            "report_draft": draft,
            "agent_messages": publish_agent_message(
                sender="report_agent",
                stage="report",
                message_type="summary",
                content=(
                    "Research-only report prepared for the slow-loop branch without a quantitative game matrix."
                ),
                recipients=["critic_agent"],
                action_preference="critic_agent",
                confidence=0.74,
                metadata={
                    "recommendation_count": len(draft.school_recommendations),
                    "warning_count": len(draft.risk_warnings),
                    "used_fallback": True,
                    "report_mode": "research_only",
                },
            )["agent_messages"],
            "agent_memories": remember(
                agent_name="report_agent",
                stage="report",
                note_type="research_only_report",
                content="Generated a report wrapper for deep-research output without a game matrix.",
                importance=0.76,
            )["agent_memories"],
            "current_agent": "report_agent",
            "debug_logs": ["[OK] Report Agent: research-only report generated"],
            "messages": [AIMessage(content="Research-only report generated and forwarded to critic for audit.")],
        }

    if not profile or not matrix:
        return {
            "current_agent": "report_agent",
            "agent_messages": publish_agent_message(
                sender="report_agent",
                stage="report",
                message_type="failure",
                content="Report generation aborted because profile or game matrix was missing.",
                recipients=["critic_agent"],
                action_preference="critic_agent",
                confidence=0.2,
            )["agent_messages"],
            "agent_memories": remember(
                agent_name="report_agent",
                stage="report",
                note_type="failure",
                content="Missing profile or game matrix while generating report.",
                importance=0.8,
            )["agent_memories"],
            "debug_logs": ["[ERROR] Report Agent: missing required data"],
            "messages": [AIMessage(content="Report generation failed because required data was missing.")],
        }

    data_source = matrix.major_group_rows if matrix.major_group_rows else matrix.rows
    matrix_summary = {
        "basic_stats": {
            "total_rush": matrix.total_rush,
            "total_target": matrix.total_target,
            "total_safe": matrix.total_safe,
            "expected_utility": matrix.expected_utility,
            "portfolio_risk": matrix.portfolio_risk,
            "is_balanced": matrix.is_balanced,
            "selection_method": matrix.selection_method,
            "total_count": len(data_source),
            "expected_admission_prob": (
                matrix.volunteer_plan.expected_admission_prob if matrix.volunteer_plan else None
            ),
            "expected_first_hit_utility": (
                matrix.volunteer_plan.expected_first_hit_utility if matrix.volunteer_plan else None
            ),
            "expected_tail_risk": (
                matrix.volunteer_plan.expected_tail_risk if matrix.volunteer_plan else None
            ),
            "expected_plan_value": (
                matrix.volunteer_plan.expected_plan_value if matrix.volunteer_plan else None
            ),
            "key_prefix_count": (
                matrix.volunteer_plan.key_prefix_count if matrix.volunteer_plan else None
            ),
            "shadowed_choice_count": (
                matrix.volunteer_plan.shadowed_choice_count if matrix.volunteer_plan else None
            ),
        },
        "user_position": {
            "rank": profile.rank,
            "score": profile.score,
            "subject_group": profile.subject_group,
        },
        "research_context": [
            msg.content for msg in inbound_messages[-3:]
        ],
        "recommendations": [
            {
                "school": row.school_name,
                "school_code": getattr(row, "school_code", ""),
                "strategy": row.strategy_tag.value,
                "admission_prob": row.admission_prob,
                "choice_index": getattr(row, "choice_index", None),
                "survival_before_prob": getattr(row, "survival_before_prob", 1.0),
                "first_hit_prob": getattr(row, "first_hit_prob", 0.0),
                "cumulative_hit_prob": getattr(row, "cumulative_hit_prob", 0.0),
                "prefix_role": getattr(row, "prefix_role", "unclassified"),
                "is_key_prefix": getattr(row, "is_key_prefix", False),
                "consequence_score": getattr(row, "consequence_score", 0.0),
                "rank_diff": row.rank_diff,
                "adjustment_risk": row.adjustment_risk,
                "tail_assignment_risk": getattr(row, "tail_assignment_risk", row.adjustment_risk),
                "adjustment_advice": getattr(getattr(row, "adjustment_advice", None), "value", "cautious"),
                "worst_case_major": getattr(row, "worst_case_major", None),
                "bundle_type": getattr(getattr(row, "bundle_type", None), "value", "unknown"),
                "quant_score": getattr(row, "quant_score", 0.0),
                "rank_buffer_score": getattr(row, "rank_buffer_score", 0.0),
                "history_stability_score": getattr(row, "history_stability_score", 0.0),
                "data_confidence_score": getattr(row, "data_confidence_score", 0.0),
                "trend_score": getattr(row, "trend_score", 0.0),
                "deterministic_risk_band": getattr(row, "deterministic_risk_band", ""),
                "quant_evidence": getattr(row, "quant_evidence", []) or [],
                "major_group": getattr(row, "major_group_code", ""),
                "major_list": getattr(row, "major_list", []),
                "suggested_major_choices": [
                    {
                        "major_code": major.major_code,
                        "major_name": major.major_name,
                        "user_utility": major.user_utility,
                        "is_blacklisted": major.is_blacklisted,
                    }
                    for major in getattr(row, "suggested_major_choices", [])[:6]
                ],
                **_row_tradeoff_payload(row),
                **_row_decision_evidence_payload(row),
            }
            for row in data_source
        ],
        "volunteer_plan": matrix.volunteer_plan.model_dump() if matrix.volunteer_plan else None,
    }

    llm = get_llm()
    structured_llm = llm.with_structured_output(ReportDraft)
    prompt = (report_generation_prompt + FIRST_HIT_REPORT_INSTRUCTIONS).format(
        user_profile=profile.model_dump_json(indent=2),
        game_matrix=str(matrix_summary),
    )

    try:
        draft = structured_llm.invoke(prompt)
        if not draft.school_recommendations:
            raise ValueError("LLM returned empty school_recommendations")
        draft.generate_markdown()
        draft = _append_key_decision_evidence(draft, matrix)
        warning_count = len(draft.risk_warnings)
        recommendation_count = len(draft.school_recommendations)
        return {
            "report_draft": draft,
            "agent_messages": publish_agent_message(
                sender="report_agent",
                stage="report",
                message_type="summary",
                content=(
                    f"Structured report generated with {recommendation_count} recommendations, "
                    f"{warning_count} warnings, inbound_context={len(inbound_messages)}."
                ),
                recipients=["critic_agent"],
                action_preference="critic_agent",
                confidence=0.82,
                metadata={
                    "recommendation_count": recommendation_count,
                    "warning_count": warning_count,
                    "used_fallback": False,
                },
            )["agent_messages"],
            "agent_memories": remember(
                agent_name="report_agent",
                stage="report",
                note_type="report_summary",
                content=(
                    f"Generated structured report with {recommendation_count} recommendations "
                    f"and {warning_count} warnings."
                ),
                importance=0.8,
            )["agent_memories"],
            "current_agent": "report_agent",
            "debug_logs": ["[OK] Report Agent: structured report generated"],
            "messages": [AIMessage(content="Report generated and forwarded to critic for audit.")],
        }
    except Exception as exc:
        fallback_draft = _build_fallback_report(profile, matrix, data_source)
        fallback_draft = _append_key_decision_evidence(fallback_draft, matrix)
        recommendation_count = len(fallback_draft.school_recommendations)
        warning_count = len(fallback_draft.risk_warnings)
        return {
            "report_draft": fallback_draft,
            "agent_messages": publish_agent_message(
                sender="report_agent",
                stage="report",
                message_type="summary",
                content=(
                    f"Fallback report generated with {recommendation_count} recommendations "
                    f"after structured generation failed: {exc}"
                ),
                recipients=["critic_agent"],
                action_preference="critic_agent",
                confidence=0.6,
                metadata={
                    "recommendation_count": recommendation_count,
                    "warning_count": warning_count,
                    "used_fallback": True,
                },
            )["agent_messages"],
            "agent_memories": remember(
                agent_name="report_agent",
                stage="report",
                note_type="fallback_report",
                content=f"Used fallback report generation because structured LLM failed: {exc}",
                importance=0.7,
            )["agent_memories"],
            "current_agent": "report_agent",
            "debug_logs": [f"[WARN] Report Agent: fallback report generated because {exc}"],
            "messages": [AIMessage(content="Fallback report generated and forwarded to critic.")],
        }

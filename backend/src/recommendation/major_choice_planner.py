"""Build six-slot major choices and volunteer-plan rows."""

from __future__ import annotations

from models.game_matrix import MajorOption, VolunteerChoice, VolunteerPlan
from models.user_profile import UserProfile
from recommendation.prefix_optimizer import optimize_prefix_order


KEY_FIRST_HIT_THRESHOLD = 0.10
ACTIVE_BACKUP_FIRST_HIT_THRESHOLD = 0.03
ACTIVE_BACKUP_SURVIVAL_THRESHOLD = 0.10
HIGH_TAIL_RISK_THRESHOLD = 0.55


def build_major_options_from_records(records: list[dict], fallback_majors: list[str] | None = None) -> list[MajorOption]:
    """Convert enrollment-plan records to MajorOption models."""
    options: list[MajorOption] = []
    for record in records:
        major_name = str(record.get("major_name") or "").strip()
        if not major_name:
            continue
        options.append(
            MajorOption(
                school_code=str(record.get("school_code") or ""),
                school_name=str(record.get("school_name") or ""),
                major_group_code=str(record.get("major_group_code") or ""),
                major_code=str(record.get("major_code") or ""),
                major_name=major_name,
                subject_requirement=record.get("subject_requirement"),
                plan_quota=record.get("plan_quota"),
                tuition=record.get("tuition"),
                remarks=record.get("remarks"),
                historical_min_scores=record.get("historical_min_scores") or {},
                historical_min_ranks=record.get("historical_min_ranks") or {},
            )
        )

    if options or not fallback_majors:
        return options

    return [
        MajorOption(major_name=str(major).strip())
        for major in fallback_majors
        if str(major).strip()
    ]


def choose_six_majors(options: list[MajorOption], max_choices: int = 6) -> list[MajorOption]:
    """Choose up to six majors for the volunteer form."""
    non_blacklisted = [option for option in options if not option.is_blacklisted]
    candidates = non_blacklisted if non_blacklisted else options
    return sorted(
        candidates,
        key=lambda option: (
            option.user_utility,
            -option.major_rank_risk,
            option.plan_quota or 0,
        ),
        reverse=True,
    )[:max_choices]


def build_volunteer_choice(row, choice_index: int) -> VolunteerChoice:
    """Build a Guangdong volunteer-form row from a scored MajorGroupRow."""
    suggested_choices = row.suggested_major_choices or row.major_options[:6]
    expected_utility = (
        sum(option.user_utility for option in suggested_choices) / len(suggested_choices)
        if suggested_choices
        else row.major_utility_mean
    )
    explanation = (
        f"{row.school_name}{row.major_group_code}专业组：投档概率约{row.admission_prob:.1%}，"
        f"组内尾部风险约{row.tail_assignment_risk:.0%}，"
        f"调剂建议为{row.adjustment_advice.value}。"
    )

    return VolunteerChoice(
        choice_index=choice_index,
        school_code=str(row.school_code),
        school_name=row.school_name,
        major_group_code=str(row.major_group_code),
        major_choices=suggested_choices,
        obey_adjustment=row.obey_adjustment,
        adjustment_advice=row.adjustment_advice,
        group_admission_prob=row.admission_prob,
        expected_major_utility=expected_utility,
        worst_case_major=row.worst_case_major,
        tail_assignment_risk=row.tail_assignment_risk,
        strategy_tag=row.strategy_tag,
        recommendation_role=row.recommendation_role or row.strategy_tag.value,
        explanation=explanation,
        audit_flags=list(row.audit_flags),
        score_band=getattr(row, "score_band", ""),
        tradeoff_breakdown=dict(getattr(row, "tradeoff_breakdown", {}) or {}),
        pain_point_flags=list(getattr(row, "pain_point_flags", []) or []),
        market_behavior_notes=list(getattr(row, "market_behavior_notes", []) or []),
        tradeoff_summary=getattr(row, "tradeoff_summary", ""),
        arbitrage_score=getattr(row, "arbitrage_score", 0.0),
        front_major_arbitrage_score=getattr(row, "front_major_arbitrage_score", 0.0),
        relative_lift=getattr(row, "relative_lift", 0.0),
        market_discount_score=getattr(row, "market_discount_score", 0.0),
        personal_acceptability=getattr(row, "personal_acceptability", 0.0),
        sacrifice_cost=getattr(row, "sacrifice_cost", 0.0),
        assignment_opportunity=getattr(row, "assignment_opportunity", 0.0),
        front_major_hit_prob=getattr(row, "front_major_hit_prob", 0.0),
        rebound_risk=getattr(row, "rebound_risk", 0.0),
        opportunity_types=list(getattr(row, "opportunity_types", []) or []),
        opportunity_pools=list(getattr(row, "opportunity_pools", []) or []),
        arbitrage_breakdown=dict(getattr(row, "arbitrage_breakdown", {}) or {}),
        market_evidence_cards=list(getattr(row, "market_evidence_cards", []) or []),
        market_evidence_strength=getattr(row, "market_evidence_strength", 0.0),
        publicity_heat_score=getattr(row, "publicity_heat_score", 0.0),
        publicity_rebound_risk=getattr(row, "publicity_rebound_risk", 0.0),
        segment_demand_score=getattr(row, "segment_demand_score", 0.0),
        low_attention_signal=getattr(row, "low_attention_signal", 0.0),
        segment_rebound_risk=getattr(row, "segment_rebound_risk", 0.0),
        best_fit_archetypes=list(getattr(row, "best_fit_archetypes", []) or []),
        segment_demand_breakdown=dict(getattr(row, "segment_demand_breakdown", {}) or {}),
    )


def _sync_first_hit_metrics(plan: VolunteerPlan, rows: list) -> None:
    """Copy ordered first-hit metrics from the plan back to source rows and explanations."""
    for choice, row in zip(plan.choices, rows):
        row.choice_index = choice.choice_index
        row.survival_before_prob = choice.survival_before_prob
        row.first_hit_prob = choice.first_hit_prob
        row.cumulative_hit_prob = choice.cumulative_hit_prob
        row.consequence_score = choice.consequence_score
        row.prefix_role = choice.prefix_role
        row.is_key_prefix = choice.is_key_prefix

        if choice.is_key_prefix and choice.tail_assignment_risk >= HIGH_TAIL_RISK_THRESHOLD:
            flag = "key_prefix_high_tail_risk"
            if flag not in row.audit_flags:
                row.audit_flags.append(flag)
            if flag not in choice.audit_flags:
                choice.audit_flags.append(flag)

        choice.explanation = (
            f"{choice.school_name}{choice.major_group_code}专业组："
            f"单点投档概率约{choice.group_admission_prob:.1%}，"
            f"前序志愿全部未命中的概率约{choice.survival_before_prob:.1%}，"
            f"成为首个录取结果的概率约{choice.first_hit_prob:.1%}，"
            f"累计命中概率约{choice.cumulative_hit_prob:.1%}，"
            f"角色为{choice.prefix_role}，"
            f"组内尾部风险约{choice.tail_assignment_risk:.0%}，"
            f"调剂建议为{choice.adjustment_advice.value}。"
        )


def _build_plan_review_items(plan: VolunteerPlan) -> list[str]:
    """Create review items that focus on rows likely to determine the final outcome."""
    review_items = [
        "复核招生章程中的单科、体检、语种、校区和专业备注限制。",
        "优先复核 key_result / active_backup 对应专业组；后续 shadowed 行主要承担保险作用。",
        "对调剂建议为 cautious 或 avoid 的专业组进行人工确认。",
    ]

    key_high_tail_choices = [
        choice
        for choice in plan.choices
        if choice.is_key_prefix and choice.tail_assignment_risk >= HIGH_TAIL_RISK_THRESHOLD
    ]
    for choice in key_high_tail_choices[:5]:
        review_items.append(
            f"第{choice.choice_index}志愿首命中概率{choice.first_hit_prob:.1%}且尾部风险"
            f"{choice.tail_assignment_risk:.0%}，需重点确认专业组内最差专业和是否服从调剂。"
        )

    if plan.shadowed_choice_count:
        review_items.append(
            f"{plan.shadowed_choice_count}行志愿被前序高概率选择遮蔽，解释时不要把它们当作同等重要推荐。"
        )

    return review_items


def build_volunteer_plan(
    rows: list,
    profile: UserProfile,
    max_choices: int | None = None,
    optimize_prefix: bool = False,
) -> VolunteerPlan:
    """Build a structured volunteer-plan draft from final recommended rows."""
    ordered_rows = (
        optimize_prefix_order(rows=rows, profile=profile, max_choices=max_choices)
        if optimize_prefix
        else rows
    )
    selected_rows = ordered_rows[:max_choices] if max_choices else ordered_rows
    choices = [
        build_volunteer_choice(row, index + 1)
        for index, row in enumerate(selected_rows)
    ]
    plan = VolunteerPlan(
        year=2025,
        subject_group=profile.subject_group,
        user_score=profile.score,
        user_rank=profile.rank,
        choices=choices,
        plan_summary=f"生成{len(choices)}行广东院校专业组志愿草案。",
        human_review_items=[
            "复核招生章程中的单科、体检、语种和校区限制。",
            "对调剂建议为 cautious 或 avoid 的专业组进行人工确认。",
        ],
    )
    plan.calculate_statistics()
    _sync_first_hit_metrics(plan, selected_rows)
    plan.plan_summary = (
        f"生成{len(choices)}行广东院校专业组志愿草案；"
        f"预计至少一次投档命中概率{plan.expected_admission_prob:.1%}，"
        f"关键前缀{plan.key_prefix_count}行，"
        f"被前序选择遮蔽{plan.shadowed_choice_count}行。"
    )
    plan.human_review_items = _build_plan_review_items(plan)
    return plan

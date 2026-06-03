"""Parallel-world stress testing for Gaokao volunteer plans.

This is a deterministic, auditable version of "parallel world" forecasting for
volunteer planning. Each world represents one explicit external assumption
change, then reuses the existing plan-quality gate to show whether the plan is
robust or fragile under that branch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from evaluation.plan_quality_audit import audit_plan_quality
from models.game_matrix import AdjustmentAdvice, StrategyTag, VolunteerChoice, VolunteerPlan
from models.user_profile import UserProfile


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class ParallelWorldSpec:
    """One scenario branch with explicit assumptions and probability weight."""

    world_id: str
    label: str
    probability_weight: float
    assumptions: list[str] = field(default_factory=list)
    tripwires: list[str] = field(default_factory=list)


DEFAULT_PARALLEL_WORLDS = [
    ParallelWorldSpec(
        world_id="baseline",
        label="基准世界",
        probability_weight=0.30,
        assumptions=["历史位次、热度和计划变化按当前模型估计兑现。"],
        tripwires=["官方计划数和招生章程没有明显偏离；公开热度没有集中涌入关键志愿。"],
    ),
    ParallelWorldSpec(
        world_id="rank_rebound",
        label="位次回弹世界",
        probability_weight=0.20,
        assumptions=["热门学校/专业组回弹，预测概率整体偏乐观。"],
        tripwires=["同位分段讨论热度上升；近三年低位次被短视频/直播反复提及。"],
    ),
    ParallelWorldSpec(
        world_id="crowding_heat",
        label="群体拥挤世界",
        probability_weight=0.18,
        assumptions=["家庭和主播共同追逐显眼机会，低关注套利变拥挤。"],
        tripwires=["关键专业组出现高频直播推荐、社群转发或同分段集中咨询。"],
    ),
    ParallelWorldSpec(
        world_id="tail_mix_worse",
        label="尾部专业恶化世界",
        probability_weight=0.14,
        assumptions=["专业组内尾部专业、调剂和黑名单风险比基准更难承受。"],
        tripwires=["招生章程确认专业组混搭严重；家长对尾部专业接受度下降。"],
    ),
    ParallelWorldSpec(
        world_id="safe_anchor_slips",
        label="保底安全垫失效世界",
        probability_weight=0.10,
        assumptions=["看似稳妥的保底组因计划缩减或同分段拥挤而变薄。"],
        tripwires=["安全垫专业组计划数下降；保底校近两年波动扩大。"],
    ),
    ParallelWorldSpec(
        world_id="hidden_opportunity",
        label="低关注机会兑现世界",
        probability_weight=0.08,
        assumptions=["高学费、异地校区、冷门城市或路径折价继续存在，低关注机会兑现。"],
        tripwires=["公开热度保持低位；计划数稳定；专业组牺牲项与学生偏好匹配。"],
    ),
]


def _choice_heat(choice: VolunteerChoice) -> float:
    return _clamp(
        max(
            choice.rebound_risk,
            choice.publicity_rebound_risk,
            choice.segment_rebound_risk,
            1 - choice.low_attention_signal if choice.low_attention_signal > 0 else 0.0,
        )
    )


def _opportunity_signal(choice: VolunteerChoice) -> float:
    return _clamp(
        max(
            choice.market_discount_score,
            choice.low_attention_signal,
            choice.segment_demand_score * 0.85,
            choice.arbitrage_score * 0.75,
        )
    )


def _apply_probability_shock(choice: VolunteerChoice, factor: float, offset: float = 0.0) -> None:
    choice.group_admission_prob = _clamp(choice.group_admission_prob * factor + offset)


def _apply_tail_shock(choice: VolunteerChoice, delta: float) -> None:
    choice.tail_assignment_risk = _clamp(choice.tail_assignment_risk + delta)
    choice.expected_major_utility = _clamp(choice.expected_major_utility - max(delta, 0.0) * 0.35)


def _apply_world(plan: VolunteerPlan, world: ParallelWorldSpec) -> VolunteerPlan:
    stressed = plan.model_copy(deep=True)
    for choice in stressed.choices:
        heat = _choice_heat(choice)
        opportunity = _opportunity_signal(choice)
        if world.world_id == "rank_rebound":
            shock = 0.90 if choice.strategy_tag == StrategyTag.RUSH else 0.94
            _apply_probability_shock(choice, shock)
        elif world.world_id == "crowding_heat":
            _apply_probability_shock(choice, 1 - 0.18 * max(heat, 0.35))
            if heat >= 0.35 or choice.strategy_tag == StrategyTag.RUSH:
                _apply_tail_shock(choice, 0.05 + 0.08 * heat)
        elif world.world_id == "tail_mix_worse":
            if choice.adjustment_advice in {AdjustmentAdvice.CAUTIOUS, AdjustmentAdvice.AVOID} or choice.tail_assignment_risk >= 0.25:
                _apply_tail_shock(choice, 0.18)
            else:
                _apply_tail_shock(choice, 0.06)
        elif world.world_id == "safe_anchor_slips":
            if choice.strategy_tag == StrategyTag.SAFE or choice.group_admission_prob >= 0.88:
                _apply_probability_shock(choice, 0.78)
                _apply_tail_shock(choice, 0.04)
        elif world.world_id == "hidden_opportunity":
            if opportunity >= 0.35 and heat < 0.55:
                _apply_probability_shock(choice, 1.08, 0.02 * opportunity)
                choice.tail_assignment_risk = _clamp(choice.tail_assignment_risk - 0.04 * opportunity)
        elif world.world_id == "baseline":
            pass
        else:
            raise ValueError(f"Unknown parallel world: {world.world_id}")
    stressed.calculate_statistics()
    return stressed


def _status_value(status: str) -> int:
    return {"pass": 3, "needs_revision": 2, "blocked": 1}.get(status, 0)


def _summarize_sensitivity(world_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [row for row in world_rows if row["world_id"] != "baseline"]
    rows = sorted(
        rows,
        key=lambda row: (
            _status_value(str(row["plan_quality_status"])),
            row["plan_quality_score"],
            row["expected_admission_prob"],
        ),
    )
    return [
        {
            "world_id": row["world_id"],
            "label": row["label"],
            "status": row["plan_quality_status"],
            "probability_weight": row["probability_weight"],
            "score_delta_vs_baseline": row.get("score_delta_vs_baseline", 0.0),
            "admission_delta_vs_baseline": row.get("admission_delta_vs_baseline", 0.0),
            "top_findings": row.get("top_findings", []),
            "tripwires": row.get("tripwires", []),
        }
        for row in rows[:5]
    ]


def run_parallel_world_analysis(
    *,
    plan: VolunteerPlan,
    profile: UserProfile | None = None,
    worlds: Iterable[ParallelWorldSpec] = DEFAULT_PARALLEL_WORLDS,
) -> dict[str, Any]:
    """Stress test one volunteer plan across explicit scenario branches."""
    world_specs = list(worlds)
    if not world_specs:
        raise ValueError("At least one parallel world is required.")

    world_rows: list[dict[str, Any]] = []
    baseline_score = 0.0
    baseline_admission = 0.0
    for spec in world_specs:
        stressed = _apply_world(plan, spec)
        audit = audit_plan_quality(stressed, profile)
        if spec.world_id == "baseline":
            baseline_score = float(audit.get("total_score", 0.0))
            baseline_admission = float(audit.get("expected_admission_prob", 0.0))
        world_rows.append(
            {
                "world_id": spec.world_id,
                "label": spec.label,
                "probability_weight": spec.probability_weight,
                "assumptions": spec.assumptions,
                "tripwires": spec.tripwires,
                "plan_quality_status": audit.get("status"),
                "plan_quality_score": audit.get("total_score"),
                "expected_admission_prob": audit.get("expected_admission_prob"),
                "expected_tail_risk": audit.get("expected_tail_risk"),
                "top_findings": audit.get("findings", [])[:3],
                "audit": audit,
            }
        )

    for row in world_rows:
        row["score_delta_vs_baseline"] = round(float(row["plan_quality_score"] or 0.0) - baseline_score, 6)
        row["admission_delta_vs_baseline"] = round(float(row["expected_admission_prob"] or 0.0) - baseline_admission, 6)

    total_weight = sum(max(0.0, float(row["probability_weight"])) for row in world_rows) or 1.0
    weighted_pass_rate = sum(
        float(row["probability_weight"])
        for row in world_rows
        if row["plan_quality_status"] == "pass"
    ) / total_weight
    weighted_blocked_rate = sum(
        float(row["probability_weight"])
        for row in world_rows
        if row["plan_quality_status"] == "blocked"
    ) / total_weight
    robust_status = "robust"
    if weighted_blocked_rate >= 0.12:
        robust_status = "fragile"
    elif weighted_pass_rate < 0.70:
        robust_status = "needs_hedging"
    return {
        "status": robust_status,
        "world_count": len(world_rows),
        "weighted_pass_rate": round(weighted_pass_rate, 6),
        "weighted_blocked_rate": round(weighted_blocked_rate, 6),
        "baseline_plan_quality_score": round(baseline_score, 6),
        "baseline_expected_admission_prob": round(baseline_admission, 6),
        "worlds": world_rows,
        "sensitivity_rank": _summarize_sensitivity(world_rows),
        "method_note": (
            "Parallel-world analysis makes assumptions first-class outputs, then stress-tests the same "
            "ordered plan under branch-specific shocks instead of trusting one static probability."
        ),
    }


def build_markdown_parallel_world_analysis(result: dict[str, Any]) -> str:
    """Render parallel-world analysis as Markdown."""
    lines = [
        "# Parallel World Volunteer Analysis",
        "",
        f"Status: `{result.get('status', 'unknown')}`",
        f"Worlds: {result.get('world_count', 0)}",
        f"Weighted pass rate: {float(result.get('weighted_pass_rate', 0.0)):.1%}",
        f"Weighted blocked rate: {float(result.get('weighted_blocked_rate', 0.0)):.1%}",
        "",
        result.get("method_note", ""),
        "",
        "## Worlds",
        "",
        "| World | Weight | Status | Score | Admission | Tail Risk | Score Delta |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in result.get("worlds", []) or []:
        lines.append(
            f"| `{row.get('world_id', '')}` {row.get('label', '')} | "
            f"{float(row.get('probability_weight', 0.0)):.1%} | "
            f"`{row.get('plan_quality_status', '')}` | "
            f"{float(row.get('plan_quality_score', 0.0)):.1%} | "
            f"{float(row.get('expected_admission_prob', 0.0)):.1%} | "
            f"{float(row.get('expected_tail_risk', 0.0)):.1%} | "
            f"{float(row.get('score_delta_vs_baseline', 0.0)):.1%} |"
        )

    lines.extend(["", "## Most Sensitive Worlds", ""])
    for idx, item in enumerate(result.get("sensitivity_rank", []) or [], 1):
        lines.append(
            f"{idx}. `{item.get('world_id', '')}` {item.get('label', '')}: "
            f"{item.get('status', '')}, score delta {float(item.get('score_delta_vs_baseline', 0.0)):.1%}"
        )
        for tripwire in item.get("tripwires", [])[:2]:
            lines.append(f"   - Tripwire: {tripwire}")
    return "\n".join(lines) + "\n"

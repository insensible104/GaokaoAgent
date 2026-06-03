"""Ablation runner for 2025 volunteer-plan backtesting."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

from evaluation.backtest_2025 import run_plan_backtest, summarize_backtests
from evaluation.baselines import BaselineName, build_baseline_plan
from evaluation.schemas import ActualMajorGroupOutcome, PlanBacktestResult
from models.game_matrix import MajorGroupRow, VolunteerPlan
from models.user_profile import UserProfile
from recommendation.major_choice_planner import build_volunteer_plan


AblationVariant = BaselineName | str
QUANT_TUNED_SHADOW_VARIANT = "quant_tuned_shadow"
DEFAULT_ABLATION_VARIANTS: list[str] = [
    "full",
    "probability_only",
    "history_tight_rank",
    "safe_first",
    "no_tradeoff_policy",
    "no_arbitrage",
    "arbitrage_only",
    "front_major_boost",
    "segment_market",
    "guarded_arbitrage",
    "prefix_optimizer",
    "plan_change_guarded",
]
DELTA_METRICS = [
    "success_rate",
    "sliding_rate",
    "selected_major_hit_rate",
    "preferred_major_hit_rate",
    "blacklist_hit_rate",
    "tail_assignment_rate",
    "wasted_score_rate",
    "average_first_hit_index",
    "average_first_hit_margin",
    "average_assigned_major_utility",
]


def _load_plan_record(record: dict) -> tuple[str, int, VolunteerPlan, list[str], list[str]]:
    plan_payload = record.get("plan") or record.get("volunteer_plan")
    if not plan_payload:
        raise ValueError("Each ablation record must contain `plan` or `volunteer_plan`.")
    plan = plan_payload if isinstance(plan_payload, VolunteerPlan) else VolunteerPlan(**plan_payload)
    user_rank = record.get("user_rank") or plan.user_rank
    if user_rank is None:
        raise ValueError("Each ablation record must contain `user_rank`, or plan.user_rank must be set.")
    return (
        str(record.get("case_id") or ""),
        int(user_rank),
        plan,
        list(record.get("preferred_majors") or []),
        list(record.get("blacklist_majors") or []),
    )


def _load_candidate_rows(record: dict) -> list[MajorGroupRow]:
    rows_payload = (
        record.get("candidate_rows")
        or record.get("major_group_rows")
        or record.get("rows")
        or []
    )
    return [
        row if isinstance(row, MajorGroupRow) else MajorGroupRow(**row)
        for row in rows_payload
    ]


def _load_user_profile(record: dict, plan: VolunteerPlan) -> UserProfile:
    profile_payload = record.get("user_profile") or record.get("profile")
    if profile_payload:
        return profile_payload if isinstance(profile_payload, UserProfile) else UserProfile(**profile_payload)
    if plan.user_score is None or plan.user_rank is None or not plan.subject_group:
        raise ValueError(
            "Baseline ablations require `user_profile`, or a plan with user_score, user_rank, and subject_group."
        )
    return UserProfile(
        score=int(plan.user_score),
        rank=int(plan.user_rank),
        subject_group=plan.subject_group,
        preferred_majors=list(record.get("preferred_majors") or []),
        blacklist_majors=list(record.get("blacklist_majors") or []),
    )


def _row_feature(row: MajorGroupRow, feature: str) -> float:
    if feature == "predicted_prob":
        return float(row.admission_prob or 0.0)
    value = getattr(row, feature, 0.0)
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _build_quant_tuned_shadow_plan(
    *,
    rows: list[MajorGroupRow],
    profile: UserProfile,
    weights: dict[str, float],
    max_choices: int | None,
) -> VolunteerPlan:
    if not weights:
        raise ValueError("quant_tuned_shadow requires non-empty tuning weights.")
    ordered = sorted(
        rows,
        key=lambda row: sum(_row_feature(row, feature) * float(weight) for feature, weight in weights.items()),
        reverse=True,
    )
    return build_volunteer_plan(ordered, profile, max_choices=max_choices)


def _build_variant_plan(
    *,
    variant: str,
    record: dict,
    full_plan: VolunteerPlan,
    quant_shadow_weights: dict[str, float] | None = None,
    quant_shadow_variant_name: str = QUANT_TUNED_SHADOW_VARIANT,
) -> VolunteerPlan:
    if variant == "full":
        return full_plan

    rows = _load_candidate_rows(record)
    if not rows:
        raise ValueError(
            f"Variant `{variant}` requires candidate rows in `candidate_rows`, `major_group_rows`, or `rows`."
        )
    profile = _load_user_profile(record, full_plan)
    max_choices = len(full_plan.choices) if full_plan.choices else None
    if variant == quant_shadow_variant_name:
        return _build_quant_tuned_shadow_plan(
            rows=rows,
            profile=profile,
            weights=quant_shadow_weights or {},
            max_choices=max_choices,
        )
    return build_baseline_plan(
        rows=rows,
        profile=profile,
        baseline=variant,  # type: ignore[arg-type]
        max_choices=max_choices,
    )


def _delta_vs_full(summary: dict, full_summary: dict) -> dict[str, float]:
    return {
        metric: round(float(summary.get(metric, 0.0)) - float(full_summary.get(metric, 0.0)), 6)
        for metric in DELTA_METRICS
    }


def run_ablation_backtest_records(
    *,
    records: Sequence[dict],
    actual_outcomes: Iterable[ActualMajorGroupOutcome],
    variants: Sequence[str] | None = None,
    quant_shadow_weights: dict[str, float] | None = None,
    quant_shadow_variant_name: str = QUANT_TUNED_SHADOW_VARIANT,
) -> dict:
    """Run full and baseline variants through the same 2025 outcome labels."""
    selected_variants = list(variants or DEFAULT_ABLATION_VARIANTS)
    if "full" not in selected_variants:
        selected_variants.insert(0, "full")
    if quant_shadow_weights and quant_shadow_variant_name not in selected_variants:
        selected_variants.append(quant_shadow_variant_name)
    actual_outcomes = list(actual_outcomes)

    per_variant_results: dict[str, list[PlanBacktestResult]] = defaultdict(list)
    per_case: list[dict] = []

    for record in records:
        case_id, user_rank, full_plan, preferred_majors, blacklist_majors = _load_plan_record(record)
        for variant in selected_variants:
            plan = _build_variant_plan(
                variant=variant,
                record=record,
                full_plan=full_plan,
                quant_shadow_weights=quant_shadow_weights if variant == quant_shadow_variant_name else None,
                quant_shadow_variant_name=quant_shadow_variant_name,
            )
            result = run_plan_backtest(
                plan=plan,
                actual_outcomes=actual_outcomes,
                user_rank=user_rank,
                preferred_majors=preferred_majors,
                blacklist_majors=blacklist_majors,
                case_id=case_id,
            )
            per_variant_results[variant].append(result)
            per_case.append(
                {
                    "case_id": case_id,
                    "variant": variant,
                    **result.model_dump(exclude={"choice_outcomes"}),
                }
            )

    summaries = {
        variant: summarize_backtests(per_variant_results[variant])
        for variant in selected_variants
    }
    full_summary = summaries["full"]
    deltas = {
        variant: _delta_vs_full(summary, full_summary)
        for variant, summary in summaries.items()
        if variant != "full"
    }
    return {
        "case_count": len(records),
        "variants": selected_variants,
        "quant_shadow": {
            "variant": quant_shadow_variant_name if quant_shadow_weights else None,
            "weights": quant_shadow_weights or {},
            "note": (
                "Shadow variants validate quant-tuning weights offline against frozen candidate rows; "
                "they do not change runtime recommendation weights."
            ),
        },
        "summaries": summaries,
        "deltas_vs_full": deltas,
        "per_case": per_case,
    }


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_markdown_ablation_report(result: dict) -> str:
    """Build a compact Markdown table for project docs or experiment logs."""
    lines = [
        "# 2025 Backtest Ablation Report",
        "",
        f"Cases: {result.get('case_count', 0)}",
        "",
        "| Variant | Cases | Success | Preferred Major | Blacklist | Tail Assignment | Avg Utility | Delta Success | Delta Preferred |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    full_summary = result.get("summaries", {}).get("full", {})
    for variant in result.get("variants", []):
        summary = result.get("summaries", {}).get(variant, {})
        delta = result.get("deltas_vs_full", {}).get(variant, {})
        delta_success = "" if variant == "full" else _pct(delta.get("success_rate", 0.0))
        delta_preferred = "" if variant == "full" else _pct(delta.get("preferred_major_hit_rate", 0.0))
        if variant == "full":
            delta_success = _pct(0.0)
            delta_preferred = _pct(0.0)
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{variant}`",
                    str(summary.get("case_count", 0)),
                    _pct(float(summary.get("success_rate", 0.0))),
                    _pct(float(summary.get("preferred_major_hit_rate", 0.0))),
                    _pct(float(summary.get("blacklist_hit_rate", 0.0))),
                    _pct(float(summary.get("tail_assignment_rate", 0.0))),
                    f"{float(summary.get('average_assigned_major_utility', 0.0)):.3f}",
                    delta_success,
                    delta_preferred,
                ]
            )
            + " |"
        )

    if full_summary.get("case_count", 0) == 0:
        lines.extend(["", "No cases were evaluated."])
    return "\n".join(lines) + "\n"

"""Baseline plan builders for recommendation-system ablations."""

from __future__ import annotations

from typing import Iterable, Literal

from models.game_matrix import MajorGroupRow
from models.user_profile import UserProfile
from recommendation.major_choice_planner import build_volunteer_plan
from recommendation.prefix_optimizer import optimize_prefix_order


BaselineName = Literal[
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
]


def build_baseline_plan(
    *,
    rows: Iterable[MajorGroupRow],
    profile: UserProfile,
    baseline: BaselineName,
    max_choices: int | None = None,
):
    """Build a baseline volunteer plan from the same candidate pool."""
    rows = list(rows)

    if baseline == "probability_only":
        ordered = sorted(rows, key=lambda row: row.admission_prob, reverse=True)
    elif baseline == "history_tight_rank":
        ordered = sorted(rows, key=lambda row: abs(row.rank_diff))
    elif baseline == "safe_first":
        ordered = sorted(
            rows,
            key=lambda row: (
                row.admission_prob,
                -row.tail_assignment_risk,
                row.major_utility_mean,
            ),
            reverse=True,
        )
    elif baseline == "no_tradeoff_policy":
        ordered = sorted(
            rows,
            key=lambda row: (
                row.admission_prob * 0.55
                + row.major_utility_mean * 0.30
                + row.quota_stability_score * 0.15
                - row.tail_assignment_risk * 0.25
            ),
            reverse=True,
        )
    elif baseline == "no_arbitrage":
        ordered = sorted(
            rows,
            key=lambda row: (
                row.admission_prob * 0.50
                + row.major_utility_mean * 0.25
                + row.quota_stability_score * 0.15
                + row.variance_opportunity_score * 0.05
                - row.tail_assignment_risk * 0.25
                - (0.15 if row.is_blacklist_risk else 0.0)
            ),
            reverse=True,
        )
    elif baseline == "arbitrage_only":
        ordered = sorted(
            rows,
            key=lambda row: (
                row.arbitrage_score * 0.45
                + row.front_major_arbitrage_score * 0.20
                + row.relative_lift * 0.15
                + row.market_discount_score * 0.15
                + row.admission_prob * 0.10
                - row.rebound_risk * 0.15
                - row.tail_assignment_risk * 0.10
            ),
            reverse=True,
        )
    elif baseline == "front_major_boost":
        ordered = sorted(
            rows,
            key=lambda row: (
                row.admission_prob * 0.32
                + row.major_utility_mean * 0.20
                + row.front_major_arbitrage_score * 0.28
                + row.front_major_hit_prob * 0.12
                + row.arbitrage_score * 0.08
                - row.tail_assignment_risk * 0.20
                - row.rebound_risk * 0.08
            ),
            reverse=True,
        )
    elif baseline == "segment_market":
        ordered = sorted(
            rows,
            key=lambda row: (
                row.admission_prob * 0.42
                + row.major_utility_mean * 0.20
                + row.quota_stability_score * 0.08
                + row.arbitrage_score * 0.08
                + row.front_major_arbitrage_score * 0.08
                + row.segment_demand_score * 0.10
                + row.low_attention_signal * 0.04
                - row.segment_rebound_risk * 0.10
                - row.tail_assignment_risk * 0.24
                - (0.15 if row.is_blacklist_risk else 0.0)
            ),
            reverse=True,
        )
    elif baseline == "guarded_arbitrage":
        def guarded_score(row: MajorGroupRow) -> float:
            guard_penalty = 0.0
            if row.admission_prob < 0.50:
                guard_penalty += 0.15
            if row.major_utility_mean < 0.45:
                guard_penalty += 0.10
            if row.tail_assignment_risk > 0.55:
                guard_penalty += 0.25
            if row.segment_rebound_risk > 0.55 or row.rebound_risk > 0.55:
                guard_penalty += 0.15
            if row.is_blacklist_risk:
                guard_penalty += 0.20
            return (
                row.admission_prob * 0.34
                + row.major_utility_mean * 0.18
                + row.front_major_arbitrage_score * 0.16
                + row.front_major_hit_prob * 0.08
                + row.arbitrage_score * 0.10
                + row.segment_demand_score * 0.10
                + row.low_attention_signal * 0.05
                + row.quota_stability_score * 0.05
                - row.tail_assignment_risk * 0.22
                - max(row.segment_rebound_risk, row.rebound_risk) * 0.12
                - guard_penalty
            )

        ordered = sorted(rows, key=guarded_score, reverse=True)
    elif baseline == "prefix_optimizer":
        ordered = optimize_prefix_order(
            rows=rows,
            profile=profile,
            max_choices=max_choices,
        )
    else:
        raise ValueError(f"Unknown baseline: {baseline}")

    return build_volunteer_plan(ordered, profile, max_choices=max_choices)

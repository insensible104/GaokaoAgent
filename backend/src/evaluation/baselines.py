"""Baseline plan builders for recommendation-system ablations."""

from __future__ import annotations

from typing import Iterable, Literal

from models.game_matrix import MajorGroupRow
from models.user_profile import UserProfile
from recommendation.major_choice_planner import build_volunteer_plan


BaselineName = Literal[
    "probability_only",
    "history_tight_rank",
    "safe_first",
    "no_tradeoff_policy",
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
    else:
        raise ValueError(f"Unknown baseline: {baseline}")

    return build_volunteer_plan(ordered, profile, max_choices=max_choices)


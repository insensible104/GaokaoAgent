"""Preserve strategy-bucket coverage through Pareto filtering and selection."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from engines.pareto_optimizer import Objective, compute_pareto_frontier
from models.game_matrix import MajorGroupRow, StrategyTag


STRATEGY_ORDER = (StrategyTag.RUSH, StrategyTag.TARGET, StrategyTag.SAFE)


def count_strategy_rows(rows: Iterable[MajorGroupRow]) -> dict[str, int]:
    counts = {tag.value: 0 for tag in STRATEGY_ORDER}
    for row in rows:
        value = row.strategy_tag.value if hasattr(row.strategy_tag, "value") else str(row.strategy_tag)
        if value in counts:
            counts[value] += 1
    return counts


def _pareto_ranked_bucket(rows: list[MajorGroupRow]) -> list[MajorGroupRow]:
    if len(rows) <= 1:
        return rows[:]
    objectives = [
        Objective(name="admission", key="admission_prob", maximize=True),
        Objective(name="fit", key="comprehensive_score", maximize=True),
        Objective(name="adjustment", key="adjustment_risk", maximize=False),
    ]
    result = compute_pareto_frontier(
        candidates=[
            {
                "volunteer_index": index,
                "school_name": row.school_name,
                "major_name": ",".join(row.major_list[:3]),
                "admission_prob": row.admission_prob,
                "comprehensive_score": row.comprehensive_score,
                "adjustment_risk": row.adjustment_risk,
            }
            for index, row in enumerate(rows)
        ],
        objectives=objectives,
        max_rank=len(rows),
    )
    rank_by_index = {
        solution.volunteer_index: solution.pareto_rank
        for solution in result.all_solutions
    }
    return sorted(
        rows,
        key=lambda row: (
            rank_by_index.get(rows.index(row), len(rows) + 1),
            -float(row.comprehensive_score),
            -float(row.admission_prob),
            float(row.adjustment_risk),
        ),
    )


def retain_strategy_candidates(
    rows: Iterable[MajorGroupRow],
    *,
    desired: dict[str, int],
    reserve: int = 3,
) -> list[MajorGroupRow]:
    """Apply Pareto ordering inside each strategy without collapsing a bucket."""
    source = list(rows)
    retained: list[MajorGroupRow] = []
    for tag in STRATEGY_ORDER:
        bucket = [row for row in source if row.strategy_tag == tag]
        keep_count = min(len(bucket), max(0, int(desired.get(tag.value, 0))) + max(0, reserve))
        retained.extend(_pareto_ranked_bucket(bucket)[:keep_count])
    return retained


def fill_plan_capacity(
    *,
    selected_rows: Iterable[MajorGroupRow],
    all_rows: Iterable[MajorGroupRow],
    total_count: int,
) -> tuple[list[MajorGroupRow], dict[str, int]]:
    """Fill unused plan slots with real candidates without changing strategy tags."""
    selected = list(selected_rows)
    requested = max(0, int(total_count))
    initial_count = len(selected)
    selected_keys = {
        (row.school_code, row.major_group_code)
        for row in selected
    }
    strategy_priority = {
        StrategyTag.TARGET: 0,
        StrategyTag.SAFE: 1,
        StrategyTag.RUSH: 2,
    }
    remaining = [
        row
        for row in all_rows
        if (row.school_code, row.major_group_code) not in selected_keys
    ]
    remaining.sort(
        key=lambda row: (
            strategy_priority.get(row.strategy_tag, 3),
            -float(row.comprehensive_score),
            -float(row.admission_prob),
            float(row.adjustment_risk),
            row.school_name,
            row.major_group_code,
        )
    )
    selected.extend(remaining[: max(0, requested - initial_count)])
    final_count = len(selected)
    return selected, {
        "requested_count": requested,
        "initial_count": initial_count,
        "filled_count": max(0, final_count - initial_count),
        "final_count": final_count,
        "remaining_shortfall": max(0, requested - final_count),
    }


def build_coverage_report(
    *,
    desired: dict[str, int],
    classified_rows: Iterable[MajorGroupRow],
    post_pareto_rows: Iterable[MajorGroupRow],
    selected_rows: Iterable[MajorGroupRow],
) -> dict[str, Any]:
    desired_counts = {
        tag.value: max(0, int(desired.get(tag.value, 0)))
        for tag in STRATEGY_ORDER
    }
    classified = count_strategy_rows(classified_rows)
    post_pareto = count_strategy_rows(post_pareto_rows)
    selected = count_strategy_rows(selected_rows)
    deficits = {
        key: desired_counts[key] - selected[key]
        for key in desired_counts
        if selected[key] < desired_counts[key]
    }
    actions: list[str] = []
    for key in desired_counts:
        if classified[key] < desired_counts[key]:
            actions.append(
                f"{key}: only {classified[key]} qualified candidates for desired {desired_counts[key]}; "
                "do not relabel weaker rows."
            )
        elif post_pareto[key] < desired_counts[key]:
            actions.append(
                f"{key}: Pareto retention left {post_pareto[key]} candidates for desired {desired_counts[key]}."
            )
        elif selected[key] < desired_counts[key]:
            actions.append(
                f"{key}: selected {selected[key]} of desired {desired_counts[key]}; review fallback ordering."
            )
        else:
            actions.append(
                f"{key}: selected {selected[key]} candidates against desired {desired_counts[key]}."
            )

    return {
        "desired": desired_counts,
        "classified": classified,
        "post_pareto": post_pareto,
        "selected": selected,
        "deficits": deficits,
        "coverage_sufficient": not deficits,
        "actions": actions,
    }

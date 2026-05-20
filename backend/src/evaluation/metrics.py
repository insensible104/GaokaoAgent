"""Metrics for prospective volunteer-plan backtesting."""

from __future__ import annotations

from typing import Iterable, List, Mapping, Optional, Sequence

from models.game_matrix import MajorOption, VolunteerChoice, VolunteerPlan

from evaluation.schemas import (
    ActualMajorGroupOutcome,
    BacktestAggregateMetrics,
    ChoiceBacktestOutcome,
    PlanBacktestResult,
)


def _norm(value: object) -> str:
    return str(value or "").strip()


def _norm_code(value: object) -> str:
    text = _norm(value)
    if text.lower() == "nan":
        return ""
    if text.endswith(".0"):
        return text[:-2]
    return text


def _index_outcomes(
    actual_outcomes: Iterable[ActualMajorGroupOutcome],
) -> dict[tuple[str, str, str], ActualMajorGroupOutcome]:
    index: dict[tuple[str, str, str], ActualMajorGroupOutcome] = {}
    for outcome in actual_outcomes:
        full_key = (_norm_code(outcome.school_code), _norm(outcome.school_name), _norm_code(outcome.major_group_code))
        index[full_key] = outcome
        index[("", full_key[1], full_key[2])] = outcome
        if full_key[0]:
            index[(full_key[0], "", full_key[2])] = outcome
    return index


def _lookup_outcome(
    choice: VolunteerChoice,
    outcome_index: Mapping[tuple[str, str, str], ActualMajorGroupOutcome],
) -> Optional[ActualMajorGroupOutcome]:
    full_key = (_norm_code(choice.school_code), _norm(choice.school_name), _norm_code(choice.major_group_code))
    name_group_key = ("", full_key[1], full_key[2])
    code_group_key = (full_key[0], "", full_key[2])
    return (
        outcome_index.get(full_key)
        or outcome_index.get(name_group_key)
        or outcome_index.get(code_group_key)
    )


def _major_utility(major_name: Optional[str], choices: Sequence[MajorOption]) -> float:
    if not major_name:
        return 0.0
    for option in choices:
        if option.major_name == major_name:
            return float(option.user_utility)
    return 0.5


def _contains_keyword(name: Optional[str], keywords: Sequence[str]) -> bool:
    if not name:
        return False
    return any(keyword and keyword in name for keyword in keywords)


def _resolve_assigned_major(
    *,
    user_rank: int,
    choice: VolunteerChoice,
    outcome: ActualMajorGroupOutcome,
) -> tuple[Optional[str], Optional[str], Optional[int], bool]:
    """Resolve actual in-group assignment from 2025 major cutoffs.

    The first pass follows the user's ordered six majors. If none of those
    majors is reachable and adjustment is accepted, the fallback is the
    reachable major with the largest cutoff rank, which approximates the
    coldest admitted tail major.
    """
    if not outcome.major_min_ranks:
        return None, None, None, False

    selected_names = [option.major_name for option in choice.major_choices]
    for major_name in selected_names:
        cutoff = outcome.major_min_ranks.get(major_name)
        if cutoff is not None and user_rank <= cutoff:
            return major_name, outcome.major_codes.get(major_name), cutoff - user_rank, True

    if not choice.obey_adjustment:
        return None, None, None, False

    reachable = [
        (major_name, cutoff)
        for major_name, cutoff in outcome.major_min_ranks.items()
        if user_rank <= cutoff
    ]
    if not reachable:
        return None, None, None, False

    assigned_name, cutoff = sorted(reachable, key=lambda item: item[1], reverse=True)[0]
    return (
        assigned_name,
        outcome.major_codes.get(assigned_name),
        cutoff - user_rank,
        assigned_name in selected_names,
    )


def evaluate_volunteer_plan(
    *,
    plan: VolunteerPlan,
    actual_outcomes: Iterable[ActualMajorGroupOutcome],
    user_rank: int,
    preferred_majors: Sequence[str] | None = None,
    blacklist_majors: Sequence[str] | None = None,
    case_id: str = "",
    wasted_margin_threshold: int = 12_000,
    low_utility_threshold: float = 0.35,
) -> PlanBacktestResult:
    """Evaluate a frozen volunteer plan against actual 2025 outcomes."""
    preferred_majors = preferred_majors or []
    blacklist_majors = blacklist_majors or []
    outcome_index = _index_outcomes(actual_outcomes)

    choice_outcomes: List[ChoiceBacktestOutcome] = []
    first_hit: ChoiceBacktestOutcome | None = None

    for choice in plan.choices:
        actual = _lookup_outcome(choice, outcome_index)
        if not actual:
            choice_outcomes.append(
                ChoiceBacktestOutcome(
                    choice_index=choice.choice_index,
                    school_code=choice.school_code,
                    school_name=choice.school_name,
                    major_group_code=choice.major_group_code,
                    group_admitted=False,
                    failure_reason="missing_actual_outcome",
                )
            )
            continue

        group_admitted = user_rank <= actual.actual_group_min_rank
        assigned_major = None
        assigned_major_code = None
        assigned_margin = None
        selected_hit = False
        if group_admitted:
            assigned_major, assigned_major_code, assigned_margin, selected_hit = _resolve_assigned_major(
                user_rank=user_rank,
                choice=choice,
                outcome=actual,
            )

        utility = _major_utility(assigned_major, choice.major_choices)
        preferred_hit = _contains_keyword(assigned_major, preferred_majors)
        blacklist_hit = _contains_keyword(assigned_major, blacklist_majors)
        tail_hit = bool(group_admitted and (not selected_hit or utility <= low_utility_threshold or blacklist_hit))

        outcome = ChoiceBacktestOutcome(
            choice_index=choice.choice_index,
            school_code=choice.school_code,
            school_name=choice.school_name,
            major_group_code=choice.major_group_code,
            group_admitted=group_admitted,
            group_rank_margin=actual.actual_group_min_rank - user_rank,
            assigned_major_name=assigned_major,
            assigned_major_code=assigned_major_code,
            assigned_major_rank_margin=assigned_margin,
            assigned_major_utility=utility,
            selected_major_hit=selected_hit,
            preferred_major_hit=preferred_hit,
            blacklist_hit=blacklist_hit,
            tail_assignment_hit=tail_hit,
            failure_reason="" if group_admitted else "rank_below_actual_group_cutoff",
        )
        if group_admitted and first_hit is None:
            outcome.is_first_hit = True
            first_hit = outcome
        choice_outcomes.append(outcome)

    success = first_hit is not None
    sliding = not success
    wasted_score_risk = bool(success and first_hit and (first_hit.group_rank_margin or 0) >= wasted_margin_threshold)
    metrics = {
        "success": 1.0 if success else 0.0,
        "sliding": 1.0 if sliding else 0.0,
        "first_hit_index": float(first_hit.choice_index) if first_hit else 0.0,
        "first_hit_margin": float(first_hit.group_rank_margin or 0) if first_hit else 0.0,
        "assigned_major_utility": first_hit.assigned_major_utility if first_hit else 0.0,
        "selected_major_hit": 1.0 if first_hit and first_hit.selected_major_hit else 0.0,
        "preferred_major_hit": 1.0 if first_hit and first_hit.preferred_major_hit else 0.0,
        "blacklist_hit": 1.0 if first_hit and first_hit.blacklist_hit else 0.0,
        "tail_assignment_hit": 1.0 if first_hit and first_hit.tail_assignment_hit else 0.0,
        "wasted_score_risk": 1.0 if wasted_score_risk else 0.0,
    }

    return PlanBacktestResult(
        case_id=case_id,
        user_rank=user_rank,
        success=success,
        first_hit_index=first_hit.choice_index if first_hit else None,
        first_hit_school=first_hit.school_name if first_hit else None,
        first_hit_major_group=first_hit.major_group_code if first_hit else None,
        assigned_major_name=first_hit.assigned_major_name if first_hit else None,
        assigned_major_code=first_hit.assigned_major_code if first_hit else None,
        first_hit_margin=first_hit.group_rank_margin if first_hit else None,
        assigned_major_utility=first_hit.assigned_major_utility if first_hit else 0.0,
        selected_major_hit=bool(first_hit and first_hit.selected_major_hit),
        preferred_major_hit=bool(first_hit and first_hit.preferred_major_hit),
        blacklist_hit=bool(first_hit and first_hit.blacklist_hit),
        tail_assignment_hit=bool(first_hit and first_hit.tail_assignment_hit),
        wasted_score_risk=wasted_score_risk,
        sliding=sliding,
        failure_reason="" if success else "all_choices_failed_actual_2025_cutoff",
        choice_outcomes=choice_outcomes,
        metrics=metrics,
    )


def aggregate_backtest_results(results: Sequence[PlanBacktestResult]) -> BacktestAggregateMetrics:
    """Aggregate plan-level 2025 backtest results."""
    if not results:
        return BacktestAggregateMetrics(
            case_count=0,
            success_rate=0.0,
            sliding_rate=0.0,
            selected_major_hit_rate=0.0,
            preferred_major_hit_rate=0.0,
            blacklist_hit_rate=0.0,
            tail_assignment_rate=0.0,
            wasted_score_rate=0.0,
            average_first_hit_index=0.0,
            average_first_hit_margin=0.0,
            average_assigned_major_utility=0.0,
        )

    count = len(results)
    success_results = [result for result in results if result.success]

    def mean(values: Sequence[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    return BacktestAggregateMetrics(
        case_count=count,
        success_rate=mean([1.0 if result.success else 0.0 for result in results]),
        sliding_rate=mean([1.0 if result.sliding else 0.0 for result in results]),
        selected_major_hit_rate=mean([1.0 if result.selected_major_hit else 0.0 for result in results]),
        preferred_major_hit_rate=mean([1.0 if result.preferred_major_hit else 0.0 for result in results]),
        blacklist_hit_rate=mean([1.0 if result.blacklist_hit else 0.0 for result in results]),
        tail_assignment_rate=mean([1.0 if result.tail_assignment_hit else 0.0 for result in results]),
        wasted_score_rate=mean([1.0 if result.wasted_score_risk else 0.0 for result in results]),
        average_first_hit_index=mean([float(result.first_hit_index or 0) for result in success_results]),
        average_first_hit_margin=mean([float(result.first_hit_margin or 0) for result in success_results]),
        average_assigned_major_utility=mean([result.assigned_major_utility for result in success_results]),
    )

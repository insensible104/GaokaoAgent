"""Smoke tests for 2025 prospective backtest evaluation."""

from __future__ import annotations

from models.game_matrix import AdjustmentAdvice, MajorOption, VolunteerChoice, VolunteerPlan
from evaluation.backtest_2025 import run_plan_backtest
from evaluation.metrics import aggregate_backtest_results
from evaluation.schemas import ActualMajorGroupOutcome


def _choice(index: int, school: str, group: str, prob: float, majors: list[MajorOption]) -> VolunteerChoice:
    return VolunteerChoice(
        choice_index=index,
        school_code=f"{index:05d}",
        school_name=school,
        major_group_code=group,
        major_choices=majors,
        obey_adjustment=True,
        adjustment_advice=AdjustmentAdvice.CAUTIOUS,
        group_admission_prob=prob,
        expected_major_utility=sum(major.user_utility for major in majors) / len(majors),
        tail_assignment_risk=0.4,
    )


def test_2025_backtest_finds_first_hit_and_major_assignment() -> None:
    cs = MajorOption(major_name="计算机类", user_utility=0.95)
    civil = MajorOption(major_name="土木类", user_utility=0.15, is_blacklisted=True)
    plan = VolunteerPlan(
        user_rank=12000,
        choices=[
            _choice(1, "A大学", "201", 0.55, [cs]),
            _choice(2, "B大学", "202", 0.82, [cs, civil]),
        ],
    )
    plan.calculate_statistics()
    actual = [
        ActualMajorGroupOutcome(
            school_code="00001",
            school_name="A大学",
            major_group_code="201",
            actual_group_min_rank=11000,
            major_min_ranks={"计算机类": 10500},
            major_codes={"计算机类": "101"},
        ),
        ActualMajorGroupOutcome(
            school_code="00002",
            school_name="B大学",
            major_group_code="202",
            actual_group_min_rank=15000,
            major_min_ranks={"计算机类": 11500, "土木类": 18000},
            major_codes={"计算机类": "101", "土木类": "106"},
        ),
    ]

    result = run_plan_backtest(
        plan=plan,
        actual_outcomes=actual,
        user_rank=12000,
        preferred_majors=["计算机"],
        blacklist_majors=["土木"],
        case_id="smoke",
    )

    assert result.success is True
    assert result.first_hit_index == 2
    assert result.assigned_major_name == "土木类"
    assert result.assigned_major_code == "106"
    assert result.blacklist_hit is True
    assert result.tail_assignment_hit is True
    assert result.choice_outcomes[0].failure_reason == "rank_below_actual_group_cutoff"


def test_aggregate_metrics_are_stable() -> None:
    cs = MajorOption(major_name="计算机类", user_utility=0.95)
    plan = VolunteerPlan(
        user_rank=9000,
        choices=[_choice(1, "C大学", "301", 0.9, [cs])],
    )
    plan.calculate_statistics()
    actual = [
        ActualMajorGroupOutcome(
            school_code="00001",
            school_name="C大学",
            major_group_code="301",
            actual_group_min_rank=10000,
            major_min_ranks={"计算机类": 9800},
            major_codes={"计算机类": "101"},
        )
    ]
    result = run_plan_backtest(
        plan=plan,
        actual_outcomes=actual,
        user_rank=9000,
        preferred_majors=["计算机"],
    )
    summary = aggregate_backtest_results([result])

    assert summary.case_count == 1
    assert summary.success_rate == 1.0
    assert summary.selected_major_hit_rate == 1.0
    assert summary.average_first_hit_index == 1.0
    assert result.assigned_major_code == "101"


def test_2025_backtest_matches_school_rename_by_code_and_group() -> None:
    option = MajorOption(major_name="Accounting", user_utility=0.9)
    plan = VolunteerPlan(
        user_rank=10000,
        choices=[
            VolunteerChoice(
                choice_index=1,
                school_code="11847",
                school_name="Old School Name",
                major_group_code="216",
                major_choices=[option],
                obey_adjustment=True,
                adjustment_advice=AdjustmentAdvice.CAUTIOUS,
                group_admission_prob=0.8,
                expected_major_utility=0.9,
                tail_assignment_risk=0.1,
            )
        ],
    )
    plan.calculate_statistics()
    actual = [
        ActualMajorGroupOutcome(
            school_code="11847",
            school_name="New School Name",
            major_group_code="216",
            actual_group_min_rank=12000,
            major_min_ranks={"Accounting": 12000},
            major_codes={"Accounting": "01"},
        )
    ]

    result = run_plan_backtest(
        plan=plan,
        actual_outcomes=actual,
        user_rank=10000,
    )

    assert result.success is True
    assert result.first_hit_school == "Old School Name"
    assert result.assigned_major_code == "01"


if __name__ == "__main__":
    test_2025_backtest_finds_first_hit_and_major_assignment()
    test_aggregate_metrics_are_stable()
    test_2025_backtest_matches_school_rename_by_code_and_group()
    print("2025 backtest smoke tests passed")

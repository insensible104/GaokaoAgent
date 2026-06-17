"""Smoke tests for conservative volunteer-plan probability disclosure."""

from models.game_matrix import (
    MajorOption,
    VolunteerChoice,
    VolunteerPlan,
)
from recommendation import major_choice_planner


def _choice(index: int, probability: float) -> VolunteerChoice:
    return VolunteerChoice(
        choice_index=index,
        school_code=str(index),
        school_name=f"School {index}",
        major_group_code=str(800 + index),
        major_choices=[MajorOption(major_name="Computer Science")],
        group_admission_prob=probability,
        expected_major_utility=0.8,
        tail_assignment_risk=0.1,
    )


def test_plan_probability_is_disclosed_as_uncalibrated_interval() -> None:
    plan = VolunteerPlan(
        year=2026,
        subject_group="physics",
        user_rank=12000,
        choices=[_choice(1, 0.6), _choice(2, 0.6)],
    )

    plan.calculate_statistics()

    assert plan.probability_is_calibrated is False
    assert plan.probability_method == "correlated_outcomes_heuristic"
    assert plan.admission_probability_lower_bound == 0.6
    assert plan.admission_probability_upper_bound == 1.0
    assert plan.expected_admission_prob == 0.84
    assert "相关" in plan.probability_warning


def test_family_facing_probability_uses_range_not_precise_point() -> None:
    assert hasattr(major_choice_planner, "format_plan_probability_range")
    plan = VolunteerPlan(
        year=2026,
        subject_group="physics",
        user_rank=12000,
        choices=[_choice(1, 0.6), _choice(2, 0.6)],
    )
    plan.calculate_statistics()

    text = major_choice_planner.format_plan_probability_range(plan)

    assert text == "60.0%-100.0%"
    assert "84.0%" not in text


if __name__ == "__main__":
    test_plan_probability_is_disclosed_as_uncalibrated_interval()
    test_family_facing_probability_uses_range_not_precise_point()
    print("volunteer plan probability-boundary smoke tests passed")

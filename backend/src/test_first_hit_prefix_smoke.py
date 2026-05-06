"""Smoke test for ordered volunteer-plan first-hit metrics."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from models.game_matrix import MajorGroupRow, MajorOption, StrategyTag
from models.user_profile import UserProfile
from recommendation.major_choice_planner import build_volunteer_plan


def _row(index: int, prob: float, strategy: StrategyTag) -> MajorGroupRow:
    option = MajorOption(
        school_code=f"10{index:03d}",
        school_name=f"School {index}",
        major_group_code=f"{200 + index}",
        major_name="Computer Science",
        user_utility=0.9,
    )
    return MajorGroupRow(
        school_name=f"School {index}",
        school_code=f"10{index:03d}",
        major_group_code=f"{200 + index}",
        major_list=[option.major_name],
        major_count=1,
        major_options=[option],
        suggested_major_choices=[option],
        admission_prob=prob,
        min_rank_pred=10000 + index,
        rank_diff=1000,
        rank_ci_lower=9000,
        rank_ci_upper=12000,
        strategy_tag=strategy,
        comprehensive_score=prob,
    )


def main():
    profile = UserProfile(score=610, rank=20000, subject_group="physics")
    rows = [
        _row(1, 0.90, StrategyTag.TARGET),
        _row(2, 0.80, StrategyTag.SAFE),
        _row(3, 0.90, StrategyTag.SAFE),
    ]

    plan = build_volunteer_plan(rows, profile)

    assert round(plan.choices[0].survival_before_prob, 6) == 1.0
    assert round(plan.choices[0].first_hit_prob, 6) == 0.9
    assert round(plan.choices[1].survival_before_prob, 6) == 0.1
    assert round(plan.choices[1].first_hit_prob, 6) == 0.08
    assert round(plan.choices[2].survival_before_prob, 6) == 0.02
    assert round(plan.choices[2].first_hit_prob, 6) == 0.018
    assert round(plan.expected_admission_prob, 6) == 0.998

    assert plan.choices[0].prefix_role == "key_result"
    assert plan.choices[1].prefix_role == "active_backup"
    assert plan.choices[2].prefix_role == "safety_anchor"
    assert plan.key_choice_indexes == [1, 2]
    assert plan.shadowed_choice_count == 1

    assert rows[0].choice_index == 1
    assert rows[0].first_hit_prob == plan.choices[0].first_hit_prob
    assert rows[2].prefix_role == "safety_anchor"

    print("first-hit prefix smoke test passed")


if __name__ == "__main__":
    main()

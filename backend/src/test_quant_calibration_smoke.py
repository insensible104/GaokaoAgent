"""Smoke tests for quant calibration reports."""

from __future__ import annotations

from evaluation.calibration import (
    build_markdown_calibration_report,
    run_quant_calibration_records,
)
from evaluation.schemas import ActualMajorGroupOutcome
from models.game_matrix import AdjustmentAdvice, MajorOption, VolunteerChoice, VolunteerPlan


def _choice(
    index: int,
    school: str,
    group: str,
    prob: float,
    quant_score: float,
    risk_band: str,
) -> VolunteerChoice:
    return VolunteerChoice(
        choice_index=index,
        school_code=f"{index:05d}",
        school_name=school,
        major_group_code=group,
        major_choices=[MajorOption(major_name="计算机类", user_utility=0.9)],
        obey_adjustment=True,
        adjustment_advice=AdjustmentAdvice.CAUTIOUS,
        group_admission_prob=prob,
        first_hit_prob=0.10 * index,
        expected_major_utility=0.9,
        tail_assignment_risk=0.2,
        quant_score=quant_score,
        rank_buffer_score=quant_score,
        history_stability_score=0.7,
        data_confidence_score=0.8,
        trend_score=0.6,
        deterministic_risk_band=risk_band,
        quant_evidence=["位次缓冲 +1000 名，约 1.00 个不确定性宽度"],
    )


def test_quant_calibration_groups_predictions_against_outcomes() -> None:
    plan = VolunteerPlan(
        user_rank=12000,
        choices=[
            _choice(1, "A大学", "201", 0.35, 0.42, "boundary_rush"),
            _choice(2, "B大学", "202", 0.85, 0.88, "safe_anchor"),
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
        ),
        ActualMajorGroupOutcome(
            school_code="00002",
            school_name="B大学",
            major_group_code="202",
            actual_group_min_rank=15000,
            major_min_ranks={"计算机类": 14500},
        ),
    ]
    result = run_quant_calibration_records(
        records=[
            {
                "case_id": "calibration-smoke",
                "user_rank": 12000,
                "plan": plan.model_dump(mode="json"),
                "preferred_majors": ["计算机"],
            }
        ],
        actual_outcomes=actual,
    )

    assert result["case_count"] == 1
    assert result["choice_count"] == 2
    assert result["overall"]["observed_admit_rate"] == 0.5
    assert result["overall"]["expected_admit_rate"] == 0.6
    risk_bands = {row["bucket"]: row for row in result["by_risk_band"]}
    assert risk_bands["boundary_rush"]["observed_admit_rate"] == 0.0
    assert risk_bands["safe_anchor"]["observed_admit_rate"] == 1.0
    markdown = build_markdown_calibration_report(result)
    assert "Quant Calibration Report" in markdown
    assert "By Deterministic Risk Band" in markdown
    assert "`safe_anchor`" in markdown


if __name__ == "__main__":
    test_quant_calibration_groups_predictions_against_outcomes()
    print("quant calibration smoke tests passed")

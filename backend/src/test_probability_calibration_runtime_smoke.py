"""Smoke tests for historically calibrated online admission probabilities."""

from models.game_matrix import MajorGroupRow, StrategyTag, VolunteerChoice, VolunteerPlan
from models.user_profile import UserProfile
from recommendation.major_choice_planner import build_volunteer_plan
from recommendation.probability_calibration import (
    BetaCalibrationModel,
    ProbabilityCalibrationArtifact,
    apply_group_probability_calibration,
    calibrate_probability,
)


def _artifact() -> ProbabilityCalibrationArtifact:
    return ProbabilityCalibrationArtifact(
        version="test-v1",
        calibration_year=2025,
        source="prospective frozen plans against actual outcomes",
        x_thresholds=[0.0, 0.5, 1.0],
        y_thresholds=[0.10, 0.35, 0.45],
        subsequent_choice_hazard_scale=0.20,
        cross_validation={"plan_brier": 0.22, "plan_absolute_calibration_error": 0.01},
    )


def test_group_calibration_is_monotonic_and_preserves_raw_probability() -> None:
    row = MajorGroupRow(
        school_name="Test University",
        school_code="10001",
        major_group_code="201",
        admission_prob=0.90,
        min_rank_pred=12000,
        rank_ci_lower=10000,
        rank_ci_upper=14000,
        strategy_tag=StrategyTag.SAFE,
        comprehensive_score=0.8,
    )

    apply_group_probability_calibration(row, _artifact())

    assert row.raw_admission_prob == 0.90
    assert row.admission_prob == 0.43
    assert row.probability_is_calibrated is True
    assert row.probability_calibration_year == 2025
    assert row.probability_method == "historical_isotonic"


def test_subject_beta_calibration_separates_subjects_and_falls_back_globally() -> None:
    artifact = ProbabilityCalibrationArtifact(
        version="test-beta-v1",
        calibration_year=2025,
        source="grouped cross-validation",
        method="beta_subject",
        global_beta=BetaCalibrationModel(
            intercept=0.0,
            log_probability_coefficient=1.0,
            log_one_minus_probability_coefficient=-1.0,
        ),
        subject_beta={
            "history": BetaCalibrationModel(
                intercept=-1.0,
                log_probability_coefficient=1.0,
                log_one_minus_probability_coefficient=-1.0,
                blend_weight=0.75,
            ),
            "physics": BetaCalibrationModel(
                intercept=1.0,
                log_probability_coefficient=1.0,
                log_one_minus_probability_coefficient=-1.0,
                blend_weight=0.75,
            ),
        },
        subsequent_choice_hazard_scale=0.20,
    )

    history = calibrate_probability(0.80, artifact, subject_group="历史")
    physics = calibrate_probability(0.80, artifact, subject_group="物理类")
    fallback = calibrate_probability(0.80, artifact, subject_group="unknown")

    assert 0.0 <= history < fallback < physics <= 1.0
    assert fallback == 0.80


def test_calibrated_plan_uses_correlation_aware_incremental_hazard() -> None:
    choices = [
        VolunteerChoice(
            choice_index=index,
            school_code=str(index),
            school_name=f"School {index}",
            major_group_code=str(200 + index),
            group_admission_prob=0.45,
            raw_group_admission_prob=0.90,
            probability_is_calibrated=True,
            probability_calibration_year=2025,
            expected_major_utility=0.8,
            strategy_tag=StrategyTag.TARGET,
        )
        for index in range(1, 4)
    ]
    plan = VolunteerPlan(
        year=2026,
        choices=choices,
        probability_is_calibrated=True,
        probability_method="historical_isotonic_correlated_hazard",
        probability_calibration_year=2025,
        subsequent_choice_hazard_scale=0.20,
    )

    plan.calculate_statistics()

    assert plan.choices[0].first_hit_prob == 0.45
    assert round(plan.choices[1].first_hit_prob, 6) == 0.0495
    assert round(plan.choices[2].first_hit_prob, 6) == 0.045045
    assert plan.expected_admission_prob == 0.544545
    assert plan.admission_probability_lower_bound == 0.45
    assert plan.admission_probability_upper_bound == 0.544545
    assert plan.key_choice_indexes == [1, 2, 3]
    assert plan.shadowed_choice_count == 0


def test_volunteer_plan_preserves_subject_beta_method_metadata() -> None:
    row = MajorGroupRow(
        school_name="Test University",
        school_code="10001",
        major_group_code="201",
        admission_prob=0.35,
        raw_admission_prob=0.90,
        probability_is_calibrated=True,
        probability_method="historical_beta_subject",
        probability_calibration_year=2025,
        probability_hazard_scale=0.20,
        min_rank_pred=12000,
        rank_ci_lower=10000,
        rank_ci_upper=14000,
        strategy_tag=StrategyTag.TARGET,
        comprehensive_score=0.8,
    )

    plan = build_volunteer_plan(
        [row],
        UserProfile(score=580, rank=30000, subject_group="历史"),
    )

    assert plan.probability_method == "historical_beta_subject_correlated_hazard"


if __name__ == "__main__":
    test_group_calibration_is_monotonic_and_preserves_raw_probability()
    test_calibrated_plan_uses_correlation_aware_incremental_hazard()
    print("probability calibration runtime smoke tests passed")

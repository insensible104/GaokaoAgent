"""Tests for canonical student career-profile assessment scoring."""

import pytest
from pydantic import ValidationError

from recommendation.student_profile_assessment import (
    CareerAssessmentInput,
    score_career_assessment,
)


def _answers(per_dimension: int, *, high_dimension: str = "I") -> dict[str, int]:
    result: dict[str, int] = {}
    for dimension in "RIASEC":
        for index in range(1, per_dimension + 1):
            result[f"{dimension}{index}"] = 5 if dimension == high_dimension else 2
    return result


def test_quick_assessment_scores_six_dimensions_and_top_codes() -> None:
    result = score_career_assessment(
        CareerAssessmentInput(
            mode="quick",
            answers=_answers(2, high_dimension="I"),
            mbti_type="intj",
            career_values=["growth", "autonomy", "stability"],
        )
    )

    assert result.status == "completed"
    assert result.answer_count == 12
    assert result.holland_code.investigative == 1.0
    assert result.holland_code.realistic == 0.25
    assert result.top_codes[0] == "I"
    assert result.mbti_type == "INTJ"
    assert result.career_values == ["growth", "autonomy", "stability"]


def test_complete_assessment_requires_thirty_answers() -> None:
    with pytest.raises(ValidationError, match="30"):
        CareerAssessmentInput(mode="complete", answers=_answers(2))


def test_quick_assessment_rejects_unknown_question_or_invalid_score() -> None:
    answers = _answers(2)
    answers["X1"] = 5
    with pytest.raises(ValidationError, match="question"):
        CareerAssessmentInput(mode="quick", answers=answers)

    answers = _answers(2)
    answers["R1"] = 6
    with pytest.raises(ValidationError):
        CareerAssessmentInput(mode="quick", answers=answers)


def test_skip_mode_has_no_fake_holland_result() -> None:
    result = score_career_assessment(CareerAssessmentInput(mode="skip"))

    assert result.status == "not_taken"
    assert result.holland_code is None
    assert result.top_codes == []


def test_mbti_and_career_values_are_bounded() -> None:
    with pytest.raises(ValidationError, match="MBTI"):
        CareerAssessmentInput(mode="skip", mbti_type="ABCD")

    with pytest.raises(ValidationError, match="three"):
        CareerAssessmentInput(
            mode="skip",
            career_values=["growth", "autonomy", "stability", "income"],
        )

    with pytest.raises(ValidationError, match="career value"):
        CareerAssessmentInput(mode="skip", career_values=["fame"])

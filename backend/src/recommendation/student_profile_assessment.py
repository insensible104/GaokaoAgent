"""Canonical scoring for optional student career-profile assessments."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from models.user_profile import HollandCode


RIASEC_ORDER = "RIASEC"
DIMENSION_FIELDS = {
    "R": "realistic",
    "I": "investigative",
    "A": "artistic",
    "S": "social",
    "E": "enterprising",
    "C": "conventional",
}
VALID_MBTI_TYPES = {
    "ISTJ", "ISFJ", "INFJ", "INTJ",
    "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP",
    "ESTJ", "ESFJ", "ENFJ", "ENTJ",
}
VALID_CAREER_VALUES = {
    "stability",
    "income",
    "growth",
    "autonomy",
    "creativity",
    "social_impact",
    "work_life_balance",
    "leadership",
}


def required_question_ids(mode: str) -> set[str]:
    per_dimension = 2 if mode == "quick" else 5 if mode == "complete" else 0
    return {
        f"{dimension}{index}"
        for dimension in RIASEC_ORDER
        for index in range(1, per_dimension + 1)
    }


class CareerAssessmentInput(BaseModel):
    """Raw answers and optional self-reported career-profile context."""

    mode: Literal["skip", "quick", "complete"] = "skip"
    answers: dict[str, int] = Field(default_factory=dict)
    mbti_type: str | None = None
    career_values: list[str] = Field(default_factory=list)

    @field_validator("mbti_type", mode="before")
    @classmethod
    def normalize_mbti_type(cls, value):
        if value in (None, "", "unknown"):
            return None
        normalized = str(value).strip().upper()
        if normalized not in VALID_MBTI_TYPES:
            raise ValueError("MBTI type must be one of the 16 standard codes")
        return normalized

    @field_validator("career_values")
    @classmethod
    def validate_career_values(cls, values: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))
        if len(normalized) > 3:
            raise ValueError("career values are limited to three choices")
        unknown = [value for value in normalized if value not in VALID_CAREER_VALUES]
        if unknown:
            raise ValueError(f"unknown career value: {unknown[0]}")
        return normalized

    @model_validator(mode="after")
    def validate_answer_set(self):
        expected = required_question_ids(self.mode)
        if self.mode == "skip":
            if self.answers:
                raise ValueError("skip mode cannot include assessment answers")
            return self

        unknown = set(self.answers) - expected
        if unknown:
            raise ValueError("assessment question ids do not match the selected mode")
        expected_count = len(expected)
        if len(self.answers) != expected_count:
            raise ValueError(f"{self.mode} assessment requires exactly {expected_count} answers")
        missing = expected - set(self.answers)
        if missing:
            raise ValueError("assessment question ids do not match the selected mode")
        invalid = [score for score in self.answers.values() if not isinstance(score, int) or not 1 <= score <= 5]
        if invalid:
            raise ValueError("assessment answer scores must be integers from 1 to 5")
        return self


class CareerAssessmentResult(BaseModel):
    """Normalized measured profile derived from a validated assessment."""

    mode: Literal["skip", "quick", "complete"]
    status: Literal["not_taken", "completed"]
    answer_count: int = 0
    holland_code: HollandCode | None = None
    top_codes: list[str] = Field(default_factory=list)
    mbti_type: str | None = None
    career_values: list[str] = Field(default_factory=list)


def score_career_assessment(assessment: CareerAssessmentInput) -> CareerAssessmentResult:
    """Score RIASEC answers on a normalized 0-1 scale."""
    if assessment.mode == "skip":
        return CareerAssessmentResult(
            mode=assessment.mode,
            status="not_taken",
            mbti_type=assessment.mbti_type,
            career_values=assessment.career_values,
        )

    dimension_scores: dict[str, float] = {}
    for code, field_name in DIMENSION_FIELDS.items():
        values = [score for question_id, score in assessment.answers.items() if question_id.startswith(code)]
        normalized = ((sum(values) / len(values)) - 1.0) / 4.0
        dimension_scores[field_name] = round(normalized, 6)

    holland_code = HollandCode(**dimension_scores)
    score_by_code = {
        code: getattr(holland_code, field_name)
        for code, field_name in DIMENSION_FIELDS.items()
    }
    top_codes = sorted(RIASEC_ORDER, key=lambda code: (-score_by_code[code], RIASEC_ORDER.index(code)))[:3]
    return CareerAssessmentResult(
        mode=assessment.mode,
        status="completed",
        answer_count=len(assessment.answers),
        holland_code=holland_code,
        top_codes=top_codes,
        mbti_type=assessment.mbti_type,
        career_values=assessment.career_values,
    )

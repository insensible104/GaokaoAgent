"""School-level strategy signals used by ranking and explanation."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.user_profile import SchoolMajorPreference, UserProfile
from utils.school_major_scoring import (
    PreferenceStrategy,
    calculate_comprehensive_score,
)


@dataclass
class SchoolMajorSignal:
    """Aggregated school-major tradeoff signal for one major group."""

    average_score: float = 0.0
    preference: PreferenceStrategy = PreferenceStrategy.BALANCED
    tradeoff_label: str = "学校专业均衡"
    per_major_scores: list[dict] = field(default_factory=list)


def _normalize_preference(preference: SchoolMajorPreference) -> PreferenceStrategy:
    """Map UserProfile preference enum to scoring preference enum."""
    if preference == SchoolMajorPreference.PRIORITIZE_SCHOOL:
        return PreferenceStrategy.PRIORITIZE_SCHOOL
    if preference == SchoolMajorPreference.PRIORITIZE_MAJOR:
        return PreferenceStrategy.PRIORITIZE_MAJOR
    return PreferenceStrategy.BALANCED


def _tradeoff_label(preference: PreferenceStrategy) -> str:
    if preference == PreferenceStrategy.PRIORITIZE_SCHOOL:
        return "冲学校"
    if preference == PreferenceStrategy.PRIORITIZE_MAJOR:
        return "保专业"
    return "学校专业均衡"


def score_school_major_signal(
    school_name: str,
    major_names: list[str],
    profile: UserProfile,
) -> SchoolMajorSignal:
    """Score school-platform value and major quality for a major group."""
    preference = _normalize_preference(profile.school_major_preference)
    scores: list[dict] = []

    for major_name in major_names[:6]:
        if not major_name:
            continue
        try:
            score_result = calculate_comprehensive_score(
                school_name=school_name,
                major_name=major_name,
                preference=preference,
                use_platform_bonus=True,
            )
        except Exception as exc:
            scores.append(
                {
                    "major_name": major_name,
                    "error": str(exc),
                    "comprehensive_score": None,
                }
            )
            continue

        scores.append({"major_name": major_name, **score_result})

    valid_scores = [
        item["comprehensive_score"]
        for item in scores
        if item.get("comprehensive_score") is not None
    ]
    average_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

    return SchoolMajorSignal(
        average_score=average_score,
        preference=preference,
        tradeoff_label=_tradeoff_label(preference),
        per_major_scores=scores,
    )


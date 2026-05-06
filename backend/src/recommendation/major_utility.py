"""User-specific utility scoring for majors inside a Guangdong major group."""

from __future__ import annotations

from models.game_matrix import MajorOption
from models.user_profile import SchoolMajorPreference, UserProfile
from recommendation.major_taxonomy import classify_major, infer_preferred_categories


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword and keyword in text for keyword in keywords)


def _rank_risk_from_history(option: MajorOption, user_rank: int | None) -> float:
    """Estimate within-major rank risk from historical major-level ranks."""
    if not user_rank:
        return 0.5

    ranks = [
        rank
        for rank in option.historical_min_ranks.values()
        if rank and rank > 0
    ]
    if not ranks:
        return 0.5

    median_rank = sorted(ranks)[len(ranks) // 2]
    # If user's rank is much worse than the major's historical line, risk is high.
    rank_gap = user_rank - median_rank
    if rank_gap <= -3000:
        return 0.15
    if rank_gap <= 0:
        return 0.3
    if rank_gap <= 3000:
        return 0.55
    if rank_gap <= 8000:
        return 0.75
    return 0.9


def score_major_utility(option: MajorOption, profile: UserProfile) -> MajorOption:
    """Return a copy of the option with user-specific utility annotations."""
    category = classify_major(option.major_name)
    preferred_categories = infer_preferred_categories(profile.preferred_majors)
    name = option.major_name or ""
    reasons: list[str] = []

    is_blacklisted = _contains_any(name, profile.blacklist_majors)
    is_keyword_preferred = _contains_any(name, profile.preferred_majors)
    is_category_preferred = bool(preferred_categories and category in preferred_categories)

    if is_blacklisted:
        utility = 0.0
        reasons.append("命中用户黑名单专业")
    else:
        utility = 0.45
        if is_keyword_preferred:
            utility += 0.35
            reasons.append("命中用户明确偏好专业")
        elif is_category_preferred:
            utility += 0.25
            reasons.append("与用户偏好方向同类")

        if category in {"civil_architecture", "materials_chem_env", "bio_food_agri"}:
            utility -= 0.08
            reasons.append("属于常见低接受度或高误解风险方向，需确认真实接受度")

        if profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_MAJOR and not (
            is_keyword_preferred or is_category_preferred
        ):
            utility -= 0.15
            reasons.append("用户偏专业，该专业不在偏好方向内")

        if profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_SCHOOL:
            utility += 0.05

        if option.plan_quota is not None and option.plan_quota <= 2:
            utility -= 0.03
            reasons.append("专业计划数较少，组内专业分配不确定性更高")

        utility = max(0.0, min(1.0, utility))

    major_rank_risk = _rank_risk_from_history(option, profile.rank)
    is_acceptable = (not is_blacklisted) and utility >= 0.35

    return option.model_copy(
        update={
            "category": category,
            "user_utility": utility,
            "is_preferred": is_keyword_preferred or is_category_preferred,
            "is_acceptable": is_acceptable,
            "is_blacklisted": is_blacklisted,
            "major_rank_risk": major_rank_risk,
            "risk_reasons": reasons,
        }
    )


def score_major_options(options: list[MajorOption], profile: UserProfile) -> list[MajorOption]:
    """Score every major option for a user."""
    return [score_major_utility(option, profile) for option in options]


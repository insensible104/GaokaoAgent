"""First-hit-aware ordering for Guangdong volunteer-plan prefixes.

The optimizer is intentionally transparent: it does not try to learn a hidden
policy. It separates opportunity rows from safe anchors so high-probability,
low-utility rows do not shadow better front-major opportunities too early.
"""

from __future__ import annotations

from typing import Iterable

from models.game_matrix import MajorGroupRow, StrategyTag
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _risk_budget(profile: UserProfile) -> float:
    if profile.risk_tolerance == RiskTolerance.AGGRESSIVE:
        return 0.58
    if profile.risk_tolerance == RiskTolerance.CONSERVATIVE:
        return 0.38
    return 0.48


def _value_weight(profile: UserProfile) -> tuple[float, float]:
    if profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_MAJOR:
        return 0.50, 0.18
    if profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_SCHOOL:
        return 0.34, 0.28
    return 0.42, 0.22


def prefix_value_score(row: MajorGroupRow, profile: UserProfile) -> float:
    """Score one row for prefix ordering under tail/rebound guards."""
    major_weight, arbitrage_weight = _value_weight(profile)
    rebound = max(row.rebound_risk, row.segment_rebound_risk, row.publicity_rebound_risk)
    tail = row.tail_assignment_risk
    front_major = max(row.front_major_arbitrage_score, row.front_major_hit_prob * row.major_utility_mean)
    opportunity = max(row.arbitrage_score, row.segment_demand_score, row.market_discount_score)
    base = (
        major_weight * row.major_utility_mean
        + arbitrage_weight * opportunity
        + 0.16 * front_major
        + 0.12 * row.admission_prob
        + 0.06 * row.low_attention_signal
        + 0.04 * row.quota_stability_score
    )
    penalty = (
        0.28 * tail
        + 0.16 * rebound
        + (0.20 if row.is_blacklist_risk else 0.0)
        + (0.12 if row.major_utility_mean < 0.40 else 0.0)
        + (0.10 if tail > _risk_budget(profile) else 0.0)
    )
    return _clamp(base - penalty + 0.20)


def _safe_anchor_score(row: MajorGroupRow) -> float:
    return _clamp(
        0.48 * row.admission_prob
        + 0.24 * row.major_utility_mean
        + 0.14 * row.quota_stability_score
        - 0.22 * row.tail_assignment_risk
        - 0.18 * max(row.rebound_risk, row.segment_rebound_risk)
        - (0.20 if row.is_blacklist_risk else 0.0)
    )


def _is_safe_anchor(row: MajorGroupRow) -> bool:
    return row.strategy_tag == StrategyTag.SAFE


def _is_reckless(row: MajorGroupRow, profile: UserProfile) -> bool:
    rebound = max(row.rebound_risk, row.segment_rebound_risk, row.publicity_rebound_risk)
    return (
        row.is_blacklist_risk
        or row.tail_assignment_risk >= max(0.62, _risk_budget(profile) + 0.18)
        or rebound >= 0.68
    )


def _is_tail_heavy_opportunity(row: MajorGroupRow, profile: UserProfile) -> bool:
    """Whether a non-reckless opportunity should wait behind safe anchors."""
    front_major = max(row.front_major_arbitrage_score, row.front_major_hit_prob * row.major_utility_mean)
    standout_front_major = row.major_utility_mean >= 0.72 and front_major >= 0.24
    return row.tail_assignment_risk > _risk_budget(profile) + 0.06 and not standout_front_major


def _is_reliable_value_anchor(row: MajorGroupRow, profile: UserProfile) -> bool:
    """Whether a row is strong enough to protect at the front of the prefix."""
    if row.is_blacklist_risk:
        return False
    return (
        row.admission_prob >= 0.88
        and row.tail_assignment_risk <= min(0.20, _risk_budget(profile))
        and row.major_utility_mean >= 0.44
        and (
            row.strategy_tag == StrategyTag.SAFE
            or row.segment_demand_score >= 0.20
            or row.arbitrage_score >= 0.42
        )
    )


def optimize_prefix_order(
    *,
    rows: Iterable[MajorGroupRow],
    profile: UserProfile,
    max_choices: int | None = None,
) -> list[MajorGroupRow]:
    """Return rows ordered to improve first-hit value under safety anchors.

    Opportunity rows are placed before clean safe anchors; reckless rows are
    pushed behind both unless the candidate pool is too small.
    """
    candidates = list(rows)
    if not candidates:
        return []

    limit = max_choices or len(candidates)
    reckless = [row for row in candidates if _is_reckless(row, profile)]
    clean = [row for row in candidates if row not in reckless]
    reliable_anchor = [row for row in clean if _is_reliable_value_anchor(row, profile)]
    safe = [row for row in clean if _is_safe_anchor(row) and row not in reliable_anchor]
    opportunity = [row for row in clean if row not in safe and row not in reliable_anchor]

    reliable_anchor = sorted(
        reliable_anchor,
        key=lambda row: (
            _safe_anchor_score(row),
            row.segment_demand_score,
            row.arbitrage_score,
            row.admission_prob,
        ),
        reverse=True,
    )
    opportunity = sorted(
        opportunity,
        key=lambda row: (
            prefix_value_score(row, profile),
            row.front_major_arbitrage_score,
            row.major_utility_mean,
            row.admission_prob,
        ),
        reverse=True,
    )
    clean_opportunity = [
        row for row in opportunity if not _is_tail_heavy_opportunity(row, profile)
    ]
    tail_heavy_opportunity = [
        row for row in opportunity if _is_tail_heavy_opportunity(row, profile)
    ]
    safe = sorted(
        safe,
        key=lambda row: (
            _safe_anchor_score(row),
            row.admission_prob,
            -row.tail_assignment_risk,
        ),
        reverse=True,
    )
    reckless = sorted(
        reckless,
        key=lambda row: (
            prefix_value_score(row, profile),
            -row.tail_assignment_risk,
        ),
        reverse=True,
    )

    if limit >= 8:
        safe_anchor_count = min(len(safe), 2)
    elif limit >= 5:
        safe_anchor_count = min(len(safe), 2)
    elif limit >= 3:
        safe_anchor_count = min(len(safe), 1)
    else:
        safe_anchor_count = 0

    front_anchor_count = min(len(reliable_anchor), 2 if limit >= 5 else 1)
    front_anchor = reliable_anchor[:front_anchor_count]
    reserved_safe = safe[:safe_anchor_count]
    fill_limit = max(0, limit - len(front_anchor) - len(reserved_safe))
    ordered = front_anchor + clean_opportunity[:fill_limit] + reserved_safe
    if len(ordered) < limit:
        remaining_safe = [row for row in safe if row not in reserved_safe]
        remaining_anchor = [row for row in reliable_anchor if row not in front_anchor]
        remaining_clean = [row for row in clean_opportunity if row not in ordered]
        ordered.extend(
            (remaining_clean + remaining_anchor + tail_heavy_opportunity + remaining_safe + reckless)[
                : limit - len(ordered)
            ]
        )
    if len(ordered) < limit:
        ordered.extend([row for row in reckless if row not in ordered][: limit - len(ordered)])
    return ordered[:limit]

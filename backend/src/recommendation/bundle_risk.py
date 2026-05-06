"""Risk analysis for mixed major groups."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.game_matrix import AdjustmentAdvice, BundleType, MajorOption, QuotaBucket
from recommendation.policy_config import (
    HIGH_TAIL_RISK_THRESHOLD,
    HIGH_UTILITY_DISPERSION,
    LOW_ACCEPTABLE_MAJOR_RATIO,
    MEDIUM_QUOTA_MAX,
    MILD_UTILITY_DISPERSION,
    MIN_ACCEPTABLE_FOR_ADJUSTMENT,
    SMALL_QUOTA_MAX,
)


@dataclass
class BundleRiskResult:
    acceptable_major_ratio: float = 1.0
    blacklist_major_ratio: float = 0.0
    major_utility_mean: float = 0.5
    major_utility_min: float = 0.5
    major_utility_dispersion: float = 0.0
    tail_assignment_risk: float = 0.0
    bundle_type: BundleType = BundleType.UNKNOWN
    adjustment_advice: AdjustmentAdvice = AdjustmentAdvice.CAUTIOUS
    obey_adjustment: bool = True
    worst_case_major: str | None = None
    risk_reasons: list[str] = field(default_factory=list)
    audit_flags: list[str] = field(default_factory=list)


def quota_bucket(quota: int | None) -> QuotaBucket:
    """Bucket a major-group quota for stability/opportunity features."""
    if quota is None or quota <= 0:
        return QuotaBucket.UNKNOWN
    if quota <= SMALL_QUOTA_MAX:
        return QuotaBucket.SMALL
    if quota <= MEDIUM_QUOTA_MAX:
        return QuotaBucket.MEDIUM
    return QuotaBucket.LARGE


def quota_stability_score(quota: int | None) -> float:
    """Estimate stability from quota size."""
    if quota is None or quota <= 0:
        return 0.3
    if quota <= 5:
        return 0.25
    if quota <= 10:
        return 0.4
    if quota <= 40:
        return 0.65
    return 0.85


def variance_opportunity_score(quota: int | None, utility_dispersion: float) -> float:
    """Estimate high-variance opportunity potential."""
    if quota is None or quota <= 0:
        base = 0.35
    elif quota <= 5:
        base = 0.8
    elif quota <= 10:
        base = 0.65
    elif quota <= 40:
        base = 0.4
    else:
        base = 0.2
    return max(0.0, min(1.0, base + utility_dispersion * 0.15))


def analyze_bundle_risk(options: list[MajorOption]) -> BundleRiskResult:
    """Analyze internal major mix and adjustment risk for a major group."""
    if not options:
        return BundleRiskResult(
            acceptable_major_ratio=0.0,
            blacklist_major_ratio=0.0,
            major_utility_mean=0.0,
            major_utility_min=0.0,
            major_utility_dispersion=0.0,
            tail_assignment_risk=1.0,
            bundle_type=BundleType.UNKNOWN,
            adjustment_advice=AdjustmentAdvice.AVOID,
            obey_adjustment=False,
            risk_reasons=["未找到该专业组的2025招生专业明细"],
            audit_flags=["missing_major_options"],
        )

    utilities = [option.user_utility for option in options]
    acceptable_count = sum(1 for option in options if option.is_acceptable)
    blacklist_count = sum(1 for option in options if option.is_blacklisted)
    preferred_count = sum(1 for option in options if option.is_preferred)

    total = len(options)
    acceptable_ratio = acceptable_count / total
    blacklist_ratio = blacklist_count / total
    utility_mean = sum(utilities) / total
    utility_min = min(utilities)
    utility_max = max(utilities)
    utility_dispersion = utility_max - utility_min
    worst_option = min(options, key=lambda option: option.user_utility)

    tail_assignment_risk = max(
        0.0,
        min(
            1.0,
            (1 - acceptable_ratio) * 0.45
            + blacklist_ratio * 0.35
            + (1 - utility_min) * 0.20
            + utility_dispersion * 0.15,
        ),
    )

    reasons: list[str] = []
    audit_flags: list[str] = []
    if blacklist_count:
        reasons.append(f"组内有{blacklist_count}个专业命中用户黑名单")
        audit_flags.append("blacklist_major_in_group")
    if acceptable_ratio < LOW_ACCEPTABLE_MAJOR_RATIO:
        reasons.append("组内用户可接受专业不足一半")
        audit_flags.append("low_acceptable_major_ratio")
    if preferred_count > 0 and acceptable_ratio < 0.75:
        reasons.append("组内存在偏好专业，但尾部专业接受度不足")
        audit_flags.append("preferred_major_with_tail_risk")
    if utility_dispersion >= HIGH_UTILITY_DISPERSION:
        reasons.append("组内专业效用差异较大，存在混搭风险")
        audit_flags.append("high_major_utility_dispersion")

    if blacklist_ratio >= 0.5:
        bundle_type = BundleType.BLACKLIST_BLOCKED
    elif preferred_count > 0 and tail_assignment_risk >= HIGH_TAIL_RISK_THRESHOLD:
        bundle_type = BundleType.BAIT_RISK
    elif tail_assignment_risk >= 0.5 or utility_dispersion >= HIGH_UTILITY_DISPERSION:
        bundle_type = BundleType.HIGHLY_MIXED
    elif tail_assignment_risk >= 0.25 or utility_dispersion >= MILD_UTILITY_DISPERSION:
        bundle_type = BundleType.MILD_MIXED
    else:
        bundle_type = BundleType.CLEAN_FIT

    if bundle_type in {BundleType.CLEAN_FIT, BundleType.MILD_MIXED} and blacklist_count == 0:
        adjustment_advice = AdjustmentAdvice.RECOMMEND
        obey_adjustment = True
    elif bundle_type == BundleType.BLACKLIST_BLOCKED or acceptable_ratio < MIN_ACCEPTABLE_FOR_ADJUSTMENT:
        adjustment_advice = AdjustmentAdvice.AVOID
        obey_adjustment = False
    else:
        adjustment_advice = AdjustmentAdvice.CAUTIOUS
        obey_adjustment = True

    return BundleRiskResult(
        acceptable_major_ratio=acceptable_ratio,
        blacklist_major_ratio=blacklist_ratio,
        major_utility_mean=utility_mean,
        major_utility_min=utility_min,
        major_utility_dispersion=utility_dispersion,
        tail_assignment_risk=tail_assignment_risk,
        bundle_type=bundle_type,
        adjustment_advice=adjustment_advice,
        obey_adjustment=obey_adjustment,
        worst_case_major=worst_option.major_name,
        risk_reasons=reasons,
        audit_flags=audit_flags,
    )

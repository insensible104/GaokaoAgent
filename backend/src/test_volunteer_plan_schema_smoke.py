"""Smoke test for Guangdong volunteer-plan schemas and mixed major-group risk."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from engines.enrollment_loader import EnrollmentPlanLoader
from models.game_matrix import GameMatrix, MajorGroupRow, StrategyTag, VolatilityLevel
from models.user_profile import SchoolMajorPreference, UserProfile
from recommendation.bundle_risk import (
    analyze_bundle_risk,
    quota_bucket,
    quota_stability_score,
    variance_opportunity_score,
)
from recommendation.major_choice_planner import (
    build_major_options_from_records,
    build_volunteer_plan,
    choose_six_majors,
)
from recommendation.major_utility import score_major_options


def main():
    data_dir = Path(__file__).parents[1] / "data"
    loader = EnrollmentPlanLoader(data_dir=str(data_dir))
    records = loader.get_major_group_options(
        school_code="10008",
        major_group_code="214",
        category="物理",
    )
    assert len(records) == 8

    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_majors=["计算机"],
        blacklist_majors=["土木", "材料"],
        school_major_preference=SchoolMajorPreference.PRIORITIZE_MAJOR,
    )

    options = build_major_options_from_records(records)
    options = score_major_options(options, profile)
    risk = analyze_bundle_risk(options)
    choices = choose_six_majors(options)
    quota = sum(option.plan_quota or 0 for option in options)

    assert choices[0].major_name == "计算机类"
    assert risk.tail_assignment_risk >= 0.55
    assert "blacklist_major_in_group" in risk.audit_flags

    row = MajorGroupRow(
        school_name="北京科技大学",
        school_code="10008",
        major_group_code="214",
        major_list=[choice.major_name for choice in choices],
        major_count=len(options),
        major_options=options,
        suggested_major_choices=choices,
        admission_prob=0.78,
        min_rank_pred=14724,
        rank_diff=2724,
        rank_ci_lower=13000,
        rank_ci_upper=17000,
        volatility=VolatilityLevel.MEDIUM,
        quota=quota,
        quota_bucket=quota_bucket(quota),
        quota_stability_score=quota_stability_score(quota),
        variance_opportunity_score=variance_opportunity_score(quota, risk.major_utility_dispersion),
        adjustment_risk=risk.tail_assignment_risk,
        worst_case_major=risk.worst_case_major,
        is_blacklist_risk=risk.blacklist_major_ratio > 0,
        acceptable_major_ratio=risk.acceptable_major_ratio,
        blacklist_major_ratio=risk.blacklist_major_ratio,
        major_utility_mean=risk.major_utility_mean,
        major_utility_min=risk.major_utility_min,
        major_utility_dispersion=risk.major_utility_dispersion,
        tail_assignment_risk=risk.tail_assignment_risk,
        bundle_type=risk.bundle_type,
        obey_adjustment=risk.obey_adjustment,
        adjustment_advice=risk.adjustment_advice,
        risk_reasons=risk.risk_reasons,
        audit_flags=risk.audit_flags,
        strategy_tag=StrategyTag.TARGET,
        comprehensive_score=0.66,
        quant_score=0.71,
        rank_buffer_score=0.78,
        history_stability_score=0.64,
        data_confidence_score=0.69,
        trend_score=0.55,
        deterministic_risk_band="solid_target",
        quant_evidence=["位次缓冲 +2724 名，约 1.10 个不确定性宽度"],
    )

    plan = build_volunteer_plan([row], profile)
    matrix = GameMatrix(major_group_rows=[row], volunteer_plan=plan)
    matrix.calculate_statistics()

    choice = matrix.volunteer_plan.choices[0]
    assert choice.school_code == "10008"
    assert choice.major_group_code == "214"
    assert 1 <= len(choice.major_choices) <= 6
    assert choice.worst_case_major == "土木类"
    assert choice.quant_score == 0.71
    assert choice.deterministic_risk_band == "solid_target"
    assert "位次缓冲" in choice.quant_evidence[0]

    print("volunteer plan schema smoke test passed")


if __name__ == "__main__":
    main()

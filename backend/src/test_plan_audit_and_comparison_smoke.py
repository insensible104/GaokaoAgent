"""Smoke tests for product-facing plan audit and A/B comparison."""

from __future__ import annotations

from evaluation.plan_audit import build_plan_audit_summary
from evaluation.plan_comparison import compare_volunteer_plans
from models.game_matrix import GameMatrix, MajorOption, StrategyTag, VolunteerChoice, VolunteerPlan
from models.user_profile import RiskTolerance, UserProfile


def _choice(
    index: int,
    prob: float,
    strategy: StrategyTag,
    *,
    utility: float = 0.78,
    tail_risk: float = 0.10,
    blacklisted: bool = False,
) -> VolunteerChoice:
    return VolunteerChoice(
        choice_index=index,
        school_code=f"S{index}",
        school_name=f"Audit University {index}",
        major_group_code=f"20{index}",
        major_choices=[
            MajorOption(
                major_name="Computer Science" if not blacklisted else "Civil Engineering",
                is_blacklisted=blacklisted,
                user_utility=0.0 if blacklisted else utility,
            )
        ],
        group_admission_prob=prob,
        expected_major_utility=0.0 if blacklisted else utility,
        tail_assignment_risk=tail_risk,
        strategy_tag=strategy,
        explanation="rank and major evidence attached",
        quant_evidence=["rank_buffer=ok"],
    )


def _plan(*choices: VolunteerChoice) -> VolunteerPlan:
    return VolunteerPlan(
        province="Guangdong",
        year=2026,
        subject_group="physics",
        user_score=620,
        user_rank=12000,
        choices=list(choices),
    )


def test_plan_audit_summary_exposes_student_facing_risk_items() -> None:
    plan = _plan(
        _choice(1, 0.36, StrategyTag.RUSH, tail_risk=0.08),
        _choice(2, 0.55, StrategyTag.TARGET, tail_risk=0.12),
        _choice(3, 0.97, StrategyTag.SAFE, tail_risk=0.05),
    )
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="physics",
        risk_tolerance=RiskTolerance.BALANCED,
    )
    audit = build_plan_audit_summary(
        plan,
        profile,
        coverage_report={
            "coverage_sufficient": True,
            "deficits": {},
            "selected": {"rush": 1, "target": 1, "safe": 1},
        },
        data_vintage={
            "target_year": 2026,
            "formal_recommendation_ready": False,
            "limitations": ["Missing 2026 enrollment plan."],
        },
    )

    assert audit["protocol_version"] == "plan-audit-summary-v1"
    assert audit["status"] in {"pass", "needs_revision"}
    assert audit["key_prefix"]["count"] >= 2
    assert audit["coverage"]["coverage_sufficient"] is True
    assert audit["data_boundary"]["formal_recommendation_ready"] is False
    assert any(item["type"] == "data_boundary" for item in audit["student_facing_items"])


def test_plan_comparison_prefers_safer_lower_tail_plan() -> None:
    safer = _plan(
        _choice(1, 0.50, StrategyTag.TARGET, utility=0.80, tail_risk=0.08),
        _choice(2, 0.96, StrategyTag.SAFE, utility=0.72, tail_risk=0.05),
    )
    risky = _plan(
        _choice(1, 0.35, StrategyTag.RUSH, utility=0.90, tail_risk=0.52),
        _choice(2, 0.44, StrategyTag.RUSH, utility=0.82, tail_risk=0.45),
    )

    comparison = compare_volunteer_plans(
        left=safer,
        right=risky,
        left_label="safer",
        right_label="risky",
    )

    assert comparison["protocol_version"] == "plan-comparison-v1"
    assert comparison["winner"] == "safer"
    assert comparison["deltas"]["expected_tail_risk"] < 0
    assert any(item["metric"] == "expected_tail_risk" for item in comparison["deciding_factors"])


def test_game_matrix_serializes_plan_audit_summary() -> None:
    matrix = GameMatrix(
        plan_audit_summary={
            "protocol_version": "plan-audit-summary-v1",
            "status": "needs_revision",
        }
    )

    assert matrix.model_dump()["plan_audit_summary"]["protocol_version"] == "plan-audit-summary-v1"


if __name__ == "__main__":
    test_plan_audit_summary_exposes_student_facing_risk_items()
    test_plan_comparison_prefers_safer_lower_tail_plan()
    test_game_matrix_serializes_plan_audit_summary()
    print("plan audit and comparison smoke tests passed")

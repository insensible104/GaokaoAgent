"""Smoke tests for enrollment-plan change signals in ranking."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from evaluation.baselines import build_baseline_plan
from models.game_matrix import MajorGroupRow, QuotaBucket, StrategyTag, VolatilityLevel
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from recommendation.enrollment_diff import EnrollmentDiffEvent
from recommendation.plan_change_signals import attach_plan_change_signals

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from generate_frozen_plans_2025 import load_plan_change_events_from_json  # noqa: E402


def _row(
    *,
    school_name: str,
    school_code: str,
    group: str,
    admission_prob: float,
    major_utility: float,
    tail_risk: float,
) -> MajorGroupRow:
    return MajorGroupRow(
        school_name=school_name,
        school_code=school_code,
        major_group_code=group,
        major_list=["Test Major"],
        major_count=1,
        admission_prob=admission_prob,
        min_rank_pred=10000,
        rank_diff=300,
        rank_ci_lower=8000,
        rank_ci_upper=12000,
        volatility=VolatilityLevel.MEDIUM,
        quota=20,
        quota_bucket=QuotaBucket.MEDIUM,
        quota_stability_score=0.55,
        variance_opportunity_score=0.35,
        major_utility_mean=major_utility,
        major_utility_min=major_utility,
        major_utility_dispersion=0.10,
        tail_assignment_risk=tail_risk,
        strategy_tag=StrategyTag.TARGET,
        comprehensive_score=major_utility,
    )


def _profile() -> UserProfile:
    return UserProfile(
        score=590,
        rank=18888,
        subject_group="physics",
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.BALANCED,
    )


def test_plan_change_signals_attach_to_matching_rows_and_choices() -> None:
    row = _row(
        school_name="A University",
        school_code="10001",
        group="201",
        admission_prob=0.62,
        major_utility=0.72,
        tail_risk=0.20,
    )
    events = [
        EnrollmentDiffEvent(
            change_type="new_group",
            school_code="10001",
            school_name="A University",
            subject_group="physics",
            major_group_code="201",
            major_name="Computer Science",
            evidence="group absent from previous snapshot",
        ),
        EnrollmentDiffEvent(
            change_type="quota_increase",
            school_code="10001",
            school_name="A University",
            subject_group="physics",
            major_group_code="201",
            major_name="Computer Science",
            before=2,
            after=5,
            evidence="quota increased by 150%",
        ),
    ]

    attach_plan_change_signals([row], events, subject_group="physics")

    assert row.plan_change_score >= 0.60
    assert "new_group" in row.plan_change_types
    assert "quota_increase" in row.plan_change_types
    assert row.plan_change_evidence


def test_plan_change_guarded_baseline_prefers_evidence_without_high_tail_risk() -> None:
    changed = _row(
        school_name="Changed Opportunity",
        school_code="10001",
        group="201",
        admission_prob=0.62,
        major_utility=0.72,
        tail_risk=0.18,
    )
    plain = _row(
        school_name="Plain Target",
        school_code="10002",
        group="201",
        admission_prob=0.64,
        major_utility=0.72,
        tail_risk=0.18,
    )
    risky_changed = _row(
        school_name="Risky Changed",
        school_code="10003",
        group="201",
        admission_prob=0.66,
        major_utility=0.75,
        tail_risk=0.72,
    )
    attach_plan_change_signals(
        [changed, risky_changed],
        [
            EnrollmentDiffEvent("split_or_regroup", "10001", "Changed Opportunity", "physics", "201"),
            EnrollmentDiffEvent("new_group", "10003", "Risky Changed", "physics", "201"),
        ],
        subject_group="physics",
    )

    plan = build_baseline_plan(
        rows=[plain, changed, risky_changed],
        profile=_profile(),
        baseline="plan_change_guarded",
        max_choices=3,
    )

    assert plan.choices[0].school_name == "Changed Opportunity"
    assert plan.choices[0].plan_change_score > 0
    assert plan.choices[-1].school_name == "Risky Changed"


def test_frozen_plan_generator_loads_plan_change_events(tmp_path: Path) -> None:
    payload = {
        "events": [
            {
                "change_type": "new_group",
                "school_code": "10001",
                "school_name": "A University",
                "subject_group": "physics",
                "major_group_code": "201",
                "major_name": "Computer Science",
                "evidence": "group absent from previous snapshot",
            }
        ]
    }
    path = tmp_path / "diff.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    events = load_plan_change_events_from_json(path)

    assert len(events) == 1
    assert events[0].change_type == "new_group"
    assert events[0].school_code == "10001"


if __name__ == "__main__":
    test_plan_change_signals_attach_to_matching_rows_and_choices()
    test_plan_change_guarded_baseline_prefers_evidence_without_high_tail_risk()
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        test_frozen_plan_generator_loads_plan_change_events(Path(tmp))
    print("plan change signal smoke tests passed")

"""Smoke tests for online plan-change explanations and source conflicts."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from models.game_matrix import MajorGroupRow, StrategyTag, VolatilityLevel
from recommendation.enrollment_diff import EnrollmentDiffEvent
from recommendation.plan_change_explanation import build_plan_change_explanation
from recommendation.plan_change_signals import (
    attach_plan_change_signals,
    load_online_plan_change_events,
)
from agents.game_agent import _attach_online_plan_changes


def _row() -> MajorGroupRow:
    return MajorGroupRow(
        school_name="Evidence University",
        school_code="10001",
        major_group_code="201",
        major_list=["Computer Science"],
        admission_prob=0.68,
        min_rank_pred=13000,
        rank_ci_lower=11000,
        rank_ci_upper=15000,
        volatility=VolatilityLevel.MEDIUM,
        adjustment_risk=0.12,
        strategy_tag=StrategyTag.TARGET,
        comprehensive_score=0.76,
    )


def test_official_quota_change_builds_before_after_explanation() -> None:
    row = _row()
    attach_plan_change_signals(
        [row],
        [
            EnrollmentDiffEvent(
                change_type="quota_increase",
                school_code="10001",
                school_name=row.school_name,
                subject_group="physics",
                major_group_code="201",
                major_name="Computer Science",
                before=20,
                after=30,
                evidence="quota increased by 50%",
            )
        ],
        subject_group="physics",
    )

    explanation = build_plan_change_explanation(row)

    assert explanation["status"] == "resolved"
    assert explanation["ranking_impact"] == "official_diff_applied"
    assert explanation["official_changes"][0]["before"] == 20
    assert explanation["official_changes"][0]["after"] == 30
    assert "20 -> 30" in explanation["summary"]


def test_reference_conflict_becomes_review_item_without_overriding_official_change() -> None:
    row = _row()
    attach_plan_change_signals(
        [row],
        [
            EnrollmentDiffEvent(
                change_type="quota_increase",
                school_code="10001",
                school_name=row.school_name,
                subject_group="physics",
                major_group_code="201",
                before=20,
                after=30,
                evidence="quota increased by 50%",
            )
        ],
        subject_group="physics",
    )
    row.market_evidence_cards = [
        {
            "signal_type": "plan_change_signal",
            "claim": "A secondary article says the quota decreased this year.",
            "source": "https://example.invalid/article",
            "usable_for_prediction": False,
        }
    ]

    explanation = build_plan_change_explanation(row)

    assert explanation["status"] == "review_required"
    assert explanation["ranking_impact"] == "official_diff_applied"
    assert explanation["reference_claims"][0]["applied_to_ranking"] is False
    assert explanation["review_items"]


def test_no_evidence_has_explicit_none_status() -> None:
    explanation = build_plan_change_explanation(_row())

    assert explanation["status"] == "none"
    assert explanation["ranking_impact"] == "none"
    assert explanation["official_changes"] == []
    assert explanation["reference_claims"] == []


def test_online_loader_keeps_only_exact_before_after_changes() -> None:
    payload = {
        "events": [
            {
                "change_type": "quota_increase",
                "school_code": "10001",
                "school_name": "A",
                "subject_group": "physics",
                "major_group_code": "201",
                "before": 20,
                "after": 30,
                "evidence": "quota increased by 50%",
            },
            {
                "change_type": "new_group",
                "school_code": "10001",
                "school_name": "A",
                "subject_group": "physics",
                "major_group_code": "202",
                "evidence": "group absent from previous snapshot",
            },
        ]
    }
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "diff.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        events = load_online_plan_change_events(path)

    assert len(events) == 1
    assert events[0].change_type == "quota_increase"


def test_game_agent_attaches_online_plan_change_explanation() -> None:
    row = _row()
    payload = {
        "events": [
            {
                "change_type": "quota_increase",
                "school_code": "10001",
                "school_name": row.school_name,
                "subject_group": "physics",
                "major_group_code": "201",
                "before": 20,
                "after": 30,
                "evidence": "quota increased by 50%",
            }
        ]
    }
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "diff.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        attached = _attach_online_plan_changes([row], subject_group="physics", diff_path=path)

    assert attached == 1
    assert row.plan_change_explanation["ranking_impact"] == "official_diff_applied"


if __name__ == "__main__":
    test_official_quota_change_builds_before_after_explanation()
    test_reference_conflict_becomes_review_item_without_overriding_official_change()
    test_no_evidence_has_explicit_none_status()
    test_online_loader_keeps_only_exact_before_after_changes()
    test_game_agent_attaches_online_plan_change_explanation()
    print("plan change explanation smoke tests passed")

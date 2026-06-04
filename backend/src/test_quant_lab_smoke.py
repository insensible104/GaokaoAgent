"""Smoke tests for QuantLab experiment registration and slice scoreboards."""

from __future__ import annotations

from evaluation.quant_lab import build_markdown_quant_lab_report, build_quant_lab_experiment
from evaluation.slice_scoreboard import (
    attach_slice_tags_to_per_case,
    build_markdown_slice_scoreboard,
    build_slice_scoreboard,
    strongest_slice_regressions,
)
from models.game_matrix import VolunteerPlan
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


def _record(case_id: str, rank: int, subject: str = "physics") -> dict:
    profile = UserProfile(
        score=620,
        rank=rank,
        subject_group=subject,
        preferred_cities=["广州"],
        preferred_majors=["computer", "software"],
        blacklist_majors=["civil"],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_MAJOR,
        major_cognition_risk=0.7,
        regret_sensitivity=0.8,
    )
    plan = VolunteerPlan(subject_group=subject, user_score=620, user_rank=rank)
    return {
        "case_id": case_id,
        "user_rank": rank,
        "user_profile": profile.model_dump(),
        "plan": plan.model_dump(),
    }


def test_slice_scoreboard_attaches_profile_segments_and_regressions():
    records = [_record("case_001", 12_000)]
    per_case = [
        {
            "case_id": "case_001",
            "variant": "full",
            "success": True,
            "sliding": False,
            "preferred_major_hit": True,
            "selected_major_hit": True,
            "blacklist_hit": False,
            "tail_assignment_hit": False,
            "wasted_score_risk": False,
            "assigned_major_utility": 0.8,
        },
        {
            "case_id": "case_001",
            "variant": "probability_only",
            "success": False,
            "sliding": True,
            "preferred_major_hit": False,
            "selected_major_hit": False,
            "blacklist_hit": False,
            "tail_assignment_hit": False,
            "wasted_score_risk": False,
            "assigned_major_utility": 0.0,
        },
    ]

    enriched = attach_slice_tags_to_per_case(records=records, per_case=per_case)
    scoreboard = build_slice_scoreboard(enriched)
    regressions = strongest_slice_regressions(scoreboard)
    markdown = build_markdown_slice_scoreboard(scoreboard)

    assert enriched[0]["slice_tags"]
    assert any(row["slice"] == "subject_physics" for row in scoreboard["rows"])
    assert any(item["variant"] == "probability_only" for item in regressions)
    assert "Quant Slice Scoreboard" in markdown


def test_quant_lab_manifest_keeps_shadow_promotion_gate_conservative():
    ablation_summary = {
        "variants": ["full", "front_major_boost", "unsafe_shadow"],
        "summaries": {
            "full": {
                "success_rate": 0.70,
                "blacklist_hit_rate": 0.0,
                "tail_assignment_rate": 0.20,
                "preferred_major_hit_rate": 0.30,
                "average_assigned_major_utility": 0.50,
            },
            "front_major_boost": {
                "success_rate": 0.70,
                "blacklist_hit_rate": 0.0,
                "tail_assignment_rate": 0.21,
                "preferred_major_hit_rate": 0.36,
                "average_assigned_major_utility": 0.52,
            },
            "unsafe_shadow": {
                "success_rate": 0.72,
                "blacklist_hit_rate": 0.10,
                "tail_assignment_rate": 0.35,
                "preferred_major_hit_rate": 0.40,
                "average_assigned_major_utility": 0.55,
            },
        },
        "slice_scoreboard": {"slice_count": 8, "rows": []},
    }

    manifest = build_quant_lab_experiment(
        experiment_id="smoke_quant_lab",
        ablation_summary=ablation_summary,
        tuning_summary={
            "best": {
                "name": "candidate",
                "weights": {"predicted_prob": 0.8, "quant_score": 0.2},
                "objective_delta_vs_current": -0.01,
                "holdout": {"objective_delta_vs_current": -0.02, "brier_delta_vs_current": -0.01},
            }
        },
    )
    report = build_markdown_quant_lab_report(manifest)

    assert manifest["protocol_version"] == "gaokao-quant-lab-v1"
    assert manifest["promotion_gate"]["status"] == "candidate_found"
    assert manifest["promotion_gate"]["winners"][0]["variant"] == "front_major_boost"
    assert all(item["variant"] != "unsafe_shadow" for item in manifest["promotion_gate"]["winners"])
    assert "Promotion Gate" in report


if __name__ == "__main__":
    test_slice_scoreboard_attaches_profile_segments_and_regressions()
    test_quant_lab_manifest_keeps_shadow_promotion_gate_conservative()
    print("quant lab smoke tests passed")

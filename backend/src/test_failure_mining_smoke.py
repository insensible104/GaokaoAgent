"""Smoke tests for case-level failure mining."""

from __future__ import annotations

from evaluation.failure_mining import (
    build_markdown_failure_mining,
    mine_ablation_failure_deltas,
    mine_backtest_failures,
)
from evaluation.quant_lab import build_markdown_quant_lab_report, build_quant_lab_experiment


def test_backtest_failure_mining_buckets_and_worst_cases():
    results = [
        {
            "case_id": "slide_case",
            "user_rank": 120000,
            "success": False,
            "sliding": True,
            "preferred_major_hit": False,
            "blacklist_hit": False,
            "tail_assignment_hit": False,
            "wasted_score_risk": False,
            "assigned_major_utility": 0.0,
            "choice_outcomes": [
                {
                    "choice_index": 1,
                    "failure_reason": "missing_actual_outcome",
                }
            ],
        },
        {
            "case_id": "tail_case",
            "user_rank": 30000,
            "success": True,
            "sliding": False,
            "preferred_major_hit": False,
            "blacklist_hit": True,
            "tail_assignment_hit": True,
            "wasted_score_risk": False,
            "assigned_major_utility": 0.2,
            "first_hit_index": 2,
            "first_hit_school": "Risk University",
            "assigned_major_name": "civil engineering",
            "choice_outcomes": [],
        },
    ]

    result = mine_backtest_failures(results)
    markdown = build_markdown_failure_mining(result)

    buckets = {row["bucket"]: row["case_count"] for row in result["failure_buckets"]}
    assert buckets["sliding"] == 1
    assert buckets["blacklist_hit"] == 1
    assert buckets["tail_assignment"] == 1
    assert buckets["preferred_major_miss"] == 1
    assert result["missing_actual_choice_count"] == 1
    assert result["worst_cases"][0]["case_id"] in {"slide_case", "tail_case"}
    assert "Backtest Failure Mining" in markdown


def test_ablation_failure_mining_finds_new_variant_regressions():
    per_case = [
        {
            "case_id": "case_001",
            "variant": "full",
            "success": True,
            "sliding": False,
            "preferred_major_hit": True,
            "blacklist_hit": False,
            "tail_assignment_hit": False,
        },
        {
            "case_id": "case_001",
            "variant": "unsafe_variant",
            "success": True,
            "sliding": False,
            "preferred_major_hit": False,
            "blacklist_hit": True,
            "tail_assignment_hit": True,
        },
    ]

    result = mine_ablation_failure_deltas(per_case)

    buckets = result["variant_failure_deltas"]["unsafe_variant"]
    bucket_names = {row["bucket"] for row in buckets}
    assert "new_blacklist_hit" in bucket_names
    assert "new_tail_assignment" in bucket_names
    assert result["case_regressions"][0]["variant"] == "unsafe_variant"


def test_quant_lab_manifest_includes_failure_mining_digest():
    failure_mining = mine_backtest_failures(
        [
            {
                "case_id": "slide_case",
                "success": False,
                "sliding": True,
                "preferred_major_hit": False,
                "blacklist_hit": False,
                "tail_assignment_hit": False,
                "wasted_score_risk": False,
                "choice_outcomes": [],
            }
        ]
    )
    manifest = build_quant_lab_experiment(
        experiment_id="failure_mining_smoke",
        failure_mining=failure_mining,
    )
    report = build_markdown_quant_lab_report(manifest)

    assert manifest["metric_digest"]["failure_mining"]["failure_case_count"] == 1.0
    assert manifest["failure_mining"]["failure_buckets"][0]["bucket"] == "sliding"
    assert "Failure Mining" in report


if __name__ == "__main__":
    test_backtest_failure_mining_buckets_and_worst_cases()
    test_ablation_failure_mining_finds_new_variant_regressions()
    test_quant_lab_manifest_includes_failure_mining_digest()
    print("failure mining smoke tests passed")

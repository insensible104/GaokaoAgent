"""Smoke tests for self-improvement audit reports."""

from __future__ import annotations

from evaluation.improvement_audit import (
    build_improvement_audit,
    build_markdown_improvement_audit,
)


def test_improvement_audit_prioritizes_blockers() -> None:
    result = build_improvement_audit(
        backtest_summary={
            "case_count": 20,
            "success_rate": 0.82,
            "sliding_rate": 0.18,
            "preferred_major_hit_rate": 0.35,
            "blacklist_hit_rate": 0.06,
            "tail_assignment_rate": 0.30,
            "wasted_score_rate": 0.24,
        },
        calibration_summary={
            "overall": {
                "absolute_calibration_error": 0.18,
                "brier_score": 0.24,
            },
            "by_probability_bucket": [
                {
                    "bucket": "60-80%",
                    "choice_count": 10,
                    "expected_admit_rate": 0.70,
                    "observed_admit_rate": 0.40,
                    "absolute_calibration_error": 0.30,
                }
            ],
            "by_risk_band": [
                {"bucket": "boundary_rush", "choice_count": 5, "observed_admit_rate": 0.60},
                {"bucket": "thin_target", "choice_count": 5, "observed_admit_rate": 0.40},
            ],
        },
        ablation_summary={
            "deltas_vs_full": {
                "safe_first": {
                    "success_rate": 0.04,
                    "preferred_major_hit_rate": -0.01,
                    "tail_assignment_rate": 0.00,
                    "blacklist_hit_rate": 0.00,
                }
            }
        },
    )

    assert result["status"] == "blocked_for_agency_grade_claims"
    assert result["severity_counts"]["P0"] >= 1
    assert any("风险档不单调" in item["finding"] for item in result["findings"])
    assert any("safe_first" in item["finding"] for item in result["findings"])
    markdown = build_markdown_improvement_audit(result)
    assert "GaokaoAgent Self-Improvement Audit" in markdown
    assert "高考志愿平权化" in markdown


if __name__ == "__main__":
    test_improvement_audit_prioritizes_blockers()
    print("improvement audit smoke tests passed")

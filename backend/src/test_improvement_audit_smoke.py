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
        tuning_summary={
            "baseline": {"brier_score": 0.25, "objective": 0.30},
            "best": {
                "name": "grid_candidate_001",
                "weights": {"predicted_prob": 0.6, "quant_score": 0.4},
                "brier_score": 0.20,
                "objective": 0.24,
            },
        },
        intake_audit={
            "status": "needs_clarification",
            "readiness_score": 0.58,
            "missing_items": [{"dimension": "region_boundary", "missing": ["是否接受省外"]}],
        },
        plan_quality_audit={
            "status": "needs_revision",
            "total_score": 0.62,
            "findings": [{"area": "safe_anchor", "recommendation": "补足保底"}],
        },
        report_quality_audit={
            "status": "needs_revision",
            "total_score": 0.55,
            "findings": [{"area": "risk_explanation", "recommendation": "补风险解释"}],
        },
        delivery_bundle={
            "status": "needs_revision",
            "delivery_gates": [
                {"gate": "plan_quality", "status": "needs_revision"},
                {"gate": "report_quality", "status": "needs_revision"},
            ],
            "next_actions": ["修复志愿表结构质量审计"],
        },
        delivery_portfolio={
            "status": "blocked_for_scale",
            "case_count": 10,
            "ready_to_deliver_rate": 0.30,
            "blocked_rate": 0.20,
            "top_failed_gates": [
                {"gate": "plan_quality", "failed_count": 6, "failed_rate": 0.60},
                {"gate": "report_quality", "failed_count": 3, "failed_rate": 0.30},
            ],
            "top_next_actions": [
                {"action": "根据志愿表结构质量审计调整保底。", "count": 5, "rate": 0.50}
            ],
            "worst_cases": [
                {"case_id": "case-blocked", "status": "blocked", "portfolio_score": 0.2}
            ],
        },
    )

    assert result["status"] == "blocked_for_agency_grade_claims"
    assert result["severity_counts"]["P0"] >= 1
    assert any("风险档不单调" in item["finding"] for item in result["findings"])
    assert any("safe_first" in item["finding"] for item in result["findings"])
    assert any(item["area"] == "quant_tuning" for item in result["findings"])
    assert any(item["area"] == "intake_readiness" for item in result["findings"])
    assert any(item["area"] == "plan_quality" for item in result["findings"])
    assert any(item["area"] == "report_quality" for item in result["findings"])
    assert any(item["area"] == "delivery_bundle" for item in result["findings"])
    assert any(item["area"] == "delivery_portfolio" for item in result["findings"])
    assert any(item["area"] == "delivery_portfolio_gate" for item in result["findings"])
    markdown = build_markdown_improvement_audit(result)
    assert "GaokaoAgent Self-Improvement Audit" in markdown
    assert "高考志愿平权化" in markdown


if __name__ == "__main__":
    test_improvement_audit_prioritizes_blockers()
    print("improvement audit smoke tests passed")

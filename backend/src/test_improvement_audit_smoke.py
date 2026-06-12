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
            "client_delivery_allowed_rate": 0.40,
            "client_delivery_blocked_rate": 0.60,
            "client_delivery_status_counts": {"allowed": 4, "blocked": 6},
            "top_client_delivery_blocked_reasons": [
                {
                    "reason": "客户确认包仅在内部质检通过后开放。",
                    "count": 6,
                    "rate": 0.60,
                }
            ],
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
        research_evidence_audit={
            "status": "blocked_for_quant_ingestion",
            "card_count": 2,
            "source_type_counts": {"wechat": 1, "manual_verification_required": 1},
            "usable_prediction_card_count": 1,
            "average_confidence": 0.50,
            "controlled_signals": {"publicity_heat_signal": 0.72},
            "checks": [
                {
                    "name": "social_sources_are_reference_only",
                    "passed": False,
                    "severity": "P0",
                    "evidence": 1,
                    "target": "0 social/creator cards marked usable_for_prediction",
                    "blocker_reason": "Social, WeChat, livestream, or creator evidence leaked into prediction use.",
                }
            ],
            "next_required_evidence": [
                "Social, WeChat, livestream, or creator evidence leaked into prediction use."
            ],
        },
        failure_mining={
            "case_count": 3,
            "failure_case_count": 2,
            "failure_case_rate": 0.666667,
            "failure_buckets": [
                {"bucket": "sliding", "case_count": 1, "case_rate": 0.333333},
                {"bucket": "blacklist_hit", "case_count": 1, "case_rate": 0.333333},
                {"bucket": "tail_assignment", "case_count": 1, "case_rate": 0.333333},
            ],
            "worst_cases": [
                {
                    "case_id": "slide-case",
                    "failure_reasons": ["sliding"],
                    "severity_score": 1.0,
                }
            ],
        },
        ablation_failure_deltas={
            "baseline_variant": "full",
            "variant_failure_deltas": {
                "unsafe_variant": [
                    {"bucket": "new_blacklist_hit", "case_count": 1},
                    {"bucket": "new_tail_assignment", "case_count": 1},
                ]
            },
            "case_regressions": [
                {
                    "case_id": "case-unsafe",
                    "variant": "unsafe_variant",
                    "new_failures": ["blacklist_hit", "tail_assignment"],
                    "severity_score": 1.65,
                }
            ],
        },
    )

    assert result["status"] == "blocked_for_agency_grade_claims"
    assert result["severity_counts"]["P0"] >= 1
    assert result["prioritized_actions"] == result["findings"]
    assert any("风险档不单调" in item["finding"] for item in result["findings"])
    assert any("safe_first" in item["finding"] for item in result["findings"])
    assert any(item["area"] == "quant_tuning" for item in result["findings"])
    assert any(item["area"] == "intake_readiness" for item in result["findings"])
    assert any(item["area"] == "plan_quality" for item in result["findings"])
    assert any(item["area"] == "report_quality" for item in result["findings"])
    assert any(item["area"] == "delivery_bundle" for item in result["findings"])
    assert any(item["area"] == "delivery_portfolio" for item in result["findings"])
    assert any(
        item["area"] == "delivery_portfolio_client_delivery"
        for item in result["findings"]
    )
    assert any(item["area"] == "delivery_portfolio_gate" for item in result["findings"])
    assert any(item["area"] == "research_evidence" for item in result["findings"])
    assert any(item["area"] == "research_evidence_confidence" for item in result["findings"])
    assert any(item["area"] == "failure_sliding" for item in result["findings"])
    assert any(item["area"] == "failure_blacklist_hit" for item in result["findings"])
    assert any(item["area"] == "ablation_case_regression" for item in result["findings"])
    assert any(item["area"] == "ablation_failure_delta" for item in result["findings"])
    markdown = build_markdown_improvement_audit(result)
    assert "GaokaoAgent Self-Improvement Audit" in markdown
    assert "高考志愿平权化" in markdown


if __name__ == "__main__":
    test_improvement_audit_prioritizes_blockers()
    print("improvement audit smoke tests passed")

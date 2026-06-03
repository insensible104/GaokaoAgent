"""Smoke tests for delivery portfolio audits."""

from __future__ import annotations

from evaluation.delivery_portfolio import (
    audit_delivery_portfolio,
    build_markdown_delivery_portfolio_audit,
)


def test_delivery_portfolio_audit_aggregates_failed_gates() -> None:
    manifests = [
        {
            "case_id": "case-ready",
            "status": "ready_to_deliver",
            "intake_readiness_score": 0.90,
            "plan_quality_score": 0.88,
            "report_quality_score": 0.86,
            "delivery_gates": [
                {"gate": "intake_audit", "status": "ready_for_recommendation"},
                {"gate": "plan_quality", "status": "pass"},
                {"gate": "report_quality", "status": "pass"},
            ],
            "next_actions": [],
        },
        {
            "case_id": "case-revision",
            "status": "needs_revision",
            "intake_readiness_score": 0.80,
            "plan_quality_score": 0.52,
            "report_quality_score": 0.66,
            "delivery_gates": [
                {"gate": "intake_audit", "status": "ready_for_recommendation"},
                {"gate": "plan_quality", "status": "needs_revision"},
                {"gate": "report_quality", "status": "needs_revision"},
            ],
            "next_actions": ["修复志愿表结构质量审计"],
        },
        {
            "case_id": "case-blocked",
            "status": "blocked",
            "intake_readiness_score": 0.20,
            "plan_quality_score": 0.0,
            "report_quality_score": 0.70,
            "delivery_gates": [
                {"gate": "intake_audit", "status": "blocked_missing_core"},
                {"gate": "plan_quality", "status": "not_provided"},
                {"gate": "report_quality", "status": "pass"},
            ],
            "next_actions": ["先补齐分数、位次、选科等硬信息。"],
        },
    ]

    result = audit_delivery_portfolio(manifests)

    assert result["case_count"] == 3
    assert result["status"] == "blocked_for_scale"
    assert abs(result["ready_to_deliver_rate"] - (1 / 3)) < 1e-6
    assert result["status_counts"]["blocked"] == 1
    assert any(item["gate"] == "plan_quality" and item["failed_count"] == 2 for item in result["top_failed_gates"])
    assert result["worst_cases"][0]["case_id"] == "case-blocked"
    markdown = build_markdown_delivery_portfolio_audit(result)
    assert "Delivery Portfolio Audit" in markdown
    assert "Top Failed Gates" in markdown


if __name__ == "__main__":
    test_delivery_portfolio_audit_aggregates_failed_gates()
    print("delivery portfolio smoke tests passed")

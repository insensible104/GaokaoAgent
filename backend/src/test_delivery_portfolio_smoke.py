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
            "client_delivery": {
                "allowed": True,
                "status": "allowed",
                "blocked_reason": "",
            },
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
            "client_delivery": {
                "allowed": False,
                "status": "blocked",
                "blocked_reason": (
                    "客户确认包仅在交付包可交付或待签署确认时开放；"
                    "当前仍需先修订内部质检问题。"
                ),
            },
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
    assert abs(result["client_delivery_allowed_rate"] - (1 / 3)) < 1e-6
    assert abs(result["client_delivery_blocked_rate"] - (2 / 3)) < 1e-6
    assert result["status_counts"]["blocked"] == 1
    assert result["client_delivery_status_counts"]["blocked"] == 2
    assert any(
        item["gate"] == "plan_quality" and item["failed_count"] == 2
        for item in result["top_failed_gates"]
    )
    assert any(
        item["count"] == 1 and "客户确认包" in item["reason"]
        for item in result["top_client_delivery_blocked_reasons"]
    )
    assert any(
        item["count"] == 1 and "缺少显式 client_delivery 门控" in item["reason"]
        for item in result["top_client_delivery_blocked_reasons"]
    )
    assert result["worst_cases"][0]["case_id"] == "case-blocked"
    markdown = build_markdown_delivery_portfolio_audit(result)
    assert "Delivery Portfolio Audit" in markdown
    assert "Client Delivery Gate" in markdown
    assert "Top Failed Gates" in markdown


if __name__ == "__main__":
    test_delivery_portfolio_audit_aggregates_failed_gates()
    print("delivery portfolio smoke tests passed")

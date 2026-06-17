"""Smoke tests for next-iteration planning."""

from __future__ import annotations

from evaluation.next_iteration_plan import build_markdown_next_iteration_plan, build_next_iteration_plan


def test_next_iteration_plan_merges_audit_repair_and_replay_artifacts() -> None:
    result = build_next_iteration_plan(
        improvement_audit={
            "status": "blocked_for_agency_grade_claims",
            "findings": [
                {
                    "severity": "P0",
                    "area": "backtest",
                    "finding": "滑档率高于可接受边界",
                    "target": "sliding_rate <= 3%",
                    "recommendation": "收紧 safe_anchor 门槛。",
                    "evidence": {"sliding_rate": 0.12},
                },
                {
                    "severity": "P0",
                    "area": "delivery_portfolio_client_delivery",
                    "finding": "批量案例中客户确认包允许交付比例低于规模化服务目标",
                    "target": "client_delivery_allowed_rate >= 85%",
                    "recommendation": "优先处理高频 client_delivery blocked reason。",
                    "evidence": {"client_delivery_allowed_rate": 0.40},
                }
            ],
        },
        coverage_repair_plan={
            "repair_spec_count": 2,
            "profile_specs": [
                {
                    "case_id": "coverage_repair_001",
                    "priority": "P0",
                    "target_tags": ["rank_boundary_or_lower", "major_has_blacklist"],
                    "profile": {"rank": 118000, "subject_group": "history"},
                }
            ],
        },
        replay_queue_summary={
            "queue_count": 1,
            "missing_case_count": 0,
            "items": [
                {
                    "replay_metadata": {
                        "case_id": "case_slide",
                        "priority": "P0",
                        "failure_reasons": ["sliding"],
                        "recommended_focus": ["safe_anchor_and_first_hit_prefix"],
                    }
                }
            ],
        },
        claim_readiness_portfolio={
            "portfolio_status": "needs_targeted_iteration",
            "common_blockers": [
                {
                    "check": "benchmark_coverage",
                    "count": 2,
                    "blocker_reason": "Frozen cases do not cover critical slices.",
                }
            ],
        },
        research_evidence_audit={
            "status": "blocked_for_quant_ingestion",
            "checks": [
                {
                    "name": "social_sources_are_reference_only",
                    "passed": False,
                    "severity": "P0",
                    "blocker_reason": "Social evidence leaked into prediction use.",
                }
            ],
            "next_required_evidence": ["Social evidence leaked into prediction use."],
        },
        source_paths={
            "coverage_repair_plan": "logs/experiments/run/benchmark_coverage_repair_plan.json",
            "replay_queue_jsonl": "logs/experiments/run/failure_replay_queue.jsonl",
            "delivery_bundle_glob": "logs/cases/*/delivery_bundle.json",
        },
    )
    markdown = build_markdown_next_iteration_plan(result)

    assert result["status"] == "repair_p0_before_next_claim"
    assert result["priority_counts"]["P0"] >= 4
    assert any(item["source"] == "benchmark_coverage_repair" for item in result["work_items"])
    assert any(item["source"] == "failure_replay_queue" for item in result["work_items"])
    assert any("generate_frozen_plans_2025.py" in command for command in result["next_run_commands"])
    assert any("failure_replay_queue.jsonl" in command for command in result["next_run_commands"])
    assert any("delivery-portfolio-audit" in command for command in result["next_run_commands"])
    assert any("logs/cases/*/delivery_bundle.json" in command for command in result["next_run_commands"])
    assert "Next Iteration Plan" in markdown


if __name__ == "__main__":
    test_next_iteration_plan_merges_audit_repair_and_replay_artifacts()
    print("next iteration plan smoke tests passed")

"""Smoke tests for claim-readiness portfolio aggregation."""

from __future__ import annotations

from evaluation.claim_portfolio import (
    build_claim_readiness_portfolio,
    build_markdown_claim_readiness_portfolio,
)
from evaluation.claim_readiness import build_claim_readiness
from evaluation.quant_lab import build_quant_lab_experiment


def _manifest(*, good: bool) -> dict:
    coverage = {
        "status": "ready" if good else "insufficient",
        "coverage_score": 1.0 if good else 0.4,
        "gap_summary": {
            "missing_required_tag_count": 0 if good else 3,
            "missing_critical_pair_count": 0 if good else 2,
            "thin_required_tag_count": 0,
            "thin_critical_pair_count": 0,
        },
    }
    backtest = {
        "case_count": 30 if good else 8,
        "success_rate": 0.97 if good else 0.80,
        "sliding_rate": 0.01 if good else 0.12,
        "preferred_major_hit_rate": 0.60 if good else 0.30,
        "blacklist_hit_rate": 0.0 if good else 0.05,
        "tail_assignment_rate": 0.08 if good else 0.22,
        "average_assigned_major_utility": 0.70,
    }
    calibration = {"overall": {"brier_score": 0.12 if good else 0.30}}
    audit = {"prioritized_actions": [] if good else [{"priority": "P0"}]}
    ablation = {
        "summaries": {
            "full": backtest,
            "candidate": {
                **backtest,
                "preferred_major_hit_rate": backtest["preferred_major_hit_rate"] + 0.02,
            },
        },
        "slice_scoreboard": {"rows": [] if not good else [{"variant": "full", "slice": "rank_20k_60k"}]},
    }
    return build_quant_lab_experiment(
        experiment_id="portfolio_good" if good else "portfolio_bad",
        backtest_summary=backtest,
        calibration_summary=calibration,
        ablation_summary=ablation,
        improvement_audit=audit,
        failure_mining={"failure_case_rate": 0.05 if good else 0.35},
        benchmark_coverage=coverage,
    )


def test_claim_portfolio_ranks_candidate_and_blockers():
    reports = [
        build_claim_readiness(_manifest(good=False)),
        build_claim_readiness(_manifest(good=True)),
    ]
    result = build_claim_readiness_portfolio(reports)
    markdown = build_markdown_claim_readiness_portfolio(result)

    assert result["portfolio_status"] == "has_agency_candidate"
    assert result["best_status"] == "agency_candidate_claim"
    assert result["best_experiment_id"] == "portfolio_good"
    assert result["status_counts"]["blocked_for_agency_grade_claims"] == 1
    assert result["status_counts"]["agency_candidate_claim"] == 1
    assert any(item["check"] == "minimum_backtest_cases" for item in result["common_blockers"])
    assert "Claim Readiness Portfolio" in markdown


if __name__ == "__main__":
    test_claim_portfolio_ranks_candidate_and_blockers()
    print("claim portfolio smoke tests passed")

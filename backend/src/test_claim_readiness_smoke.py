"""Smoke tests for QuantLab claim readiness gates."""

from __future__ import annotations

from evaluation.claim_readiness import build_claim_readiness, build_markdown_claim_readiness
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
        experiment_id="claim_good" if good else "claim_bad",
        backtest_summary=backtest,
        calibration_summary=calibration,
        ablation_summary=ablation,
        improvement_audit=audit,
        failure_mining={"failure_case_rate": 0.05 if good else 0.35},
        benchmark_coverage=coverage,
    )


def test_claim_readiness_blocks_unsupported_agency_claims():
    result = build_claim_readiness(_manifest(good=False))
    markdown = build_markdown_claim_readiness(result)

    assert result["status"] == "blocked_for_agency_grade_claims"
    assert any("Do not claim" in item for item in result["forbidden_claims"])
    assert "Claim Readiness Audit" in markdown


def test_claim_readiness_allows_agency_candidate_when_gates_pass():
    result = build_claim_readiness(_manifest(good=True))

    assert result["status"] == "agency_candidate_claim"
    assert all(row["passed"] for row in result["checks"])
    assert any("candidate" in item for item in result["allowed_claims"])


if __name__ == "__main__":
    test_claim_readiness_blocks_unsupported_agency_claims()
    test_claim_readiness_allows_agency_candidate_when_gates_pass()
    print("claim readiness smoke tests passed")

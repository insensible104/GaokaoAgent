"""Smoke tests for benchmark coverage audits."""

from __future__ import annotations

from evaluation.benchmark_coverage import (
    audit_benchmark_coverage,
    build_coverage_repair_plan,
    build_markdown_benchmark_coverage,
    build_markdown_benchmark_coverage_comparison,
    build_markdown_coverage_repair_plan,
    compare_benchmark_coverage,
)
from evaluation.quant_lab import build_quant_lab_experiment


def _record(
    case_id: str,
    *,
    subject: str,
    rank: int,
    risk: str = "balanced",
    tradeoff: str = "balanced",
    cities: list[str] | None = None,
    majors: list[str] | None = None,
    blacklist: list[str] | None = None,
    cognition: float = 0.2,
    regret: float = 0.5,
) -> dict:
    return {
        "case_id": case_id,
        "user_rank": rank,
        "user_profile": {
            "score": 600,
            "rank": rank,
            "subject_group": subject,
            "risk_tolerance": risk,
            "school_major_preference": tradeoff,
            "preferred_cities": cities or [],
            "preferred_majors": majors or [],
            "blacklist_majors": blacklist or [],
            "major_cognition_risk": cognition,
            "regret_sensitivity": regret,
        },
    }


def test_benchmark_coverage_finds_required_tags_and_pairs():
    records = [
        _record(
            "history_boundary_city_locked",
            subject="历史",
            rank=130000,
            risk="conservative",
            tradeoff="prioritize_major",
            cities=["广州"],
            majors=["法学", "汉语言文学"],
            blacklist=["旅游管理"],
            cognition=0.7,
            regret=0.8,
        ),
        _record(
            "physics_target_open",
            subject="物理",
            rank=30000,
            risk="balanced",
            tradeoff="balanced",
            majors=["计算机"],
        ),
        _record(
            "physics_top_school",
            subject="物理",
            rank=3000,
            risk="aggressive",
            tradeoff="prioritize_school",
            cities=[],
            majors=[],
        ),
    ]

    result = audit_benchmark_coverage(records, min_cases_per_tag=1, min_cases_per_pair=1)
    markdown = build_markdown_benchmark_coverage(result)
    repair_plan = build_coverage_repair_plan(result)
    repair_markdown = build_markdown_coverage_repair_plan(repair_plan)
    manifest = build_quant_lab_experiment(
        experiment_id="coverage_smoke",
        benchmark_coverage=result,
    )

    required = {row["tag"]: row for row in result["required_tag_coverage"]}
    pairs = {tuple(row["pair"]): row for row in result["critical_pair_coverage"]}
    assert required["subject_history"]["status"] == "covered"
    assert required["rank_boundary_or_lower"]["status"] == "covered"
    assert required["major_cognition_high"]["status"] == "covered"
    assert pairs[("rank_boundary_or_lower", "subject_history")]["status"] == "covered"
    assert result["status"] == "insufficient"
    assert "Benchmark Coverage Audit" in markdown
    assert repair_plan["repair_spec_count"] > 0
    assert repair_plan["profile_specs"][0]["profile"]["rank"] is not None
    assert "Benchmark Coverage Repair Plan" in repair_markdown
    assert manifest["metric_digest"]["benchmark_coverage"]["status"] == "insufficient"


def test_benchmark_coverage_comparison_tracks_repair_effect():
    before = audit_benchmark_coverage(
        [
            _record(
                "physics_target_open",
                subject="物理",
                rank=30000,
            )
        ],
        min_cases_per_tag=1,
        min_cases_per_pair=1,
    )
    after = audit_benchmark_coverage(
        [
            _record(
                "physics_target_open",
                subject="物理",
                rank=30000,
            ),
            _record(
                "history_boundary_city_locked",
                subject="历史",
                rank=130000,
                risk="conservative",
                tradeoff="prioritize_major",
                cities=["广州"],
                majors=["法学", "汉语言文学"],
                blacklist=["旅游管理"],
                cognition=0.7,
                regret=0.8,
            ),
        ],
        min_cases_per_tag=1,
        min_cases_per_pair=1,
    )

    comparison = compare_benchmark_coverage(before, after)
    markdown = build_markdown_benchmark_coverage_comparison(comparison)

    assert comparison["coverage_score_delta"] > 0
    assert "subject_history" in comparison["fixed_required_tags"]
    assert "rank_boundary_or_lower + subject_history" in comparison["fixed_critical_pairs"]
    assert comparison["status"] == "improved"
    assert "Benchmark Coverage Comparison" in markdown


if __name__ == "__main__":
    test_benchmark_coverage_finds_required_tags_and_pairs()
    test_benchmark_coverage_comparison_tracks_repair_effect()
    print("benchmark coverage smoke tests passed")

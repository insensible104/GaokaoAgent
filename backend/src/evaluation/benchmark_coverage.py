"""Benchmark coverage audit for frozen GaokaoAgent plan records.

Backtests are only useful when the frozen case set covers the user segments we
care about. This module audits coverage before treating experiment metrics as
evidence for agency-grade claims.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any, Sequence

from evaluation.slice_scoreboard import build_record_slice_tags


PROTOCOL_VERSION = "gaokao-benchmark-coverage-v1"
REPAIR_PLAN_PROTOCOL_VERSION = "gaokao-benchmark-coverage-repair-v1"

DIMENSION_PREFIXES = {
    "subject": "subject_",
    "rank": "rank_",
    "risk": "risk_",
    "tradeoff": "tradeoff_",
    "region": "region_",
    "major": "major_",
    "cognition": "major_cognition_",
    "regret": "regret_",
}
REQUIRED_TAGS = [
    "subject_physics",
    "subject_history",
    "rank_top_5k",
    "rank_5k_20k",
    "rank_20k_60k",
    "rank_60k_120k",
    "rank_boundary_or_lower",
    "risk_conservative",
    "risk_balanced",
    "risk_aggressive",
    "tradeoff_prioritize_school",
    "tradeoff_balanced",
    "tradeoff_prioritize_major",
    "region_guangdong_or_city_locked",
    "region_narrow_preference",
    "region_open",
    "major_has_blacklist",
    "major_strict_preference",
    "major_has_preference",
    "major_cognition_high",
    "regret_sensitive",
]
CRITICAL_PAIR_GROUPS = [
    ("subject_history", "rank_boundary_or_lower"),
    ("subject_history", "rank_60k_120k"),
    ("rank_boundary_or_lower", "region_guangdong_or_city_locked"),
    ("rank_boundary_or_lower", "major_has_blacklist"),
    ("rank_boundary_or_lower", "major_strict_preference"),
    ("rank_60k_120k", "region_narrow_preference"),
    ("rank_60k_120k", "major_strict_preference"),
    ("risk_conservative", "major_has_blacklist"),
    ("risk_conservative", "regret_sensitive"),
    ("tradeoff_prioritize_major", "major_has_blacklist"),
]
RANK_REPRESENTATIVES = {
    "rank_top_5k": 3000,
    "rank_5k_20k": 12000,
    "rank_20k_60k": 38000,
    "rank_60k_120k": 78000,
    "rank_boundary_or_lower": 130000,
}


def _case_id(record: dict[str, Any]) -> str:
    return str(record.get("case_id") or record.get("id") or "")


def _dimension_for_tag(tag: str) -> str:
    for dimension, prefix in DIMENSION_PREFIXES.items():
        if tag.startswith(prefix):
            return dimension
    return "other"


def _coverage_status(missing_required: int, weak_required: int, missing_pairs: int, weak_pairs: int) -> str:
    if missing_required or missing_pairs:
        return "insufficient"
    if weak_required or weak_pairs:
        return "thin"
    return "ready"


def _coverage_score(
    *,
    required_rows: Sequence[dict[str, Any]],
    pair_rows: Sequence[dict[str, Any]],
) -> float:
    checks = list(required_rows) + list(pair_rows)
    if not checks:
        return 0.0
    passed = sum(1 for row in checks if row.get("status") == "covered")
    thin = sum(1 for row in checks if row.get("status") == "thin")
    return round((passed + thin * 0.5) / len(checks), 6)


def audit_benchmark_coverage(
    records: Sequence[dict[str, Any]],
    *,
    min_cases_per_tag: int = 2,
    min_cases_per_pair: int = 1,
    required_tags: Sequence[str] = REQUIRED_TAGS,
    critical_pair_groups: Sequence[tuple[str, str]] = CRITICAL_PAIR_GROUPS,
) -> dict[str, Any]:
    """Audit whether a frozen benchmark covers important user slices."""
    tag_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    cases_by_tag: dict[str, list[str]] = {}
    cases_by_pair: dict[tuple[str, str], list[str]] = {}
    dimension_counts: dict[str, Counter[str]] = {}

    for record in records:
        case_id = _case_id(dict(record))
        tags = sorted(set(build_record_slice_tags(dict(record))))
        for tag in tags:
            tag_counts[tag] += 1
            cases_by_tag.setdefault(tag, []).append(case_id)
            dimension_counts.setdefault(_dimension_for_tag(tag), Counter())[tag] += 1
        for left, right in combinations(tags, 2):
            pair = tuple(sorted((left, right)))
            pair_counts[pair] += 1
            cases_by_pair.setdefault(pair, []).append(case_id)

    required_rows = []
    for tag in required_tags:
        count = tag_counts[tag]
        if count == 0:
            status = "missing"
        elif count < min_cases_per_tag:
            status = "thin"
        else:
            status = "covered"
        required_rows.append(
            {
                "tag": tag,
                "dimension": _dimension_for_tag(tag),
                "case_count": count,
                "min_case_count": min_cases_per_tag,
                "status": status,
                "sample_case_ids": cases_by_tag.get(tag, [])[:5],
            }
        )

    pair_rows = []
    for raw_pair in critical_pair_groups:
        pair = tuple(sorted((str(raw_pair[0]), str(raw_pair[1]))))
        count = pair_counts[pair]
        if count == 0:
            status = "missing"
        elif count < min_cases_per_pair:
            status = "thin"
        else:
            status = "covered"
        pair_rows.append(
            {
                "pair": list(pair),
                "case_count": count,
                "min_case_count": min_cases_per_pair,
                "status": status,
                "sample_case_ids": cases_by_pair.get(pair, [])[:5],
            }
        )

    missing_required = sum(1 for row in required_rows if row["status"] == "missing")
    weak_required = sum(1 for row in required_rows if row["status"] == "thin")
    missing_pairs = sum(1 for row in pair_rows if row["status"] == "missing")
    weak_pairs = sum(1 for row in pair_rows if row["status"] == "thin")
    return {
        "protocol_version": PROTOCOL_VERSION,
        "case_count": len(records),
        "status": _coverage_status(missing_required, weak_required, missing_pairs, weak_pairs),
        "coverage_score": _coverage_score(required_rows=required_rows, pair_rows=pair_rows),
        "min_cases_per_tag": min_cases_per_tag,
        "min_cases_per_pair": min_cases_per_pair,
        "dimension_counts": {
            dimension: [
                {"tag": tag, "case_count": count}
                for tag, count in counts.most_common()
            ]
            for dimension, counts in sorted(dimension_counts.items())
        },
        "required_tag_coverage": required_rows,
        "critical_pair_coverage": pair_rows,
        "gap_summary": {
            "missing_required_tag_count": missing_required,
            "thin_required_tag_count": weak_required,
            "missing_critical_pair_count": missing_pairs,
            "thin_critical_pair_count": weak_pairs,
        },
        "recommendations": _recommendations(required_rows, pair_rows),
    }


def _recommendations(required_rows: Sequence[dict[str, Any]], pair_rows: Sequence[dict[str, Any]]) -> list[str]:
    recommendations: list[str] = []
    missing_tags = [row["tag"] for row in required_rows if row["status"] == "missing"]
    thin_tags = [row["tag"] for row in required_rows if row["status"] == "thin"]
    missing_pairs = [row["pair"] for row in pair_rows if row["status"] == "missing"]
    if missing_tags:
        recommendations.append("Add frozen cases for missing required tags: " + ", ".join(missing_tags[:8]))
    if thin_tags:
        recommendations.append("Increase case count for thin required tags: " + ", ".join(thin_tags[:8]))
    if missing_pairs:
        rendered = [" + ".join(pair) for pair in missing_pairs[:6]]
        recommendations.append("Add hard intersection cases for critical pairs: " + "; ".join(rendered))
    if not recommendations:
        recommendations.append("Benchmark coverage is ready for aggregate metric review.")
    return recommendations


def _profile_spec_for_tags(tags: Sequence[str]) -> dict[str, Any]:
    tag_set = set(tags)
    subject = "历史" if "subject_history" in tag_set else "物理"
    rank = next((RANK_REPRESENTATIVES[tag] for tag in tags if tag in RANK_REPRESENTATIVES), 38000)
    risk = "balanced"
    if "risk_conservative" in tag_set:
        risk = "conservative"
    if "risk_aggressive" in tag_set:
        risk = "aggressive"
    tradeoff = "balanced"
    if "tradeoff_prioritize_school" in tag_set:
        tradeoff = "prioritize_school"
    if "tradeoff_prioritize_major" in tag_set:
        tradeoff = "prioritize_major"

    preferred_cities: list[str] = []
    if "region_guangdong_or_city_locked" in tag_set:
        preferred_cities = ["广州"]
    elif "region_narrow_preference" in tag_set:
        preferred_cities = ["北京"]

    preferred_majors = ["计算机"]
    blacklist_majors: list[str] = []
    if subject == "历史":
        preferred_majors = ["法学"]
    if "major_strict_preference" in tag_set:
        preferred_majors = ["计算机", "软件工程"] if subject == "物理" else ["法学", "汉语言文学"]
    if "major_has_blacklist" in tag_set:
        preferred_majors = ["计算机", "软件工程"] if subject == "物理" else ["法学", "汉语言文学"]
        blacklist_majors = ["土木", "材料"] if subject == "物理" else ["旅游管理", "酒店管理"]
    elif "major_open" in tag_set:
        preferred_majors = []

    return {
        "score": None,
        "rank": rank,
        "subject_group": subject,
        "preferred_cities": preferred_cities,
        "excluded_cities": [],
        "preferred_majors": preferred_majors,
        "blacklist_majors": blacklist_majors,
        "risk_tolerance": risk,
        "school_major_preference": tradeoff,
        "preference_confidence": 0.72,
        "major_cognition_risk": 0.72 if "major_cognition_high" in tag_set else 0.25,
        "regret_sensitivity": 0.78 if "regret_sensitive" in tag_set else 0.50,
    }


def _gap_priority(row: dict[str, Any], *, is_pair: bool) -> str:
    if row.get("status") == "missing" and is_pair:
        return "P0"
    if row.get("status") == "missing":
        return "P1"
    return "P2"


def build_coverage_repair_plan(
    coverage: dict[str, Any],
    *,
    max_specs: int = 50,
) -> dict[str, Any]:
    """Convert coverage gaps into profile specs for the next frozen-plan run."""
    specs: list[dict[str, Any]] = []
    seen_targets: set[tuple[str, ...]] = set()

    def add_spec(*, tags: Sequence[str], source: str, row: dict[str, Any], is_pair: bool) -> None:
        if len(specs) >= max_specs:
            return
        target = tuple(sorted(str(tag) for tag in tags))
        if target in seen_targets:
            return
        seen_targets.add(target)
        missing_count = max(1, int(row.get("min_case_count", 1) or 1) - int(row.get("case_count", 0) or 0))
        index = len(specs) + 1
        specs.append(
            {
                "case_id": f"coverage_repair_{index:03d}",
                "priority": _gap_priority(row, is_pair=is_pair),
                "source": source,
                "coverage_status": row.get("status"),
                "target_tags": list(target),
                "recommended_case_count": missing_count,
                "profile": _profile_spec_for_tags(target),
                "reason": (
                    f"{source} coverage is {row.get('status')} "
                    f"({row.get('case_count', 0)}/{row.get('min_case_count', 1)} cases)."
                ),
            }
        )

    for row in coverage.get("critical_pair_coverage") or []:
        if row.get("status") != "covered":
            add_spec(tags=row.get("pair") or [], source="critical_pair", row=row, is_pair=True)
    for row in coverage.get("required_tag_coverage") or []:
        if row.get("status") != "covered":
            add_spec(tags=[row.get("tag")], source="required_tag", row=row, is_pair=False)

    return {
        "protocol_version": REPAIR_PLAN_PROTOCOL_VERSION,
        "source_protocol_version": coverage.get("protocol_version"),
        "coverage_status": coverage.get("status"),
        "coverage_score": coverage.get("coverage_score"),
        "repair_spec_count": len(specs),
        "profile_specs": specs,
        "usage": (
            "Pass this file to scripts/generate_frozen_plans_2025.py "
            "--coverage-repair-plan before the next backtest run."
        ),
    }


def build_markdown_coverage_repair_plan(result: dict[str, Any]) -> str:
    """Build a Markdown report for coverage repair specs."""
    lines = [
        "# Benchmark Coverage Repair Plan",
        "",
        f"Coverage status: `{result.get('coverage_status', 'unknown')}`",
        f"Repair specs: {result.get('repair_spec_count', 0)}",
        "",
        "| Priority | Case | Source | Target Tags | Rank | Subject |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for spec in result.get("profile_specs", []) or []:
        profile = spec.get("profile") or {}
        tags = ", ".join(f"`{tag}`" for tag in spec.get("target_tags", []) or [])
        lines.append(
            f"| `{spec.get('priority', '')}` | `{spec.get('case_id', '')}` | "
            f"`{spec.get('source', '')}` | {tags} | {profile.get('rank', '')} | "
            f"`{profile.get('subject_group', '')}` |"
        )
    if not result.get("profile_specs"):
        lines.append("|  | `none` |  |  |  |  |")
    lines.extend(["", "## Usage", "", f"- {result.get('usage', '')}"])
    return "\n".join(lines)


def build_markdown_benchmark_coverage(result: dict[str, Any]) -> str:
    """Build a Markdown report for benchmark coverage."""
    lines = [
        "# Benchmark Coverage Audit",
        "",
        f"Status: `{result.get('status', 'unknown')}`",
        f"Cases: {result.get('case_count', 0)}",
        f"Coverage score: {float(result.get('coverage_score', 0.0)):.1%}",
        "",
        "## Required Tags",
        "",
        "| Tag | Dimension | Cases | Required | Status |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in result.get("required_tag_coverage", []) or []:
        lines.append(
            f"| `{row.get('tag', '')}` | `{row.get('dimension', '')}` | "
            f"{row.get('case_count', 0)} | {row.get('min_case_count', 0)} | "
            f"`{row.get('status', '')}` |"
        )

    lines.extend(["", "## Critical Pairs", "", "| Pair | Cases | Required | Status |", "| --- | ---: | ---: | --- |"])
    for row in result.get("critical_pair_coverage", []) or []:
        pair = " + ".join(f"`{item}`" for item in row.get("pair", []) or [])
        lines.append(
            f"| {pair} | {row.get('case_count', 0)} | {row.get('min_case_count', 0)} | "
            f"`{row.get('status', '')}` |"
        )

    lines.extend(["", "## Recommendations", ""])
    for item in result.get("recommendations") or []:
        lines.append(f"- {item}")
    return "\n".join(lines)

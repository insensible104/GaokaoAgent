"""Slice-level scoreboards for quant experiment comparisons.

Top quant systems do not only report one aggregate metric. They also inspect
whether a candidate policy silently harms important user segments. For Gaokao
planning, the critical segments are subject group, rank band, preference
strictness, region constraints, risk tolerance, and school-vs-major tradeoff.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Sequence

from models.game_matrix import VolunteerPlan
from models.user_profile import UserProfile


METRIC_FIELDS = [
    "success",
    "sliding",
    "selected_major_hit",
    "preferred_major_hit",
    "blacklist_hit",
    "tail_assignment_hit",
    "wasted_score_risk",
]
MEAN_FIELDS = [
    "first_hit_index",
    "first_hit_margin",
    "assigned_major_utility",
]
GUANGDONG_CORE_CITIES = {
    "广州",
    "深圳",
    "珠海",
    "佛山",
    "东莞",
    "中山",
    "惠州",
    "江门",
    "肇庆",
    "汕头",
    "湛江",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _rank_band(rank: int | None) -> str:
    if rank is None:
        return "rank_unknown"
    if rank <= 5_000:
        return "rank_top_5k"
    if rank <= 20_000:
        return "rank_5k_20k"
    if rank <= 60_000:
        return "rank_20k_60k"
    if rank <= 120_000:
        return "rank_60k_120k"
    return "rank_boundary_or_lower"


def _subject_group(value: str | None) -> str:
    text = str(value or "").strip().lower()
    if "物理" in text or "physics" in text:
        return "subject_physics"
    if "历史" in text or "history" in text:
        return "subject_history"
    return "subject_unknown"


def _region_constraint(profile: UserProfile | None) -> str:
    if profile is None:
        return "region_unknown"
    preferred = [str(item).strip() for item in profile.preferred_cities if str(item).strip()]
    excluded = [str(item).strip() for item in profile.excluded_cities if str(item).strip()]
    if preferred and all(city in GUANGDONG_CORE_CITIES or "广东" in city for city in preferred):
        return "region_guangdong_or_city_locked"
    if preferred and len(preferred) <= 2:
        return "region_narrow_preference"
    if excluded:
        return "region_has_exclusions"
    return "region_open"


def _major_constraint(profile: UserProfile | None) -> str:
    if profile is None:
        return "major_unknown"
    if profile.blacklist_majors:
        return "major_has_blacklist"
    if len(profile.preferred_majors) >= 2:
        return "major_strict_preference"
    if profile.preferred_majors:
        return "major_has_preference"
    return "major_open"


def _profile_from_record(record: dict[str, Any]) -> UserProfile | None:
    payload = record.get("user_profile") or record.get("profile")
    if not payload:
        return None
    return payload if isinstance(payload, UserProfile) else UserProfile(**payload)


def _plan_from_record(record: dict[str, Any]) -> VolunteerPlan | None:
    payload = record.get("plan") or record.get("volunteer_plan")
    if not payload:
        return None
    return payload if isinstance(payload, VolunteerPlan) else VolunteerPlan(**payload)


def build_record_slice_tags(record: dict[str, Any]) -> list[str]:
    """Build stable slice tags from a frozen plan record."""
    profile = _profile_from_record(record)
    plan = _plan_from_record(record)
    rank = (
        int(profile.rank)
        if profile and profile.rank is not None
        else int(record.get("user_rank") or plan.user_rank)
        if plan and (record.get("user_rank") or plan.user_rank) is not None
        else None
    )
    subject = (
        profile.subject_group
        if profile
        else plan.subject_group
        if plan
        else str(record.get("subject_group") or "")
    )
    risk = f"risk_{str(profile.risk_tolerance.value if profile else 'unknown')}"
    tradeoff = f"tradeoff_{str(profile.school_major_preference.value if profile else 'unknown')}"
    cognition = (
        "major_cognition_high"
        if profile and profile.major_cognition_risk >= 0.55
        else "major_cognition_normal"
    )
    regret = (
        "regret_sensitive"
        if profile and profile.regret_sensitivity >= 0.65
        else "regret_normal"
    )
    return [
        _subject_group(subject),
        _rank_band(rank),
        risk,
        tradeoff,
        _region_constraint(profile),
        _major_constraint(profile),
        cognition,
        regret,
    ]


def attach_slice_tags_to_per_case(
    *,
    records: Sequence[dict[str, Any]],
    per_case: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach user-slice tags to ablation per-case rows by case_id."""
    tags_by_case = {
        str(record.get("case_id") or ""): build_record_slice_tags(record)
        for record in records
    }
    default_tags = build_record_slice_tags(records[0]) if records else []
    enriched: list[dict[str, Any]] = []
    for row in per_case:
        case_id = str(row.get("case_id") or "")
        enriched.append({**row, "slice_tags": list(tags_by_case.get(case_id) or default_tags)})
    return enriched


def _summarize_case_rows(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {"case_count": len(rows)}
    for field in METRIC_FIELDS:
        summary[f"{field}_rate"] = round(
            _mean([1.0 if row.get(field) else 0.0 for row in rows]),
            6,
        )
    for field in MEAN_FIELDS:
        values = [
            _safe_float(row.get(field))
            for row in rows
            if row.get(field) is not None
        ]
        summary[f"average_{field}"] = round(_mean(values), 6)
    return summary


def build_slice_scoreboard(
    per_case: Sequence[dict[str, Any]],
    *,
    min_case_count: int = 1,
) -> dict[str, Any]:
    """Aggregate ablation result rows by variant and user slice."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in per_case:
        variant = str(row.get("variant") or "unknown")
        for tag in row.get("slice_tags") or ["slice_unknown"]:
            grouped[(variant, str(tag))].append(row)

    rows: list[dict[str, Any]] = []
    for (variant, slice_tag), values in sorted(grouped.items()):
        if len(values) < min_case_count:
            continue
        rows.append(
            {
                "variant": variant,
                "slice": slice_tag,
                **_summarize_case_rows(values),
            }
        )
    return {
        "min_case_count": min_case_count,
        "slice_count": len(rows),
        "rows": rows,
    }


def strongest_slice_regressions(
    scoreboard: dict[str, Any],
    *,
    baseline_variant: str = "full",
    metric: str = "success_rate",
    top_k: int = 8,
) -> list[dict[str, Any]]:
    """Find slices where non-baseline variants underperform the baseline."""
    by_slice_variant = {
        (row.get("slice"), row.get("variant")): row
        for row in scoreboard.get("rows", [])
    }
    regressions: list[dict[str, Any]] = []
    for (slice_tag, variant), row in by_slice_variant.items():
        if variant == baseline_variant:
            continue
        baseline = by_slice_variant.get((slice_tag, baseline_variant))
        if not baseline:
            continue
        delta = _safe_float(row.get(metric)) - _safe_float(baseline.get(metric))
        if delta < 0:
            regressions.append(
                {
                    "slice": slice_tag,
                    "variant": variant,
                    "metric": metric,
                    "delta_vs_baseline": round(delta, 6),
                    "case_count": row.get("case_count", 0),
                }
            )
    return sorted(regressions, key=lambda item: item["delta_vs_baseline"])[:top_k]


def build_markdown_slice_scoreboard(scoreboard: dict[str, Any]) -> str:
    """Build a compact Markdown slice scoreboard."""
    lines = [
        "# Quant Slice Scoreboard",
        "",
        f"Minimum cases per slice: {scoreboard.get('min_case_count', 1)}",
        "",
        "| Variant | Slice | Cases | Success | Preferred | Blacklist | Tail | Wasted | Avg Utility |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in scoreboard.get("rows", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('variant', '')}`",
                    f"`{row.get('slice', '')}`",
                    str(row.get("case_count", 0)),
                    f"{_safe_float(row.get('success_rate')) * 100:.1f}%",
                    f"{_safe_float(row.get('preferred_major_hit_rate')) * 100:.1f}%",
                    f"{_safe_float(row.get('blacklist_hit_rate')) * 100:.1f}%",
                    f"{_safe_float(row.get('tail_assignment_hit_rate')) * 100:.1f}%",
                    f"{_safe_float(row.get('wasted_score_risk_rate')) * 100:.1f}%",
                    f"{_safe_float(row.get('average_assigned_major_utility')):.3f}",
                ]
            )
            + " |"
        )
    if not scoreboard.get("rows"):
        lines.append("| `empty` | `empty` | 0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.000 |")

    regressions = strongest_slice_regressions(scoreboard)
    lines.extend(["", "## Strongest Success Regressions", ""])
    if regressions:
        for item in regressions:
            lines.append(
                f"- `{item['variant']}` on `{item['slice']}`: "
                f"{item['delta_vs_baseline'] * 100:.1f}pp vs `full` "
                f"({item['case_count']} cases)"
            )
    else:
        lines.append("- No slice-level success regression found against `full`.")
    return "\n".join(lines)

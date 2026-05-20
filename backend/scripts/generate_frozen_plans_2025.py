"""Generate frozen 2025 volunteer-plan records for backtest and ablation.

This script intentionally uses only prediction-time inputs:

- 2021-2024 historical admission CSVs
- 2025 enrollment plan CSV
- 2025 score-rank tables for score approximation

It must not read `data/actual_2025.csv` or any post-hoc outcome file.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = BACKEND_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agents.game_agent import _resolve_runtime_data_dir
from engines.enrollment_loader import EnrollmentPlanLoader
from engines.probability import calculate_admission_probability, classify_strategy_tag
from engines.quant_engine import GaokaoQuantEngine
from models.game_matrix import MajorGroupRow, StrategyTag, VolatilityLevel
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from recommendation.bundle_risk import (
    analyze_bundle_risk,
    quota_bucket,
    quota_stability_score,
    variance_opportunity_score,
)
from recommendation.major_choice_planner import (
    build_major_options_from_records,
    build_volunteer_plan,
    choose_six_majors,
)
from recommendation.major_utility import score_major_options
from recommendation.policy_config import TAIL_RISK_SCORE_PENALTY_WEIGHT
from recommendation.school_signal import score_school_major_signal
from recommendation.tradeoff_policy import score_tradeoff
from rl.runtime_policy import RLRuntimePolicy
from utils.city_mapping import calculate_city_preference_score, get_school_city


SUBJECTS = ["物理", "历史"]
PHYSICS_RANKS = [1800, 4500, 8000, 12000, 18000, 26000, 38000, 55000, 76000, 98000, 130000, 180000]
HISTORY_RANKS = [900, 2200, 4500, 8000, 12000, 18000, 28000, 42000, 60000, 78000, 98000, 130000]

PREFERENCE_TEMPLATES = {
    "物理": [
        (["广州", "深圳"], ["计算机", "软件工程"], ["土木", "材料"], RiskTolerance.BALANCED, SchoolMajorPreference.PRIORITIZE_MAJOR),
        (["广州", "珠海"], ["临床医学", "口腔医学"], ["护理", "生物"], RiskTolerance.CONSERVATIVE, SchoolMajorPreference.PRIORITIZE_MAJOR),
        (["深圳", "广州"], ["电子信息", "自动化"], ["化工", "环境"], RiskTolerance.BALANCED, SchoolMajorPreference.BALANCED),
        (["广州"], ["金融", "经济"], ["旅游管理", "工商管理"], RiskTolerance.AGGRESSIVE, SchoolMajorPreference.PRIORITIZE_SCHOOL),
    ],
    "历史": [
        (["广州", "深圳"], ["法学"], ["旅游管理", "酒店管理"], RiskTolerance.BALANCED, SchoolMajorPreference.PRIORITIZE_MAJOR),
        (["广州"], ["汉语言文学", "新闻传播"], ["外国语", "翻译"], RiskTolerance.CONSERVATIVE, SchoolMajorPreference.BALANCED),
        (["深圳", "广州"], ["经济学", "金融"], ["旅游管理", "工商管理"], RiskTolerance.BALANCED, SchoolMajorPreference.PRIORITIZE_SCHOOL),
        (["珠海", "广州"], ["会计", "财务管理"], ["市场营销"], RiskTolerance.AGGRESSIVE, SchoolMajorPreference.BALANCED),
    ],
}


def _score_for_rank(data_dir: Path, subject_group: str, rank: int) -> int:
    path = data_dir / f"2025_{subject_group}_yifenyiduan.csv"
    if not path.exists():
        return 620 if subject_group == "物理" else 600
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df = df.dropna(subset=["rank", "score"])
    if df.empty:
        return 620 if subject_group == "物理" else 600
    idx = (df["rank"] - rank).abs().idxmin()
    return int(df.loc[idx, "score"])


def generate_profiles(*, data_dir: Path, num_cases: int, seed: int) -> list[tuple[str, UserProfile]]:
    rng = random.Random(seed)
    cases: list[tuple[str, UserProfile]] = []
    rank_grid = {"物理": PHYSICS_RANKS, "历史": HISTORY_RANKS}

    for subject_group in SUBJECTS:
        for idx, rank in enumerate(rank_grid[subject_group]):
            cities, majors, blacklist, risk, preference = PREFERENCE_TEMPLATES[subject_group][
                idx % len(PREFERENCE_TEMPLATES[subject_group])
            ]
            score = _score_for_rank(data_dir, subject_group, rank)
            cases.append(
                (
                    f"{subject_group}_rank_{rank:06d}",
                    UserProfile(
                        score=score,
                        rank=rank,
                        subject_group=subject_group,
                        preferred_cities=list(cities),
                        preferred_majors=list(majors),
                        blacklist_majors=list(blacklist),
                        risk_tolerance=risk,
                        school_major_preference=preference,
                        preference_confidence=0.72,
                        regret_sensitivity=0.65 if risk != RiskTolerance.AGGRESSIVE else 0.45,
                    ),
                )
            )

    rng.shuffle(cases)
    return cases[:num_cases]


def _strategy_tag(raw: str) -> StrategyTag:
    try:
        return StrategyTag(raw)
    except ValueError:
        return StrategyTag.TARGET


def _volatility_level(min_rank_pred: int, volatility_std: float) -> VolatilityLevel:
    if volatility_std > max(1, min_rank_pred) * 0.10:
        return VolatilityLevel.HIGH
    if volatility_std < max(1, min_rank_pred) * 0.05:
        return VolatilityLevel.LOW
    return VolatilityLevel.MEDIUM


def build_candidate_rows(
    *,
    profile: UserProfile,
    engine: GaokaoQuantEngine,
    enrollment_loader: EnrollmentPlanLoader,
    target_count: int,
    min_probability: float,
) -> list[MajorGroupRow]:
    major_groups = engine.search_major_groups(
        user_rank=int(profile.rank or 0),
        subject_group=profile.subject_group,
        target_count=target_count,
    )

    rows: list[MajorGroupRow] = []
    seen: set[tuple[str, str, str]] = set()

    for _, group in major_groups.iterrows():
        historical_school = str(group["school"]).strip()
        school_code = EnrollmentPlanLoader._normalize_code(group.get("school_code", historical_school)) or historical_school
        major_group_raw = group["major_group"]
        major_group_code = EnrollmentPlanLoader._normalize_code(major_group_raw)

        hist_data = engine.get_major_group_history(school=historical_school, major_group=major_group_raw)
        probability = calculate_admission_probability(user_rank=int(profile.rank or 0), hist_data=hist_data)
        if not probability or probability["prob"] < min_probability:
            continue

        plan_records = enrollment_loader.get_major_group_options(
            school_name=historical_school,
            school_code=school_code,
            major_group_code=major_group_code,
            category=profile.subject_group,
        )
        if not plan_records:
            continue

        canonical_record = plan_records[0]
        school = str(canonical_record.get("school_name") or historical_school).strip()
        school_code = EnrollmentPlanLoader._normalize_code(canonical_record.get("school_code") or school_code) or school_code
        major_group_code = (
            EnrollmentPlanLoader._normalize_code(canonical_record.get("major_group_code") or major_group_code)
            or major_group_code
        )
        key = (school_code, school, major_group_code)
        if key in seen:
            continue
        seen.add(key)

        fallback_majors = [str(item).strip() for item in group["major"] if str(item).strip()]
        major_options = build_major_options_from_records(plan_records, fallback_majors=fallback_majors)
        major_options = score_major_options(major_options, profile)
        bundle_risk = analyze_bundle_risk(major_options)
        suggested_major_choices = choose_six_majors(major_options)
        suggested_major_names = [option.major_name for option in suggested_major_choices]
        full_major_names = [option.major_name for option in major_options] or fallback_majors

        school_signal = score_school_major_signal(
            school_name=school,
            major_names=suggested_major_names or fallback_majors[:6],
            profile=profile,
        )
        if school_signal.average_score <= 0:
            continue

        is_blacklist_risk = any(
            keyword in major
            for major in full_major_names
            for keyword in profile.blacklist_majors
        )
        if full_major_names and is_blacklist_risk:
            blacklist_count = len(
                [
                    major
                    for major in full_major_names
                    if any(keyword in major for keyword in profile.blacklist_majors)
                ]
            )
            if blacklist_count == len(full_major_names):
                continue

        admission_prob = float(probability["prob"])
        min_rank_pred = int(probability["min_rank_pred"])
        rank_diff = min_rank_pred - int(profile.rank or 0)
        z_score = float(probability.get("z_score", 0.0))
        strategy = _strategy_tag(classify_strategy_tag(admission_prob, z_score=z_score))
        quota = sum(option.plan_quota or 0 for option in major_options) or int(group.get("quota", 0) or 0)

        city_score = calculate_city_preference_score(
            city=get_school_city(school),
            preferred_cities=profile.preferred_cities,
            excluded_cities=profile.excluded_cities,
        )
        final_score = (
            school_signal.average_score * 0.6
            + admission_prob * 100 * 0.4
        )
        final_score *= 1 - bundle_risk.tail_assignment_risk * TAIL_RISK_SCORE_PENALTY_WEIGHT
        final_score *= city_score

        row = MajorGroupRow(
            school_name=school,
            school_code=school_code,
            major_group_code=major_group_code,
            major_list=suggested_major_names or fallback_majors[:6],
            major_count=len(full_major_names),
            major_options=major_options,
            suggested_major_choices=suggested_major_choices,
            admission_prob=admission_prob,
            min_rank_pred=min_rank_pred,
            rank_diff=rank_diff,
            rank_ci_lower=int(probability["ci_lower"]),
            rank_ci_upper=int(probability["ci_upper"]),
            volatility=_volatility_level(min_rank_pred, float(probability["volatility_std"])),
            quota=quota if quota > 0 else None,
            quota_bucket=quota_bucket(quota),
            quota_stability_score=quota_stability_score(quota),
            variance_opportunity_score=variance_opportunity_score(quota, bundle_risk.major_utility_dispersion),
            adjustment_risk=bundle_risk.tail_assignment_risk,
            worst_case_major=bundle_risk.worst_case_major,
            is_blacklist_risk=is_blacklist_risk,
            acceptable_major_ratio=bundle_risk.acceptable_major_ratio,
            blacklist_major_ratio=bundle_risk.blacklist_major_ratio,
            major_utility_mean=bundle_risk.major_utility_mean,
            major_utility_min=bundle_risk.major_utility_min,
            major_utility_dispersion=bundle_risk.major_utility_dispersion,
            tail_assignment_risk=bundle_risk.tail_assignment_risk,
            bundle_type=bundle_risk.bundle_type,
            obey_adjustment=bundle_risk.obey_adjustment,
            adjustment_advice=bundle_risk.adjustment_advice,
            recommendation_role=f"{strategy.value}:{school_signal.tradeoff_label}",
            risk_reasons=bundle_risk.risk_reasons,
            audit_flags=bundle_risk.audit_flags,
            strategy_tag=strategy,
            comprehensive_score=max(0.0, min(1.0, final_score / 100.0)),
            sentiment_score=0.0,
        )

        tradeoff = score_tradeoff(
            row=row,
            profile=profile,
            school_major_score=school_signal.average_score / 100.0,
            city_preference_score=city_score,
        )
        row.comprehensive_score = tradeoff.final_score
        row.score_band = tradeoff.score_band
        row.tradeoff_breakdown = tradeoff.breakdown
        row.pain_point_flags = tradeoff.pain_point_flags
        row.market_behavior_notes = tradeoff.market_behavior_notes
        row.tradeoff_summary = tradeoff.summary
        row.recommendation_role = f"{row.recommendation_role}:{tradeoff.score_band}"
        rows.append(row)

    return sorted(rows, key=lambda item: item.comprehensive_score, reverse=True)


def build_frozen_record(
    *,
    case_id: str,
    profile: UserProfile,
    candidate_rows: list[MajorGroupRow],
    max_choices: int,
) -> dict:
    runtime_policy = RLRuntimePolicy()
    final_rows, optimization_summary = runtime_policy.select_candidates(
        rows=candidate_rows,
        profile=profile,
        total_count=min(max_choices, len(candidate_rows)),
    )
    if not final_rows:
        final_rows = candidate_rows[:max_choices]
        optimization_summary = {
            "policy_source": "fallback",
            "checkpoint_loaded": False,
            "selected_count": len(final_rows),
            "portfolio": {"generated": False, "reason": "fallback_sorted_candidates"},
        }

    plan = build_volunteer_plan(final_rows, profile, max_choices=max_choices)
    return {
        "case_id": case_id,
        "user_rank": profile.rank,
        "preferred_majors": list(profile.preferred_majors),
        "blacklist_majors": list(profile.blacklist_majors),
        "generation_metadata": {
            "method": "fast_historical_probability_runtime_policy",
            "uses_actual_2025": False,
            "candidate_rows": len(candidate_rows),
            "plan_choices": len(plan.choices),
            "optimization_summary": optimization_summary,
        },
        "user_profile": profile.model_dump(mode="json"),
        "candidate_rows": [row.model_dump(mode="json") for row in candidate_rows],
        "plan": plan.model_dump(mode="json"),
    }


def write_jsonl(path: Path, records: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate frozen 2025 volunteer plans.")
    parser.add_argument("--output", default="logs/frozen_plans_2025.jsonl")
    parser.add_argument("--num-cases", type=int, default=24)
    parser.add_argument("--seed", type=int, default=20250520)
    parser.add_argument("--target-count", type=int, default=120)
    parser.add_argument("--max-choices", type=int, default=30)
    parser.add_argument("--min-probability", type=float, default=0.08)
    args = parser.parse_args()

    data_dir = Path(_resolve_runtime_data_dir())
    if "actual_2025" in str(data_dir):
        raise RuntimeError(f"Refusing to generate plans from post-hoc outcome path: {data_dir}")

    print(f"[frozen] prediction data dir: {data_dir}")
    engine = GaokaoQuantEngine(data_dir=str(data_dir))
    enrollment_loader = EnrollmentPlanLoader(data_dir=str(data_dir))
    profiles = generate_profiles(data_dir=data_dir, num_cases=args.num_cases, seed=args.seed)

    records: list[dict] = []
    skipped: list[dict] = []
    for case_id, profile in profiles:
        print(f"[frozen] case={case_id} rank={profile.rank} subject={profile.subject_group}")
        rows = build_candidate_rows(
            profile=profile,
            engine=engine,
            enrollment_loader=enrollment_loader,
            target_count=args.target_count,
            min_probability=args.min_probability,
        )
        if len(rows) < 5:
            skipped.append({"case_id": case_id, "reason": "too_few_candidates", "candidate_rows": len(rows)})
            print(f"[frozen][skip] {case_id}: {len(rows)} candidates")
            continue
        records.append(
            build_frozen_record(
                case_id=case_id,
                profile=profile,
                candidate_rows=rows,
                max_choices=args.max_choices,
            )
        )

    output_path = Path(args.output)
    write_jsonl(output_path, records)

    summary = {
        "output": str(output_path),
        "records": len(records),
        "skipped": skipped,
        "num_cases_requested": args.num_cases,
        "target_count": args.target_count,
        "max_choices": args.max_choices,
        "min_probability": args.min_probability,
        "uses_actual_2025": False,
    }
    summary_path = output_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

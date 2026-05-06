"""2025 prospective backtest runner.

This module loads post-hoc 2025 actual outcomes only for evaluation. It should
not be called by the online recommender before a volunteer plan is frozen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Sequence

import pandas as pd

from models.game_matrix import VolunteerPlan

from evaluation.metrics import aggregate_backtest_results, evaluate_volunteer_plan
from evaluation.schemas import ActualMajorGroupOutcome, PlanBacktestResult


DEFAULT_COLUMN_MAP = {
    "school_code": ["school_code", "院校代码"],
    "school_name": ["school_name", "院校名称", "学校名称"],
    "major_group_code": ["major_group_code", "专业组代码", "专业组"],
    "group_min_rank": ["actual_group_min_rank", "2025_专业组最低位次", "2025_最低位次", "投档最低位次"],
    "major_code": ["major_code", "专业代码", "专业号", "专业序号"],
    "major_name": ["major_name", "专业名称", "录取专业"],
    "major_min_rank": ["actual_major_min_rank", "2025_专业最低位次", "专业最低位次", "录取最低位次"],
}


def _pick_column(df: pd.DataFrame, candidates: Sequence[str]) -> str | None:
    for column in candidates:
        if column in df.columns:
            return column
    return None


def _to_int(value) -> int | None:
    if pd.isna(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def load_actual_outcomes_csv(
    path: str | Path,
    *,
    column_map: Mapping[str, Sequence[str]] | None = None,
    encoding: str = "utf-8-sig",
) -> list[ActualMajorGroupOutcome]:
    """Load actual 2025 group and in-group major cutoffs from CSV."""
    column_map = column_map or DEFAULT_COLUMN_MAP
    df = pd.read_csv(path, encoding=encoding)

    school_code_col = _pick_column(df, column_map["school_code"])
    school_name_col = _pick_column(df, column_map["school_name"])
    group_code_col = _pick_column(df, column_map["major_group_code"])
    group_rank_col = _pick_column(df, column_map["group_min_rank"])
    major_code_col = _pick_column(df, column_map.get("major_code", []))
    major_name_col = _pick_column(df, column_map["major_name"])
    major_rank_col = _pick_column(df, column_map["major_min_rank"])

    required = {
        "school_name": school_name_col,
        "major_group_code": group_code_col,
        "group_min_rank": group_rank_col,
    }
    missing = [name for name, column in required.items() if not column]
    if missing:
        raise ValueError(f"Missing required actual-outcome columns: {missing}")

    grouped: dict[tuple[str, str, str], dict] = {}
    for _, row in df.iterrows():
        group_min_rank = _to_int(row[group_rank_col])
        if group_min_rank is None:
            continue
        school_code = str(row[school_code_col]).strip() if school_code_col else ""
        school_name = str(row[school_name_col]).strip()
        group_code = str(row[group_code_col]).strip()
        key = (school_code, school_name, group_code)
        bucket = grouped.setdefault(
            key,
            {
                "school_code": school_code,
                "school_name": school_name,
                "major_group_code": group_code,
                "actual_group_min_rank": group_min_rank,
                "major_min_ranks": {},
                "major_codes": {},
            },
        )
        bucket["actual_group_min_rank"] = max(bucket["actual_group_min_rank"], group_min_rank)

        if major_name_col and major_rank_col:
            major_rank = _to_int(row[major_rank_col])
            major_name = str(row[major_name_col]).strip()
            if major_name and major_rank is not None:
                bucket["major_min_ranks"][major_name] = major_rank
                if major_code_col:
                    major_code = str(row[major_code_col]).strip()
                    if major_code and major_code.lower() != "nan":
                        bucket["major_codes"][major_name] = major_code

    return [ActualMajorGroupOutcome(**payload) for payload in grouped.values()]


def run_plan_backtest(
    *,
    plan: VolunteerPlan,
    actual_outcomes: Iterable[ActualMajorGroupOutcome],
    user_rank: int,
    preferred_majors: Sequence[str] | None = None,
    blacklist_majors: Sequence[str] | None = None,
    case_id: str = "",
) -> PlanBacktestResult:
    """Evaluate one frozen plan under actual 2025 outcomes."""
    return evaluate_volunteer_plan(
        plan=plan,
        actual_outcomes=actual_outcomes,
        user_rank=user_rank,
        preferred_majors=preferred_majors,
        blacklist_majors=blacklist_majors,
        case_id=case_id,
    )


def summarize_backtests(results: Sequence[PlanBacktestResult]) -> dict:
    """Return a dict summary suitable for JSON export or result tables."""
    return aggregate_backtest_results(results).model_dump()

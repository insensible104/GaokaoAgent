"""Detect and disclose the data years supporting a recommendation run."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field


YEAR_PREFIX = re.compile(r"^(20\d{2})_")


class RecommendationDataVintage(BaseModel):
    target_year: int
    latest_historical_admission_year: int | None = None
    enrollment_plan_year: int | None = None
    rank_table_year: int | None = None
    formal_recommendation_ready: bool = False
    limitations: list[str] = Field(default_factory=list)


def _latest_year(paths: list[Path]) -> int | None:
    years = []
    for path in paths:
        match = YEAR_PREFIX.match(path.name)
        if match:
            years.append(int(match.group(1)))
    return max(years) if years else None


def inspect_recommendation_data_vintage(
    data_dir: str | Path,
    *,
    target_year: int,
) -> RecommendationDataVintage:
    """Inspect file names without loading admissions data into memory."""
    root = Path(data_dir)
    csv_files = list(root.glob("*.csv")) if root.exists() else []
    enrollment_files = [path for path in csv_files if "enrollment" in path.name.lower()]
    rank_table_files = [
        path
        for path in csv_files
        if "yifenyiduan" in path.name.lower() or "一分一段" in path.name
    ]
    historical_files = [
        path
        for path in csv_files
        if path not in enrollment_files
        and path not in rank_table_files
        and "actual_" not in path.name.lower()
    ]

    historical_year = _latest_year(historical_files)
    enrollment_year = _latest_year(enrollment_files)
    rank_table_year = _latest_year(rank_table_files)
    limitations: list[str] = []

    if enrollment_year != target_year:
        limitations.append(
            f"Missing {target_year} enrollment plan; latest available plan is {enrollment_year or 'none'}."
        )
    if rank_table_year != target_year:
        limitations.append(
            f"Missing {target_year} rank table; latest available table is {rank_table_year or 'none'}."
        )
    if historical_year is None or historical_year < target_year - 1:
        limitations.append(
            f"Historical admission outcomes stop at {historical_year or 'none'}; {target_year - 1} outcomes are not available."
        )

    return RecommendationDataVintage(
        target_year=target_year,
        latest_historical_admission_year=historical_year,
        enrollment_plan_year=enrollment_year,
        rank_table_year=rank_table_year,
        formal_recommendation_ready=not limitations,
        limitations=limitations,
    )

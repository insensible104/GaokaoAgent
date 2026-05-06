"""Schemas for 2025 prospective backtesting.

The evaluation layer intentionally separates prediction-time artifacts from
outcome-time labels. A valid 2025 backtest may use 2025 enrollment plans during
recommendation, but only reads these outcome schemas after a plan is frozen.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ActualMajorGroupOutcome(BaseModel):
    """Actual 2025 admission result for one school-major group."""

    school_code: str = ""
    school_name: str
    major_group_code: str
    actual_group_min_rank: int = Field(description="Worst admitted rank for the major group")
    major_min_ranks: Dict[str, int] = Field(
        default_factory=dict,
        description="Actual worst admitted rank by in-group major name",
    )
    major_codes: Dict[str, str] = Field(
        default_factory=dict,
        description="Actual in-group major code by major name",
    )
    metadata: Dict[str, str] = Field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str, str]:
        return (
            str(self.school_code or "").strip(),
            self.school_name.strip(),
            str(self.major_group_code).strip(),
        )


class ChoiceBacktestOutcome(BaseModel):
    """Outcome of one ordered volunteer choice under actual 2025 labels."""

    choice_index: int
    school_code: str = ""
    school_name: str
    major_group_code: str
    group_admitted: bool
    group_rank_margin: Optional[int] = None
    assigned_major_name: Optional[str] = None
    assigned_major_code: Optional[str] = None
    assigned_major_rank_margin: Optional[int] = None
    assigned_major_utility: float = 0.0
    selected_major_hit: bool = False
    preferred_major_hit: bool = False
    blacklist_hit: bool = False
    tail_assignment_hit: bool = False
    is_first_hit: bool = False
    failure_reason: str = ""


class PlanBacktestResult(BaseModel):
    """Backtest result for one generated volunteer plan."""

    case_id: str = ""
    user_rank: int
    success: bool
    first_hit_index: Optional[int] = None
    first_hit_school: Optional[str] = None
    first_hit_major_group: Optional[str] = None
    assigned_major_name: Optional[str] = None
    assigned_major_code: Optional[str] = None
    first_hit_margin: Optional[int] = None
    assigned_major_utility: float = 0.0
    selected_major_hit: bool = False
    preferred_major_hit: bool = False
    blacklist_hit: bool = False
    tail_assignment_hit: bool = False
    wasted_score_risk: bool = False
    sliding: bool = False
    failure_reason: str = ""
    choice_outcomes: List[ChoiceBacktestOutcome] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)


class BacktestAggregateMetrics(BaseModel):
    """Aggregate metrics across many plan-level backtest results."""

    case_count: int
    success_rate: float
    sliding_rate: float
    selected_major_hit_rate: float
    preferred_major_hit_rate: float
    blacklist_hit_rate: float
    tail_assignment_rate: float
    wasted_score_rate: float
    average_first_hit_index: float
    average_first_hit_margin: float
    average_assigned_major_utility: float

"""Structured models for supervisor orchestration decisions."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SupervisorAction(str, Enum):
    """Finite action space for the top-level supervisor policy."""

    PROFILE = "profiling_agent"
    GAME = "game_agent"
    REPORT = "report_agent"
    DEEP_RESEARCH = "deep_research"
    MULTIMODAL = "multimodal_parser"
    CRITIC = "critic_agent"
    END = "END"


class SupervisorObservation(BaseModel):
    """Compact feature summary for one orchestration step."""

    stage: str = Field(description="Decision stage inside the workflow")
    has_user_profile: bool = Field(default=False)
    has_game_matrix: bool = Field(default=False)
    has_report: bool = Field(default=False)
    has_research_report: bool = Field(default=False)
    active_loop: Optional[str] = Field(default=None)
    intent_type: Optional[str] = Field(default=None)
    intent_confidence: float = Field(default=0.0)
    requires_search: bool = Field(default=False)
    requires_vision: bool = Field(default=False)
    retry_count: int = Field(default=0)
    research_loop_count: int = Field(default=0)
    candidate_count: int = Field(default=0)
    safe_count: int = Field(default=0)
    target_count: int = Field(default=0)
    rush_count: int = Field(default=0)
    has_volunteer_plan: bool = Field(default=False)
    expected_admission_prob: float = Field(default=0.0)
    key_prefix_count: int = Field(default=0)
    key_high_tail_count: int = Field(default=0)
    shadowed_choice_count: int = Field(default=0)
    high_crowding_count: int = Field(default=0)
    pain_point_count: int = Field(default=0)
    hidden_opportunity_count: int = Field(default=0)
    bait_group_count: int = Field(default=0)
    city_mismatch_count: int = Field(default=0)
    avg_crowding_risk: float = Field(default=0.0)
    debug_log_count: int = Field(default=0)
    has_deep_research_trigger: bool = Field(default=False)
    reflection_count: int = Field(default=0)
    negative_step_ratio: float = Field(default=0.0)
    issue_count: int = Field(default=0)
    protocol_violation_count: int = Field(default=0)


class SupervisorDecision(BaseModel):
    """One logged routing decision from the supervisor policy."""

    stage: str = Field(description="Decision stage")
    policy_name: str = Field(description="Policy identifier")
    selected_action: str = Field(description="Chosen next action")
    candidate_actions: List[str] = Field(default_factory=list)
    rationale: str = Field(default="")
    observation: SupervisorObservation
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SupervisorEpisodeSummary(BaseModel):
    """Terminal summary for one orchestration trajectory."""

    reward: float = Field(description="Proxy reward for offline orchestration learning")
    reward_components: Dict[str, float] = Field(
        default_factory=dict,
        description="Named reward terms used to build the terminal proxy reward.",
    )
    success: bool = Field(description="Whether the run produced a usable result")
    approved: bool = Field(description="Whether critic approved the result")
    trace_length: int = Field(description="Number of supervisor decisions")
    retry_count: int = Field(description="Total retry count")
    issue_count: int = Field(description="Audit issue count")
    protocol_violation_count: int = Field(default=0, description="Communication protocol violations")

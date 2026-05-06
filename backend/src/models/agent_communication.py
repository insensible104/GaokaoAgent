"""Structured communication primitives for the multi-agent layer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """One public protocol message exchanged between agents."""

    protocol_version: str = Field(default="agent-protocol-v1")
    message_id: str = Field(default_factory=lambda: uuid4().hex)
    thread_id: str = Field(default="default")
    parent_message_id: Optional[str] = Field(default=None)
    sender: str = Field(description="Source agent")
    recipients: List[str] = Field(default_factory=list, description="Explicit recipients or ['broadcast']")
    stage: str = Field(description="Workflow stage where the message was created")
    message_type: str = Field(description="task / proposal / critique / vote / summary")
    priority: str = Field(default="normal", description="low / normal / high / critical")
    status: str = Field(default="open", description="open / acknowledged / resolved / blocked")
    requires_ack: bool = Field(default=False)
    content: str = Field(description="Human-readable summary")
    action_preference: Optional[str] = Field(default=None, description="Preferred next action")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    references: List[str] = Field(default_factory=list, description="Optional evidence references")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentMemoryEntry(BaseModel):
    """One local memory note owned by an agent."""

    agent_name: str = Field(description="Owner agent")
    stage: str = Field(description="Stage where the memory was produced")
    note_type: str = Field(description="observation / reflection / heuristic / failure")
    content: str = Field(description="Short private note")
    importance: float = Field(default=0.5, ge=0.0, le=1.0)


class DeliberationSummary(BaseModel):
    """Aggregated result of a parallel multi-agent deliberation."""

    stage: str = Field(description="Deliberation stage")
    recommended_action: str = Field(description="Aggregated next action recommendation")
    rationale: str = Field(description="Why this action was chosen")
    vote_scores: Dict[str, float] = Field(default_factory=dict)
    participating_agents: List[str] = Field(default_factory=list)
    missing_required_agents: List[str] = Field(default_factory=list)
    protocol_violations: List[str] = Field(default_factory=list)
    message_count: int = Field(default=0)
    dissent_count: int = Field(default=0)
    consensus_strength: float = Field(default=0.0, ge=0.0, le=1.0)
    requires_research: bool = Field(default=False)

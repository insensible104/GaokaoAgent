"""Helpers for explicit inter-agent communication and local memory."""

from __future__ import annotations

from typing import Iterable, List, Optional

from models.agent_communication import AgentMemoryEntry, AgentMessage, DeliberationSummary
from models.state import SupervisorState


AGENT_PROTOCOL_VERSION = "agent-protocol-v1"


def publish_agent_message(
    *,
    sender: str,
    stage: str,
    message_type: str,
    content: str,
    recipients: Optional[List[str]] = None,
    thread_id: Optional[str] = None,
    parent_message_id: Optional[str] = None,
    priority: str = "normal",
    status: str = "open",
    requires_ack: bool = False,
    action_preference: Optional[str] = None,
    confidence: float = 0.5,
    references: Optional[List[str]] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Build a state update for one protocol message."""
    message = AgentMessage(
        protocol_version=AGENT_PROTOCOL_VERSION,
        thread_id=thread_id or f"{stage}:{message_type}",
        parent_message_id=parent_message_id,
        sender=sender,
        recipients=recipients or ["broadcast"],
        stage=stage,
        message_type=message_type,
        priority=priority,
        status=status,
        requires_ack=requires_ack,
        content=content,
        action_preference=action_preference,
        confidence=confidence,
        references=references or [],
        metadata=metadata or {},
    )
    return {"agent_messages": [message]}


def remember(
    *,
    agent_name: str,
    stage: str,
    note_type: str,
    content: str,
    importance: float = 0.5,
) -> dict:
    """Build a state update for one local memory note."""
    memory = AgentMemoryEntry(
        agent_name=agent_name,
        stage=stage,
        note_type=note_type,
        content=content,
        importance=importance,
    )
    return {"agent_memories": [memory]}


def publish_deliberation(summary: DeliberationSummary) -> dict:
    return {"deliberation_summaries": [summary], "recommended_next_action": summary.recommended_action}


def get_messages_for_stage(
    state: SupervisorState,
    *,
    stage: str,
    recipients: Optional[Iterable[str]] = None,
    message_types: Optional[Iterable[str]] = None,
) -> List[AgentMessage]:
    """Return protocol messages visible to the requested recipients."""
    visible_recipients = set(recipients or [])
    allowed_types = set(message_types or [])
    results: List[AgentMessage] = []
    for raw_message in state.get("agent_messages", []):
        message = raw_message if isinstance(raw_message, AgentMessage) else AgentMessage(**raw_message)
        if message.stage != stage:
            continue
        if allowed_types and message.message_type not in allowed_types:
            continue
        if not visible_recipients:
            results.append(message)
            continue
        if "broadcast" in message.recipients or visible_recipients.intersection(message.recipients):
            results.append(message)
    return results


def validate_stage_protocol(
    state: SupervisorState,
    *,
    stage: str,
    recipients: Optional[Iterable[str]] = None,
    required_messages: Optional[dict[str, str]] = None,
) -> List[str]:
    """Return human-readable violations for a stage-level communication contract."""
    messages = get_messages_for_stage(state, stage=stage, recipients=recipients)
    violations: List[str] = []

    for sender, message_type in (required_messages or {}).items():
        found = any(
            message.sender == sender and message.message_type == message_type
            for message in messages
        )
        if not found:
            violations.append(
                f"missing {message_type} from {sender} at stage={stage}"
            )

    blocked = [
        message
        for message in messages
        if message.priority == "critical" and message.status == "blocked"
    ]
    for message in blocked:
        violations.append(
            f"blocked critical message {message.message_id} from {message.sender}"
        )

    return violations


def get_agent_memories(state: SupervisorState, agent_name: str) -> List[AgentMemoryEntry]:
    memories: List[AgentMemoryEntry] = []
    for raw_entry in state.get("agent_memories", []):
        entry = raw_entry if isinstance(raw_entry, AgentMemoryEntry) else AgentMemoryEntry(**raw_entry)
        if entry.agent_name == agent_name:
            memories.append(entry)
    return memories


def latest_deliberation(state: SupervisorState, stage: str) -> Optional[DeliberationSummary]:
    summaries = []
    for raw_summary in state.get("deliberation_summaries", []):
        summary = raw_summary if isinstance(raw_summary, DeliberationSummary) else DeliberationSummary(**raw_summary)
        if summary.stage == stage:
            summaries.append(summary)
    return summaries[-1] if summaries else None

"""Parallel advisor agents and deliberation coordinator for a more agentic workflow."""

from __future__ import annotations

import os
from collections import defaultdict

from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from models.agent_communication import DeliberationSummary
from models.game_matrix import StrategyTag
from models.state import SupervisorState
from utils.llm_factory import get_llm
from utils.agent_bus import (
    get_agent_memories,
    get_messages_for_stage,
    publish_agent_message,
    publish_deliberation,
    remember,
    validate_stage_protocol,
)


POST_GAME_STAGE = "post_game_deliberation"
POST_GAME_REQUIRED_MESSAGES = {
    "game_agent": "proposal",
    "risk_guardian_agent": "vote",
    "opportunity_advocate_agent": "vote",
    "evidence_guardian_agent": "vote",
}
POST_GAME_ADVISORS = {
    "risk_guardian_agent",
    "opportunity_advocate_agent",
    "evidence_guardian_agent",
}


class AdvisorLLMVote(BaseModel):
    """Structured critique returned by an optional LLM advisor pass."""

    action_preference: str = Field(
        default="report_agent",
        description="One of report_agent or deep_research",
    )
    confidence: float = Field(default=0.6, ge=0, le=1)
    critique: str = Field(default="")
    evidence_gaps: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    recommendation_delta: str = Field(default="")


def _llm_advisor_enabled() -> bool:
    return os.getenv("ENABLE_LLM_ADVISORS", "0").lower() in {"1", "true", "yes", "on"}


def _apply_optional_llm_vote(
    *,
    agent_name: str,
    role_description: str,
    rule_action: str,
    rule_confidence: float,
    rule_content: str,
    stats: dict,
    state: SupervisorState,
) -> tuple[str, float, str, dict]:
    """Use an LLM as a second-pass critic over deterministic advisor evidence."""
    metadata = {"llm_advisor_used": False}
    if not _llm_advisor_enabled():
        return rule_action, rule_confidence, rule_content, metadata

    profile = state.get("user_profile")
    profile_payload = profile.model_dump() if hasattr(profile, "model_dump") else str(profile)
    prompt = f"""
You are {agent_name}, a role-specific Gaokao volunteer-plan advisor.

Role:
{role_description}

Deterministic evidence packet:
{stats}

Rule-based preliminary decision:
action={rule_action}
confidence={rule_confidence}
rationale={rule_content}

User behavioral profile:
{profile_payload}

Return a structured critique. Choose action_preference only from:
- report_agent: evidence is sufficient to produce final explanation
- deep_research: the plan needs external evidence, stronger risk audit, or more investigation

Do not invent schools or admission probabilities. Judge whether the evidence packet supports the next action.
"""
    try:
        structured_llm = get_llm(temperature=0).with_structured_output(AdvisorLLMVote)
        vote: AdvisorLLMVote = structured_llm.invoke(prompt)
        if vote.action_preference not in {"report_agent", "deep_research"}:
            raise ValueError(f"invalid advisor action: {vote.action_preference}")
        content = (
            f"{rule_content} LLM critique: {vote.critique} "
            f"evidence_gaps={vote.evidence_gaps}; risk_flags={vote.risk_flags}; "
            f"delta={vote.recommendation_delta}"
        )
        metadata.update(
            {
                "llm_advisor_used": True,
                "llm_advisor_action": vote.action_preference,
                "llm_advisor_confidence": vote.confidence,
                "llm_evidence_gaps": vote.evidence_gaps,
                "llm_risk_flags": vote.risk_flags,
            }
        )
        return vote.action_preference, vote.confidence, content, metadata
    except Exception as exc:
        metadata["llm_advisor_error"] = str(exc)
        return rule_action, rule_confidence, rule_content, metadata


def _game_stats(state: SupervisorState) -> dict:
    game_matrix = state.get("game_matrix")
    if not game_matrix:
        return {
            "candidate_count": 0,
            "safe_count": 0,
            "target_count": 0,
            "rush_count": 0,
            "risk": 0.0,
            "expected_utility": 0.0,
            "key_prefix_count": 0,
            "key_high_tail_count": 0,
            "high_crowding_count": 0,
            "pain_point_count": 0,
            "hidden_opportunity_count": 0,
            "bait_group_count": 0,
            "city_mismatch_count": 0,
            "expected_admission_prob": 0.0,
            "has_volunteer_plan": False,
        }

    rows = game_matrix.major_group_rows or []
    volunteer_plan = getattr(game_matrix, "volunteer_plan", None)
    key_choices = [choice for choice in volunteer_plan.choices if choice.is_key_prefix] if volunteer_plan else []
    key_high_tail_choices = [
        choice
        for choice in key_choices
        if choice.tail_assignment_risk >= 0.55
    ]
    high_crowding_rows = [
        row
        for row in rows
        if (getattr(row, "tradeoff_breakdown", {}) or {}).get("crowding_risk", 0.0) >= 0.62
    ]
    rows_with_pain_points = [
        row
        for row in rows
        if getattr(row, "pain_point_flags", None)
    ]
    hidden_opportunity_rows = [
        row
        for row in rows
        if "high_variance_opportunity" in (getattr(row, "pain_point_flags", []) or [])
    ]
    bait_group_rows = [
        row
        for row in rows
        if (
            "bait_major_group" in (getattr(row, "pain_point_flags", []) or [])
            or "tail_major_regret" in (getattr(row, "pain_point_flags", []) or [])
        )
    ]
    city_mismatch_rows = [
        row
        for row in rows
        if "city_mismatch" in (getattr(row, "pain_point_flags", []) or [])
    ]
    return {
        "candidate_count": len(rows),
        "safe_count": len([row for row in rows if row.strategy_tag == StrategyTag.SAFE]),
        "target_count": len([row for row in rows if row.strategy_tag == StrategyTag.TARGET]),
        "rush_count": len([row for row in rows if row.strategy_tag == StrategyTag.RUSH]),
        "risk": game_matrix.portfolio_risk,
        "expected_utility": game_matrix.expected_utility,
        "key_prefix_count": len(key_choices),
        "key_high_tail_count": len(key_high_tail_choices),
        "high_crowding_count": len(high_crowding_rows),
        "pain_point_count": len(rows_with_pain_points),
        "hidden_opportunity_count": len(hidden_opportunity_rows),
        "bait_group_count": len(bait_group_rows),
        "city_mismatch_count": len(city_mismatch_rows),
        "expected_admission_prob": volunteer_plan.expected_admission_prob if volunteer_plan else 0.0,
        "has_volunteer_plan": volunteer_plan is not None,
    }


def risk_guardian_agent_node(state: SupervisorState) -> dict:
    """Conservative advisor focused on downside risk and missing evidence."""
    stats = _game_stats(state)
    inbound = get_messages_for_stage(
        state,
        stage=POST_GAME_STAGE,
        recipients=["risk_guardian_agent"],
    )
    prior_memories = get_agent_memories(state, "risk_guardian_agent")
    intent = state.get("intent_classification")
    needs_search = bool(intent.requires_search) if intent else False
    proposal = inbound[-1] if inbound else None
    proposal_safe_count = int((proposal.metadata or {}).get("safe_count", stats["safe_count"])) if proposal else stats["safe_count"]
    should_research = (
        stats["candidate_count"] < 15
        or proposal_safe_count == 0
        or stats["risk"] > 0.22
        or stats["key_high_tail_count"] > 0
        or (needs_search and stats["bait_group_count"] > 0)
        or (
            needs_search
            and stats["high_crowding_count"] > 0
            and stats["key_high_tail_count"] > 0
        )
        or any("[TRIGGER_DEEP_RESEARCH]" in log for log in state.get("debug_logs", []))
    )
    action = "deep_research" if should_research else "report_agent"
    confidence = 0.85 if should_research else 0.65
    content = (
        f"RiskGuardian sees candidate_count={stats['candidate_count']}, "
        f"safe_count={proposal_safe_count}, risk={stats['risk']:.3f}, "
        f"key_high_tail_count={stats['key_high_tail_count']}, "
        f"bait_group_count={stats['bait_group_count']}, "
        f"high_crowding_count={stats['high_crowding_count']}, "
        f"memory_count={len(prior_memories)}; "
        f"recommend {action}."
    )
    action, confidence, content, llm_metadata = _apply_optional_llm_vote(
        agent_name="risk_guardian_agent",
        role_description=(
            "Focus on downside risk, first-hit tail assignment, blacklist exposure, "
            "weak safety anchors, and whether deep research is needed before reporting."
        ),
        rule_action=action,
        rule_confidence=confidence,
        rule_content=content,
        stats=stats,
        state=state,
    )
    update = {}
    update.update(
        publish_agent_message(
            sender="risk_guardian_agent",
            stage=POST_GAME_STAGE,
            message_type="vote",
            content=content,
            recipients=["deliberation_coordinator"],
            thread_id=proposal.thread_id if proposal else POST_GAME_STAGE,
            parent_message_id=proposal.message_id if proposal else None,
            priority="high" if should_research else "normal",
            status="resolved",
            action_preference=action,
            confidence=confidence,
            metadata={**stats, **llm_metadata},
        )
    )
    update.update(
        remember(
            agent_name="risk_guardian_agent",
            stage=POST_GAME_STAGE,
            note_type="risk_assessment",
            content=content,
            importance=confidence,
        )
    )
    update["current_agent"] = "risk_guardian_agent"
    update["messages"] = [AIMessage(content="Risk guardian review completed.")]
    return update


def opportunity_advocate_agent_node(state: SupervisorState) -> dict:
    """Opportunity-seeking advisor focused on utility and user upside."""
    stats = _game_stats(state)
    inbound = get_messages_for_stage(
        state,
        stage=POST_GAME_STAGE,
        recipients=["opportunity_advocate_agent"],
    )
    prior_memories = get_agent_memories(state, "opportunity_advocate_agent")
    intent = state.get("intent_classification")
    needs_search = bool(intent.requires_search) if intent else False
    proposal = inbound[-1] if inbound else None
    proposal_rush_count = int((proposal.metadata or {}).get("rush_count", stats["rush_count"])) if proposal else stats["rush_count"]
    should_research = (
        proposal_rush_count == 0 and stats["expected_utility"] < 0.7
    ) or (stats["has_volunteer_plan"] and stats["key_prefix_count"] == 0) or (
        needs_search
        and stats["high_crowding_count"] > 0
        and stats["hidden_opportunity_count"] == 0
    )
    action = "deep_research" if should_research else "report_agent"
    confidence = 0.60 if should_research else 0.82
    content = (
        f"OpportunityAdvocate sees rush_count={proposal_rush_count}, "
        f"expected_utility={stats['expected_utility']:.3f}, "
        f"key_prefix_count={stats['key_prefix_count']}, "
        f"hidden_opportunity_count={stats['hidden_opportunity_count']}, "
        f"city_mismatch_count={stats['city_mismatch_count']}, "
        f"memory_count={len(prior_memories)}; "
        f"recommend {action}."
    )
    action, confidence, content, llm_metadata = _apply_optional_llm_vote(
        agent_name="opportunity_advocate_agent",
        role_description=(
            "Focus on upside, hidden opportunity, over-conservatism, wasted rank, "
            "city/major tradeoff, and whether the plan misses a better frontier."
        ),
        rule_action=action,
        rule_confidence=confidence,
        rule_content=content,
        stats=stats,
        state=state,
    )
    update = {}
    update.update(
        publish_agent_message(
            sender="opportunity_advocate_agent",
            stage=POST_GAME_STAGE,
            message_type="vote",
            content=content,
            recipients=["deliberation_coordinator"],
            thread_id=proposal.thread_id if proposal else POST_GAME_STAGE,
            parent_message_id=proposal.message_id if proposal else None,
            priority="high" if should_research else "normal",
            status="resolved",
            action_preference=action,
            confidence=confidence,
            metadata={**stats, **llm_metadata},
        )
    )
    update.update(
        remember(
            agent_name="opportunity_advocate_agent",
            stage=POST_GAME_STAGE,
            note_type="opportunity_assessment",
            content=content,
            importance=confidence,
        )
    )
    update["current_agent"] = "opportunity_advocate_agent"
    update["messages"] = [AIMessage(content="Opportunity advocate review completed.")]
    return update


def evidence_guardian_agent_node(state: SupervisorState) -> dict:
    """Evidence-focused advisor that checks whether external validation is still needed."""
    intent = state.get("intent_classification")
    stats = _game_stats(state)
    inbound = get_messages_for_stage(
        state,
        stage=POST_GAME_STAGE,
        recipients=["evidence_guardian_agent"],
    )
    prior_memories = get_agent_memories(state, "evidence_guardian_agent")
    proposal = inbound[-1] if inbound else None
    needs_search = bool(intent.requires_search) if intent else False
    search_done = bool(state.get("search_queries") or state.get("web_research_results") or state.get("research_report"))
    proposal_candidate_count = int((proposal.metadata or {}).get("candidate_count", stats["candidate_count"])) if proposal else stats["candidate_count"]
    should_research = needs_search and not search_done
    action = "deep_research" if should_research else "report_agent"
    confidence = 0.90 if should_research else 0.70
    content = (
        f"EvidenceGuardian sees requires_search={needs_search}, search_done={search_done}, "
        f"candidate_count={proposal_candidate_count}, "
        f"key_high_tail_count={stats['key_high_tail_count']}, "
        f"high_crowding_count={stats['high_crowding_count']}, "
        f"bait_group_count={stats['bait_group_count']}, "
        f"memory_count={len(prior_memories)}; "
        f"recommend {action}."
    )
    evidence_stats = {
        "requires_search": needs_search,
        "search_done": search_done,
        "candidate_count": proposal_candidate_count,
        "key_high_tail_count": stats["key_high_tail_count"],
        "high_crowding_count": stats["high_crowding_count"],
        "bait_group_count": stats["bait_group_count"],
        "hidden_opportunity_count": stats["hidden_opportunity_count"],
    }
    action, confidence, content, llm_metadata = _apply_optional_llm_vote(
        agent_name="evidence_guardian_agent",
        role_description=(
            "Focus on missing evidence, market-crowding claims, bait major groups, "
            "deep-research triggers, and whether the report would overclaim."
        ),
        rule_action=action,
        rule_confidence=confidence,
        rule_content=content,
        stats=evidence_stats,
        state=state,
    )
    update = {}
    update.update(
        publish_agent_message(
            sender="evidence_guardian_agent",
            stage=POST_GAME_STAGE,
            message_type="vote",
            content=content,
            recipients=["deliberation_coordinator"],
            thread_id=proposal.thread_id if proposal else POST_GAME_STAGE,
            parent_message_id=proposal.message_id if proposal else None,
            priority="high" if should_research else "normal",
            status="resolved",
            action_preference=action,
            confidence=confidence,
            metadata={**evidence_stats, **llm_metadata},
        )
    )
    update.update(
        remember(
            agent_name="evidence_guardian_agent",
            stage=POST_GAME_STAGE,
            note_type="evidence_assessment",
            content=content,
            importance=confidence,
        )
    )
    update["current_agent"] = "evidence_guardian_agent"
    update["messages"] = [AIMessage(content="Evidence guardian review completed.")]
    return update


def _build_deliberation_quality(
    *,
    messages: list,
    participating_agents: list[str],
    missing_required_agents: list[str],
    protocol_violations: list[str],
    consensus_strength: float,
) -> tuple[float, list[str], dict[str, str]]:
    """Summarize whether the advisor round is strong enough to trust."""
    advisor_actions = {
        message.sender: message.action_preference
        for message in messages
        if message.sender in POST_GAME_ADVISORS and message.action_preference
    }
    flags: list[str] = []
    if protocol_violations:
        flags.append("protocol_violation")
    if missing_required_agents:
        flags.append("missing_required_agent")

    max_candidate_count = max(
        [int((message.metadata or {}).get("candidate_count", 0)) for message in messages]
        or [0]
    )
    max_safe_count = max(
        [int((message.metadata or {}).get("safe_count", 0)) for message in messages]
        or [0]
    )
    max_key_tail_count = max(
        [int((message.metadata or {}).get("key_high_tail_count", 0)) for message in messages]
        or [0]
    )
    max_bait_count = max(
        [int((message.metadata or {}).get("bait_group_count", 0)) for message in messages]
        or [0]
    )
    max_crowding_count = max(
        [int((message.metadata or {}).get("high_crowding_count", 0)) for message in messages]
        or [0]
    )
    requires_unfinished_search = any(
        bool((message.metadata or {}).get("requires_search"))
        and not bool((message.metadata or {}).get("search_done"))
        for message in messages
    )
    llm_errors = [
        str((message.metadata or {}).get("llm_advisor_error"))
        for message in messages
        if (message.metadata or {}).get("llm_advisor_error")
    ]

    if max_candidate_count and max_candidate_count < 15:
        flags.append("thin_candidate_slate")
    if max_candidate_count and max_safe_count == 0:
        flags.append("missing_safe_anchor")
    if max_key_tail_count > 0:
        flags.append("key_tail_assignment_risk")
    if max_bait_count > 0:
        flags.append("bait_major_group_risk")
    if max_crowding_count > 0:
        flags.append("crowding_risk")
    if requires_unfinished_search:
        flags.append("external_evidence_required")
    if llm_errors:
        flags.append("llm_advisor_fallback")

    deduped_flags = list(dict.fromkeys(flags))
    if protocol_violations:
        return 0.0, deduped_flags, advisor_actions

    coverage = len(participating_agents) / max(len(POST_GAME_ADVISORS), 1)
    score = 0.55 + 0.25 * coverage + 0.20 * consensus_strength
    score -= 0.12 * len(deduped_flags)
    return round(min(1.0, max(0.0, score)), 3), deduped_flags, advisor_actions


def deliberation_coordinator_node(state: SupervisorState) -> dict:
    """Aggregate advisor votes into a shared recommendation for the supervisor."""
    votes = defaultdict(float)
    protocol_violations = validate_stage_protocol(
        state,
        stage=POST_GAME_STAGE,
        recipients=["deliberation_coordinator"],
        required_messages=POST_GAME_REQUIRED_MESSAGES,
    )
    messages = get_messages_for_stage(
        state,
        stage=POST_GAME_STAGE,
        recipients=["deliberation_coordinator"],
        message_types=["vote"],
    )
    participating_agents = sorted(
        {
            message.sender
            for message in messages
            if message.sender in POST_GAME_ADVISORS
        }
    )
    missing_required_agents = sorted(POST_GAME_ADVISORS - set(participating_agents))

    for message in messages:
        if message.sender in POST_GAME_ADVISORS and message.action_preference:
            votes[message.action_preference] += message.confidence

    if protocol_violations:
        recommended_action = "deep_research"
        top_score = 0.0
        second_score = 0.0
        dissent_count = 0
        consensus_strength = 0.0
    elif votes:
        ranked_votes = sorted(votes.items(), key=lambda item: item[1], reverse=True)
        recommended_action, top_score = ranked_votes[0]
        second_score = ranked_votes[1][1] if len(ranked_votes) > 1 else 0.0
        dissent_count = len([item for item in ranked_votes if item[1] > 0 and item[0] != recommended_action])
        consensus_strength = min(1.0, max(0.0, top_score - second_score))
    else:
        recommended_action = "report_agent"
        top_score = 0.0
        second_score = 0.0
        dissent_count = 0
        consensus_strength = 0.0

    requires_research = recommended_action == "deep_research"
    if protocol_violations:
        rationale = (
            f"Protocol violations={protocol_violations}; "
            f"fallback to {recommended_action}."
        )
    else:
        rationale = (
            f"Votes={dict(votes)}; recommended {recommended_action} with "
            f"margin {top_score - second_score:.2f}."
        )
    quality_score, quality_flags, advisor_actions = _build_deliberation_quality(
        messages=messages,
        participating_agents=participating_agents,
        missing_required_agents=missing_required_agents,
        protocol_violations=protocol_violations,
        consensus_strength=consensus_strength,
    )
    summary = DeliberationSummary(
        stage=POST_GAME_STAGE,
        recommended_action=recommended_action,
        rationale=rationale,
        vote_scores=dict(votes),
        participating_agents=participating_agents,
        missing_required_agents=missing_required_agents,
        protocol_violations=protocol_violations,
        message_count=len(messages),
        dissent_count=dissent_count,
        consensus_strength=round(consensus_strength, 3),
        requires_research=requires_research,
        quality_score=quality_score,
        quality_flags=quality_flags,
        advisor_actions=advisor_actions,
    )

    update = {}
    update.update(publish_deliberation(summary))
    update.update(
        publish_agent_message(
            sender="deliberation_coordinator",
            stage=POST_GAME_STAGE,
            message_type="summary",
            content=rationale,
            recipients=["broadcast"],
            action_preference=recommended_action,
            confidence=min(1.0, max(top_score, 0.5)),
            thread_id=POST_GAME_STAGE,
            priority="high" if protocol_violations else "normal",
            status="blocked" if protocol_violations else "resolved",
            metadata={
                "dissent_count": dissent_count,
                "consensus_strength": consensus_strength,
                "quality_score": quality_score,
                "quality_flags": quality_flags,
                "advisor_actions": advisor_actions,
                "protocol_violation_count": len(protocol_violations),
                "message_count": len(messages),
            },
        )
    )
    update.update(
        remember(
            agent_name="deliberation_coordinator",
            stage=POST_GAME_STAGE,
            note_type="deliberation",
            content=rationale,
            importance=max(0.6, consensus_strength),
        )
    )
    update["current_agent"] = "deliberation_coordinator"
    update["protocol_violations"] = protocol_violations
    update["debug_logs"] = [
        (
            f"[Deliberation] action={recommended_action}, votes={dict(votes)}, "
            f"dissent={dissent_count}, quality={quality_score:.3f}, "
            f"flags={quality_flags}, violations={protocol_violations}"
        )
    ]
    update["messages"] = [AIMessage(content="Deliberation completed.")]
    return update

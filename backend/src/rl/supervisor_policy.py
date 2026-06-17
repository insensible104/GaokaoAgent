"""Supervisor policy layer for orchestration-focused RL."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from models.audit_result import AuditResult
from models.intent import IntentClassification, IntentType, LoopType
from models.orchestration import (
    SupervisorAction,
    SupervisorDecision,
    SupervisorEpisodeSummary,
    SupervisorObservation,
)
from models.state import SupervisorState
from rl.orchestration_alignment import format_supervisor_prompt
from rl.reward_model_scorer import SupervisorRewardModelScorer
from utils.agent_bus import latest_deliberation
from utils.llm_factory import get_llm


POLICY_NAME = "heuristic_supervisor_v1"
LEARNED_POLICY_PATH = Path(__file__).resolve().parents[2] / "rl_checkpoints" / "supervisor_action_ranker.pkl"
DEFAULT_REWARD_MODEL_PATH = Path(__file__).resolve().parents[2] / "rl_checkpoints" / "supervisor_reward_model.json"


class LLMSupervisorSelection(BaseModel):
    """Structured output for the optional learned LLM supervisor policy."""

    selected_action: str = Field(description="One action from the provided candidate list")
    rationale: str = Field(default="", description="Short reason for the choice")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


def _candidate_count(state: SupervisorState) -> int:
    game_matrix = state.get("game_matrix")
    if not game_matrix:
        return 0
    rows = getattr(game_matrix, "major_group_rows", None) or getattr(game_matrix, "rows", [])
    return len(rows)


def _market_stats(items: List[Any]) -> Dict[str, float]:
    """Aggregate tradeoff-policy signals for routing and trajectory rewards."""
    crowding_values = [
        float((getattr(item, "tradeoff_breakdown", {}) or {}).get("crowding_risk", 0.0))
        for item in items
    ]
    pain_flags = [set(getattr(item, "pain_point_flags", []) or []) for item in items]
    return {
        "high_crowding_count": len([value for value in crowding_values if value >= 0.62]),
        "pain_point_count": len([flags for flags in pain_flags if flags]),
        "hidden_opportunity_count": len(
            [flags for flags in pain_flags if "high_variance_opportunity" in flags]
        ),
        "bait_group_count": len(
            [
                flags
                for flags in pain_flags
                if "bait_major_group" in flags or "tail_major_regret" in flags
            ]
        ),
        "city_mismatch_count": len([flags for flags in pain_flags if "city_mismatch" in flags]),
        "avg_crowding_risk": (
            sum(crowding_values) / len(crowding_values)
            if crowding_values
            else 0.0
        ),
    }


def _negative_step_ratio(state: SupervisorState) -> float:
    rewards = state.get("step_rewards", [])
    if not rewards:
        return 0.0
    negative = len([reward for reward in rewards if getattr(reward, "reward_value", 0.0) < 0])
    return negative / max(len(rewards), 1)


def _protocol_violations(state: SupervisorState) -> List[str]:
    """Collect protocol violations from state and deliberation summaries."""
    violations: List[str] = []
    violations.extend([str(item) for item in state.get("protocol_violations", []) if item])

    for raw_summary in state.get("deliberation_summaries", []):
        if hasattr(raw_summary, "protocol_violations"):
            summary_violations = getattr(raw_summary, "protocol_violations", []) or []
        elif isinstance(raw_summary, dict):
            summary_violations = raw_summary.get("protocol_violations", []) or []
        else:
            summary_violations = []
        violations.extend([str(item) for item in summary_violations if item])

    deduped: List[str] = []
    seen = set()
    for item in violations:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def build_observation(state: SupervisorState, stage: str) -> SupervisorObservation:
    """Extract compact state features for one routing decision."""
    intent: IntentClassification | None = state.get("intent_classification")
    game_matrix = state.get("game_matrix")
    audit: AuditResult | None = state.get("audit_result")
    volunteer_plan = getattr(game_matrix, "volunteer_plan", None) if game_matrix else None
    key_choices = [choice for choice in volunteer_plan.choices if choice.is_key_prefix] if volunteer_plan else []
    matrix_rows = (
        (getattr(game_matrix, "major_group_rows", None) or getattr(game_matrix, "rows", []))
        if game_matrix
        else []
    )
    market_items = key_choices or (getattr(volunteer_plan, "choices", []) if volunteer_plan else matrix_rows)
    market_stats = _market_stats(list(market_items))
    key_high_tail_count = len(
        [
            choice
            for choice in key_choices
            if getattr(choice, "tail_assignment_risk", 0.0) >= 0.55
        ]
    )

    total_rush = getattr(game_matrix, "total_rush", 0) if game_matrix else 0
    total_target = getattr(game_matrix, "total_target", 0) if game_matrix else 0
    total_safe = getattr(game_matrix, "total_safe", 0) if game_matrix else 0

    return SupervisorObservation(
        stage=stage,
        has_user_profile=state.get("user_profile") is not None,
        has_game_matrix=game_matrix is not None,
        has_report=state.get("report_draft") is not None,
        has_research_report=bool(state.get("research_report")),
        active_loop=state.get("active_loop").value if state.get("active_loop") else None,
        intent_type=intent.primary_intent.value if intent else None,
        intent_confidence=float(intent.confidence) if intent else 0.0,
        requires_search=bool(intent.requires_search) if intent else False,
        requires_vision=bool(intent.requires_vision) if intent else False,
        retry_count=int(state.get("retry_count", 0)),
        research_loop_count=int(state.get("research_loop_count", 0)),
        candidate_count=_candidate_count(state),
        safe_count=total_safe,
        target_count=total_target,
        rush_count=total_rush,
        has_volunteer_plan=volunteer_plan is not None,
        expected_admission_prob=(
            float(getattr(volunteer_plan, "expected_admission_prob", 0.0))
            if volunteer_plan
            else 0.0
        ),
        key_prefix_count=len(key_choices),
        key_high_tail_count=key_high_tail_count,
        shadowed_choice_count=(
            int(getattr(volunteer_plan, "shadowed_choice_count", 0))
            if volunteer_plan
            else 0
        ),
        high_crowding_count=int(market_stats["high_crowding_count"]),
        pain_point_count=int(market_stats["pain_point_count"]),
        hidden_opportunity_count=int(market_stats["hidden_opportunity_count"]),
        bait_group_count=int(market_stats["bait_group_count"]),
        city_mismatch_count=int(market_stats["city_mismatch_count"]),
        avg_crowding_risk=round(float(market_stats["avg_crowding_risk"]), 3),
        debug_log_count=len(state.get("debug_logs", [])),
        has_deep_research_trigger=any(
            "[TRIGGER_DEEP_RESEARCH]" in log for log in state.get("debug_logs", [])
        ),
        reflection_count=len(state.get("reflection_history", [])),
        negative_step_ratio=round(_negative_step_ratio(state), 3),
        issue_count=len(audit.issues) if audit else 0,
        protocol_violation_count=len(_protocol_violations(state)),
    )


class HeuristicSupervisorPolicy:
    """A replaceable policy layer for the current LangGraph supervisor."""

    _cached_ranker = None
    _ranker_loaded = False
    _cached_llm_policy = None
    _llm_policy_loaded = False
    _cached_reward_scorer = None
    _reward_scorer_loaded = False

    def __init__(self) -> None:
        self.use_learned_policy = os.getenv("ENABLE_LEARNED_SUPERVISOR_POLICY", "0") == "1"
        self.use_llm_policy = os.getenv("ENABLE_LLM_SUPERVISOR_POLICY", "0") == "1"
        self.use_reward_model_policy = os.getenv("ENABLE_REWARD_MODEL_SUPERVISOR", "0") == "1"
        self.reward_model_path = Path(
            os.getenv("SUPERVISOR_REWARD_MODEL_PATH", str(DEFAULT_REWARD_MODEL_PATH))
        )

    def _get_ranker(self):
        if not self.use_learned_policy:
            return None
        if self.__class__._ranker_loaded:
            return self.__class__._cached_ranker
        self.__class__._ranker_loaded = True
        if not LEARNED_POLICY_PATH.exists():
            return None
        try:
            from rl.orchestration_alignment import SupervisorActionRanker

            self.__class__._cached_ranker = SupervisorActionRanker.load(LEARNED_POLICY_PATH)
        except Exception as exc:
            print(f"[WARN] learned supervisor policy load failed: {exc}")
            self.__class__._cached_ranker = None
        return self.__class__._cached_ranker

    def _get_llm_policy(self):
        if not self.use_llm_policy:
            return None
        if self.__class__._llm_policy_loaded:
            return self.__class__._cached_llm_policy
        self.__class__._llm_policy_loaded = True
        try:
            temperature = float(os.getenv("SUPERVISOR_POLICY_TEMPERATURE", "0.0"))
            llm = get_llm(temperature=temperature)
            self.__class__._cached_llm_policy = llm.with_structured_output(LLMSupervisorSelection)
        except Exception as exc:
            print(f"[WARN] learned LLM supervisor policy load failed: {exc}")
            self.__class__._cached_llm_policy = None
        return self.__class__._cached_llm_policy

    def _get_reward_scorer(self):
        if not self.use_reward_model_policy:
            return None
        if self.__class__._reward_scorer_loaded:
            return self.__class__._cached_reward_scorer
        self.__class__._reward_scorer_loaded = True
        if not self.reward_model_path.exists():
            return None
        try:
            self.__class__._cached_reward_scorer = SupervisorRewardModelScorer.load(
                self.reward_model_path
            )
        except Exception as exc:
            print(f"[WARN] supervisor reward scorer load failed: {exc}")
            self.__class__._cached_reward_scorer = None
        return self.__class__._cached_reward_scorer

    def _extract_user_message(self, state: SupervisorState) -> str:
        raw_messages = state.get("messages", [])
        if not raw_messages:
            return ""
        last_message = raw_messages[-1]
        return last_message.content if hasattr(last_message, "content") else str(last_message)

    def _apply_llm_policy(
        self,
        *,
        state: SupervisorState,
        stage: str,
        observation: SupervisorObservation,
        candidates: List[str],
        selected_action: str,
        rationale: str,
        metadata: Dict[str, Any],
    ) -> tuple[str, str, Dict[str, Any]]:
        llm_policy = self._get_llm_policy()
        if not llm_policy or len(candidates) <= 1:
            return selected_action, rationale, metadata

        deliberation = latest_deliberation(state, "post_game_deliberation")
        user_message = self._extract_user_message(state)
        prompt = (
            format_supervisor_prompt(
                message=user_message,
                stage=stage,
                observation=observation.model_dump(),
                candidate_actions=candidates,
            )
            + "\n"
            + f"Heuristic choice: {selected_action}\n"
            + f"Current metadata: {json.dumps(metadata, ensure_ascii=False, sort_keys=True)}\n"
            + f"Deliberation summary: {json.dumps(deliberation.model_dump(), ensure_ascii=False, sort_keys=True) if deliberation else 'null'}\n"
            + "Prefer safe and well-justified orchestration decisions. "
            + "Only override the heuristic if the evidence is materially stronger."
        )

        try:
            choice: LLMSupervisorSelection = llm_policy.invoke(prompt)
            llm_action = choice.selected_action
            if llm_action not in candidates:
                metadata["llm_policy_error"] = f"invalid action: {llm_action}"
                return selected_action, rationale, metadata

            updated_metadata = dict(metadata)
            updated_metadata.update(
                {
                    "llm_policy_used": True,
                    "llm_policy_confidence": choice.confidence,
                    "llm_policy_action": llm_action,
                }
            )

            if llm_action != selected_action and choice.confidence >= 0.55:
                updated_rationale = (
                    f"{rationale} Learned LLM supervisor overrode the prior choice "
                    f"from {selected_action} to {llm_action}. {choice.rationale}"
                )
                return llm_action, updated_rationale, updated_metadata

            updated_metadata["llm_policy_followed_prior"] = True
            if choice.rationale:
                rationale = f"{rationale} LLM supervisor agreed: {choice.rationale}"
            return selected_action, rationale, updated_metadata
        except Exception as exc:
            metadata["llm_policy_error"] = str(exc)
            return selected_action, rationale, metadata

    def _apply_reward_model_policy(
        self,
        *,
        state: SupervisorState,
        stage: str,
        observation: SupervisorObservation,
        candidates: List[str],
        selected_action: str,
        rationale: str,
        metadata: Dict[str, Any],
    ) -> tuple[str, str, Dict[str, Any]]:
        reward_scorer = self._get_reward_scorer()
        if not reward_scorer or len(candidates) <= 1:
            return selected_action, rationale, metadata

        try:
            reward_scores = reward_scorer.score_actions(
                message=self._extract_user_message(state),
                stage=stage,
                observation=observation.model_dump(),
                candidate_actions=candidates,
            )
            if not reward_scores:
                return selected_action, rationale, metadata

            best_action = max(reward_scores, key=reward_scores.get)
            selected_score = reward_scores.get(selected_action, 0.0)
            best_score = reward_scores.get(best_action, 0.0)

            updated_metadata = dict(metadata)
            updated_metadata.update(
                {
                    "reward_model_used": True,
                    "reward_model_backend": reward_scorer.backend,
                    "reward_model_scores": reward_scores,
                    "reward_model_prior_action": selected_action,
                }
            )

            if best_action != selected_action and best_score - selected_score >= 0.08:
                updated_rationale = (
                    f"{rationale} Reward-model reranker preferred {best_action} over "
                    f"{selected_action} at stage {stage}."
                )
                return best_action, updated_rationale, updated_metadata

            updated_metadata["reward_model_followed_prior"] = True
            return selected_action, rationale, updated_metadata
        except Exception as exc:
            metadata["reward_model_error"] = str(exc)
            return selected_action, rationale, metadata

    def decide_after_router(self, state: SupervisorState) -> SupervisorDecision:
        active_loop = state.get("active_loop")
        if active_loop == LoopType.SLOW:
            action = SupervisorAction.DEEP_RESEARCH
            rationale = "Intent classification requires web research."
        elif active_loop == LoopType.MULTIMODAL:
            action = SupervisorAction.MULTIMODAL
            rationale = "Intent classification requires multimodal parsing."
        else:
            action = SupervisorAction.PROFILE
            rationale = "Default to profiling before downstream recommendation."

        return self._decision(
            state=state,
            stage="after_router",
            action=action,
            candidates=[
                SupervisorAction.PROFILE.value,
                SupervisorAction.DEEP_RESEARCH.value,
                SupervisorAction.MULTIMODAL.value,
            ],
            rationale=rationale,
        )

    def decide_after_profiling(self, state: SupervisorState) -> SupervisorDecision:
        intent: IntentClassification | None = state.get("intent_classification")
        loop_history = state.get("loop_history", [])
        profile = state.get("user_profile")

        if profile and not getattr(profile, "recommendation_ready", True):
            missing_fields = list(getattr(profile, "missing_critical_fields", []) or [])
            return self._decision(
                state=state,
                stage="after_profiling",
                action=SupervisorAction.END,
                candidates=[
                    SupervisorAction.GAME.value,
                    SupervisorAction.DEEP_RESEARCH.value,
                    SupervisorAction.END.value,
                ],
                rationale="Critical student inputs are missing; do not generate a formal recommendation.",
                metadata={"missing_critical_fields": missing_fields},
            )

        if (
            intent
            and intent.primary_intent == IntentType.MIXED
            and intent.requires_search
            and "slow" not in loop_history
        ):
            return self._decision(
                state=state,
                stage="after_profiling",
                action=SupervisorAction.DEEP_RESEARCH,
                candidates=[
                    SupervisorAction.GAME.value,
                    SupervisorAction.DEEP_RESEARCH.value,
                ],
                rationale="Mixed intent still needs external research before recommendation.",
            )

        return self._decision(
            state=state,
            stage="after_profiling",
            action=SupervisorAction.GAME,
            candidates=[
                SupervisorAction.GAME.value,
                SupervisorAction.DEEP_RESEARCH.value,
            ],
            rationale="Profile is available; continue to recommendation.",
        )

    def decide_after_game(self, state: SupervisorState) -> SupervisorDecision:
        intent: IntentClassification | None = state.get("intent_classification")
        loop_history = state.get("loop_history", [])
        game_matrix = state.get("game_matrix")
        deliberation = latest_deliberation(state, "post_game_deliberation")
        volunteer_plan = getattr(game_matrix, "volunteer_plan", None) if game_matrix else None
        if volunteer_plan and "slow" not in loop_history:
            key_choices = [choice for choice in volunteer_plan.choices if choice.is_key_prefix]
            key_high_tail_count = len(
                [
                    choice
                    for choice in key_choices
                    if getattr(choice, "tail_assignment_risk", 0.0) >= 0.55
                ]
            )
            key_market_stats = _market_stats(key_choices)
            if not key_choices:
                return self._decision(
                    state=state,
                    stage="after_game",
                    action=SupervisorAction.DEEP_RESEARCH,
                    candidates=[
                        SupervisorAction.REPORT.value,
                        SupervisorAction.DEEP_RESEARCH.value,
                    ],
                    rationale=(
                        "Volunteer plan has no key prefix; first-hit outcome is not auditable yet."
                    ),
                    metadata={"first_hit_reason": "missing_key_prefix"},
                )
            if key_high_tail_count > 0:
                return self._decision(
                    state=state,
                    stage="after_game",
                    action=SupervisorAction.DEEP_RESEARCH,
                    candidates=[
                        SupervisorAction.REPORT.value,
                        SupervisorAction.DEEP_RESEARCH.value,
                    ],
                    rationale=(
                        "Key first-hit choices have high tail-assignment risk; "
                        "request evidence before reporting."
                    ),
                    metadata={
                        "first_hit_reason": "key_prefix_high_tail_risk",
                        "key_high_tail_count": key_high_tail_count,
                    },
                )
            if (
                key_market_stats["bait_group_count"] > 0
                or key_market_stats["high_crowding_count"] > 0
            ) and intent and intent.requires_search and not state.get("research_report"):
                return self._decision(
                    state=state,
                    stage="after_game",
                    action=SupervisorAction.DEEP_RESEARCH,
                    candidates=[
                        SupervisorAction.REPORT.value,
                        SupervisorAction.DEEP_RESEARCH.value,
                    ],
                    rationale=(
                        "Key first-hit choices carry parallel-volunteer market-game or "
                        "mixed-major bait signals; verify evidence before reporting."
                    ),
                    metadata={
                        "first_hit_reason": "market_game_requires_evidence",
                        "high_crowding_count": int(key_market_stats["high_crowding_count"]),
                        "bait_group_count": int(key_market_stats["bait_group_count"]),
                    },
                )
            if getattr(volunteer_plan, "expected_admission_prob", 1.0) < 0.90:
                return self._decision(
                    state=state,
                    stage="after_game",
                    action=SupervisorAction.DEEP_RESEARCH,
                    candidates=[
                        SupervisorAction.REPORT.value,
                        SupervisorAction.DEEP_RESEARCH.value,
                    ],
                    rationale=(
                        "Volunteer plan cumulative first-hit admission probability is below "
                        "the safety threshold."
                    ),
                    metadata={
                        "first_hit_reason": "low_expected_admission_prob",
                        "expected_admission_prob": volunteer_plan.expected_admission_prob,
                    },
                )

        if deliberation and deliberation.recommended_action in {
            SupervisorAction.REPORT.value,
            SupervisorAction.DEEP_RESEARCH.value,
        }:
            return self._decision(
                state=state,
                stage="after_game",
                action=SupervisorAction(deliberation.recommended_action),
                candidates=[
                    SupervisorAction.REPORT.value,
                    SupervisorAction.DEEP_RESEARCH.value,
                ],
                rationale=(
                    "Parallel advisor deliberation completed. "
                    f"Consensus={deliberation.consensus_strength:.2f}, "
                    f"dissent={deliberation.dissent_count}. "
                    f"{deliberation.rationale}"
                ),
                metadata={
                    "deliberation_votes": deliberation.vote_scores,
                    "consensus_strength": deliberation.consensus_strength,
                    "dissent_count": deliberation.dissent_count,
                },
            )

        if intent and intent.requires_search and "slow" not in loop_history:
            return self._decision(
                state=state,
                stage="after_game",
                action=SupervisorAction.DEEP_RESEARCH,
                candidates=[
                    SupervisorAction.REPORT.value,
                    SupervisorAction.DEEP_RESEARCH.value,
                ],
                rationale="Task requires retrieval-backed verification before reporting.",
            )

        if any("[TRIGGER_DEEP_RESEARCH]" in log for log in state.get("debug_logs", [])) and "slow" not in loop_history:
            return self._decision(
                state=state,
                stage="after_game",
                action=SupervisorAction.DEEP_RESEARCH,
                candidates=[
                    SupervisorAction.REPORT.value,
                    SupervisorAction.DEEP_RESEARCH.value,
                ],
                rationale="Game agent flagged insufficient confidence and requested deeper research.",
            )

        if game_matrix and len(game_matrix.major_group_rows) < 15 and "slow" not in loop_history:
            return self._decision(
                state=state,
                stage="after_game",
                action=SupervisorAction.DEEP_RESEARCH,
                candidates=[
                    SupervisorAction.REPORT.value,
                    SupervisorAction.DEEP_RESEARCH.value,
                ],
                rationale="Candidate pool is too small; try deep research before final report.",
            )

        return self._decision(
            state=state,
            stage="after_game",
            action=SupervisorAction.REPORT,
            candidates=[
                SupervisorAction.REPORT.value,
                SupervisorAction.DEEP_RESEARCH.value,
            ],
            rationale="Recommendation result is sufficient for report generation.",
        )

    def decide_after_report(self, state: SupervisorState) -> SupervisorDecision:
        return self._decision(
            state=state,
            stage="after_report",
            action=SupervisorAction.CRITIC,
            candidates=[SupervisorAction.CRITIC.value],
            rationale="All reports should pass critic/audit before completion.",
        )

    def decide_after_critic(self, state: SupervisorState) -> SupervisorDecision:
        audit: AuditResult | None = state.get("audit_result")
        retry_count = state.get("retry_count", 0)
        loop_history = state.get("loop_history", [])
        max_retry = 3

        if retry_count >= max_retry and audit and not audit.is_approved and "slow" not in loop_history:
            if any("保底" in issue or "滑档" in issue for issue in audit.issues):
                return self._decision(
                    state=state,
                    stage="after_critic",
                    action=SupervisorAction.DEEP_RESEARCH,
                    candidates=[
                        SupervisorAction.GAME.value,
                        SupervisorAction.REPORT.value,
                        SupervisorAction.PROFILE.value,
                        SupervisorAction.DEEP_RESEARCH.value,
                        SupervisorAction.END.value,
                    ],
                    rationale="Repeated failures indicate a root-cause search is more useful than another fast-loop retry.",
                )

        if retry_count >= max_retry:
            return self._decision(
                state=state,
                stage="after_critic",
                action=SupervisorAction.END,
                candidates=[
                    SupervisorAction.GAME.value,
                    SupervisorAction.REPORT.value,
                    SupervisorAction.PROFILE.value,
                    SupervisorAction.DEEP_RESEARCH.value,
                    SupervisorAction.END.value,
                ],
                rationale="Maximum retry budget reached; terminate to avoid infinite loops.",
            )

        if not audit or audit.is_approved:
            return self._decision(
                state=state,
                stage="after_critic",
                action=SupervisorAction.END,
                candidates=[
                    SupervisorAction.GAME.value,
                    SupervisorAction.REPORT.value,
                    SupervisorAction.PROFILE.value,
                    SupervisorAction.DEEP_RESEARCH.value,
                    SupervisorAction.END.value,
                ],
                rationale="Audit approved the result or no further fix is required.",
            )

        reroute_to = audit.reroute_to or SupervisorAction.END.value
        if reroute_to not in {
            SupervisorAction.GAME.value,
            SupervisorAction.REPORT.value,
            SupervisorAction.PROFILE.value,
            SupervisorAction.DEEP_RESEARCH.value,
        }:
            reroute_to = SupervisorAction.END.value

        return self._decision(
            state=state,
            stage="after_critic",
            action=SupervisorAction(reroute_to) if reroute_to != SupervisorAction.END.value else SupervisorAction.END,
            candidates=[
                SupervisorAction.GAME.value,
                SupervisorAction.REPORT.value,
                SupervisorAction.PROFILE.value,
                SupervisorAction.DEEP_RESEARCH.value,
                SupervisorAction.END.value,
            ],
            rationale=f"Critic requested reroute to {reroute_to}.",
            metadata={"audit_issues": audit.issues[:5]},
        )

    def _decision(
        self,
        state: SupervisorState,
        stage: str,
        action: SupervisorAction,
        candidates: List[str],
        rationale: str,
        metadata: Dict[str, Any] | None = None,
    ) -> SupervisorDecision:
        observation = build_observation(state, stage)
        decision_metadata = dict(metadata or {})
        selected_action = action.value
        ranker = self._get_ranker()

        if ranker and len(candidates) > 1:
            try:
                action_scores = ranker.score_actions(
                    stage=stage,
                    observation=observation.model_dump(),
                    candidate_actions=candidates,
                )
                if action_scores:
                    best_action = max(action_scores, key=action_scores.get)
                    default_score = action_scores.get(selected_action, 0.0)
                    best_score = action_scores.get(best_action, 0.0)
                    if best_score - default_score >= 0.05:
                        selected_action = best_action
                        rationale = (
                            f"{rationale} Learned action ranker overrode the heuristic choice "
                            f"from {action.value} to {best_action}."
                        )
                    decision_metadata.update(
                        {
                            "learned_policy_used": True,
                            "learned_action_scores": action_scores,
                            "heuristic_action": action.value,
                        }
                    )
            except Exception as exc:
                decision_metadata["learned_policy_error"] = str(exc)

        selected_action, rationale, decision_metadata = self._apply_llm_policy(
            state=state,
            stage=stage,
            observation=observation,
            candidates=candidates,
            selected_action=selected_action,
            rationale=rationale,
            metadata=decision_metadata,
        )
        selected_action, rationale, decision_metadata = self._apply_reward_model_policy(
            state=state,
            stage=stage,
            observation=observation,
            candidates=candidates,
            selected_action=selected_action,
            rationale=rationale,
            metadata=decision_metadata,
        )

        return SupervisorDecision(
            stage=stage,
            policy_name=POLICY_NAME,
            selected_action=selected_action,
            candidate_actions=candidates,
            rationale=rationale,
            observation=observation,
            metadata=decision_metadata,
        )


def compute_episode_summary(state: SupervisorState) -> SupervisorEpisodeSummary:
    """Compute a proxy reward for offline orchestration learning."""
    audit: AuditResult | None = state.get("audit_result")
    approved = bool(audit and audit.is_approved)
    has_result = bool(state.get("report_draft") or state.get("research_report"))
    trace = state.get("orchestration_trace", [])
    retry_count = int(state.get("retry_count", 0))
    issue_count = len(audit.issues) if audit else 0
    negative_ratio = _negative_step_ratio(state)
    protocol_violation_count = len(_protocol_violations(state))
    game_matrix = state.get("game_matrix")
    volunteer_plan = getattr(game_matrix, "volunteer_plan", None) if game_matrix else None

    components: Dict[str, float] = {
        "approval": 0.45 if approved else -0.25,
        "has_result": 0.20 if has_result else -0.35,
        "retry_penalty": -min(retry_count, 3) * 0.12,
        "issue_penalty": -min(issue_count, 4) * 0.08,
        "trace_length_penalty": -min(max(len(trace) - 4, 0), 4) * 0.04,
        "negative_step_penalty": -negative_ratio * 0.25,
        "protocol_violation_penalty": -min(protocol_violation_count, 5) * 0.10,
    }

    if volunteer_plan:
        expected_admission_prob = float(getattr(volunteer_plan, "expected_admission_prob", 0.0))
        expected_first_hit_utility = float(getattr(volunteer_plan, "expected_first_hit_utility", 0.0))
        expected_tail_risk = float(getattr(volunteer_plan, "expected_tail_risk", 0.0))
        expected_plan_value = float(getattr(volunteer_plan, "expected_plan_value", 0.0))
        key_high_tail_count = len(
            [
                choice
                for choice in getattr(volunteer_plan, "choices", [])
                if getattr(choice, "is_key_prefix", False)
                and getattr(choice, "tail_assignment_risk", 0.0) >= 0.55
            ]
        )
        market_stats = _market_stats(list(getattr(volunteer_plan, "choices", [])))

        components.update(
            {
                "expected_admission": (expected_admission_prob - 0.90) * 0.80,
                "first_hit_utility": expected_first_hit_utility * 0.25,
                "tail_risk_penalty": -expected_tail_risk * 0.35,
                "plan_value": max(-1.0, min(1.0, expected_plan_value)) * 0.15,
                "key_high_tail_penalty": -min(key_high_tail_count, 5) * 0.08,
                "market_crowding_penalty": -min(market_stats["high_crowding_count"], 5) * 0.04,
                "bait_group_penalty": -min(market_stats["bait_group_count"], 5) * 0.05,
                "hidden_opportunity_bonus": min(market_stats["hidden_opportunity_count"], 5) * 0.025,
            }
        )

    reward = sum(components.values())
    reward = max(-1.0, min(1.0, reward))

    return SupervisorEpisodeSummary(
        reward=round(reward, 4),
        reward_components={key: round(value, 4) for key, value in components.items()},
        success=has_result,
        approved=approved,
        trace_length=len(trace),
        retry_count=retry_count,
        issue_count=issue_count,
        protocol_violation_count=protocol_violation_count,
    )


def append_trace_record(state: SupervisorState, decision: SupervisorDecision) -> Dict[str, Any]:
    """Build state updates for one supervisor decision."""
    return {
        "next_action": decision.selected_action,
        "orchestration_trace": [decision.model_dump()],
        "debug_logs": [
            f"[SupervisorPolicy:{decision.stage}] -> {decision.selected_action} | {decision.rationale}"
        ],
    }


def persist_trace(
    *,
    session_id: str,
    state: SupervisorState,
    output_path: str | None = None,
) -> Path:
    """Persist one trajectory as JSONL for later imitation / preference learning."""
    summary = compute_episode_summary(state)
    payload = {
        "session_id": session_id,
        "intent_type": (
            state["intent_classification"].primary_intent.value
            if state.get("intent_classification")
            else None
        ),
        "loop_type": state["active_loop"].value if state.get("active_loop") else None,
        "trace": state.get("orchestration_trace", []),
        "deliberation_summaries": [
            summary.model_dump() if hasattr(summary, "model_dump") else summary
            for summary in state.get("deliberation_summaries", [])
        ],
        "summary": summary.model_dump(),
    }

    target = Path(output_path) if output_path else Path(__file__).resolve().parents[2] / "logs" / "orchestration_traces.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return target

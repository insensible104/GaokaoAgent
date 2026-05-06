"""Data pipeline utilities for orchestration-focused RL."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from graph.dual_loop_supervisor import supervisor_graph
from models.state import SupervisorState
from rl.supervisor_policy import compute_episode_summary


class SyntheticCase(BaseModel):
    """One synthetic or normalized user request for orchestration training."""

    case_id: str
    source: str = "synthetic"
    category: str
    difficulty: str
    message: str
    score: Optional[int] = None
    rank: Optional[int] = None
    subject_group: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _rank_to_score(rank: int, subject_group: str) -> int:
    """A rough score prior used only for synthetic case generation."""
    if rank <= 2000:
        base = 665
    elif rank <= 5000:
        base = 645
    elif rank <= 10000:
        base = 625
    elif rank <= 20000:
        base = 605
    elif rank <= 40000:
        base = 580
    elif rank <= 70000:
        base = 550
    else:
        base = 520
    return base if subject_group == "物理" else max(480, base - 15)


def _load_seed_cases(seed_cases_path: Path) -> List[SyntheticCase]:
    if not seed_cases_path.exists():
        return []

    payload = json.loads(seed_cases_path.read_text(encoding="utf-8"))
    cases = []
    for raw_case in payload.get("test_cases", []):
        question = raw_case.get("question", "")
        normalized = SyntheticCase(
            case_id=raw_case.get("id", f"seed-{len(cases)+1:04d}"),
            source="seed_tests",
            category=raw_case.get("category", "unknown"),
            difficulty=raw_case.get("difficulty", "medium"),
            message=question,
            metadata={
                "expected_intent": raw_case.get("expected_intent"),
                "expected_loops": raw_case.get("expected_loops", []),
                "expected_tools": raw_case.get("expected_tools", []),
            },
        )
        cases.append(normalized)
    return cases


def _render_case_message(
    *,
    category: str,
    rank: int,
    score: int,
    subject_group: str,
    major: str,
    city: str,
    risk_phrase: str,
    school_pref: str,
    extra_constraint: str,
    research_focus: str,
    multimodal_focus: str,
) -> str:
    if category == "quant":
        return (
            f"我{score}分，位次{rank}，{subject_group}类，想学{major}，"
            f"{risk_phrase}，{school_pref}，请推荐能报的学校。"
        )
    if category == "quant_research":
        return (
            f"我{score}分，位次{rank}，{subject_group}类，想学{major}，希望在{city}，"
            f"{risk_phrase}，{research_focus}，请给我可报学校和分析。"
        )
    if category == "quant_multimodal":
        return (
            f"我{score}分，位次{rank}，{subject_group}类，想学{major}，"
            f"{multimodal_focus}，还要考虑{extra_constraint}，请帮我判断能报哪些学校。"
        )
    if category == "research":
        return (
            f"我主要考虑{major}方向，{school_pref}，想了解{research_focus}，"
            f"尤其关注{city}相关院校。"
        )
    if category == "research_multimodal":
        return (
            f"我想报{major}，但需要确认{multimodal_focus}，同时也想了解{research_focus}，"
            f"{school_pref}。"
        )
    return (
        f"我{score}分，位次{rank}，{subject_group}类，想学{major}，希望在{city}，"
        f"{risk_phrase}，{research_focus}，并确认{multimodal_focus}，还要满足{extra_constraint}。"
    )


def generate_synthetic_cases(
    *,
    num_cases: int = 300,
    seed: int = 42,
    include_seed_cases: bool = True,
    seed_cases_path: str | Path = Path("backend/tests/test_cases.json"),
) -> List[SyntheticCase]:
    """Generate a curriculum of synthetic user requests."""
    rng = random.Random(seed)

    categories = [
        ("quant", 0.18),
        ("quant_research", 0.32),
        ("quant_multimodal", 0.16),
        ("research", 0.10),
        ("research_multimodal", 0.10),
        ("triple_loop", 0.14),
    ]
    difficulties = [("medium", 0.45), ("hard", 0.35), ("very_hard", 0.20)]

    majors = [
        "计算机科学与技术",
        "人工智能",
        "软件工程",
        "电子信息工程",
        "自动化",
        "金融学",
        "临床医学",
        "法学",
        "电气工程及其自动化",
        "数据科学与大数据技术",
    ]
    cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "武汉", "成都", "西安"]
    school_preferences = [
        "学校层次优先",
        "专业匹配优先",
        "希望学校和专业尽量平衡",
    ]
    risk_phrases = [
        "希望稳一点",
        "可以适当冲一冲",
        "不希望滑档",
        "可以接受有一点风险",
    ]
    extra_constraints = [
        "不接受调剂",
        "希望将来保研机会多",
        "最好省内读书",
        "希望就业去向更偏互联网",
        "家庭更希望留在东部城市",
    ]
    research_focuses = [
        "保研率和就业质量",
        "学科评估和实验室实力",
        "近三年的就业去向和薪资水平",
        "转专业政策和培养方案",
        "城市资源、校友网络和实习机会",
    ]
    multimodal_focuses = [
        "招生章程里的体检限制",
        "PDF 招生简章里的单科要求",
        "色弱是否受限",
        "体检表和招生章程是否冲突",
        "专业组备注中的选考限制",
    ]
    subject_groups = ["物理", "历史"]

    seed_cases: List[SyntheticCase] = []
    if include_seed_cases:
        seed_cases = _load_seed_cases(Path(seed_cases_path))

    synthetic_target = max(0, num_cases - len(seed_cases))
    synthetic_cases: List[SyntheticCase] = []

    for idx in range(synthetic_target):
        category = rng.choices([item[0] for item in categories], weights=[item[1] for item in categories], k=1)[0]
        difficulty = rng.choices([item[0] for item in difficulties], weights=[item[1] for item in difficulties], k=1)[0]
        subject_group = rng.choice(subject_groups)
        rank = rng.randint(1500, 120000)
        if difficulty == "hard":
            rank = rng.randint(5000, 150000)
        elif difficulty == "very_hard":
            rank = rng.randint(1000, 200000)
        score = _rank_to_score(rank, subject_group)
        major = rng.choice(majors)
        city = rng.choice(cities)
        risk_phrase = rng.choice(risk_phrases)
        school_pref = rng.choice(school_preferences)
        extra_constraint = rng.choice(extra_constraints)
        research_focus = rng.choice(research_focuses)
        multimodal_focus = rng.choice(multimodal_focuses)

        message = _render_case_message(
            category=category,
            rank=rank,
            score=score,
            subject_group=subject_group,
            major=major,
            city=city,
            risk_phrase=risk_phrase,
            school_pref=school_pref,
            extra_constraint=extra_constraint,
            research_focus=research_focus,
            multimodal_focus=multimodal_focus,
        )

        synthetic_cases.append(
            SyntheticCase(
                case_id=f"SYN{idx + 1:04d}",
                source="synthetic",
                category=category,
                difficulty=difficulty,
                message=message,
                score=score,
                rank=rank,
                subject_group=subject_group,
                metadata={
                    "major": major,
                    "city": city,
                    "risk_phrase": risk_phrase,
                    "school_preference": school_pref,
                    "extra_constraint": extra_constraint,
                    "research_focus": research_focus,
                    "multimodal_focus": multimodal_focus,
                },
            )
        )

    combined = seed_cases[:num_cases] + synthetic_cases
    return combined[:num_cases]


def save_cases_jsonl(cases: Iterable[SyntheticCase], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case.model_dump(), ensure_ascii=False) + "\n")
    return path


def load_cases(input_path: str | Path) -> List[SyntheticCase]:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Case file not found: {path}")

    if path.suffix.lower() == ".jsonl":
        return [
            SyntheticCase(**json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "test_cases" in payload:
        return _load_seed_cases(path)
    if isinstance(payload, list):
        return [SyntheticCase(**item) for item in payload]
    raise ValueError(f"Unsupported case file format: {path}")


def build_initial_state(case: SyntheticCase) -> SupervisorState:
    """Build the graph input state for one case."""
    return {
        "messages": [HumanMessage(content=case.message)],
        "intent_classification": None,
        "active_loop": None,
        "loop_history": [],
        "user_profile": None,
        "game_matrix": None,
        "report_draft": None,
        "research_topic": None,
        "search_queries": [],
        "web_research_results": [],
        "knowledge_gaps": [],
        "research_loop_count": 0,
        "research_report": None,
        "pdf_sources": [],
        "vision_results": [],
        "health_restrictions": [],
        "audit_result": None,
        "step_rewards": [],
        "reflection_history": [],
        "orchestration_trace": [],
        "next_action": None,
        "orchestration_reward": None,
        "orchestration_reward_components": None,
        "agent_messages": [],
        "agent_memories": [],
        "deliberation_summaries": [],
        "protocol_violations": [],
        "recommended_next_action": None,
        "current_agent": "",
        "retry_count": 0,
        "human_approved": False,
        "max_loops": 3,
        "debug_logs": [],
    }


def run_single_rollout(case: SyntheticCase, recursion_limit: int = 50) -> Dict[str, Any]:
    """Execute one graph rollout and return a serialized record."""
    initial_state = build_initial_state(case)

    try:
        final_state = supervisor_graph.invoke(initial_state, config={"recursion_limit": recursion_limit})
        summary = compute_episode_summary(final_state)
        intent = final_state.get("intent_classification")
        loop_type = final_state.get("active_loop")
        audit = final_state.get("audit_result")
        game_matrix = final_state.get("game_matrix")

        volunteer_plan = getattr(game_matrix, "volunteer_plan", None) if game_matrix else None

        return {
            "case": case.model_dump(),
            "success": summary.success,
            "intent_type": intent.primary_intent.value if intent else None,
            "loop_type": loop_type.value if loop_type else None,
            "trace": final_state.get("orchestration_trace", []),
            "orchestration_reward": final_state.get("orchestration_reward"),
            "orchestration_reward_components": (
                final_state.get("orchestration_reward_components")
                or summary.reward_components
            ),
            "agent_messages": [
                msg.model_dump() if hasattr(msg, "model_dump") else msg
                for msg in final_state.get("agent_messages", [])
            ],
            "deliberation_summaries": [
                summary_item.model_dump() if hasattr(summary_item, "model_dump") else summary_item
                for summary_item in final_state.get("deliberation_summaries", [])
            ],
            "protocol_violations": final_state.get("protocol_violations", []),
            "summary": summary.model_dump(),
            "audit": audit.model_dump() if audit else None,
            "game_matrix_stats": (
                {
                    "candidate_count": len(game_matrix.major_group_rows),
                    "rush_count": game_matrix.total_rush,
                    "target_count": game_matrix.total_target,
                    "safe_count": game_matrix.total_safe,
                    "agentic_rl_used": getattr(game_matrix, "agentic_rl_used", False),
                    "expected_admission_prob": (
                        getattr(volunteer_plan, "expected_admission_prob", None)
                        if volunteer_plan
                        else None
                    ),
                    "key_prefix_count": (
                        getattr(volunteer_plan, "key_prefix_count", None)
                        if volunteer_plan
                        else None
                    ),
                    "shadowed_choice_count": (
                        getattr(volunteer_plan, "shadowed_choice_count", None)
                        if volunteer_plan
                        else None
                    ),
                    "expected_plan_value": (
                        getattr(volunteer_plan, "expected_plan_value", None)
                        if volunteer_plan
                        else None
                    ),
                }
                if game_matrix
                else None
            ),
            "debug_logs": final_state.get("debug_logs", []),
            "error": None,
        }
    except Exception as exc:
        return {
            "case": case.model_dump(),
            "success": False,
            "intent_type": None,
            "loop_type": None,
            "trace": [],
            "orchestration_reward": None,
            "orchestration_reward_components": None,
            "agent_messages": [],
            "deliberation_summaries": [],
            "protocol_violations": [],
            "summary": {
                "reward": -1.0,
                "success": False,
                "approved": False,
                "trace_length": 0,
                "retry_count": 0,
                "issue_count": 1,
            },
            "audit": None,
            "game_matrix_stats": None,
            "debug_logs": [f"[ROLLOUT_ERROR] {exc}"],
            "error": str(exc),
        }


def rollout_cases(
    *,
    cases: Iterable[SyntheticCase],
    output_path: str | Path,
    recursion_limit: int = 50,
) -> Path:
    """Run graph rollouts and append one JSON object per case."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for case in cases:
            record = run_single_rollout(case, recursion_limit=recursion_limit)
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def _stage_candidates(stage: str, decision: Dict[str, Any]) -> List[str]:
    candidates = decision.get("candidate_actions") or []
    if candidates:
        return candidates
    fallback = {
        "after_router": ["profiling_agent", "deep_research", "multimodal_parser"],
        "after_profiling": ["game_agent", "deep_research"],
        "after_game": ["report_agent", "deep_research"],
        "after_report": ["critic_agent"],
        "after_critic": ["game_agent", "report_agent", "profiling_agent", "deep_research", "END"],
    }
    return fallback.get(stage, [])


def estimate_action_value(decision: Dict[str, Any], candidate_action: str, final_summary: Dict[str, Any]) -> float:
    """Counterfactual proxy score for one candidate action."""
    observation = decision.get("observation", {})
    stage = decision.get("stage")
    base = float(final_summary.get("reward", 0.0))
    score = base * 0.35

    if stage == "after_router":
        if observation.get("requires_vision"):
            score += 0.85 if candidate_action == "multimodal_parser" else -0.70
        elif observation.get("active_loop") == "slow":
            score += 0.80 if candidate_action == "deep_research" else -0.55
        else:
            score += 0.75 if candidate_action == "profiling_agent" else -0.30

    elif stage == "after_profiling":
        needs_research = observation.get("intent_type") == "mixed" and observation.get("requires_search")
        if needs_research:
            score += 0.70 if candidate_action == "deep_research" else -0.35
        else:
            score += 0.65 if candidate_action == "game_agent" else -0.25

    elif stage == "after_game":
        should_research = (
            observation.get("has_deep_research_trigger")
            or observation.get("candidate_count", 0) < 15
            or observation.get("protocol_violation_count", 0) > 0
            or observation.get("key_high_tail_count", 0) > 0
            or observation.get("bait_group_count", 0) > 0
            or observation.get("high_crowding_count", 0) > 0
            or (observation.get("requires_search") and observation.get("research_loop_count", 0) == 0)
        )
        if should_research:
            score += 0.75 if candidate_action == "deep_research" else -0.40
        else:
            score += 0.70 if candidate_action == "report_agent" else -0.20

        if observation.get("has_volunteer_plan") and observation.get("expected_admission_prob", 1.0) < 0.90:
            score += 0.20 if candidate_action == "deep_research" else -0.10

    elif stage == "after_report":
        score += 0.60 if candidate_action == "critic_agent" else -0.50

    elif stage == "after_critic":
        retry_count = observation.get("retry_count", 0)
        issue_count = observation.get("issue_count", 0)
        if issue_count == 0:
            score += 0.80 if candidate_action == "END" else -0.45
        elif retry_count >= 3 and observation.get("active_loop") != "slow":
            score += 0.65 if candidate_action == "deep_research" else (-0.10 if candidate_action == "END" else -0.35)
        else:
            preferred = decision.get("selected_action")
            score += 0.60 if candidate_action == preferred else -0.20

    if candidate_action == decision.get("selected_action"):
        score += 0.05

    return round(score, 4)


def build_pairwise_preferences(rollout_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Construct pairwise preferences from recorded supervisor traces."""
    preferences: List[Dict[str, Any]] = []

    for record in rollout_records:
        case = record.get("case", {})
        summary = record.get("summary", {})
        for step_index, decision in enumerate(record.get("trace", [])):
            stage = decision.get("stage", "unknown")
            chosen_action = decision.get("selected_action")
            if not chosen_action:
                continue

            scored_candidates = []
            for candidate_action in _stage_candidates(stage, decision):
                scored_candidates.append(
                    (
                        candidate_action,
                        estimate_action_value(decision, candidate_action, summary),
                    )
                )
            scored_candidates.sort(key=lambda item: item[1], reverse=True)

            chosen_score = dict(scored_candidates).get(chosen_action)
            if chosen_score is None:
                continue

            for alt_action, alt_score in scored_candidates:
                if alt_action == chosen_action:
                    continue
                preferences.append(
                    {
                        "case_id": case.get("case_id"),
                        "message": case.get("message"),
                        "stage": stage,
                        "step_index": step_index,
                        "observation": decision.get("observation", {}),
                        "chosen_action": chosen_action,
                        "rejected_action": alt_action,
                        "chosen_score": chosen_score,
                        "rejected_score": alt_score,
                        "margin": round(chosen_score - alt_score, 4),
                        "label_source": "proxy_counterfactual",
                    }
                )

    return preferences


def load_rollout_records(input_path: str | Path) -> List[Dict[str, Any]]:
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Rollout file not found: {path}")
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def save_jsonl(records: Iterable[Dict[str, Any]], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path

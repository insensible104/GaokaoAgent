"""Smoke test that supervisor RL observations include first-hit plan signals."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from models.game_matrix import GameMatrix, MajorGroupRow, MajorOption, StrategyTag
from models.intent import IntentClassification, IntentType, LoopType
from models.user_profile import UserProfile
from recommendation.major_choice_planner import build_volunteer_plan
from rl.orchestration_data_pipeline import estimate_action_value
from rl.supervisor_policy import build_observation


def _row(index: int, prob: float, tail_risk: float) -> MajorGroupRow:
    option = MajorOption(
        school_code=f"10{index:03d}",
        school_name=f"School {index}",
        major_group_code=f"{200 + index}",
        major_name="Computer Science",
        user_utility=0.9,
    )
    return MajorGroupRow(
        school_name=f"School {index}",
        school_code=f"10{index:03d}",
        major_group_code=f"{200 + index}",
        major_list=[option.major_name],
        major_count=1,
        major_options=[option],
        suggested_major_choices=[option],
        admission_prob=prob,
        min_rank_pred=10000 + index,
        rank_diff=1000,
        rank_ci_lower=9000,
        rank_ci_upper=12000,
        adjustment_risk=tail_risk,
        tail_assignment_risk=tail_risk,
        strategy_tag=StrategyTag.TARGET,
        comprehensive_score=prob,
    )


def main():
    profile = UserProfile(score=610, rank=20000, subject_group="physics")
    rows = [_row(1, 0.75, 0.7), _row(2, 0.9, 0.1)]
    plan = build_volunteer_plan(rows, profile)
    matrix = GameMatrix(major_group_rows=rows, volunteer_plan=plan)
    matrix.calculate_statistics()
    state = {
        "intent_classification": IntentClassification(
            primary_intent=IntentType.QUANT,
            secondary_intents=[],
            reasoning="first-hit smoke",
            requires_quant=True,
            requires_search=False,
            requires_vision=False,
            confidence=0.9,
        ),
        "active_loop": LoopType.FAST,
        "game_matrix": matrix,
        "debug_logs": [],
        "reflection_history": [],
        "step_rewards": [],
        "retry_count": 0,
        "research_loop_count": 0,
    }

    observation = build_observation(state, "after_game")
    assert observation.has_volunteer_plan is True
    assert observation.key_prefix_count >= 1
    assert observation.key_high_tail_count == 1
    assert observation.expected_admission_prob > 0.9

    decision = {
        "stage": "after_game",
        "selected_action": "deep_research",
        "candidate_actions": ["report_agent", "deep_research"],
        "observation": observation.model_dump(),
    }
    summary = {"reward": 0.6}
    deep_research_value = estimate_action_value(decision, "deep_research", summary)
    report_value = estimate_action_value(decision, "report_agent", summary)
    assert deep_research_value > report_value

    print("orchestration first-hit observation smoke test passed")


if __name__ == "__main__":
    main()

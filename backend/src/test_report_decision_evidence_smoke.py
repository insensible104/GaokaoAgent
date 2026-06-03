"""Smoke tests for deterministic decision-evidence report sections."""

from types import SimpleNamespace

from agents.report_agent import _append_key_decision_evidence
from models.game_matrix import VolunteerChoice, VolunteerPlan
from models.report import ReportDraft


def test_report_appends_key_decision_evidence() -> None:
    choice = VolunteerChoice(
        choice_index=1,
        school_code="10001",
        school_name="测试大学",
        major_group_code="201",
        group_admission_prob=0.72,
        is_key_prefix=True,
        quant_score=0.68,
        data_confidence_score=0.74,
        deterministic_risk_band="thin_target",
        quant_evidence=["位次缓冲 +800 名，约 0.50 个不确定性宽度"],
        market_evidence_cards=[
            {
                "signal_type": "opportunity_thesis",
                "claim": "Primary leak mechanism is campus_discount=0.65.",
            },
            {
                "signal_type": "student_fit",
                "claim": "Student fit is driven by balanced fit.",
            },
            {
                "signal_type": "downside_guard",
                "claim": "Downside guard: tail_risk=0.20.",
            },
        ],
    )
    plan = VolunteerPlan(choices=[choice])
    matrix = SimpleNamespace(volunteer_plan=plan)
    draft = ReportDraft(
        executive_summary="摘要",
        strategy_analysis="策略",
        school_recommendations=["原始推荐"],
    )
    draft.generate_markdown()

    draft = _append_key_decision_evidence(draft, matrix)

    text = "\n".join(draft.school_recommendations)
    assert "关键志愿解释" in text
    assert "机会逻辑" in text
    assert "适配理由" in text
    assert "风险边界" in text
    assert "量化校验" in text
    assert "thin_target" in text
    assert "位次缓冲" in text
    assert "campus_discount=0.65" in draft.full_markdown


if __name__ == "__main__":
    test_report_appends_key_decision_evidence()
    print("report decision evidence smoke tests passed")

"""Smoke tests for protocol integration in deep research, report, and critic agents."""

from __future__ import annotations

from models.game_matrix import GameMatrix, MajorGroupRow, StrategyTag, VolatilityLevel
from models.intent import LoopType
from models.report import ReportDraft
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from models.audit_result import AuditStatus
from recommendation.major_choice_planner import build_volunteer_plan
from agents.critic_agent_enhanced import audit_fast_loop, critic_agent_node
from agents.deep_research_agent import deep_research_agent_node
from agents.report_agent import _format_recommendation, _row_decision_evidence_payload, report_agent_node


def _make_row(name: str, tag: StrategyTag, prob: float) -> MajorGroupRow:
    return MajorGroupRow(
        school_name=name,
        school_code=f"{name[:2]}01",
        major_group_code=f"{name[:2]}-G1",
        major_list=["计算机科学与技术"],
        major_count=1,
        admission_prob=prob,
        min_rank_pred=12000,
        rank_diff=500,
        rank_ci_lower=11000,
        rank_ci_upper=13000,
        fear_index=0.0,
        volatility=VolatilityLevel.MEDIUM,
        adjustment_risk=0.02,
        strategy_tag=tag,
        comprehensive_score=0.85,
        sentiment_score=0.0,
    )


def _profile() -> UserProfile:
    return UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_cities=["广州"],
        preferred_majors=["计算机科学与技术"],
        blacklist_majors=[],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.BALANCED,
    )


def test_deep_research_failure_emits_protocol_message() -> None:
    state = {
        "messages": [],
        "research_topic": None,
    }
    result = deep_research_agent_node(state)
    assert result["agent_messages"], "deep research should emit protocol failure message"
    assert result["agent_memories"], "deep research should emit local failure memory"


def test_report_failure_emits_protocol_message() -> None:
    result = report_agent_node({"user_profile": None, "game_matrix": None})
    assert result["agent_messages"], "report agent should emit protocol failure message"


def test_report_recommendation_includes_decision_evidence_cards() -> None:
    row = _make_row("Evidence大学", StrategyTag.TARGET, 0.72)
    row.market_evidence_cards = [
        {
            "signal_type": "opportunity_thesis",
            "claim": "Primary leak mechanism is low attention; arbitrage_score=0.61.",
            "value": 0.61,
            "confidence": 0.72,
        },
        {
            "signal_type": "student_fit",
            "claim": "Student fit is driven by school/tier lift; acceptability=0.84.",
            "value": 0.68,
            "confidence": 0.72,
        },
        {
            "signal_type": "downside_guard",
            "claim": "Downside guard: tail_risk=0.18, rebound_risk=0.22, blacklist=False.",
            "value": 0.18,
            "confidence": 0.78,
        },
    ]

    text = _format_recommendation(row)

    assert "机会逻辑" in text
    assert "适配理由" in text
    assert "风险边界" in text
    assert "arbitrage_score=0.61" in text


def test_report_payload_includes_decision_evidence_cards() -> None:
    row = _make_row("Payload大学", StrategyTag.TARGET, 0.72)
    row.market_evidence_cards = [
        {
            "signal_type": "opportunity_thesis",
            "claim": "Primary leak mechanism is low attention; arbitrage_score=0.61.",
            "value": 0.61,
            "confidence": 0.72,
        },
        {
            "signal_type": "student_fit",
            "claim": "Student fit is driven by school/tier lift; acceptability=0.84.",
            "value": 0.68,
            "confidence": 0.72,
        },
    ]

    payload = _row_decision_evidence_payload(row)

    assert payload["decision_evidence_cards"]
    assert payload["decision_evidence_cards"][0]["signal_type"] == "opportunity_thesis"


def test_critic_rejects_key_prefix_report_missing_decision_evidence() -> None:
    opportunity = _make_row("Evidence大学", StrategyTag.TARGET, 0.72)
    opportunity.market_evidence_cards = [
        {
            "signal_type": "opportunity_thesis",
            "claim": "Primary leak mechanism is low attention; arbitrage_score=0.61.",
            "value": 0.61,
            "confidence": 0.72,
        },
        {
            "signal_type": "student_fit",
            "claim": "Student fit is driven by school/tier lift; acceptability=0.84.",
            "value": 0.68,
            "confidence": 0.72,
        },
        {
            "signal_type": "downside_guard",
            "claim": "Downside guard: tail_risk=0.18, rebound_risk=0.22, blacklist=False.",
            "value": 0.18,
            "confidence": 0.78,
        },
    ]
    safe = _make_row("Safe大学", StrategyTag.SAFE, 0.96)
    rows = [opportunity, safe]
    plan = build_volunteer_plan(rows, _profile())
    matrix = GameMatrix(major_group_rows=rows, volunteer_plan=plan)
    matrix.calculate_statistics()
    report = ReportDraft(
        executive_summary="summary",
        strategy_analysis="analysis",
        school_recommendations=["Evidence大学 only probability text"],
        risk_warnings=["basic warning"],
        regret_value=100,
    )
    report.generate_markdown()

    audit = audit_fast_loop(report, matrix, _profile(), retry_count=0)

    assert audit.status == AuditStatus.REJECT_LOGIC
    assert audit.reroute_to == "report_agent"
    assert any("decision evidence" in issue for issue in audit.issues)


def test_critic_emits_protocol_message_on_pass() -> None:
    matrix = GameMatrix(
        major_group_rows=[
            _make_row("A大学", StrategyTag.SAFE, 0.95),
            _make_row("B大学", StrategyTag.TARGET, 0.86),
            _make_row("C大学", StrategyTag.RUSH, 0.58),
        ]
    )
    matrix.calculate_statistics()
    report = ReportDraft(
        executive_summary="summary",
        strategy_analysis="analysis",
        school_recommendations=["A大学", "B大学", "C大学"],
        risk_warnings=["warning"],
        regret_value=300.0,
    )
    report.generate_markdown()
    state = {
        "report_draft": report,
        "game_matrix": matrix,
        "user_profile": _profile(),
        "retry_count": 0,
        "messages": [],
        "active_loop": LoopType.FAST,
        "search_queries": [],
        "pdf_sources": [],
    }
    result = critic_agent_node(state)
    assert result["agent_messages"], "critic should emit protocol message"
    assert result["agent_memories"], "critic should emit local memory"


if __name__ == "__main__":
    test_deep_research_failure_emits_protocol_message()
    test_report_failure_emits_protocol_message()
    test_report_recommendation_includes_decision_evidence_cards()
    test_report_payload_includes_decision_evidence_cards()
    test_critic_rejects_key_prefix_report_missing_decision_evidence()
    test_critic_emits_protocol_message_on_pass()
    print("agent protocol smoke tests passed")

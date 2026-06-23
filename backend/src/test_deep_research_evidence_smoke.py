"""Smoke tests for deep-research evidence cards and citation audit."""

from __future__ import annotations

import os

from agents.critic_agent_enhanced import audit_slow_loop
from models.audit_result import AuditStatus
from subgraphs.deep_research import _evidence_appendix, execute_research, synthesize_report


def test_deep_research_fallback_generates_readable_evidence_cards() -> None:
    original_key = os.environ.pop("TAVILY_API_KEY", None)
    try:
        result = execute_research(
            {
                "research_topic": "测试专业培养方案",
                "sub_questions": ["某大学计算机专业招生章程是什么？"],
                "search_queries": [],
                "search_results": [],
                "research_evidence_cards": [],
                "is_sufficient": False,
                "knowledge_gaps": [],
                "information_density": 0.0,
                "research_loop_count": 0,
                "max_research_loops": 1,
                "research_report": None,
                "debug_logs": [],
            }
        )
    finally:
        if original_key is not None:
            os.environ["TAVILY_API_KEY"] = original_key

    cards = result["research_evidence_cards"]

    assert cards
    assert cards[0]["source_type"] == "manual_verification_required"
    assert cards[0]["usable_for_prediction"] is False
    appendix = _evidence_appendix(cards)
    assert "引用与证据附录" in appendix
    assert "fallback_no_web_search" in appendix
    assert_no_mojibake(appendix)


def test_slow_loop_audit_requires_evidence_appendix_and_cards() -> None:
    missing = audit_slow_loop({"research_report": "# 调研报告\n\n没有引用。"}, retry_count=0)
    assert missing.status == AuditStatus.REJECT_LOGIC

    with_cards = audit_slow_loop(
        {
            "research_report": "# 调研报告\n\n## 引用与证据附录\n\n1. fallback source",
            "research_evidence_cards": [
                {
                    "signal_type": "research_todo",
                    "source_type": "manual_verification_required",
                    "value": 0.0,
                    "confidence": 0.2,
                    "claim": "Need official verification.",
                    "source": "fallback_no_web_search",
                    "usable_for_prediction": False,
                }
            ],
        },
        retry_count=0,
    )

    assert with_cards.status == AuditStatus.PASS
    assert any("官方/准官方" in issue for issue in with_cards.issues)
    assert any("不可直接用于预测" in issue for issue in with_cards.issues)


def test_synthesize_report_preserves_readable_evidence_appendix() -> None:
    result = synthesize_report(
        {
            "research_topic": "测试专业组招生计划",
            "search_results": ["- 学校官网发布招生计划调整。"],
            "research_evidence_cards": [
                {
                    "signal_type": "external_research",
                    "source_type": "official_or_school",
                    "value": 0.8,
                    "confidence": 0.9,
                    "claim": "学校官网发布招生计划调整。",
                    "source": "https://admission.example.edu.cn/plan",
                    "cutoff_date": "2026-06-04",
                    "usable_for_prediction": True,
                }
            ],
            "knowledge_gaps": [],
        }
    )

    assert "引用与证据附录" in result["research_report"]
    assert "official_or_school" in result["research_report"]
    assert_no_mojibake(result["research_report"])


def assert_no_mojibake(text: str) -> None:
    markers = ["锛", "鍙", "鎷", "骞", "涓", "寰", "鏍", "€", "�"]
    assert not any(marker in text for marker in markers), text


if __name__ == "__main__":
    test_deep_research_fallback_generates_readable_evidence_cards()
    test_slow_loop_audit_requires_evidence_appendix_and_cards()
    test_synthesize_report_preserves_readable_evidence_appendix()
    print("deep research evidence smoke tests passed")

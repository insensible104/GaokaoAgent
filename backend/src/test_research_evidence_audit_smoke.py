"""Smoke tests for deep-research evidence audits."""

from __future__ import annotations

from evaluation.research_evidence_audit import (
    audit_research_evidence_cards,
    build_markdown_research_evidence_audit,
)


def test_research_evidence_audit_accepts_prediction_ready_official_cards():
    cards = [
        {
            "signal_type": "external_research",
            "source_type": "official_or_school",
            "value": 0.80,
            "confidence": 0.90,
            "claim": "Brand Institute 801 招生计划 扩招，院校专业组调整，招生人数增加。",
            "source": "https://admission.brand.example/2026-plan",
            "cutoff_date": "2026-06-04",
            "usable_for_prediction": True,
        },
        {
            "signal_type": "external_research",
            "source_type": "wechat",
            "value": 0.70,
            "confidence": 0.75,
            "claim": "Brand Institute 801 被微信主播热推，公众号讨论度很高。",
            "source": "wechat_public_observation",
            "cutoff_date": "2026-06-04",
            "usable_for_prediction": False,
        },
    ]

    result = audit_research_evidence_cards(cards, scope_terms=["Brand Institute", "801"])
    markdown = build_markdown_research_evidence_audit(result)

    assert result["status"] == "prediction_feature_ready"
    assert result["usable_prediction_card_count"] == 1
    assert result["prediction_signal_count"] >= 1
    assert result["reference_signal_count"] >= 1
    assert all(row["passed"] for row in result["checks"])
    assert "Research Evidence Audit" in markdown


def test_research_evidence_audit_blocks_social_prediction_leakage():
    cards = [
        {
            "signal_type": "external_research",
            "source_type": "wechat",
            "value": 0.90,
            "confidence": 0.80,
            "claim": "某公众号称该专业组今年会爆火。",
            "source": "wechat_public_observation",
            "cutoff_date": "2026-06-04",
            "usable_for_prediction": True,
        },
        {
            "signal_type": "research_todo",
            "source_type": "manual_verification_required",
            "value": 0.0,
            "confidence": 0.20,
            "claim": "Fallback research outline. Official source verification is still required.",
            "source": "fallback_no_web_search",
            "cutoff_date": "runtime_fallback",
            "usable_for_prediction": False,
        },
    ]

    result = audit_research_evidence_cards(cards)

    assert result["status"] == "blocked_for_quant_ingestion"
    assert any(row["name"] == "social_sources_are_reference_only" and not row["passed"] for row in result["checks"])
    assert any("Social, WeChat" in item for item in result["next_required_evidence"])


if __name__ == "__main__":
    test_research_evidence_audit_accepts_prediction_ready_official_cards()
    test_research_evidence_audit_blocks_social_prediction_leakage()
    print("research evidence audit smoke tests passed")

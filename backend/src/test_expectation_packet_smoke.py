"""Smoke tests for expectation-management packets."""

from __future__ import annotations

from evaluation.expectation_packet import (
    build_expectation_packet,
    build_markdown_expectation_packet,
)
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


def test_expectation_packet_requires_unconfirmed_constraints() -> None:
    profile = UserProfile(
        score=450,
        rank=198000,
        subject_group="历史",
        preferred_cities=["广州"],
        preferred_majors=["会计"],
        risk_tolerance=RiskTolerance.CONSERVATIVE,
        school_major_preference=SchoolMajorPreference.UNKNOWN,
        regret_sensitivity=0.8,
    )

    packet = build_expectation_packet(profile)

    assert packet["status"] == "needs_confirmation"
    item_by_id = {item["id"]: item for item in packet["confirmation_items"]}
    assert item_by_id["region_boundary"]["status"] == "known"
    assert item_by_id["school_major_tradeoff"]["status"] == "needs_confirmation"
    assert any("不承诺录取结果" in text for text in [packet["non_guarantee_clause"]])
    signoff_by_id = {item["id"]: item for item in packet["client_signoff_checklist"]}
    assert signoff_by_id["constraint_freeze"]["status"] == "pending_signature"
    assert signoff_by_id["non_guarantee"]["required"] is True
    markdown = build_markdown_expectation_packet(packet)
    assert "志愿填报预期确认单" in markdown
    assert "客户签收清单" in markdown
    assert "是否接受省外" in markdown
    assert "家长确认" in markdown


def test_expectation_packet_can_be_ready_when_core_constraints_known() -> None:
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_cities=["广州", "深圳"],
        excluded_cities=["北京"],
        preferred_majors=["计算机"],
        blacklist_majors=["土木"],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_MAJOR,
    )

    packet = build_expectation_packet(profile)

    assert packet["status"] == "needs_confirmation"
    item_by_id = {item["id"]: item for item in packet["confirmation_items"]}
    assert item_by_id["rank_score_subject"]["status"] == "known"
    assert item_by_id["major_boundary"]["status"] == "known"
    assert item_by_id["adjustment_acceptance"]["status"] == "needs_confirmation"
    signoff_ids = {item["id"] for item in packet["client_signoff_checklist"]}
    assert "blacklist_hard_boundary" in signoff_ids
    assert "region_tradeoff" in signoff_ids


if __name__ == "__main__":
    test_expectation_packet_requires_unconfirmed_constraints()
    test_expectation_packet_can_be_ready_when_core_constraints_known()
    print("expectation packet smoke tests passed")

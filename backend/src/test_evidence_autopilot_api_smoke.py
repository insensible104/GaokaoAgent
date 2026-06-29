"""Smoke tests for the Evidence Autopilot backend bridge."""

from __future__ import annotations

from fastapi.testclient import TestClient

import main
from evidence_autopilot_api import (
    EvidenceAutopilotResearchRequest,
    build_evidence_autopilot_research_response,
)


def test_evidence_autopilot_research_builder_returns_readable_auditable_tasks() -> None:
    request = EvidenceAutopilotResearchRequest(
        province="广东",
        schoolName="华南理工大学",
        majorName="智能制造与数据工程",
        targetYear=2026,
    )

    response = build_evidence_autopilot_research_response(request)

    assert response.success is True
    assert response.targetLabel == "广东 2026 华南理工大学 智能制造与数据工程"
    assert len(response.tasks) >= 8
    assert len(response.searchQueries) >= 8
    assert len(response.evidenceCards) == len(response.tasks)
    assert "不会承诺录取、升学或就业结果" in response.claimBoundary
    assert "合规人工采集任务" in response.claimBoundary
    assert_no_mojibake(response.claimBoundary)

    claims = {task.claim for task in response.tasks}
    for claim in {
        "official_admission",
        "rank_history",
        "faculty_research",
        "undergrad_access",
        "employment_market",
        "graduate_progression",
        "civil_service_path",
        "counter_evidence",
    }:
        assert claim in claims

    official = next(task for task in response.tasks if task.claim == "official_admission")
    assert official.channel == "official_pdf"
    assert official.title == "官方招生计划与章程核验"
    assert "招生章程" in official.query
    assert "原文摘录" in official.requiredFields

    operator_tasks = [task for task in response.tasks if task.channel.endswith("_operator")]
    assert operator_tasks
    assert all("不绕过" in task.reviewAction and "平台限制" in task.reviewAction for task in operator_tasks)

    for task in response.tasks:
        assert_no_mojibake(task.title)
        assert_no_mojibake(task.query)
        assert_no_mojibake(task.reviewAction)
        for field in task.requiredFields:
            assert_no_mojibake(field)

    statuses = {card.status for card in response.evidenceCards}
    assert statuses <= {"requires_capture", "operator_review"}
    assert "verified" not in statuses
    assert all(card.sourceTitle for card in response.evidenceCards)
    assert all(card.excerpt == "" for card in response.evidenceCards)


def test_evidence_autopilot_research_endpoint_is_wired_to_fastapi() -> None:
    client = TestClient(main.app)

    response = client.post(
        "/api/evidence-autopilot/research",
        json={
            "province": "广东",
            "schoolName": "华南理工大学",
            "majorName": "智能制造与数据工程",
            "targetYear": 2026,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["targetLabel"] == "广东 2026 华南理工大学 智能制造与数据工程"
    assert payload["tasks"]
    assert payload["searchQueries"]
    assert payload["evidenceCards"]
    assert "/api/evidence-autopilot/research" in main.get_runtime_status()["entrypoints"]["api"]


def assert_no_mojibake(text: str) -> None:
    markers = ["锛", "鍙", "鎷", "骞", "涓", "寰", "鏍", "€", "�"]
    assert not any(marker in text for marker in markers), text


if __name__ == "__main__":
    test_evidence_autopilot_research_builder_returns_readable_auditable_tasks()
    test_evidence_autopilot_research_endpoint_is_wired_to_fastapi()
    print("evidence autopilot API smoke tests passed")

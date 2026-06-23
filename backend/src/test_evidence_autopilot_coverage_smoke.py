"""Coverage summary tests for the Evidence Autopilot backend bridge."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

import main
from evidence_autopilot_api import (
    EvidenceAutopilotEvidenceCard,
    EvidenceAutopilotResearchRequest,
    build_evidence_autopilot_research_response,
)


def test_coverage_summary_marks_uncaptured_p0_tasks_as_not_ready() -> None:
    request = EvidenceAutopilotResearchRequest(
        province="Guangdong",
        schoolName="South China University of Technology",
        majorName="intelligent manufacturing",
        targetYear=2026,
    )

    response = build_evidence_autopilot_research_response(request)

    coverage = response.evidenceCoverage
    assert coverage.totalTasks == len(response.tasks)
    assert coverage.capturedTaskIds == []
    assert "official-plan-charter" in coverage.missingP0TaskIds
    assert "rank-history-band" in coverage.missingP0TaskIds
    assert "counter-evidence" in coverage.operatorTaskIds
    assert coverage.readyForCounselorReview is False
    assert any("P0" in blocker for blocker in coverage.reviewBlockers)


def test_coverage_summary_counts_captured_cards_but_keeps_remaining_blocks() -> None:
    request = EvidenceAutopilotResearchRequest(
        province="Guangdong",
        schoolName="South China University of Technology",
        majorName="intelligent manufacturing",
        targetYear=2026,
        enableOfficialSourceProvider=True,
    )

    response = build_evidence_autopilot_research_response(
        request,
        official_source_providers=[
            StaticProvider(
                "official-plan-charter",
                "official_admission",
                "official",
            ),
            StaticProvider("rank-history-band", "rank_history", "official"),
            StaticProvider("faculty-research-direction", "faculty_research", "school"),
            StaticProvider("undergrad-access", "undergrad_access", "school"),
            StaticProvider("graduate-progression", "graduate_progression", "school"),
        ],
    )

    coverage = response.evidenceCoverage
    assert coverage.capturedTaskIds == [
        "official-plan-charter",
        "rank-history-band",
        "faculty-research-direction",
        "undergrad-access",
        "graduate-progression",
    ]
    assert "official-plan-charter" not in coverage.missingP0TaskIds
    assert "employment-market" in coverage.missingP0TaskIds
    assert "counter-evidence" in coverage.missingP0TaskIds
    assert coverage.readyForCounselorReview is False


def test_coverage_summary_is_exposed_by_fastapi_endpoint() -> None:
    client = TestClient(main.app)

    response = client.post(
        "/api/evidence-autopilot/research",
        json={
            "province": "Guangdong",
            "schoolName": "South China University of Technology",
            "majorName": "intelligent manufacturing",
            "targetYear": 2026,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["evidenceCoverage"]["totalTasks"] == len(payload["tasks"])
    assert payload["evidenceCoverage"]["readyForCounselorReview"] is False
    assert "reviewBlockers" in payload["evidenceCoverage"]


class StaticProvider:
    def __init__(self, task_id: str, claim: str, source_type: str) -> None:
        self.task_id = task_id
        self.claim = claim
        self.source_type = source_type

    def capture(
        self,
        request: EvidenceAutopilotResearchRequest,
    ) -> list[EvidenceAutopilotEvidenceCard]:
        return [
            EvidenceAutopilotEvidenceCard(
                taskId=self.task_id,
                claim=self.claim,
                status="captured_candidate",
                sourceTitle=f"Static source for {self.task_id}",
                sourceUrl="https://example.edu/source",
                sourceType=self.source_type,
                excerpt=f"Captured excerpt for {self.task_id}",
                capturedAt=date.today().isoformat(),
                confidence="high",
                reviewAction="Review source excerpt before delivery.",
            )
        ]

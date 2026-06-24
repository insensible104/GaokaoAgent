"""Coverage summary tests for the Evidence Autopilot backend bridge."""

from __future__ import annotations

import base64
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

import main
from evidence_autopilot_api import (
    EvidenceAutopilotEvidenceCard,
    EvidenceAutopilotResearchRequest,
    ReviewedEvidenceCard,
    build_evidence_autopilot_research_response,
)
from reviewed_evidence_store import append_reviewed_evidence_record
from reviewed_evidence_attachment_store import save_reviewed_evidence_attachment


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


def test_reviewed_evidence_cards_can_close_operator_p0_gates(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_AUTOPILOT_ATTACHMENT_DIR", str(tmp_path))
    request = EvidenceAutopilotResearchRequest(
        province="Guangdong",
        schoolName="South China University of Technology",
        majorName="intelligent manufacturing",
        targetYear=2026,
        enableOfficialSourceProvider=True,
        reviewedEvidenceCards=[
            {
                "taskId": "employment-market",
                "claim": "employment_market",
                "status": "captured_candidate",
                "sourceTitle": "Reviewed job-market sample",
                "sourceUrl": "operator-review://boss/2026-06-24/scut-im-001",
                "sourceType": "job",
                "excerpt": "Reviewed visible job sample links intelligent manufacturing work to robotics integration.",
                "capturedAt": "2026-06-24",
                "confidence": "medium",
                "reviewAction": "Use as operator-captured job sample only; do not infer employment certainty.",
                **review_controls("job-market-screenshot", tmp_path),
            },
            {
                "taskId": "counter-evidence",
                "claim": "counter_evidence",
                "status": "captured_candidate",
                "sourceTitle": "Manual counter-evidence review log",
                "sourceUrl": "operator-review://manual/2026-06-24/scut-im-counter",
                "sourceType": "discussion",
                "excerpt": "Manual review found no blocking campus-conflict, blacklist, or complaint hit in the checked sources.",
                "capturedAt": "2026-06-24",
                "confidence": "medium",
                "reviewAction": "Use as a counter-evidence check log only; rerun before final delivery.",
                **review_controls("counter-evidence-screenshot", tmp_path),
            },
        ],
    )

    response = build_evidence_autopilot_research_response(
        request,
        official_source_providers=[
            StaticProvider("official-plan-charter", "official_admission", "official"),
            StaticProvider("rank-history-band", "rank_history", "official"),
            StaticProvider("faculty-research-direction", "faculty_research", "school"),
            StaticProvider("undergrad-access", "undergrad_access", "school"),
            StaticProvider("graduate-progression", "graduate_progression", "school"),
        ],
    )

    coverage = response.evidenceCoverage
    assert "employment-market" in coverage.capturedTaskIds
    assert "counter-evidence" in coverage.capturedTaskIds
    assert coverage.missingP0TaskIds == []
    assert coverage.readyForCounselorReview is True
    assert "Reviewed evidence cards accepted" in response.claimBoundary


def test_incomplete_reviewed_evidence_cards_do_not_close_p0_gates() -> None:
    request = EvidenceAutopilotResearchRequest(
        province="Guangdong",
        schoolName="South China University of Technology",
        majorName="intelligent manufacturing",
        targetYear=2026,
        reviewedEvidenceCards=[
            {
                "taskId": "employment-market",
                "claim": "employment_market",
                "status": "captured_candidate",
                "sourceTitle": "Incomplete job-market sample",
                "sourceUrl": "",
                "sourceType": "job",
                "excerpt": "",
                "capturedAt": "2026-06-24",
                "confidence": "medium",
                "reviewAction": "Incomplete card must remain a task.",
            }
        ],
    )

    response = build_evidence_autopilot_research_response(request)

    assert "employment-market" in response.evidenceCoverage.missingP0TaskIds
    assert "employment-market" not in response.evidenceCoverage.capturedTaskIds
    assert "Rejected reviewed evidence cards" in response.claimBoundary


def test_operator_review_card_requires_attachment_redaction_and_identity_for_p0_gate() -> None:
    request = EvidenceAutopilotResearchRequest(
        province="Guangdong",
        schoolName="South China University of Technology",
        majorName="intelligent manufacturing",
        targetYear=2026,
        reviewedEvidenceCards=[
            {
                "taskId": "employment-market",
                "claim": "employment_market",
                "status": "captured_candidate",
                "sourceTitle": "Reviewed job-market sample",
                "sourceUrl": "operator-review://boss/2026-06-24/scut-im-001",
                "sourceType": "job",
                "excerpt": "Reviewed visible job sample links intelligent manufacturing work to robotics integration.",
                "capturedAt": "2026-06-24",
                "confidence": "medium",
                "reviewAction": "Use as operator-captured job sample only; do not infer employment certainty.",
            }
        ],
    )

    response = build_evidence_autopilot_research_response(request)

    assert "employment-market" in response.evidenceCoverage.missingP0TaskIds
    assert "employment-market" not in response.evidenceCoverage.capturedTaskIds
    assert "Rejected reviewed evidence cards" in response.claimBoundary


def test_operator_review_card_requires_existing_attachment_file_for_p0_gate() -> None:
    request = EvidenceAutopilotResearchRequest(
        province="Guangdong",
        schoolName="South China University of Technology",
        majorName="intelligent manufacturing",
        targetYear=2026,
        reviewedEvidenceCards=[
            {
                "taskId": "employment-market",
                "claim": "employment_market",
                "status": "captured_candidate",
                "sourceTitle": "Reviewed job-market sample",
                "sourceUrl": "operator-review://boss/2026-06-24/scut-im-001",
                "sourceType": "job",
                "excerpt": "Reviewed visible job sample links intelligent manufacturing work to robotics integration.",
                "capturedAt": "2026-06-24",
                "confidence": "medium",
                "reviewAction": "Use as operator-captured job sample only; do not infer employment certainty.",
                **review_controls("missing-job-market-screenshot"),
            }
        ],
    )

    response = build_evidence_autopilot_research_response(request)

    assert "employment-market" in response.evidenceCoverage.missingP0TaskIds
    assert "employment-market" not in response.evidenceCoverage.capturedTaskIds
    assert "Rejected reviewed evidence cards" in response.claimBoundary


def test_research_response_can_merge_case_scoped_reviewed_evidence_ledger(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_AUTOPILOT_ATTACHMENT_DIR", str(tmp_path))
    ledger_path = tmp_path / "reviewed_evidence.jsonl"
    append_reviewed_evidence_record(
        ledger_path=ledger_path,
        target_label="Guangdong 2026 SCUT intelligent manufacturing",
        card=ReviewedCardFactory.card(
            task_id="employment-market",
            claim="employment_market",
            source_type="job",
            attachment_root=tmp_path,
        ),
        reviewer="operator-a",
        case_id="scut-im-v0",
    )
    append_reviewed_evidence_record(
        ledger_path=ledger_path,
        target_label="Other case",
        card=ReviewedCardFactory.card(
            task_id="counter-evidence",
            claim="counter_evidence",
            source_type="discussion",
            attachment_root=tmp_path,
        ),
        reviewer="operator-a",
        case_id="other-case",
    )

    request = EvidenceAutopilotResearchRequest(
        province="Guangdong",
        schoolName="South China University of Technology",
        majorName="intelligent manufacturing",
        targetYear=2026,
        caseId="scut-im-v0",
        enableReviewedEvidenceLedger=True,
    )

    response = build_evidence_autopilot_research_response(
        request,
        reviewed_evidence_ledger_path=ledger_path,
    )

    assert "employment-market" in response.evidenceCoverage.capturedTaskIds
    assert "counter-evidence" not in response.evidenceCoverage.capturedTaskIds
    assert "Reviewed evidence ledger merged: employment-market" in response.claimBoundary


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


class ReviewedCardFactory:
    @staticmethod
    def card(
        *,
        task_id: str,
        claim: str,
        source_type: str,
        attachment_root: Path,
    ) -> ReviewedEvidenceCard:
        return ReviewedEvidenceCard(
            taskId=task_id,
            claim=claim,
            status="captured_candidate",
            sourceTitle=f"Reviewed source for {task_id}",
            sourceUrl="",
            sourceType=source_type,
            excerpt=f"Reviewed excerpt for {task_id}",
            capturedAt="2026-06-24",
            confidence="medium",
            reviewAction="Use as reviewed operator evidence only.",
            **review_controls(task_id, attachment_root),
        )


def review_controls(seed: str, attachment_root: Path | None = None) -> dict:
    storage_ref = f"reviewed-evidence/{seed}.png"
    attachment = {
        "attachmentId": f"attachment-{seed}",
        "kind": "screenshot",
        "storageRef": storage_ref,
        "capturedAt": "2026-06-24T00:00:00Z",
        "redactionStatus": "redacted",
    }
    if attachment_root is not None:
        saved = save_reviewed_evidence_attachment(
            storage_root=attachment_root,
            case_id=seed,
            task_id=seed,
            reviewer_id="operator-a",
            kind="screenshot",
            content_type="image/png",
            content_base64=base64.b64encode(b"reviewed evidence screenshot").decode("ascii"),
            captured_at="2026-06-24T00:00:00Z",
            redaction_status="redacted",
            original_file_name=f"{seed}.png",
        )
        attachment = saved.attachment.model_dump()
    return {
        "attachments": [attachment],
        "redactionStatus": "redacted",
        "reviewerIdentity": {
            "reviewerId": "operator-a",
            "displayName": "Operator A",
            "role": "operator",
        },
    }

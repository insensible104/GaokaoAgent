"""Smoke tests for durable reviewed-evidence ledger records."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

import main
from evidence_autopilot_api import ReviewedEvidenceCard
from reviewed_evidence_store import append_reviewed_evidence_record, load_reviewed_evidence_cards


def test_append_reviewed_evidence_record_generates_review_id_and_ledger_entry(tmp_path) -> None:
    ledger_path = tmp_path / "reviewed_evidence.jsonl"
    card = ReviewedEvidenceCard(
        taskId="employment-market",
        claim="employment_market",
        status="captured_candidate",
        sourceTitle="Reviewed job-market sample",
        sourceUrl="",
        sourceType="job",
        excerpt="Visible job sample describes robotics integration responsibilities.",
        capturedAt="2026-06-24",
        confidence="medium",
        reviewAction="Use as operator-captured job sample only; do not infer employment certainty.",
    )

    record = append_reviewed_evidence_record(
        ledger_path=ledger_path,
        target_label="Guangdong 2026 SCUT intelligent manufacturing",
        card=card,
        reviewer="operator-a",
        case_id="scut-im-v0",
    )

    assert record.reviewId.startswith("review-")
    assert record.reviewedEvidenceCard.sourceUrl == f"operator-review://{record.reviewId}"
    assert record.ledgerPath == str(ledger_path)
    assert ledger_path.exists()

    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["reviewId"] == record.reviewId
    assert payload["targetLabel"] == "Guangdong 2026 SCUT intelligent manufacturing"
    assert payload["caseId"] == "scut-im-v0"
    assert payload["reviewer"] == "operator-a"
    assert payload["reviewedEvidenceCard"]["sourceUrl"] == f"operator-review://{record.reviewId}"


def test_reviewed_evidence_endpoint_persists_to_configured_ledger(tmp_path, monkeypatch) -> None:
    ledger_path = tmp_path / "api_reviewed_evidence.jsonl"
    monkeypatch.setenv("EVIDENCE_AUTOPILOT_REVIEWED_LEDGER", str(ledger_path))
    client = TestClient(main.app)

    response = client.post(
        "/api/evidence-autopilot/reviewed-evidence",
        json={
            "targetLabel": "Guangdong 2026 SCUT intelligent manufacturing",
            "caseId": "scut-im-v0",
            "reviewer": "operator-a",
            "card": {
                "taskId": "counter-evidence",
                "claim": "counter_evidence",
                "status": "captured_candidate",
                "sourceTitle": "Manual counter-evidence review",
                "sourceUrl": "",
                "sourceType": "discussion",
                "excerpt": "Manual review found no blocking complaint or campus-conflict hit.",
                "capturedAt": "2026-06-24",
                "confidence": "medium",
                "reviewAction": "Use as counter-evidence review log only; rerun before delivery.",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["reviewId"].startswith("review-")
    assert payload["reviewedEvidenceCard"]["sourceUrl"] == f"operator-review://{payload['reviewId']}"
    assert ledger_path.exists()
    assert "/api/evidence-autopilot/reviewed-evidence" in main.get_runtime_status()["entrypoints"]["api"]


def test_load_reviewed_evidence_cards_filters_by_case_id(tmp_path) -> None:
    ledger_path = tmp_path / "reviewed_evidence.jsonl"
    scut_card = ReviewedEvidenceCard(
        taskId="employment-market",
        claim="employment_market",
        status="captured_candidate",
        sourceTitle="SCUT reviewed job sample",
        sourceUrl="",
        sourceType="job",
        excerpt="SCUT visible job sample.",
        capturedAt="2026-06-24",
        confidence="medium",
        reviewAction="Use as operator-captured job sample only.",
    )
    other_card = scut_card.model_copy(
        update={
            "taskId": "counter-evidence",
            "claim": "counter_evidence",
            "sourceTitle": "Other case counter-evidence",
        }
    )

    append_reviewed_evidence_record(
        ledger_path=ledger_path,
        target_label="Guangdong 2026 SCUT intelligent manufacturing",
        card=scut_card,
        reviewer="operator-a",
        case_id="scut-im-v0",
    )
    append_reviewed_evidence_record(
        ledger_path=ledger_path,
        target_label="Other target",
        card=other_card,
        reviewer="operator-a",
        case_id="other-case",
    )

    cards = load_reviewed_evidence_cards(ledger_path=ledger_path, case_id="scut-im-v0")

    assert [card.taskId for card in cards] == ["employment-market"]
    assert cards[0].sourceUrl.startswith("operator-review://review-")

"""End-to-end smoke for operator evidence capture through backend storage."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from fastapi.testclient import TestClient

import main


def test_operator_evidence_capture_roundtrip_clears_backend_coverage_gate(tmp_path, monkeypatch) -> None:
    ledger_path = tmp_path / "reviewed_evidence.jsonl"
    attachment_root = tmp_path / "attachments"
    monkeypatch.setenv("EVIDENCE_AUTOPILOT_REVIEWED_LEDGER", str(ledger_path))
    monkeypatch.setenv("EVIDENCE_AUTOPILOT_ATTACHMENT_DIR", str(attachment_root))
    client = TestClient(main.app)

    upload = client.post(
        "/api/evidence-autopilot/reviewed-evidence/attachments",
        json={
            "caseId": "scut-im-v0",
            "taskId": "employment-market",
            "reviewerId": "operator-a",
            "kind": "screenshot",
            "contentType": "image/png",
            "contentBase64": base64.b64encode(b"roundtrip screenshot bytes").decode("ascii"),
            "capturedAt": "2026-06-24T08:00:00Z",
            "redactionStatus": "redacted",
            "redactionChecklist": complete_redaction_checklist(),
            "originalFileName": "job-roundtrip.png",
        },
    )
    assert upload.status_code == 200
    attachment = upload.json()["attachment"]
    assert attachment["storageRef"].startswith("reviewed-evidence/scut-im-v0/")

    submit = client.post(
        "/api/evidence-autopilot/reviewed-evidence",
        json={
            "targetLabel": "Guangdong 2026 South China University of Technology intelligent manufacturing",
            "caseId": "scut-im-v0",
            "reviewer": "operator-a",
            "card": {
                "taskId": "employment-market",
                "claim": "employment_market",
                "status": "captured_candidate",
                "sourceTitle": "Reviewed job-market sample",
                "sourceUrl": "",
                "sourceType": "job",
                "excerpt": "Visible public job sample describes manufacturing data analysis and Python workflow responsibilities.",
                "capturedAt": "2026-06-24T08:00:00Z",
                "confidence": "medium",
                "reviewAction": "Use as operator-captured job-market evidence only; do not infer employment certainty.",
                "attachments": [attachment],
                "redactionStatus": "redacted",
                "reviewerIdentity": {
                    "reviewerId": "operator-a",
                    "displayName": "Operator A",
                    "role": "operator",
                },
            },
        },
    )
    assert submit.status_code == 200
    submitted = submit.json()
    assert submitted["reviewedEvidenceCard"]["sourceUrl"].startswith("operator-review://review-")

    listing = client.get("/api/evidence-autopilot/reviewed-evidence/scut-im-v0")
    assert listing.status_code == 200
    records = listing.json()["records"]
    assert len(records) == 1
    audit = records[0]["attachmentAudit"]
    assert audit["status"] == "valid"
    assert audit["validAttachmentCount"] == 1
    assert audit["invalidAttachmentCount"] == 0

    research = client.post(
        "/api/evidence-autopilot/research",
        json={
            "province": "Guangdong",
            "schoolName": "South China University of Technology",
            "majorName": "intelligent manufacturing",
            "targetYear": 2026,
            "caseId": "scut-im-v0",
            "enableReviewedEvidenceLedger": True,
        },
    )
    assert research.status_code == 200
    payload = research.json()
    coverage = payload["evidenceCoverage"]
    assert "employment-market" in coverage["capturedTaskIds"]
    assert "employment-market" not in coverage["missingP0TaskIds"]
    assert coverage["readyForCounselorReview"] is False
    assert "official-plan-charter" in coverage["missingP0TaskIds"]
    assert "Reviewed evidence cards accepted: employment-market." in payload["claimBoundary"]


def test_operator_evidence_capture_roundtrip_rejects_tampered_readback_for_coverage(tmp_path, monkeypatch) -> None:
    ledger_path = tmp_path / "reviewed_evidence.jsonl"
    attachment_root = tmp_path / "attachments"
    monkeypatch.setenv("EVIDENCE_AUTOPILOT_REVIEWED_LEDGER", str(ledger_path))
    monkeypatch.setenv("EVIDENCE_AUTOPILOT_ATTACHMENT_DIR", str(attachment_root))
    client = TestClient(main.app)

    upload = client.post(
        "/api/evidence-autopilot/reviewed-evidence/attachments",
        json={
            "caseId": "scut-im-v0",
            "taskId": "employment-market",
            "reviewerId": "operator-a",
            "kind": "screenshot",
            "contentType": "image/png",
            "contentBase64": base64.b64encode(b"original screenshot bytes").decode("ascii"),
            "capturedAt": "2026-06-24T08:00:00Z",
            "redactionStatus": "redacted",
            "redactionChecklist": complete_redaction_checklist(),
            "originalFileName": "job-roundtrip.png",
        },
    )
    assert upload.status_code == 200
    attachment = upload.json()["attachment"]
    submit = client.post(
        "/api/evidence-autopilot/reviewed-evidence",
        json={
            "targetLabel": "Guangdong 2026 South China University of Technology intelligent manufacturing",
            "caseId": "scut-im-v0",
            "reviewer": "operator-a",
            "card": {
                "taskId": "employment-market",
                "claim": "employment_market",
                "status": "captured_candidate",
                "sourceTitle": "Reviewed job-market sample",
                "sourceUrl": "",
                "sourceType": "job",
                "excerpt": "Visible public job sample describes manufacturing data analysis and Python workflow responsibilities.",
                "capturedAt": "2026-06-24T08:00:00Z",
                "confidence": "medium",
                "reviewAction": "Use as operator-captured job-market evidence only; do not infer employment certainty.",
                "attachments": [attachment],
                "redactionStatus": "redacted",
                "reviewerIdentity": {
                    "reviewerId": "operator-a",
                    "displayName": "Operator A",
                    "role": "operator",
                },
            },
        },
    )
    assert submit.status_code == 200

    stored_path = attachment_root / attachment["storageRef"]
    stored_path.write_bytes(b"tampered after successful submission")
    listing = client.get("/api/evidence-autopilot/reviewed-evidence/scut-im-v0")
    assert listing.status_code == 200
    assert listing.json()["records"][0]["attachmentAudit"]["status"] == "invalid"

    research = client.post(
        "/api/evidence-autopilot/research",
        json={
            "province": "Guangdong",
            "schoolName": "South China University of Technology",
            "majorName": "intelligent manufacturing",
            "targetYear": 2026,
            "caseId": "scut-im-v0",
            "enableReviewedEvidenceLedger": True,
        },
    )
    assert research.status_code == 200
    coverage = research.json()["evidenceCoverage"]
    assert "employment-market" not in coverage["capturedTaskIds"]
    assert "employment-market" in coverage["missingP0TaskIds"]


def test_real_case_public_fixture_can_enter_reviewed_ledger_and_coverage(tmp_path, monkeypatch) -> None:
    ledger_path = tmp_path / "reviewed_evidence.jsonl"
    monkeypatch.setenv("EVIDENCE_AUTOPILOT_REVIEWED_LEDGER", str(ledger_path))
    client = TestClient(main.app)
    fixture = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "evidence_autopilot" / "real_case_v0.json")
        .read_text(encoding="utf-8")
    )
    undergrad_card = next(
        card
        for card in fixture["evidenceCards"]
        if card["taskId"] == "undergrad-access" and card["status"] == "captured_candidate"
    )

    submit = client.post(
        "/api/evidence-autopilot/reviewed-evidence",
        json={
            "targetLabel": real_case_target_label(fixture),
            "caseId": fixture["caseId"],
            "reviewer": "real-case-v0-source-log",
            "card": {
                "taskId": undergrad_card["taskId"],
                "claim": "undergrad_access",
                "status": "captured_candidate",
                "sourceTitle": undergrad_card["sourceTitle"],
                "sourceUrl": undergrad_card["sourceUrl"],
                "sourceType": undergrad_card["sourceType"],
                "excerpt": undergrad_card["excerpt"],
                "capturedAt": undergrad_card["capturedAt"],
                "confidence": undergrad_card["confidence"],
                "reviewAction": undergrad_card["reviewAction"],
                "attachments": [],
                "redactionStatus": "not_required",
            },
        },
    )
    assert submit.status_code == 200

    research = client.post(
        "/api/evidence-autopilot/research",
        json={
            "province": fixture["candidate"]["province"],
            "schoolName": fixture["target"]["schoolName"],
            "majorName": fixture["target"]["majorName"],
            "targetYear": fixture["candidate"]["targetYear"],
            "caseId": fixture["caseId"],
            "enableReviewedEvidenceLedger": True,
        },
    )
    assert research.status_code == 200
    coverage = research.json()["evidenceCoverage"]
    assert "undergrad-access" in coverage["capturedTaskIds"]
    assert "undergrad-access" not in coverage["missingP0TaskIds"]
    assert "Reviewed evidence cards accepted: undergrad-access." in research.json()["claimBoundary"]


def complete_redaction_checklist() -> dict:
    return {
        "studentPersonalInfoRemoved": True,
        "privateContactInfoRemoved": True,
        "accountIdentifiersRemoved": True,
        "thirdPartyPersonalInfoRemoved": True,
        "reviewerConfirmed": True,
        "notes": "Visible personal identifiers were checked before upload.",
    }


def real_case_target_label(fixture: dict) -> str:
    return (
        f"{fixture['candidate']['province']} {fixture['candidate']['targetYear']} "
        f"{fixture['target']['schoolName']} {fixture['target']['majorName']}"
    )

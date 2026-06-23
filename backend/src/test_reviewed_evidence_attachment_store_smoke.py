"""Smoke tests for reviewed-evidence attachment persistence."""

from __future__ import annotations

import base64
import json

from fastapi.testclient import TestClient

import main
from reviewed_evidence_attachment_store import save_reviewed_evidence_attachment


def test_save_reviewed_evidence_attachment_writes_binary_and_metadata(tmp_path) -> None:
    raw_bytes = b"fake screenshot bytes"

    saved = save_reviewed_evidence_attachment(
        storage_root=tmp_path,
        case_id="scut-im-v0",
        task_id="employment-market",
        reviewer_id="operator-a",
        kind="screenshot",
        content_type="image/png",
        content_base64=base64.b64encode(raw_bytes).decode("ascii"),
        captured_at="2026-06-24T00:00:00Z",
        redaction_status="redacted",
        original_file_name="job-sample.png",
    )

    assert saved.attachment.attachmentId.startswith("att-")
    assert saved.attachment.kind == "screenshot"
    assert saved.attachment.redactionStatus == "redacted"
    assert saved.attachment.storageRef.startswith("reviewed-evidence/scut-im-v0/")
    assert saved.byteSize == len(raw_bytes)
    assert len(saved.sha256) == 64

    stored_path = tmp_path / saved.attachment.storageRef
    metadata_path = stored_path.with_suffix(stored_path.suffix + ".json")
    assert stored_path.read_bytes() == raw_bytes
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["caseId"] == "scut-im-v0"
    assert metadata["taskId"] == "employment-market"
    assert metadata["reviewerId"] == "operator-a"
    assert metadata["sha256"] == saved.sha256
    assert metadata["redactionStatus"] == "redacted"


def test_reviewed_evidence_attachment_endpoint_persists_to_configured_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_AUTOPILOT_ATTACHMENT_DIR", str(tmp_path))
    client = TestClient(main.app)

    response = client.post(
        "/api/evidence-autopilot/reviewed-evidence/attachments",
        json={
            "caseId": "scut-im-v0",
            "taskId": "employment-market",
            "reviewerId": "operator-a",
            "kind": "screenshot",
            "contentType": "image/png",
            "contentBase64": base64.b64encode(b"endpoint screenshot").decode("ascii"),
            "capturedAt": "2026-06-24T00:00:00Z",
            "redactionStatus": "redacted",
            "originalFileName": "endpoint.png",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["attachment"]["attachmentId"].startswith("att-")
    assert payload["attachment"]["storageRef"].startswith("reviewed-evidence/scut-im-v0/")
    assert payload["attachment"]["redactionStatus"] == "redacted"
    assert payload["byteSize"] == len(b"endpoint screenshot")
    assert (tmp_path / payload["attachment"]["storageRef"]).is_file()
    assert (
        "/api/evidence-autopilot/reviewed-evidence/attachments"
        in main.get_runtime_status()["entrypoints"]["api"]
    )

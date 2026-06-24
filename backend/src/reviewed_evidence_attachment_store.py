"""Local file store for reviewed-evidence attachments."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel

from evidence_autopilot_api import (
    ReviewedEvidenceAttachment,
    ReviewedEvidenceAttachmentKind,
    ReviewedEvidenceRedactionStatus,
)


class SavedReviewedEvidenceAttachment(BaseModel):
    """Stored attachment plus audit metadata needed by reviewed evidence cards."""

    attachment: ReviewedEvidenceAttachment
    byteSize: int
    sha256: str
    metadataPath: str


def save_reviewed_evidence_attachment(
    *,
    storage_root: Path,
    case_id: str,
    task_id: str,
    reviewer_id: str,
    kind: ReviewedEvidenceAttachmentKind,
    content_type: str,
    content_base64: str,
    captured_at: str,
    redaction_status: ReviewedEvidenceRedactionStatus,
    original_file_name: str | None = None,
) -> SavedReviewedEvidenceAttachment:
    """Decode and persist one operator-reviewed attachment with sidecar metadata."""
    raw_bytes = _decode_base64(content_base64)
    attachment_id = _new_attachment_id()
    safe_case_id = _safe_path_segment(case_id)
    suffix = _suffix_for(content_type, original_file_name)
    storage_ref = f"reviewed-evidence/{safe_case_id}/{attachment_id}{suffix}"
    storage_path = storage_root / storage_ref
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(raw_bytes)

    digest = hashlib.sha256(raw_bytes).hexdigest()
    attachment = ReviewedEvidenceAttachment(
        attachmentId=attachment_id,
        kind=kind,
        storageRef=storage_ref,
        capturedAt=captured_at,
        redactionStatus=redaction_status,
    )
    metadata = {
        "attachmentId": attachment_id,
        "caseId": case_id,
        "taskId": task_id,
        "reviewerId": reviewer_id,
        "kind": kind,
        "contentType": content_type,
        "originalFileName": original_file_name or "",
        "byteSize": len(raw_bytes),
        "sha256": digest,
        "storageRef": storage_ref,
        "capturedAt": captured_at,
        "redactionStatus": redaction_status,
        "storedAt": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path = storage_path.with_suffix(storage_path.suffix + ".json")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    return SavedReviewedEvidenceAttachment(
        attachment=attachment,
        byteSize=len(raw_bytes),
        sha256=digest,
        metadataPath=str(metadata_path),
    )


def resolve_reviewed_evidence_attachment_path(
    *,
    storage_root: Path,
    storage_ref: str,
) -> Path:
    """Resolve an attachment storageRef inside the configured attachment root."""
    if not storage_ref.strip():
        raise ValueError("attachment storageRef is required")
    storage_root_resolved = storage_root.resolve()
    attachment_path = (storage_root_resolved / storage_ref).resolve()
    if not attachment_path.is_relative_to(storage_root_resolved):
        raise ValueError("attachment storageRef must stay inside the attachment store")
    return attachment_path


def reviewed_evidence_attachment_exists(
    *,
    storage_root: Path,
    storage_ref: str,
) -> bool:
    """Return whether a reviewed-evidence attachment file exists in the store."""
    return resolve_reviewed_evidence_attachment_path(
        storage_root=storage_root,
        storage_ref=storage_ref,
    ).is_file()


def validate_reviewed_evidence_attachment(
    *,
    storage_root: Path,
    attachment: ReviewedEvidenceAttachment,
) -> bool:
    """Validate a reviewed-evidence attachment against its stored metadata."""
    attachment_path = resolve_reviewed_evidence_attachment_path(
        storage_root=storage_root,
        storage_ref=attachment.storageRef,
    )
    if not attachment_path.is_file():
        raise ValueError(f"attachment storageRef not found: {attachment.storageRef}")

    metadata_path = attachment_path.with_suffix(attachment_path.suffix + ".json")
    if not metadata_path.is_file():
        raise ValueError(f"attachment metadata sidecar not found: {attachment.storageRef}")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"attachment metadata sidecar is invalid JSON: {attachment.storageRef}") from exc

    _require_metadata_match(metadata, "attachmentId", attachment.attachmentId, attachment.storageRef)
    _require_metadata_match(metadata, "storageRef", attachment.storageRef, attachment.storageRef)
    _require_metadata_match(metadata, "kind", attachment.kind, attachment.storageRef)
    _require_metadata_match(metadata, "capturedAt", attachment.capturedAt, attachment.storageRef)
    _require_metadata_match(metadata, "redactionStatus", attachment.redactionStatus, attachment.storageRef)

    recorded_sha256 = str(metadata.get("sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", recorded_sha256):
        raise ValueError(f"attachment sha256 metadata is invalid: {attachment.storageRef}")
    actual_sha256 = hashlib.sha256(attachment_path.read_bytes()).hexdigest()
    if recorded_sha256 != actual_sha256:
        raise ValueError(f"attachment sha256 mismatch: {attachment.storageRef}")
    return True


def _decode_base64(content_base64: str) -> bytes:
    try:
        raw_bytes = base64.b64decode(content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("contentBase64 must be valid base64") from exc
    if not raw_bytes:
        raise ValueError("attachment content must not be empty")
    return raw_bytes


def _new_attachment_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"att-{timestamp}-{uuid4().hex[:8]}"


def _safe_path_segment(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-")
    return cleaned[:80] or "case"


def _suffix_for(content_type: str, original_file_name: str | None) -> str:
    suffix = Path(original_file_name or "").suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".pdf"}:
        return suffix
    return {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
    }.get(content_type.lower().strip(), ".bin")


def _require_metadata_match(
    metadata: dict,
    field_name: str,
    expected: str,
    storage_ref: str,
) -> None:
    if str(metadata.get(field_name, "")) != str(expected):
        raise ValueError(f"attachment metadata {field_name} mismatch: {storage_ref}")

"""Durable JSONL ledger for human-reviewed Evidence Autopilot cards."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel

from evidence_autopilot_api import ReviewedEvidenceCard


class ReviewedEvidenceRecord(BaseModel):
    """One append-only reviewed-evidence ledger record."""

    reviewId: str
    targetLabel: str
    reviewedEvidenceCard: ReviewedEvidenceCard
    reviewer: str
    caseId: str | None
    recordedAt: str
    ledgerPath: str


def append_reviewed_evidence_record(
    *,
    ledger_path: Path,
    target_label: str,
    card: ReviewedEvidenceCard,
    reviewer: str,
    case_id: str | None = None,
) -> ReviewedEvidenceRecord:
    """Append one reviewed evidence card and return its generated review id."""
    review_id = _new_review_id()
    normalized_card = _with_operator_review_url(card, review_id)
    recorded_at = datetime.now(timezone.utc).isoformat()
    record = ReviewedEvidenceRecord(
        reviewId=review_id,
        targetLabel=target_label,
        reviewedEvidenceCard=normalized_card,
        reviewer=reviewer,
        caseId=case_id,
        recordedAt=recorded_at,
        ledgerPath=str(ledger_path),
    )
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.model_dump(), ensure_ascii=False, sort_keys=True))
        handle.write("\n")
    return record


def load_reviewed_evidence_cards(
    *,
    ledger_path: Path,
    case_id: str,
) -> list[ReviewedEvidenceCard]:
    """Load reviewed evidence cards for one case from the append-only ledger."""
    return [
        record.reviewedEvidenceCard
        for record in list_reviewed_evidence_records(
            ledger_path=ledger_path,
            case_id=case_id,
        )
    ]


def list_reviewed_evidence_records(
    *,
    ledger_path: Path,
    case_id: str,
) -> list[ReviewedEvidenceRecord]:
    """List full reviewed-evidence records for one case."""
    return [
        record
        for record in _iter_reviewed_evidence_records(ledger_path)
        if record.caseId == case_id
    ]


def _iter_reviewed_evidence_records(ledger_path: Path) -> list[ReviewedEvidenceRecord]:
    if not ledger_path.is_file():
        return []
    records: list[ReviewedEvidenceRecord] = []
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(ReviewedEvidenceRecord.model_validate_json(line))
        except ValueError:
            continue
    return records


def _new_review_id() -> str:
    return f"review-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"


def _with_operator_review_url(card: ReviewedEvidenceCard, review_id: str) -> ReviewedEvidenceCard:
    if card.sourceUrl.strip():
        return card
    return card.model_copy(update={"sourceUrl": f"operator-review://{review_id}"})

"""Evidence Autopilot backend bridge for auditable opportunity research."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from subgraphs.deep_research import build_evidence_autopilot_research_topics


EvidenceAutopilotChannel = Literal[
    "public_web",
    "official_pdf",
    "wechat_operator",
    "job_market_operator",
    "manual_review",
]
EvidenceAutopilotSourceType = Literal["official", "school", "paper", "job", "wechat", "discussion", "other"]
EvidenceAutopilotConfidence = Literal["high", "medium", "low"]
ReviewedEvidenceAttachmentKind = Literal["screenshot", "page_capture", "pdf", "image", "other"]
ReviewedEvidenceRedactionStatus = Literal["pending", "redacted", "not_required"]
ReviewedEvidenceReviewerRole = Literal["operator", "counselor", "qa_reviewer", "lead_counselor"]


class ReviewedEvidenceAttachment(BaseModel):
    """Attachment proof for semi-closed or operator-captured evidence."""

    attachmentId: str = Field(..., min_length=1)
    kind: ReviewedEvidenceAttachmentKind
    storageRef: str = Field(..., min_length=1)
    capturedAt: str = Field(..., min_length=1)
    redactionStatus: ReviewedEvidenceRedactionStatus = "pending"


class ReviewedEvidenceReviewerIdentity(BaseModel):
    """Reviewer identity used for operator-evidence accountability."""

    reviewerId: str = Field(..., min_length=1)
    displayName: str = Field(..., min_length=1)
    role: ReviewedEvidenceReviewerRole


class ReviewedEvidenceCard(BaseModel):
    """Human-reviewed evidence card submitted back into the research loop."""

    taskId: str
    claim: str
    status: Literal["captured_candidate"]
    sourceTitle: str
    sourceUrl: str
    sourceType: EvidenceAutopilotSourceType
    excerpt: str
    capturedAt: str
    confidence: EvidenceAutopilotConfidence
    reviewAction: str
    attachments: list[ReviewedEvidenceAttachment] = Field(default_factory=list)
    redactionStatus: ReviewedEvidenceRedactionStatus = "pending"
    reviewerIdentity: ReviewedEvidenceReviewerIdentity | None = None


class EvidenceAutopilotResearchRequest(BaseModel):
    """Candidate target for one Evidence Autopilot research run."""

    province: str = Field(..., min_length=1)
    schoolName: str = Field(..., min_length=1)
    majorName: str = Field(..., min_length=1)
    targetYear: int = Field(..., ge=2020, le=2100)
    caseId: str | None = None
    enableOfficialSourceProvider: bool = False
    enableReviewedEvidenceLedger: bool = False
    reviewedEvidenceCards: list[ReviewedEvidenceCard] = Field(default_factory=list)


class EvidenceAutopilotTask(BaseModel):
    """Search or operator task generated for one opportunity claim."""

    taskId: str
    claim: str
    title: str
    channel: EvidenceAutopilotChannel
    priority: Literal["P0", "P1", "P2"]
    query: str
    requiredFields: list[str]
    reviewAction: str


class EvidenceAutopilotEvidenceCard(BaseModel):
    """Evidence placeholder that preserves provenance requirements."""

    taskId: str
    claim: str
    status: Literal["requires_capture", "operator_review", "captured_candidate"]
    sourceTitle: str
    sourceUrl: str
    sourceType: EvidenceAutopilotSourceType
    excerpt: str
    capturedAt: str
    confidence: EvidenceAutopilotConfidence
    reviewAction: str


class EvidenceAutopilotCoverageSummary(BaseModel):
    """Machine-readable evidence gate summary for counselor review."""

    totalTasks: int
    capturedTaskIds: list[str]
    missingP0TaskIds: list[str]
    operatorTaskIds: list[str]
    readyForCounselorReview: bool
    reviewBlockers: list[str]


class EvidenceAutopilotResearchResponse(BaseModel):
    """Auditable Evidence Autopilot bridge response."""

    success: bool
    targetLabel: str
    tasks: list[EvidenceAutopilotTask]
    searchQueries: list[str]
    evidenceCards: list[EvidenceAutopilotEvidenceCard]
    evidenceCoverage: EvidenceAutopilotCoverageSummary
    claimBoundary: str


class ReviewedEvidenceSubmissionRequest(BaseModel):
    """Persist one human-reviewed evidence card into the operator ledger."""

    targetLabel: str = Field(..., min_length=1)
    card: ReviewedEvidenceCard
    reviewer: str = Field(..., min_length=1)
    caseId: str | None = None


class ReviewedEvidenceSubmissionResponse(BaseModel):
    """Append-only reviewed-evidence ledger response."""

    success: bool
    reviewId: str
    reviewedEvidenceCard: ReviewedEvidenceCard
    ledgerPath: str
    recordedAt: str


class ReviewedEvidenceListingResponse(BaseModel):
    """Case-scoped reviewed-evidence ledger listing."""

    success: bool
    caseId: str
    recordCount: int
    records: list


class ReviewedEvidenceAttachmentUploadRequest(BaseModel):
    """Upload one operator-reviewed evidence attachment into local storage."""

    caseId: str = Field(..., min_length=1)
    taskId: str = Field(..., min_length=1)
    reviewerId: str = Field(..., min_length=1)
    kind: ReviewedEvidenceAttachmentKind
    contentType: str = Field(..., min_length=1)
    contentBase64: str = Field(..., min_length=1)
    capturedAt: str = Field(..., min_length=1)
    redactionStatus: ReviewedEvidenceRedactionStatus
    originalFileName: str | None = None


class ReviewedEvidenceAttachmentUploadResponse(BaseModel):
    """Stored reviewed-evidence attachment response."""

    success: bool
    attachment: ReviewedEvidenceAttachment
    byteSize: int
    sha256: str
    metadataPath: str


class ReviewedEvidenceMergeResult(BaseModel):
    """Reviewed-card merge output with explicit accepted and rejected counts."""

    cards: list[EvidenceAutopilotEvidenceCard]
    acceptedTaskIds: list[str]
    rejectedCount: int


router = APIRouter(prefix="/api/evidence-autopilot", tags=["evidence-autopilot"])


CLAIM_BOUNDARY = (
    "Evidence Autopilot 后端只生成可审计研究任务、检索 query 和采集字段；"
    "没有 source URL、原文摘录、采集时间和置信度之前，不会承诺录取、升学或就业结果。"
    "微信、Boss 等半封闭渠道只生成合规人工采集任务。"
)


def build_evidence_autopilot_research_response(
    request: EvidenceAutopilotResearchRequest,
    official_source_provider=None,
    official_source_providers=None,
    reviewed_evidence_ledger_path: Path | None = None,
) -> EvidenceAutopilotResearchResponse:
    """Build the backend contract consumed by future frontend/live providers."""
    target_label = (
        f"{request.province} {request.targetYear} {request.schoolName} {request.majorName}"
    )
    raw_tasks = build_evidence_autopilot_research_topics(
        province=request.province,
        school_name=request.schoolName,
        major_name=request.majorName,
        target_year=request.targetYear,
    )
    tasks = [
        EvidenceAutopilotTask(
            taskId=str(task["id"]),
            claim=str(task["claim"]),
            title=str(task["title"]),
            channel=task["channel"],
            priority=task["priority"],
            query=str(task["query"]),
            requiredFields=list(task["required_fields"]),
            reviewAction=str(task["review_action"]),
        )
        for task in raw_tasks
    ]
    evidence_cards = [_build_empty_evidence_card(task) for task in tasks]
    provider_notes: list[str] = []
    if request.enableOfficialSourceProvider:
        from official_source_provider import (
            ScutOfficialAdmissionPlanProvider,
            ScutOfficialAdmissionScoreProvider,
            ScutOfficialMajorProfileProvider,
            capture_official_source_evidence,
        )

        providers = official_source_providers
        if providers is None:
            providers = [official_source_provider] if official_source_provider is not None else [
                ScutOfficialAdmissionPlanProvider(),
                ScutOfficialAdmissionScoreProvider(),
                ScutOfficialMajorProfileProvider(),
            ]
        capture_result = capture_official_source_evidence(request, providers)
        captured_cards = capture_result.cards
        if captured_cards:
            captured_by_task = {card.taskId: card for card in captured_cards}
            evidence_cards = [
                captured_by_task.get(card.taskId, card) for card in evidence_cards
            ]
            provider_notes.append(
                "Live official-source provider captured public evidence;"
                " score evidence remains historical context only."
            )
        provider_notes.extend(
            f"Official-source provider warning: {warning}"
            for warning in capture_result.warnings
        )

    ledger_cards = _load_reviewed_evidence_ledger_cards(
        request,
        reviewed_evidence_ledger_path,
    )
    if ledger_cards:
        request.reviewedEvidenceCards.extend(ledger_cards)
        provider_notes.append(
            "Reviewed evidence ledger merged: "
            f"{', '.join(card.taskId for card in ledger_cards)}."
        )

    reviewed_merge = _merge_reviewed_evidence_cards(
        tasks,
        evidence_cards,
        request.reviewedEvidenceCards,
    )
    evidence_cards = reviewed_merge.cards
    if reviewed_merge.acceptedTaskIds:
        provider_notes.append(
            "Reviewed evidence cards accepted: "
            f"{', '.join(reviewed_merge.acceptedTaskIds)}."
        )
    if reviewed_merge.rejectedCount:
        provider_notes.append(
            f"Rejected reviewed evidence cards: {reviewed_merge.rejectedCount}."
        )

    return EvidenceAutopilotResearchResponse(
        success=True,
        targetLabel=target_label,
        tasks=tasks,
        searchQueries=[task.query for task in tasks],
        evidenceCards=evidence_cards,
        evidenceCoverage=_build_evidence_coverage(tasks, evidence_cards),
        claimBoundary=f"{CLAIM_BOUNDARY}{' '.join(provider_notes)}",
    )


@router.post("/research", response_model=EvidenceAutopilotResearchResponse)
async def research_evidence_autopilot(
    request: EvidenceAutopilotResearchRequest,
) -> EvidenceAutopilotResearchResponse:
    """Return auditable research tasks for one target school-major opportunity."""
    return build_evidence_autopilot_research_response(request)


@router.post("/reviewed-evidence", response_model=ReviewedEvidenceSubmissionResponse)
async def submit_reviewed_evidence(
    request: ReviewedEvidenceSubmissionRequest,
) -> ReviewedEvidenceSubmissionResponse:
    """Persist one human-reviewed evidence card with a generated review id."""
    from reviewed_evidence_store import append_reviewed_evidence_record

    record = append_reviewed_evidence_record(
        ledger_path=_reviewed_evidence_ledger_path(),
        target_label=request.targetLabel,
        card=request.card,
        reviewer=request.reviewer,
        case_id=request.caseId,
    )
    return ReviewedEvidenceSubmissionResponse(
        success=True,
        reviewId=record.reviewId,
        reviewedEvidenceCard=record.reviewedEvidenceCard,
        ledgerPath=record.ledgerPath,
        recordedAt=record.recordedAt,
    )


@router.get("/reviewed-evidence/{case_id}", response_model=ReviewedEvidenceListingResponse)
async def list_reviewed_evidence(
    case_id: str,
) -> ReviewedEvidenceListingResponse:
    """List reviewed evidence records for one case id."""
    from reviewed_evidence_store import list_reviewed_evidence_records

    records = list_reviewed_evidence_records(
        ledger_path=_reviewed_evidence_ledger_path(),
        case_id=case_id,
    )
    return ReviewedEvidenceListingResponse(
        success=True,
        caseId=case_id,
        recordCount=len(records),
        records=[record.model_dump() for record in records],
    )


@router.post(
    "/reviewed-evidence/attachments",
    response_model=ReviewedEvidenceAttachmentUploadResponse,
)
async def upload_reviewed_evidence_attachment(
    request: ReviewedEvidenceAttachmentUploadRequest,
) -> ReviewedEvidenceAttachmentUploadResponse:
    """Persist one binary attachment for operator-reviewed evidence."""
    from reviewed_evidence_attachment_store import save_reviewed_evidence_attachment

    try:
        saved = save_reviewed_evidence_attachment(
            storage_root=_reviewed_evidence_attachment_dir(),
            case_id=request.caseId,
            task_id=request.taskId,
            reviewer_id=request.reviewerId,
            kind=request.kind,
            content_type=request.contentType,
            content_base64=request.contentBase64,
            captured_at=request.capturedAt,
            redaction_status=request.redactionStatus,
            original_file_name=request.originalFileName,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReviewedEvidenceAttachmentUploadResponse(success=True, **saved.model_dump())


def _reviewed_evidence_ledger_path() -> Path:
    configured = os.getenv("EVIDENCE_AUTOPILOT_REVIEWED_LEDGER", "").strip()
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / "logs" / "evidence_autopilot" / "reviewed_evidence.jsonl"


def _reviewed_evidence_attachment_dir() -> Path:
    configured = os.getenv("EVIDENCE_AUTOPILOT_ATTACHMENT_DIR", "").strip()
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / "logs" / "evidence_autopilot" / "attachments"


def _load_reviewed_evidence_ledger_cards(
    request: EvidenceAutopilotResearchRequest,
    ledger_path: Path | None,
) -> list[ReviewedEvidenceCard]:
    if not request.enableReviewedEvidenceLedger or not request.caseId:
        return []
    from reviewed_evidence_store import load_reviewed_evidence_cards

    return load_reviewed_evidence_cards(
        ledger_path=ledger_path or _reviewed_evidence_ledger_path(),
        case_id=request.caseId,
    )


def _build_empty_evidence_card(task: EvidenceAutopilotTask) -> EvidenceAutopilotEvidenceCard:
    operator_only = task.channel in {"wechat_operator", "job_market_operator", "manual_review"}
    return EvidenceAutopilotEvidenceCard(
        taskId=task.taskId,
        claim=task.claim,
        status="operator_review" if operator_only else "requires_capture",
        sourceTitle=f"{task.title}：待采集",
        sourceUrl="",
        sourceType=_source_type_for_task(task),
        excerpt="",
        capturedAt="",
        confidence="low",
        reviewAction=task.reviewAction,
    )


def _merge_reviewed_evidence_cards(
    tasks: list[EvidenceAutopilotTask],
    evidence_cards: list[EvidenceAutopilotEvidenceCard],
    reviewed_cards: list[ReviewedEvidenceCard],
) -> ReviewedEvidenceMergeResult:
    task_by_id = {task.taskId: task for task in tasks}
    merged_by_task = {card.taskId: card for card in evidence_cards}
    accepted_task_ids: list[str] = []
    rejected_count = 0

    for reviewed in reviewed_cards:
        task = task_by_id.get(reviewed.taskId)
        if task is None or task.claim != reviewed.claim or not _is_complete_reviewed_card(reviewed):
            rejected_count += 1
            continue
        merged_by_task[reviewed.taskId] = EvidenceAutopilotEvidenceCard(
            taskId=reviewed.taskId,
            claim=reviewed.claim,
            status=reviewed.status,
            sourceTitle=reviewed.sourceTitle,
            sourceUrl=reviewed.sourceUrl,
            sourceType=reviewed.sourceType,
            excerpt=reviewed.excerpt,
            capturedAt=reviewed.capturedAt,
            confidence=reviewed.confidence,
            reviewAction=reviewed.reviewAction,
        )
        accepted_task_ids.append(reviewed.taskId)

    return ReviewedEvidenceMergeResult(
        cards=[merged_by_task[task.taskId] for task in tasks],
        acceptedTaskIds=accepted_task_ids,
        rejectedCount=rejected_count,
    )


def _is_complete_reviewed_card(card: ReviewedEvidenceCard) -> bool:
    text_complete = all(
        value.strip()
        for value in [
            card.sourceTitle,
            card.sourceUrl,
            card.excerpt,
            card.capturedAt,
            card.reviewAction,
        ]
    )
    if not text_complete:
        return False
    if not card.sourceUrl.startswith("operator-review://"):
        return True
    return _has_operator_review_controls(card)


def _has_operator_review_controls(card: ReviewedEvidenceCard) -> bool:
    if card.reviewerIdentity is None:
        return False
    if card.redactionStatus not in {"redacted", "not_required"}:
        return False
    return any(
        attachment.redactionStatus in {"redacted", "not_required"}
        and attachment.storageRef.strip()
        and attachment.attachmentId.strip()
        for attachment in card.attachments
    )


def _build_evidence_coverage(
    tasks: list[EvidenceAutopilotTask],
    evidence_cards: list[EvidenceAutopilotEvidenceCard],
) -> EvidenceAutopilotCoverageSummary:
    captured_task_ids = {
        card.taskId
        for card in evidence_cards
        if card.status == "captured_candidate" and card.sourceUrl and card.excerpt
    }
    ordered_captured_task_ids = [
        task.taskId for task in tasks if task.taskId in captured_task_ids
    ]
    missing_p0_task_ids = [
        task.taskId
        for task in tasks
        if task.priority == "P0" and task.taskId not in captured_task_ids
    ]
    operator_task_ids = [
        task.taskId
        for task in tasks
        if task.channel in {"wechat_operator", "job_market_operator", "manual_review"}
    ]
    review_blockers = []
    if missing_p0_task_ids:
        review_blockers.append(
            f"Missing captured P0 evidence: {', '.join(missing_p0_task_ids)}"
        )
    return EvidenceAutopilotCoverageSummary(
        totalTasks=len(tasks),
        capturedTaskIds=ordered_captured_task_ids,
        missingP0TaskIds=missing_p0_task_ids,
        operatorTaskIds=operator_task_ids,
        readyForCounselorReview=not missing_p0_task_ids,
        reviewBlockers=review_blockers,
    )


def _source_type_for_task(
    task: EvidenceAutopilotTask,
) -> Literal["official", "school", "paper", "job", "wechat", "discussion", "other"]:
    if task.channel == "official_pdf":
        return "official"
    if task.channel == "job_market_operator":
        return "job"
    if task.channel == "wechat_operator":
        return "wechat"
    if task.claim == "counter_evidence":
        return "discussion"
    if task.claim == "faculty_research":
        return "school"
    return "other"

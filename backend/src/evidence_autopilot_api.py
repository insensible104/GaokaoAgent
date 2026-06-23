"""Evidence Autopilot backend bridge for auditable opportunity research."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
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


class EvidenceAutopilotResearchRequest(BaseModel):
    """Candidate target for one Evidence Autopilot research run."""

    province: str = Field(..., min_length=1)
    schoolName: str = Field(..., min_length=1)
    majorName: str = Field(..., min_length=1)
    targetYear: int = Field(..., ge=2020, le=2100)
    enableOfficialSourceProvider: bool = False
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
    return all(
        value.strip()
        for value in [
            card.sourceTitle,
            card.sourceUrl,
            card.excerpt,
            card.capturedAt,
            card.reviewAction,
        ]
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

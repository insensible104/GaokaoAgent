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


class EvidenceAutopilotResearchRequest(BaseModel):
    """Candidate target for one Evidence Autopilot research run."""

    province: str = Field(..., min_length=1)
    schoolName: str = Field(..., min_length=1)
    majorName: str = Field(..., min_length=1)
    targetYear: int = Field(..., ge=2020, le=2100)
    enableOfficialSourceProvider: bool = False


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
    sourceType: Literal["official", "school", "paper", "job", "wechat", "discussion", "other"]
    excerpt: str
    capturedAt: str
    confidence: Literal["high", "medium", "low"]
    reviewAction: str


class EvidenceAutopilotResearchResponse(BaseModel):
    """Auditable Evidence Autopilot bridge response."""

    success: bool
    targetLabel: str
    tasks: list[EvidenceAutopilotTask]
    searchQueries: list[str]
    evidenceCards: list[EvidenceAutopilotEvidenceCard]
    claimBoundary: str


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
            capture_official_source_evidence,
        )

        providers = official_source_providers
        if providers is None:
            providers = [official_source_provider] if official_source_provider is not None else [
                ScutOfficialAdmissionPlanProvider(),
                ScutOfficialAdmissionScoreProvider()
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

    return EvidenceAutopilotResearchResponse(
        success=True,
        targetLabel=target_label,
        tasks=tasks,
        searchQueries=[task.query for task in tasks],
        evidenceCards=evidence_cards,
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

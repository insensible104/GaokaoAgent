import type {
  BackendEvidenceCard,
  ReviewedEvidenceSubmissionPayload,
} from "./evidenceAutopilotApi";
import type {
  EvidenceAutopilotRealCaseCard,
  EvidenceAutopilotRealCaseFixture,
} from "./evidenceAutopilotRealCaseProvider";

const REAL_CASE_REVIEWER = "real-case-v0-source-log";

const CANONICAL_CLAIM_BY_TASK_ID: Record<string, string> = {
  "official-plan-charter": "official_admission",
  "rank-history-band": "rank_history",
  "faculty-research-direction": "faculty_research",
  "undergrad-access": "undergrad_access",
  "graduate-progression": "graduate_progression",
  "civil-service-path": "civil_service_path",
  "counter-evidence": "counter_evidence",
  "employment-market": "employment_market",
  "wechat-public-account": "wechat_public_account",
};

export function buildRealCaseReviewedEvidenceSubmissions({
  fixture,
  caseId,
}: {
  fixture: EvidenceAutopilotRealCaseFixture;
  caseId: string;
}): ReviewedEvidenceSubmissionPayload[] {
  if (!caseId.trim()) {
    throw new Error("real case reviewed evidence submissions require caseId");
  }
  const targetLabel = `${fixture.candidate.province} ${fixture.candidate.targetYear} ${fixture.target.schoolName} ${fixture.target.majorName}`;
  return fixture.evidenceCards
    .filter(isCapturedPublicCard)
    .filter((card) => Boolean(CANONICAL_CLAIM_BY_TASK_ID[card.taskId]))
    .map((card) => ({
      targetLabel,
      caseId,
      reviewer: REAL_CASE_REVIEWER,
      card: toReviewedEvidenceCard(card),
    }));
}

function isCapturedPublicCard(card: EvidenceAutopilotRealCaseCard): boolean {
  return (
    card.status === "captured_candidate"
    && Boolean(card.sourceTitle.trim())
    && /^https?:\/\//.test(card.sourceUrl)
    && Boolean(card.excerpt.trim())
    && Boolean(card.capturedAt.trim())
    && Boolean(card.reviewAction.trim())
  );
}

function toReviewedEvidenceCard(card: EvidenceAutopilotRealCaseCard): BackendEvidenceCard {
  return {
    taskId: card.taskId,
    claim: CANONICAL_CLAIM_BY_TASK_ID[card.taskId],
    status: "captured_candidate",
    sourceTitle: card.sourceTitle,
    sourceUrl: card.sourceUrl,
    sourceType: card.sourceType,
    excerpt: card.excerpt,
    capturedAt: card.capturedAt,
    confidence: card.confidence,
    reviewAction: card.reviewAction,
    attachments: [],
    redactionStatus: "not_required",
  };
}

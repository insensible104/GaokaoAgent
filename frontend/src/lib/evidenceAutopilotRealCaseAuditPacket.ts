import type { EvidenceAutopilotRealCaseFixture } from "./evidenceAutopilotRealCaseProvider";
import type { RealCaseReviewedEvidenceLedgerBootstrapResult } from "./evidenceAutopilotRealCaseLedgerBootstrap";
import type {
  ReviewedEvidenceTaskGroup,
} from "./reviewedEvidenceCaseBrowser";

export type RealCaseOpportunityAuditStatus =
  | "blocked_by_p0_gaps"
  | "requires_counter_evidence_review"
  | "ready_for_counselor_review";

export interface RealCaseSupportedClaim {
  taskId: string;
  claim: string;
  title: string;
  priority: string;
  sourceCount: number;
  sourceTitles: string[];
  excerpts: string[];
  reviewActions: string[];
}

export interface RealCaseBlockingGap {
  taskId: string;
  claim: string;
  title: string;
  priority: string;
  reason: string;
}

export interface RealCaseCounterEvidenceReview {
  requiresCounselorReview: boolean;
  records: Array<{
    taskId: string;
    sourceTitle: string;
    sourceId: string;
    excerpt: string;
    reviewAction: string;
  }>;
}

export interface RealCaseOpportunityAuditPacket {
  protocol: "real_case_opportunity_audit_packet_v1";
  caseId: string;
  targetLabel: string;
  opportunityHypothesis: string;
  status: RealCaseOpportunityAuditStatus;
  metrics: {
    submitted: number;
    ledgerRecords: number;
    readyForReport: number;
    missingP0: number;
  };
  missingP0TaskIds: string[];
  supportedClaims: RealCaseSupportedClaim[];
  blockingGaps: RealCaseBlockingGap[];
  counterEvidence: RealCaseCounterEvidenceReview;
  nextActions: string[];
  claimBoundary: string;
}

export function buildRealCaseOpportunityAuditPacket({
  fixture,
  bootstrap,
}: {
  fixture: EvidenceAutopilotRealCaseFixture;
  bootstrap: RealCaseReviewedEvidenceLedgerBootstrapResult;
}): RealCaseOpportunityAuditPacket {
  if (fixture.caseId !== bootstrap.caseId) {
    throw new Error("real case audit packet requires matching caseId");
  }
  const browser = bootstrap.browser;
  const supportedClaims = browser.taskGroups
    .filter((group) => group.status === "ready_for_report")
    .map(toSupportedClaim);
  const blockingGaps = browser.taskGroups
    .filter((group) => browser.missingP0TaskIds.includes(group.taskId))
    .map(toBlockingGap);
  const counterEvidence = buildCounterEvidenceReview(browser.taskGroups);
  const status = statusFor(browser.missingP0TaskIds, counterEvidence.requiresCounselorReview);

  return {
    protocol: "real_case_opportunity_audit_packet_v1",
    caseId: fixture.caseId,
    targetLabel: `${fixture.candidate.province} ${fixture.candidate.targetYear} ${fixture.target.schoolName} ${fixture.target.majorName}`,
    opportunityHypothesis: fixture.opportunityHypothesis,
    status,
    metrics: {
      submitted: bootstrap.submittedCount,
      ledgerRecords: bootstrap.recordCount,
      readyForReport: browser.readyForReportCount,
      missingP0: browser.missingP0TaskIds.length,
    },
    missingP0TaskIds: browser.missingP0TaskIds,
    supportedClaims,
    blockingGaps,
    counterEvidence,
    nextActions: nextActionsFor(browser.missingP0TaskIds, counterEvidence.requiresCounselorReview),
    claimBoundary:
      "Real Case opportunity audit packet summarizes case-scoped reviewed evidence readiness only; it does not prove admission probability, does not prove employment outcomes, and does not replace counselor review or source freshness checks.",
  };
}

function toSupportedClaim(group: ReviewedEvidenceTaskGroup): RealCaseSupportedClaim {
  const readyRecords = group.records.filter((record) => record.readyForReport);
  return {
    taskId: group.taskId,
    claim: group.claim,
    title: group.title,
    priority: group.priority,
    sourceCount: readyRecords.length,
    sourceTitles: unique(readyRecords.map((record) => record.sourceTitle)),
    excerpts: readyRecords.map((record) => record.excerpt),
    reviewActions: unique(readyRecords.map((record) => record.reviewAction)),
  };
}

function toBlockingGap(group: ReviewedEvidenceTaskGroup): RealCaseBlockingGap {
  return {
    taskId: group.taskId,
    claim: group.claim,
    title: group.title,
    priority: group.priority,
    reason: reasonForGap(group),
  };
}

function reasonForGap(group: ReviewedEvidenceTaskGroup): string {
  if (group.claim === "employment_market") {
    return "Missing compliant operator-captured job-market evidence with source proof, excerpt, and reviewed attachment audit.";
  }
  if (group.records.length > 0) {
    return group.records.map((record) => record.attachmentAuditDetail).join("; ");
  }
  return "No ready reviewed-evidence record exists for this P0 task.";
}

function buildCounterEvidenceReview(
  taskGroups: ReviewedEvidenceTaskGroup[],
): RealCaseCounterEvidenceReview {
  const records = taskGroups
    .filter((group) => group.claim === "counter_evidence")
    .flatMap((group) => group.records.filter((record) => record.readyForReport))
    .map((record) => ({
      taskId: record.taskId,
      sourceTitle: record.sourceTitle,
      sourceId: record.sourceId,
      excerpt: record.excerpt,
      reviewAction: record.reviewAction,
    }));
  return {
    requiresCounselorReview: records.length > 0,
    records,
  };
}

function statusFor(
  missingP0TaskIds: string[],
  counterEvidenceRequiresReview: boolean,
): RealCaseOpportunityAuditStatus {
  if (missingP0TaskIds.length > 0) return "blocked_by_p0_gaps";
  if (counterEvidenceRequiresReview) return "requires_counter_evidence_review";
  return "ready_for_counselor_review";
}

function nextActionsFor(
  missingP0TaskIds: string[],
  counterEvidenceRequiresReview: boolean,
): string[] {
  const actions: string[] = [];
  for (const taskId of missingP0TaskIds) {
    if (taskId === "employment-market") {
      actions.push("Capture employment-market operator evidence with screenshot/PDF/page proof before report use.");
    } else {
      actions.push(`Resolve missing P0 evidence before report use: ${taskId}.`);
    }
  }
  if (counterEvidenceRequiresReview) {
    actions.push("Review counter-evidence with a counselor before any family-facing opportunity wording.");
  }
  if (actions.length === 0) {
    actions.push("Proceed to counselor review while preserving source freshness and claim-boundary checks.");
  }
  return actions;
}

function unique(values: string[]): string[] {
  return [...new Set(values.filter((value) => value.trim()))];
}

import type { ReviewedEvidenceTaskGroupStatus } from "./reviewedEvidenceCaseBrowser";

export type ReviewerPanelTone = "blocked" | "needs_review" | "ready";

export interface ReviewedEvidenceCaseBrowserPanelSummaryInput {
  caseId: string;
  capturedCount: number;
  readyForReportCount: number;
  pendingCount: number;
  missingP0TaskIds: string[];
  counterEvidenceHit: boolean;
  reviewRequired: boolean;
  claimBoundary: string;
  taskGroups: Array<{
    taskId: string;
    status: ReviewedEvidenceTaskGroupStatus;
    records: unknown[];
  }>;
}

export interface ReviewedEvidenceCaseBrowserPanelSummary {
  caseId: string;
  tone: ReviewerPanelTone;
  primaryAction: string;
  metrics: {
    captured: number;
    readyForReport: number;
    pending: number;
    missingP0: number;
  };
  readyTaskCount: number;
  needsCaptureTaskCount: number;
  reviewRequired: boolean;
  claimBoundary: string;
}

export function buildReviewedEvidenceCaseBrowserPanelSummary(
  view: ReviewedEvidenceCaseBrowserPanelSummaryInput,
): ReviewedEvidenceCaseBrowserPanelSummary {
  const tone = toneFor(view);
  return {
    caseId: view.caseId,
    tone,
    primaryAction: primaryActionFor(view, tone),
    metrics: {
      captured: view.capturedCount,
      readyForReport: view.readyForReportCount,
      pending: view.pendingCount,
      missingP0: view.missingP0TaskIds.length,
    },
    readyTaskCount: view.taskGroups.filter((group) => group.status === "ready_for_report").length,
    needsCaptureTaskCount: view.taskGroups.filter((group) => group.status === "needs_capture").length,
    reviewRequired: view.reviewRequired,
    claimBoundary: view.claimBoundary,
  };
}

function toneFor(view: ReviewedEvidenceCaseBrowserPanelSummaryInput): ReviewerPanelTone {
  if (view.missingP0TaskIds.length > 0 || view.counterEvidenceHit) return "blocked";
  if (view.pendingCount > 0 || view.reviewRequired) return "needs_review";
  return "ready";
}

function primaryActionFor(
  view: ReviewedEvidenceCaseBrowserPanelSummaryInput,
  tone: ReviewerPanelTone,
): string {
  if (view.counterEvidenceHit) return "Review counter-evidence before counselor signoff.";
  if (view.missingP0TaskIds.length > 0) return "Capture missing P0 evidence before counselor signoff.";
  if (tone === "needs_review") return "Complete pending evidence capture before report use.";
  return "Evidence package can enter report review.";
}

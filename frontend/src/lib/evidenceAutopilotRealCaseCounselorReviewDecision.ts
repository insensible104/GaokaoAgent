import type { RealCaseOperatorClosureDeliveryPreviewResult } from "./evidenceAutopilotRealCaseOperatorClosureDeliveryPreview";

export type RealCaseCounselorDecision =
  | "reject"
  | "needs_more_evidence"
  | "allow_internal_report_draft";

export interface RealCaseCounselorReviewer {
  reviewerId: string;
  displayName: string;
  role: "senior_counselor" | "counselor" | string;
}

export interface RealCaseCounselorReviewDecisionInput {
  closurePreview: RealCaseOperatorClosureDeliveryPreviewResult;
  reviewer: RealCaseCounselorReviewer;
  decision: RealCaseCounselorDecision;
  reasons: string[];
  reviewedCounterEvidenceSourceIds: string[];
  sourceFreshnessChecked: boolean;
  representativenessChecked: boolean;
  claimBoundaryConfirmed: boolean;
}

export interface RealCaseCounselorReviewDecisionResult {
  protocol: "real_case_counselor_review_decision_v1";
  caseId: string;
  reviewer: RealCaseCounselorReviewer;
  decision: RealCaseCounselorDecision;
  reasons: string[];
  reviewedCounterEvidenceSourceIds: string[];
  sourceFreshnessChecked: boolean;
  representativenessChecked: boolean;
  claimBoundaryConfirmed: boolean;
  internalReportDraftAllowed: boolean;
  clientDeliveryAllowed: false;
  familyFacingAllowed: false;
  statusReason: string;
  requiredNextActions: string[];
  claimBoundary: string;
}

export function buildRealCaseCounselorReviewDecision({
  closurePreview,
  reviewer,
  decision,
  reasons,
  reviewedCounterEvidenceSourceIds,
  sourceFreshnessChecked,
  representativenessChecked,
  claimBoundaryConfirmed,
}: RealCaseCounselorReviewDecisionInput): RealCaseCounselorReviewDecisionResult {
  validateClosurePreview(closurePreview);
  validateDecisionInput({
    decision,
    reasons,
    reviewedCounterEvidenceSourceIds,
    sourceFreshnessChecked,
    representativenessChecked,
    claimBoundaryConfirmed,
    requiredCounterEvidenceSourceIds: requiredCounterEvidenceSourceIds(closurePreview),
  });

  const internalReportDraftAllowed = decision === "allow_internal_report_draft";

  return {
    protocol: "real_case_counselor_review_decision_v1",
    caseId: closurePreview.caseId,
    reviewer,
    decision,
    reasons,
    reviewedCounterEvidenceSourceIds,
    sourceFreshnessChecked,
    representativenessChecked,
    claimBoundaryConfirmed,
    internalReportDraftAllowed,
    clientDeliveryAllowed: false,
    familyFacingAllowed: false,
    statusReason: statusReasonFor(decision),
    requiredNextActions: requiredNextActionsFor({
      decision,
      sourceFreshnessChecked,
      representativenessChecked,
      claimBoundaryConfirmed,
    }),
    claimBoundary:
      "Real Case counselor review decision is an internal signoff gate only; it does not prove admission probability, does not prove employment outcomes, and does not authorize family-facing or client delivery.",
  };
}

function validateClosurePreview(closurePreview: RealCaseOperatorClosureDeliveryPreviewResult): void {
  if (closurePreview.protocol !== "real_case_operator_closure_delivery_preview_v1") {
    throw new Error("real case counselor review decision requires operator closure delivery preview");
  }
  if (closurePreview.workflow.closureReview.browser.missingP0TaskIds.length > 0) {
    throw new Error("real case counselor review decision requires P0 gaps to be closed first");
  }
  if (closurePreview.preview.manifest.client_delivery.allowed) {
    throw new Error("real case counselor review decision requires client delivery to remain blocked");
  }
}

function validateDecisionInput({
  decision,
  reasons,
  reviewedCounterEvidenceSourceIds,
  sourceFreshnessChecked,
  representativenessChecked,
  claimBoundaryConfirmed,
  requiredCounterEvidenceSourceIds,
}: {
  decision: RealCaseCounselorDecision;
  reasons: string[];
  reviewedCounterEvidenceSourceIds: string[];
  sourceFreshnessChecked: boolean;
  representativenessChecked: boolean;
  claimBoundaryConfirmed: boolean;
  requiredCounterEvidenceSourceIds: string[];
}): void {
  if (reasons.length === 0 || reasons.some((reason) => !reason.trim())) {
    throw new Error("real case counselor review decision requires reasons");
  }
  if (decision !== "reject" && !claimBoundaryConfirmed) {
    throw new Error("real case counselor review decision requires claim boundary confirmation");
  }
  if (decision === "allow_internal_report_draft") {
    const missingCounterEvidence = requiredCounterEvidenceSourceIds.filter(
      (sourceId) => !reviewedCounterEvidenceSourceIds.includes(sourceId),
    );
    if (missingCounterEvidence.length > 0) {
      throw new Error(`counter-evidence review is incomplete: ${missingCounterEvidence.join(", ")}`);
    }
    if (!sourceFreshnessChecked) {
      throw new Error("source freshness check is required before internal report draft");
    }
    if (!representativenessChecked) {
      throw new Error("source representativeness check is required before internal report draft");
    }
  }
}

function requiredCounterEvidenceSourceIds(
  closurePreview: RealCaseOperatorClosureDeliveryPreviewResult,
): string[] {
  return closurePreview.workflow.closureReview.auditPacket.counterEvidence.records.map(
    (record) => record.sourceId,
  );
}

function statusReasonFor(decision: RealCaseCounselorDecision): string {
  if (decision === "reject") {
    return "reject: counselor determined the opportunity hypothesis should not proceed.";
  }
  if (decision === "needs_more_evidence") {
    return "needs_more_evidence: counselor requires additional evidence before internal report drafting.";
  }
  return "allow_internal_report_draft: counselor allows internal drafting only, with client delivery still blocked.";
}

function requiredNextActionsFor({
  decision,
  sourceFreshnessChecked,
  representativenessChecked,
  claimBoundaryConfirmed,
}: {
  decision: RealCaseCounselorDecision;
  sourceFreshnessChecked: boolean;
  representativenessChecked: boolean;
  claimBoundaryConfirmed: boolean;
}): string[] {
  if (decision === "reject") {
    return ["Stop the opportunity case and record why it failed counselor review."];
  }
  if (decision === "allow_internal_report_draft") {
    return ["Draft internal report language with counter-evidence caveats; keep client delivery blocked."];
  }

  const actions: string[] = [];
  if (!sourceFreshnessChecked) {
    actions.push("Collect fresher source evidence before internal report drafting.");
  }
  if (!representativenessChecked) {
    actions.push("Collect stronger evidence for source representativeness before internal report drafting.");
  }
  if (!claimBoundaryConfirmed) {
    actions.push("Confirm claim boundaries before internal report drafting.");
  }
  return actions.length > 0
    ? actions
    : ["Collect additional counselor-specified evidence before internal report drafting."];
}

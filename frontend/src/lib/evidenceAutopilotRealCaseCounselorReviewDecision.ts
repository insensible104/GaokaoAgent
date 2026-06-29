import type {
  RealCaseOperatorClosureDeliveryArtifact,
  RealCaseOperatorClosureDeliveryPreviewResult,
} from "./evidenceAutopilotRealCaseOperatorClosureDeliveryPreview";

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

export interface RealCaseCounselorDecisionDeliveryPreviewInput {
  closurePreview: RealCaseOperatorClosureDeliveryPreviewResult;
  counselorDecision: RealCaseCounselorReviewDecisionResult;
}

export type RealCaseCounselorDecisionDeliveryArtifact =
  | RealCaseOperatorClosureDeliveryArtifact
  | {
      id: "real_case_counselor_decision_brief" | "real_case_counselor_decision_json";
      label: string;
      path: string;
      required: true;
      audience: "internal_review";
    };

export interface RealCaseCounselorDecisionDeliveryPreview {
  success: true;
  message: string;
  case_id: string;
  output_dir: string;
  manifest: {
    case_id: string;
    status: "counselor_decision_recorded";
    client_delivery: {
      allowed: false;
      status: "blocked";
      artifact_audiences: ["client_confirmation", "client_final"];
      blocked_reason: string;
    };
    artifacts: RealCaseCounselorDecisionDeliveryArtifact[];
    delivery_gates: Array<{
      gate: string;
      status: string;
      requirement: string;
    }>;
    next_actions: string[];
  };
  artifacts: Record<RealCaseCounselorDecisionDeliveryArtifact["id"], string>;
}

export interface RealCaseCounselorDecisionDeliveryPreviewResult {
  protocol: "real_case_counselor_decision_delivery_preview_v1";
  caseId: string;
  closurePreview: RealCaseOperatorClosureDeliveryPreviewResult;
  counselorDecision: RealCaseCounselorReviewDecisionResult;
  preview: RealCaseCounselorDecisionDeliveryPreview;
  clientFacingArtifacts: Array<[string, string]>;
  claimBoundary: string;
}

const CLIENT_FACING_AUDIENCES = new Set(["client_confirmation", "client_final"]);

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

export function buildRealCaseCounselorDecisionDeliveryPreview({
  closurePreview,
  counselorDecision,
}: RealCaseCounselorDecisionDeliveryPreviewInput): RealCaseCounselorDecisionDeliveryPreviewResult {
  validateClosurePreview(closurePreview);
  validateCounselorDecisionForPreview(closurePreview, counselorDecision);

  const preview = buildCounselorDecisionPreview({ closurePreview, counselorDecision });

  return {
    protocol: "real_case_counselor_decision_delivery_preview_v1",
    caseId: closurePreview.caseId,
    closurePreview,
    counselorDecision,
    preview,
    clientFacingArtifacts: listRealCaseCounselorDecisionClientFacingArtifacts(preview),
    claimBoundary:
      "Real Case counselor decision delivery preview is internal only; it does not prove admission probability, does not prove employment outcomes, and does not authorize client or family-facing delivery.",
  };
}

export function listRealCaseCounselorDecisionClientFacingArtifacts(
  preview: RealCaseCounselorDecisionDeliveryPreview,
): Array<[string, string]> {
  const audienceById = new Map(
    preview.manifest.artifacts.map((artifact) => [artifact.id, artifact.audience]),
  );
  return Object.entries(preview.artifacts).filter(([id]) => {
    const audience = audienceById.get(id as RealCaseCounselorDecisionDeliveryArtifact["id"]);
    return audience ? CLIENT_FACING_AUDIENCES.has(audience) : false;
  });
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

function validateCounselorDecisionForPreview(
  closurePreview: RealCaseOperatorClosureDeliveryPreviewResult,
  counselorDecision: RealCaseCounselorReviewDecisionResult,
): void {
  if (counselorDecision.protocol !== "real_case_counselor_review_decision_v1") {
    throw new Error("real case counselor decision delivery preview requires counselor review decision");
  }
  if (counselorDecision.caseId !== closurePreview.caseId) {
    throw new Error(
      `real case counselor decision delivery preview caseId mismatch: ${counselorDecision.caseId} != ${closurePreview.caseId}`,
    );
  }
  if (counselorDecision.clientDeliveryAllowed || counselorDecision.familyFacingAllowed) {
    throw new Error("real case counselor decision delivery preview requires client and family delivery to remain blocked");
  }
}

function buildCounselorDecisionPreview({
  closurePreview,
  counselorDecision,
}: RealCaseCounselorDecisionDeliveryPreviewInput): RealCaseCounselorDecisionDeliveryPreview {
  const originalPreview = closurePreview.preview;
  const blockedReason = `${counselorDecision.decision}: client delivery remains blocked after counselor decision; ${counselorDecision.statusReason}`;
  const counselorBrief = renderCounselorDecisionBrief({ closurePreview, counselorDecision });
  const counselorJson = JSON.stringify(
    {
      counselorDecision,
      reviewedCounterEvidenceRecords: counterEvidenceRecordsFor(closurePreview, counselorDecision),
    },
    null,
    2,
  );
  const counselorArtifacts: RealCaseCounselorDecisionDeliveryArtifact[] = [
    {
      id: "real_case_counselor_decision_brief",
      label: "Real Case counselor decision brief",
      path: `${closurePreview.caseId}-counselor-decision-brief.md`,
      required: true,
      audience: "internal_review",
    },
    {
      id: "real_case_counselor_decision_json",
      label: "Real Case counselor decision JSON snapshot",
      path: `${closurePreview.caseId}-counselor-decision.json`,
      required: true,
      audience: "internal_review",
    },
  ];

  return {
    ...originalPreview,
    message: "Real Case counselor decision is recorded; client delivery remains blocked.",
    manifest: {
      ...originalPreview.manifest,
      status: "counselor_decision_recorded",
      client_delivery: {
        allowed: false,
        status: "blocked",
        artifact_audiences: ["client_confirmation", "client_final"],
        blocked_reason: blockedReason,
      },
      artifacts: [...originalPreview.manifest.artifacts, ...counselorArtifacts],
      delivery_gates: [
        ...originalPreview.manifest.delivery_gates,
        {
          gate: "counselor_decision",
          status: "recorded",
          requirement:
            "Counselor decision is recorded for internal drafting only; client delivery remains blocked until a later explicit delivery signoff.",
        },
      ],
      next_actions: uniqueStrings([
        ...originalPreview.manifest.next_actions,
        ...counselorDecision.requiredNextActions,
        "Do not release family-facing language from this preview.",
      ]),
    },
    artifacts: {
      ...originalPreview.artifacts,
      real_case_counselor_decision_brief: counselorBrief,
      real_case_counselor_decision_json: counselorJson,
    },
  };
}

function renderCounselorDecisionBrief({
  closurePreview,
  counselorDecision,
}: RealCaseCounselorDecisionDeliveryPreviewInput): string {
  return [
    `# Real Case counselor decision brief: ${closurePreview.caseId}`,
    "",
    `- decision: ${counselorDecision.decision}`,
    `- reviewer: ${counselorDecision.reviewer.displayName} (${counselorDecision.reviewer.role})`,
    `- internalReportDraftAllowed: ${counselorDecision.internalReportDraftAllowed ? "true" : "false"}`,
    "- clientDeliveryAllowed: false",
    "- familyFacingAllowed: false",
    `- sourceFreshnessChecked: ${counselorDecision.sourceFreshnessChecked ? "true" : "false"}`,
    `- representativenessChecked: ${counselorDecision.representativenessChecked ? "true" : "false"}`,
    `- claimBoundaryConfirmed: ${counselorDecision.claimBoundaryConfirmed ? "true" : "false"}`,
    "",
    "## Reasons",
    ...counselorDecision.reasons.map((reason) => `- ${reason}`),
    "",
    "## Reviewed Counter-Evidence",
    ...counterEvidenceRecordsFor(closurePreview, counselorDecision).map(
      (record) => `- ${record.sourceId}: ${record.sourceTitle}`,
    ),
    "",
    "## Next Actions",
    ...counselorDecision.requiredNextActions.map((action) => `- ${action}`),
    "- Client delivery remains blocked.",
    "",
    "## Boundary",
    "- This preview does not prove admission probability.",
    "- This preview does not prove employment outcomes.",
    "- This preview is not client-facing delivery.",
  ].join("\n");
}

function uniqueStrings(values: string[]): string[] {
  return [...new Set(values)];
}

function counterEvidenceRecordsFor(
  closurePreview: RealCaseOperatorClosureDeliveryPreviewResult,
  counselorDecision: RealCaseCounselorReviewDecisionResult,
) {
  const reviewed = new Set(counselorDecision.reviewedCounterEvidenceSourceIds);
  return closurePreview.workflow.closureReview.auditPacket.counterEvidence.records
    .filter((record) => reviewed.has(record.sourceId))
    .map((record) => ({
      sourceId: record.sourceId,
      sourceTitle: record.sourceTitle,
      taskId: record.taskId,
      reviewAction: record.reviewAction,
      excerpt: record.excerpt,
    }));
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

import type { DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { OperatorReviewedEvidenceCaptureInput } from "./evidenceAutopilotApi";
import {
  executeRealCaseOperatorClosureWorkflow,
  type RealCaseOperatorClosureWorkflowResult,
} from "./evidenceAutopilotRealCaseOperatorClosure";
import type { EvidenceAutopilotRealCaseFixture } from "./evidenceAutopilotRealCaseProvider";

type FetchLike = Parameters<typeof executeRealCaseOperatorClosureWorkflow>[0]["fetchImpl"];

export interface RealCaseOperatorClosureDeliveryArtifact {
  id: "real_case_operator_closure_brief" | "real_case_operator_closure_json";
  label: string;
  path: string;
  required: true;
  audience: "internal_review";
}

export interface RealCaseOperatorClosureDeliveryManifest {
  case_id: string;
  status: "requires_counter_evidence_review";
  client_delivery: {
    allowed: false;
    status: "blocked";
    artifact_audiences: ["client_confirmation", "client_final"];
    blocked_reason: string;
  };
  artifacts: RealCaseOperatorClosureDeliveryArtifact[];
  delivery_gates: Array<{
    gate: "counter_evidence_review" | "counselor_review";
    status: "blocked";
    requirement: string;
  }>;
  next_actions: string[];
}

export interface RealCaseOperatorClosureDeliveryPreview {
  success: true;
  message: string;
  case_id: string;
  output_dir: string;
  manifest: RealCaseOperatorClosureDeliveryManifest;
  artifacts: Record<RealCaseOperatorClosureDeliveryArtifact["id"], string>;
}

export interface RealCaseOperatorClosureDeliveryPreviewResult {
  protocol: "real_case_operator_closure_delivery_preview_v1";
  caseId: string;
  workflow: RealCaseOperatorClosureWorkflowResult;
  preview: RealCaseOperatorClosureDeliveryPreview;
  clientFacingArtifacts: Array<[string, string]>;
  claimBoundary: string;
}

const CLIENT_FACING_AUDIENCES = new Set(["client_confirmation", "client_final"]);

export async function bootstrapRealCaseOperatorClosureDeliveryPreview({
  fixture,
  caseId,
  plan,
  operatorInput,
  fetchImpl,
}: {
  fixture: EvidenceAutopilotRealCaseFixture;
  caseId: string;
  plan: DeepEvidenceCollectionPlan;
  operatorInput: OperatorReviewedEvidenceCaptureInput;
  fetchImpl?: FetchLike;
}): Promise<RealCaseOperatorClosureDeliveryPreviewResult> {
  const workflow = await executeRealCaseOperatorClosureWorkflow({
    fixture,
    caseId,
    plan,
    operatorInput,
    fetchImpl,
  });
  const preview = buildRealCaseOperatorClosureDeliveryPreview(workflow);

  return {
    protocol: "real_case_operator_closure_delivery_preview_v1",
    caseId,
    workflow,
    preview,
    clientFacingArtifacts: listRealCaseOperatorClosureClientFacingArtifacts(preview),
    claimBoundary:
      "Real Case operator closure delivery preview shows operator evidence has been captured and P0 gaps are cleared, but it does not prove admission probability, does not prove employment outcomes, and does not allow client-facing delivery before counter-evidence and counselor review.",
  };
}

export function buildRealCaseOperatorClosureDeliveryPreview(
  workflow: RealCaseOperatorClosureWorkflowResult,
): RealCaseOperatorClosureDeliveryPreview {
  if (workflow.protocol !== "real_case_operator_closure_workflow_v1") {
    throw new Error("real case operator closure delivery preview requires closure workflow result");
  }

  const review = workflow.closureReview;
  const brief = renderClosureBrief(workflow);
  const json = JSON.stringify(workflow, null, 2);
  const blockedReason =
    "Client delivery remains blocked by counter-evidence and counselor review after operator evidence capture.";

  return {
    success: true,
    message: "Real Case operator evidence is captured; internal preview is blocked for counselor review.",
    case_id: workflow.caseId,
    output_dir: `operator-closure://${workflow.caseId}`,
    manifest: {
      case_id: workflow.caseId,
      status: "requires_counter_evidence_review",
      client_delivery: {
        allowed: false,
        status: "blocked",
        artifact_audiences: ["client_confirmation", "client_final"],
        blocked_reason: blockedReason,
      },
      artifacts: [
        {
          id: "real_case_operator_closure_brief",
          label: "Real Case operator closure brief",
          path: `${workflow.caseId}-operator-closure-brief.md`,
          required: true,
          audience: "internal_review",
        },
        {
          id: "real_case_operator_closure_json",
          label: "Real Case operator closure JSON snapshot",
          path: `${workflow.caseId}-operator-closure.json`,
          required: true,
          audience: "internal_review",
        },
      ],
      delivery_gates: [
        {
          gate: "counter_evidence_review",
          status: "blocked",
          requirement: "Counselor must review counter-evidence before any family-facing wording is allowed.",
        },
        {
          gate: "counselor_review",
          status: "blocked",
          requirement: "Counselor must verify source freshness, representativeness, and recommendation boundary.",
        },
      ],
      next_actions: [
        `Audit status: ${review.auditPacket.status}.`,
        `Missing P0 tasks after operator capture: ${review.browser.missingP0TaskIds.join(", ") || "none"}.`,
        "Review counter-evidence and source freshness before drafting any family-facing report language.",
      ],
    },
    artifacts: {
      real_case_operator_closure_brief: brief,
      real_case_operator_closure_json: json,
    },
  };
}

export function listRealCaseOperatorClosureClientFacingArtifacts(
  preview: RealCaseOperatorClosureDeliveryPreview,
): Array<[string, string]> {
  const audienceById = new Map(
    preview.manifest.artifacts.map((artifact) => [artifact.id, artifact.audience]),
  );
  return Object.entries(preview.artifacts).filter(([id]) => {
    const audience = audienceById.get(id as RealCaseOperatorClosureDeliveryArtifact["id"]);
    return audience ? CLIENT_FACING_AUDIENCES.has(audience) : false;
  });
}

function renderClosureBrief(workflow: RealCaseOperatorClosureWorkflowResult): string {
  const review = workflow.closureReview;
  return [
    `# Real Case operator closure brief: ${review.reportBrief.targetLabel}`,
    "",
    `- caseId: ${workflow.caseId}`,
    `- status: ${review.auditPacket.status}`,
    `- missingP0TaskIds: ${review.browser.missingP0TaskIds.join(", ") || "none"}`,
    `- familyFacingAllowed: ${review.reportBrief.familyFacingAllowed ? "true" : "false"}`,
    "",
    "## Supported Claims",
    ...review.auditPacket.supportedClaims.map((claim) =>
      `- ${claim.taskId}: ${claim.title}; sources=${claim.sourceCount}; titles=${claim.sourceTitles.join(", ")}`,
    ),
    "",
    "## Blocking Gaps",
    ...(review.auditPacket.blockingGaps.length > 0
      ? review.auditPacket.blockingGaps.map((gap) => `- ${gap.taskId}: ${gap.reason}`)
      : ["- none"]),
    "",
    "## Counter-Evidence Review",
    `- requiresCounselorReview: ${review.auditPacket.counterEvidence.requiresCounselorReview ? "true" : "false"}`,
    ...review.auditPacket.counterEvidence.records.map((record) =>
      `- ${record.taskId}: ${record.sourceTitle}; action=${record.reviewAction}; excerpt=${record.excerpt}`,
    ),
    "",
    "## Next Actions",
    ...review.auditPacket.nextActions.map((action) => `- ${action}`),
    "",
    "## Boundary",
    "- This preview does not prove admission probability.",
    "- This preview does not prove employment outcomes.",
    "- This preview is not client-facing delivery.",
  ].join("\n");
}

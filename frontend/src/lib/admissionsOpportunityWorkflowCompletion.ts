import type { AdmissionsOpportunityWorkflow } from "./admissionsOpportunityWorkflow";
import {
  evaluateWebEvidenceResults,
  type ClaimSupportStatus,
  type WebEvidenceIntakeResult,
  type WebEvidenceSearchResult,
} from "./webEvidenceIntake";
import {
  buildEvidenceBackedInterpretationPackage,
  type EvidenceBackedInterpretationPackage,
} from "./evidenceBackedInterpretationPackage";
import type { EvidenceClaimSupport } from "./webEvidencePlanner";

export interface AdmissionsOpportunityWorkflowCompletionInput {
  workflow: AdmissionsOpportunityWorkflow;
  evidenceResults: WebEvidenceSearchResult[];
  studentName?: string;
}

export interface AdmissionsOpportunityWorkflowCompletion {
  protocol: "admissions_opportunity_workflow_completion_v1";
  status: "interpretation_ready" | "blocked";
  intakeResult: WebEvidenceIntakeResult;
  interpretationPackage: EvidenceBackedInterpretationPackage | null;
  blockedReasons: string[];
  nextAction: string;
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Workflow completion can produce a counselor-review package, not a final recommendation. Final filing decisions still require counselor signoff.";

const CLAIMS: EvidenceClaimSupport[] = [
  "official_diff",
  "rank_delta",
  "risk_guard",
  "competitor_missed",
  "hypothesis_only",
  "parent_understanding",
  "final_recommendation",
];

export function completeAdmissionsOpportunityWorkflow(
  input: AdmissionsOpportunityWorkflowCompletionInput,
): AdmissionsOpportunityWorkflowCompletion {
  if (input.workflow.status !== "needs_evidence_research") {
    const blockedReasons = input.workflow.gateReasons.length > 0
      ? input.workflow.gateReasons
      : [`Workflow is gated at ${input.workflow.status}.`];

    return {
      protocol: "admissions_opportunity_workflow_completion_v1",
      status: "blocked",
      intakeResult: buildBlockedIntakeResult(blockedReasons),
      interpretationPackage: null,
      blockedReasons,
      nextAction: input.workflow.nextAction,
      claimBoundary: CLAIM_BOUNDARY,
    };
  }

  const intakeResult = evaluateWebEvidenceResults({
    evidencePlan: input.workflow.evidencePlan,
    results: input.evidenceResults,
  });
  const interpretationPackage = buildEvidenceBackedInterpretationPackage({
    discoveryLedger: input.workflow.discoveryLedger,
    evidencePlan: input.workflow.evidencePlan,
    intakeResult,
    interestBrief: input.workflow.interestBrief,
    studentName: input.studentName,
  });
  const blockedReasons = buildBlockedReasons(intakeResult, interpretationPackage);
  const status = intakeResult.status === "review_ready" && interpretationPackage.status === "counselor_review_ready"
    ? "interpretation_ready"
    : "blocked";

  return {
    protocol: "admissions_opportunity_workflow_completion_v1",
    status,
    intakeResult,
    interpretationPackage,
    blockedReasons,
    nextAction: status === "interpretation_ready"
      ? "Counselor review can start with the attached evidence-backed interpretation package."
      : "Attach blocking evidence before counselor review.",
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildBlockedReasons(
  intakeResult: WebEvidenceIntakeResult,
  interpretationPackage: EvidenceBackedInterpretationPackage,
): string[] {
  const reasons = [
    ...intakeResult.blockedTasks,
    ...interpretationPackage.unresolvedBlockers,
    ...intakeResult.rejectedEvidence.map((item) => `${item.taskId}:${item.claim}:${item.reason}`),
  ];
  return Array.from(new Set(reasons));
}

function buildBlockedIntakeResult(gateReasons: string[]): WebEvidenceIntakeResult {
  return {
    protocol: "web_evidence_intake_v1",
    status: "blocked",
    acceptedEvidence: [],
    rejectedEvidence: gateReasons.map((reason) => ({
      taskId: "upstream_gate",
      claim: "final_recommendation",
      sourceTitle: "Admissions opportunity workflow",
      reason,
    })),
    blockedTasks: gateReasons,
    claimSupport: CLAIMS.reduce<Record<EvidenceClaimSupport, ClaimSupportStatus>>((acc, claim) => {
      acc[claim] = {
        status: "unsupported",
        evidenceCount: 0,
      };
      return acc;
    }, {} as Record<EvidenceClaimSupport, ClaimSupportStatus>),
    claimBoundary: "Evidence intake is blocked because upstream workflow gates have not passed.",
  };
}

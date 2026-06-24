import type { DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { ReviewedEvidenceRecord } from "./evidenceAutopilotApi";
import type { EvidenceAutopilotRealCaseFixture } from "./evidenceAutopilotRealCaseProvider";
import {
  buildOperatorEvidenceCapturePacket,
  type OperatorEvidenceCapturePacket,
} from "./operatorEvidenceCapturePacket";
import {
  buildOperatorEvidenceCaptureWorklist,
} from "./operatorEvidenceCaptureWorklist";

export interface RealCaseReviewerHandoff {
  protocol: "real_case_reviewer_handoff_v1";
  caseId: string;
  targetLabel: string;
  status: "clear" | "blocked_by_operator_capture";
  familyFacingAllowed: boolean;
  openTaskIds: string[];
  capturePacket: OperatorEvidenceCapturePacket;
  execution: {
    workflowFunction: "executeRealCaseOperatorClosureWorkflow";
    inputContract: "OperatorReviewedEvidenceCaptureInput";
    expectedStatusAfterValidCapture: "requires_counter_evidence_review" | "ready_for_counselor_review";
    notes: string[];
  };
  reviewerChecklist: string[];
  claimBoundary: string;
}

export function buildRealCaseReviewerHandoff({
  fixture,
  caseId,
  plan,
  records,
}: {
  fixture: EvidenceAutopilotRealCaseFixture;
  caseId: string;
  plan: DeepEvidenceCollectionPlan;
  records: ReviewedEvidenceRecord[];
}): RealCaseReviewerHandoff {
  if (fixture.caseId !== caseId) {
    throw new Error("real case reviewer handoff requires matching caseId");
  }

  const worklist = buildOperatorEvidenceCaptureWorklist({
    caseId,
    plan,
    records,
  });
  const capturePacket = buildOperatorEvidenceCapturePacket({ worklist });
  const openTaskIds = capturePacket.items.map((item) => item.taskId);

  return {
    protocol: "real_case_reviewer_handoff_v1",
    caseId,
    targetLabel: plan.targetLabel,
    status: openTaskIds.length > 0 ? "blocked_by_operator_capture" : "clear",
    familyFacingAllowed: false,
    openTaskIds,
    capturePacket,
    execution: {
      workflowFunction: "executeRealCaseOperatorClosureWorkflow",
      inputContract: "OperatorReviewedEvidenceCaptureInput",
      expectedStatusAfterValidCapture: "requires_counter_evidence_review",
      notes: [
        "Fill one capture packet item into OperatorReviewedEvidenceCaptureInput before execution.",
        "After execution, ledger records are deduplicated by reviewId before readiness recomputation.",
        "A cleared operator capture gate still requires counselor review for counter-evidence and source freshness.",
      ],
    },
    reviewerChecklist: [
      "Capture only a source the reviewer can personally view and explain.",
      "Reject private chats, recruiter DMs, or unverifiable employment-market claims.",
      "Complete attachment upload and redaction checklist before ledger submission.",
      "Record source freshness and why the source supports or weakens the employment-market claim.",
      "Do not write family-facing opportunity language until the closure review and counselor review both allow it.",
    ],
    claimBoundary:
      "Real Case reviewer handoff organizes internal operator capture and closure workflow only; it does not prove admission probability, does not prove employment outcomes, does not prove source freshness, and is not a family-facing recommendation.",
  };
}

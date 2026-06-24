import type { DeepEvidenceCollectionPlan, DeepEvidenceTask } from "./deepEvidenceCollectionPlan";
import type { ReviewedEvidenceRecord } from "./evidenceAutopilotApi";
import {
  buildReviewedEvidenceCaseBrowser,
  type ReviewedEvidenceTaskGroup,
} from "./reviewedEvidenceCaseBrowser";

export type OperatorEvidenceCaptureStatus = "missing" | "needs_recapture";

export interface OperatorEvidenceCaptureWorkItem {
  taskId: string;
  claim: string;
  title: string;
  priority: string;
  blocking: boolean;
  captureStatus: OperatorEvidenceCaptureStatus;
  workflowFunction: "captureAndSubmitOperatorReviewedEvidence";
  outputFields: string[];
  requiredAttachmentKinds: string[];
  redactionChecklistRequired: boolean;
  reviewAction: string;
  reason: string;
}

export interface OperatorEvidenceCaptureWorklist {
  protocol: "operator_evidence_capture_worklist_v1";
  caseId: string;
  targetLabel: string;
  totalItems: number;
  blockingItemCount: number;
  items: OperatorEvidenceCaptureWorkItem[];
  claimBoundary: string;
}

export interface OperatorEvidenceCaptureGate {
  protocol: "operator_evidence_capture_gate_v1";
  status: "clear" | "needs_capture" | "blocked";
  blocksClientDelivery: boolean;
  totalItems: number;
  blockingItemCount: number;
  blockedReason: string;
  claimBoundary: string;
}

const OPERATOR_CAPTURE_CLAIMS = new Set([
  "employment_market",
  "wechat_public_account",
  "counter_evidence",
]);

export function buildOperatorEvidenceCaptureWorklist({
  caseId,
  plan,
  records,
}: {
  caseId: string;
  plan: DeepEvidenceCollectionPlan;
  records: ReviewedEvidenceRecord[];
}): OperatorEvidenceCaptureWorklist {
  const view = buildReviewedEvidenceCaseBrowser({ caseId, plan, records });
  const taskById = new Map(plan.tasks.map((task) => [task.id, task]));
  const items = view.taskGroups
    .filter((group) => group.status !== "ready_for_report")
    .filter((group) => OPERATOR_CAPTURE_CLAIMS.has(group.claim))
    .map((group) => toWorkItem(group, taskById.get(group.taskId)))
    .sort((left, right) => priorityRank(left.priority) - priorityRank(right.priority));

  return {
    protocol: "operator_evidence_capture_worklist_v1",
    caseId,
    targetLabel: plan.targetLabel,
    totalItems: items.length,
    blockingItemCount: items.filter((item) => item.blocking).length,
    items,
    claimBoundary:
      "Operator evidence capture worklist only organizes missing or invalid capture tasks; it does not collect evidence, bypass platform limits, or prove admission/employment outcomes.",
  };
}

export function buildOperatorEvidenceCaptureGate(
  worklist: OperatorEvidenceCaptureWorklist,
): OperatorEvidenceCaptureGate {
  const blockingItems = worklist.items.filter((item) => item.blocking);
  if (blockingItems.length > 0) {
    return {
      protocol: "operator_evidence_capture_gate_v1",
      status: "blocked",
      blocksClientDelivery: true,
      totalItems: worklist.totalItems,
      blockingItemCount: blockingItems.length,
      blockedReason: `Blocking operator evidence still needs capture: ${blockingItems
        .map((item) => item.taskId)
        .join(", ")}.`,
      claimBoundary:
        "Operator capture blocking status is a delivery-readiness control; it does not prove admission or employment outcomes.",
    };
  }
  if (worklist.items.length > 0) {
    return {
      protocol: "operator_evidence_capture_gate_v1",
      status: "needs_capture",
      blocksClientDelivery: false,
      totalItems: worklist.totalItems,
      blockingItemCount: 0,
      blockedReason: "Only non-blocking operator evidence capture items remain.",
      claimBoundary:
        "Non-blocking operator capture status is a reviewer workflow signal; it does not prove admission or employment outcomes.",
    };
  }
  return {
    protocol: "operator_evidence_capture_gate_v1",
    status: "clear",
    blocksClientDelivery: false,
    totalItems: 0,
    blockingItemCount: 0,
    blockedReason: "No operator evidence capture items remain.",
    claimBoundary:
      "Clear operator capture status only means this capture worklist has no open items; it does not prove admission or employment outcomes.",
  };
}

function toWorkItem(
  group: ReviewedEvidenceTaskGroup,
  task: DeepEvidenceTask | undefined,
): OperatorEvidenceCaptureWorkItem {
  const invalidRecord = group.records.find((record) => record.attachmentAuditStatus === "invalid");
  const captureStatus: OperatorEvidenceCaptureStatus = invalidRecord ? "needs_recapture" : "missing";
  return {
    taskId: group.taskId,
    claim: group.claim,
    title: group.title,
    priority: group.priority,
    blocking: group.priority === "P0",
    captureStatus,
    workflowFunction: "captureAndSubmitOperatorReviewedEvidence",
    outputFields: task?.outputFields ?? [],
    requiredAttachmentKinds: ["screenshot", "page_capture", "pdf", "image"],
    redactionChecklistRequired: true,
    reviewAction: reviewActionFor(captureStatus),
    reason: invalidRecord?.attachmentAuditDetail ?? "No ready operator-reviewed evidence record exists for this task.",
  };
}

function reviewActionFor(status: OperatorEvidenceCaptureStatus): string {
  if (status === "needs_recapture") {
    return "Re-capture the source, upload a fresh attachment, complete redaction checklist, and submit through captureAndSubmitOperatorReviewedEvidence.";
  }
  return "Capture the source, upload attachment proof, complete redaction checklist, and submit through captureAndSubmitOperatorReviewedEvidence.";
}

function priorityRank(priority: string): number {
  return { P0: 0, P1: 1, P2: 2 }[priority as "P0" | "P1" | "P2"] ?? 3;
}

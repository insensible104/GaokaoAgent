import {
  buildCounselorDeliveryChecklist,
  type CounselorChecklistStatus,
  type CounselorDeliveryChecklistInput,
  type CounselorDeliveryChecklistItem,
} from "./counselorDeliveryChecklist";
import {
  buildDeliveryReviewRecord,
  type DeliveryReviewRecordInput,
  type DeliveryReviewRecordSnapshot,
} from "./deliveryReviewRecord";
import type { ExternalPlanAuditSummary } from "./externalPlanAudit";

export type DeliverySignoffState =
  | "not_started"
  | "counselor_reviewed"
  | "family_confirmed"
  | "locked";

export type ParentConfirmationState = "not_requested" | "requested" | "confirmed" | "declined";

export type DeliveryWorkflowStage =
  | "intake"
  | "counselor_review"
  | "family_confirmation"
  | "ready_to_lock"
  | "locked";

export interface DeliveryCaseStatusExternalAuditSummary {
  protocol: "external_plan_audit_summary_v1";
  parsedCount: number;
  matchedCount: number;
  unmatchedCount: number;
  duplicateCount: number;
  overlapRate: number;
  needsReview: boolean;
}

export interface DeliveryCaseStatus {
  protocol: "delivery_case_status_v1";
  caseId: string;
  status: CounselorChecklistStatus;
  workflowStage: DeliveryWorkflowStage;
  reviewer: string;
  updatedAt: string;
  signoffState: DeliverySignoffState;
  parentConfirmationState: ParentConfirmationState;
  blockedItems: CounselorDeliveryChecklistItem[];
  reviewItems: CounselorDeliveryChecklistItem[];
  readyItems: CounselorDeliveryChecklistItem[];
  externalAuditSummary?: DeliveryCaseStatusExternalAuditSummary;
  reviewRecord: DeliveryReviewRecordSnapshot;
  nextAction: string;
  leadAction: string;
  claimBoundary: string;
}

export interface DeliveryCaseStatusInput extends DeliveryReviewRecordInput {
  caseId: string;
  reviewer?: string;
  updatedAt?: string | Date;
  signoffState?: DeliverySignoffState;
  parentConfirmationState?: ParentConfirmationState;
}

export const DELIVERY_CASE_STATUS_BOUNDARY =
  "Delivery case status is an operational workflow snapshot, not an admission promise. Formal delivery requires counselor signoff, family confirmation, and current official-source review.";

export function buildDeliveryCaseStatus(input: DeliveryCaseStatusInput): DeliveryCaseStatus {
  const checklistInput: CounselorDeliveryChecklistInput = input;
  const checklist = buildCounselorDeliveryChecklist(checklistInput);
  const reviewRecord = buildDeliveryReviewRecord(input);
  const blockedItems = checklist.items.filter((item) => item.status === "blocked");
  const reviewItems = checklist.items.filter((item) => item.status === "needs_review");
  const readyItems = checklist.items.filter((item) => item.status === "ready");
  const signoffState = resolveSignoffState(checklist.status, input.signoffState);
  const parentConfirmationState = resolveParentConfirmationState({
    status: checklist.status,
    signoffState,
    requested: input.parentConfirmationState,
  });
  const workflowStage = resolveWorkflowStage(checklist.status, signoffState, parentConfirmationState);
  const externalAuditSummary = summarizeExternalAudit(input.externalPlanAuditSummary);

  return {
    protocol: "delivery_case_status_v1",
    caseId: input.caseId,
    status: checklist.status,
    workflowStage,
    reviewer: input.reviewer?.trim() || input.operatorName?.trim() || "unassigned",
    updatedAt: formatIsoTimestamp(input.updatedAt ?? input.generatedAt ?? new Date()),
    signoffState,
    parentConfirmationState,
    blockedItems,
    reviewItems,
    readyItems,
    externalAuditSummary,
    reviewRecord,
    nextAction: resolveNextAction({
      blockedItems,
      reviewItems,
      externalAuditSummary,
      status: checklist.status,
    }),
    leadAction: checklist.leadAction,
    claimBoundary: DELIVERY_CASE_STATUS_BOUNDARY,
  };
}

function summarizeExternalAudit(
  audit?: ExternalPlanAuditSummary | DeliveryReviewRecordInput["externalPlanAuditSummary"] | null,
): DeliveryCaseStatusExternalAuditSummary | undefined {
  if (!audit) {
    return undefined;
  }

  const unmatchedCount = audit.unmatchedEntries?.length ?? 0;
  const duplicateCount = audit.duplicateEntries?.length ?? 0;
  const needsReview =
    unmatchedCount > 0 ||
    duplicateCount > 0 ||
    Boolean(audit.findings?.some((finding) => hasReviewSeverity(finding)));

  return {
    protocol: "external_plan_audit_summary_v1",
    parsedCount: audit.parsedCount ?? 0,
    matchedCount: audit.matchedCount ?? Math.max((audit.parsedCount ?? 0) - unmatchedCount, 0),
    unmatchedCount,
    duplicateCount,
    overlapRate: audit.overlapRate ?? 0,
    needsReview,
  };
}

function hasReviewSeverity(finding: unknown): boolean {
  if (!finding || typeof finding !== "object") {
    return false;
  }
  const severity = (finding as { severity?: unknown }).severity;
  return severity === "review" || severity === "blocker";
}

function resolveSignoffState(
  status: CounselorChecklistStatus,
  requested?: DeliverySignoffState,
): DeliverySignoffState {
  if (status === "blocked") {
    return "not_started";
  }
  if (status === "needs_review") {
    if (requested === "counselor_reviewed") {
      return "counselor_reviewed";
    }
    return "not_started";
  }
  return requested ?? "counselor_reviewed";
}

function resolveParentConfirmationState({
  status,
  signoffState,
  requested,
}: {
  status: CounselorChecklistStatus;
  signoffState: DeliverySignoffState;
  requested?: ParentConfirmationState;
}): ParentConfirmationState {
  if (status !== "ready") {
    return requested === "declined" ? "declined" : "requested";
  }
  if (signoffState === "locked" || signoffState === "family_confirmed") {
    return requested ?? "confirmed";
  }
  return requested ?? "not_requested";
}

function resolveWorkflowStage(
  status: CounselorChecklistStatus,
  signoffState: DeliverySignoffState,
  parentConfirmationState: ParentConfirmationState,
): DeliveryWorkflowStage {
  if (status === "blocked") {
    return "intake";
  }
  if (status === "needs_review") {
    return "counselor_review";
  }
  if (signoffState === "locked") {
    return "locked";
  }
  if (parentConfirmationState === "confirmed" || signoffState === "family_confirmed") {
    return "ready_to_lock";
  }
  return "family_confirmation";
}

function resolveNextAction({
  blockedItems,
  reviewItems,
  externalAuditSummary,
  status,
}: {
  blockedItems: CounselorDeliveryChecklistItem[];
  reviewItems: CounselorDeliveryChecklistItem[];
  externalAuditSummary?: DeliveryCaseStatusExternalAuditSummary;
  status: CounselorChecklistStatus;
}): string {
  if (blockedItems.some((item) => item.id === "data_boundary")) {
    return "Review official 2026 data boundary before formal delivery.";
  }
  if (blockedItems.length > 0) {
    return `Resolve blocked delivery item: ${blockedItems[0].id}.`;
  }
  if (externalAuditSummary?.needsReview) {
    return "Review external-plan unmatched or duplicate rows before family confirmation.";
  }
  if (reviewItems.length > 0) {
    return `Complete counselor review item: ${reviewItems[0].id}.`;
  }
  if (status === "ready") {
    return "Collect counselor signoff and family confirmation before locking the case.";
  }
  return "Keep the case in counselor review until all delivery checks are ready.";
}

function formatIsoTimestamp(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "invalid-date";
  }
  return date.toISOString();
}

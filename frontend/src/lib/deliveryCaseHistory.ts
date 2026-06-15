import type { DeliveryCaseStatus, DeliveryWorkflowStage } from "./deliveryCaseStatus";

export type DeliveryCaseEventType =
  | "status_snapshot"
  | "counselor_review"
  | "external_audit"
  | "parent_confirmation"
  | "case_locked";

export interface DeliveryCaseHistoryEvent {
  eventId: string;
  type: DeliveryCaseEventType;
  caseId: string;
  versionStamp: string;
  actor: string;
  createdAt: string;
  stage: DeliveryWorkflowStage;
  status: DeliveryCaseStatus["status"];
  summary: string;
  blockedCount: number;
  reviewCount: number;
  claimBoundary: string;
}

export interface DeliveryCaseHistory {
  protocol: "delivery_case_history_v1";
  caseId: string;
  currentVersion: string;
  currentStage: DeliveryWorkflowStage;
  eventCount: number;
  events: DeliveryCaseHistoryEvent[];
  lockReady: boolean;
  missingBeforeLock: string[];
  claimBoundary: string;
}

export const DELIVERY_CASE_HISTORY_BOUNDARY =
  "Delivery history is an audit trail contract for counselor operations; it records review evidence and confirmation events without creating an admission guarantee.";

export function buildDeliveryCaseHistory({
  current,
  previous = [],
  actor,
}: {
  current: DeliveryCaseStatus;
  previous?: DeliveryCaseStatus[];
  actor?: string;
}): DeliveryCaseHistory {
  const snapshots = [...previous, current];
  const events = snapshots.map((snapshot, index) => snapshotToEvent(snapshot, index, actor));
  const missingBeforeLock = resolveMissingBeforeLock(current);

  return {
    protocol: "delivery_case_history_v1",
    caseId: current.caseId,
    currentVersion: current.reviewRecord.versionStamp,
    currentStage: current.workflowStage,
    eventCount: events.length,
    events,
    lockReady: missingBeforeLock.length === 0,
    missingBeforeLock,
    claimBoundary: DELIVERY_CASE_HISTORY_BOUNDARY,
  };
}

function snapshotToEvent(
  snapshot: DeliveryCaseStatus,
  index: number,
  actor?: string,
): DeliveryCaseHistoryEvent {
  return {
    eventId: `${snapshot.caseId}-${snapshot.reviewRecord.versionStamp}-${index + 1}`,
    type: resolveEventType(snapshot),
    caseId: snapshot.caseId,
    versionStamp: snapshot.reviewRecord.versionStamp,
    actor: actor?.trim() || snapshot.reviewer || "unassigned",
    createdAt: snapshot.updatedAt,
    stage: snapshot.workflowStage,
    status: snapshot.status,
    summary: snapshot.nextAction,
    blockedCount: snapshot.blockedItems.length,
    reviewCount: snapshot.reviewItems.length,
    claimBoundary: snapshot.claimBoundary,
  };
}

function resolveEventType(snapshot: DeliveryCaseStatus): DeliveryCaseEventType {
  if (snapshot.workflowStage === "locked") {
    return "case_locked";
  }
  if (snapshot.parentConfirmationState === "confirmed") {
    return "parent_confirmation";
  }
  if (snapshot.externalAuditSummary?.needsReview) {
    return "external_audit";
  }
  if (snapshot.signoffState === "counselor_reviewed") {
    return "counselor_review";
  }
  return "status_snapshot";
}

function resolveMissingBeforeLock(current: DeliveryCaseStatus): string[] {
  const missing: string[] = [];
  if (current.status !== "ready") {
    missing.push("all delivery checklist items must be ready");
  }
  if (current.signoffState !== "family_confirmed" && current.signoffState !== "locked") {
    missing.push("counselor signoff is not complete");
  }
  if (current.parentConfirmationState !== "confirmed") {
    missing.push("family confirmation is not complete");
  }
  if (current.externalAuditSummary?.needsReview) {
    missing.push("external plan audit still needs review");
  }
  return missing;
}

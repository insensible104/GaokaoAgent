import type { DeliveryCaseStatus, DeliveryWorkflowStage } from "./deliveryCaseStatus";

export type DeliveryCaseStoreEventType =
  | "status_snapshot"
  | "counselor_review"
  | "external_audit"
  | "parent_confirmation"
  | "case_locked";

export interface DeliveryCaseStoreEventPayload {
  status: DeliveryCaseStatus["status"];
  workflowStage: DeliveryWorkflowStage;
  signoffState: DeliveryCaseStatus["signoffState"];
  parentConfirmationState: DeliveryCaseStatus["parentConfirmationState"];
  blockedCount: number;
  reviewCount: number;
  readyCount: number;
  externalAuditNeedsReview: boolean;
  reviewRecordVersion: string;
  nextAction: string;
  claimBoundary: string;
}

export interface DeliveryCaseStoreEvent {
  protocol: "delivery_case_store_event_v1";
  eventId: string;
  eventType: DeliveryCaseStoreEventType;
  caseId: string;
  sequence: number;
  actor: string;
  createdAt: string;
  checksum: string;
  payload: DeliveryCaseStoreEventPayload;
}

export interface DeliveryCaseEventStoreSnapshot {
  protocol: "delivery_case_event_store_v1";
  caseId: string;
  eventCount: number;
  lastEventId?: string;
  currentStage: DeliveryWorkflowStage | "empty";
  lockReady: boolean;
  missingBeforeLock: string[];
  events: DeliveryCaseStoreEvent[];
  claimBoundary: string;
}

export interface DeliveryCaseEventStoreReplay {
  protocol: "delivery_case_event_replay_v1";
  caseId: string;
  currentStage: DeliveryWorkflowStage | "empty";
  eventCount: number;
  lockReady: boolean;
  missingBeforeLock: string[];
  events: Array<{
    eventId: string;
    type: DeliveryCaseStoreEventType;
    actor: string;
    createdAt: string;
    stage: DeliveryWorkflowStage;
    status: DeliveryCaseStatus["status"];
    blockedCount: number;
    reviewCount: number;
    summary: string;
  }>;
  claimBoundary: string;
}

export const DELIVERY_CASE_EVENT_STORE_BOUNDARY =
  "Delivery case event store is a client-side audit contract for case operations; it records workflow events but does not replace backend persistence, permissions, or official-source review.";

export function createDeliveryCaseEventStore(caseId: string): DeliveryCaseEventStoreSnapshot {
  return {
    protocol: "delivery_case_event_store_v1",
    caseId,
    eventCount: 0,
    currentStage: "empty",
    lockReady: false,
    missingBeforeLock: ["no delivery status events recorded"],
    events: [],
    claimBoundary: DELIVERY_CASE_EVENT_STORE_BOUNDARY,
  };
}

export function recordDeliveryCaseStatusEvent({
  store,
  status,
  actor,
  createdAt,
}: {
  store: DeliveryCaseEventStoreSnapshot;
  status: DeliveryCaseStatus;
  actor?: string;
  createdAt?: string | Date;
}): DeliveryCaseEventStoreSnapshot {
  if (store.caseId !== status.caseId) {
    throw new Error(`caseId mismatch: store ${store.caseId} cannot record status ${status.caseId}`);
  }

  const sequence = store.events.length + 1;
  const payload = buildEventPayload(status);
  const event: DeliveryCaseStoreEvent = {
    protocol: "delivery_case_store_event_v1",
    eventId: `${status.caseId}-${status.reviewRecord.versionStamp}-${sequence}`,
    eventType: resolveEventType(status),
    caseId: status.caseId,
    sequence,
    actor: actor?.trim() || status.reviewer || "unassigned",
    createdAt: formatIsoTimestamp(createdAt ?? status.updatedAt),
    checksum: buildChecksum(status.caseId, sequence, payload),
    payload,
  };
  const events = [...store.events, event];
  const missingBeforeLock = resolveMissingBeforeLockFromPayload(payload);

  return {
    protocol: "delivery_case_event_store_v1",
    caseId: status.caseId,
    eventCount: events.length,
    lastEventId: event.eventId,
    currentStage: payload.workflowStage,
    lockReady: missingBeforeLock.length === 0,
    missingBeforeLock,
    events,
    claimBoundary: DELIVERY_CASE_EVENT_STORE_BOUNDARY,
  };
}

export function serializeDeliveryCaseEventStore(store: DeliveryCaseEventStoreSnapshot): string {
  return JSON.stringify(store, null, 2);
}

export function parseDeliveryCaseEventStore(serialized: string): DeliveryCaseEventStoreSnapshot {
  const parsed = JSON.parse(serialized) as Partial<DeliveryCaseEventStoreSnapshot>;
  if (parsed.protocol !== "delivery_case_event_store_v1") {
    throw new Error("invalid delivery case event store protocol");
  }
  if (!parsed.caseId || !Array.isArray(parsed.events)) {
    throw new Error("invalid delivery case event store payload");
  }
  return {
    protocol: "delivery_case_event_store_v1",
    caseId: parsed.caseId,
    eventCount: parsed.events.length,
    lastEventId: parsed.lastEventId,
    currentStage: parsed.currentStage ?? "empty",
    lockReady: parsed.lockReady === true,
    missingBeforeLock: parsed.missingBeforeLock ?? [],
    events: parsed.events,
    claimBoundary: parsed.claimBoundary ?? DELIVERY_CASE_EVENT_STORE_BOUNDARY,
  };
}

export function replayDeliveryCaseEventStore(store: DeliveryCaseEventStoreSnapshot): DeliveryCaseEventStoreReplay {
  const lastEvent = store.events.at(-1);
  const missingBeforeLock = lastEvent
    ? resolveMissingBeforeLockFromPayload(lastEvent.payload)
    : ["no delivery status events recorded"];

  return {
    protocol: "delivery_case_event_replay_v1",
    caseId: store.caseId,
    currentStage: lastEvent?.payload.workflowStage ?? "empty",
    eventCount: store.events.length,
    lockReady: missingBeforeLock.length === 0,
    missingBeforeLock,
    events: store.events.map((event) => ({
      eventId: event.eventId,
      type: event.eventType,
      actor: event.actor,
      createdAt: event.createdAt,
      stage: event.payload.workflowStage,
      status: event.payload.status,
      blockedCount: event.payload.blockedCount,
      reviewCount: event.payload.reviewCount,
      summary: event.payload.nextAction,
    })),
    claimBoundary: DELIVERY_CASE_EVENT_STORE_BOUNDARY,
  };
}

function buildEventPayload(status: DeliveryCaseStatus): DeliveryCaseStoreEventPayload {
  return {
    status: status.status,
    workflowStage: status.workflowStage,
    signoffState: status.signoffState,
    parentConfirmationState: status.parentConfirmationState,
    blockedCount: status.blockedItems.length,
    reviewCount: status.reviewItems.length,
    readyCount: status.readyItems.length,
    externalAuditNeedsReview: status.externalAuditSummary?.needsReview === true,
    reviewRecordVersion: status.reviewRecord.versionStamp,
    nextAction: status.nextAction,
    claimBoundary: status.claimBoundary,
  };
}

function resolveEventType(status: DeliveryCaseStatus): DeliveryCaseStoreEventType {
  if (status.workflowStage === "locked") {
    return "case_locked";
  }
  if (status.parentConfirmationState === "confirmed") {
    return "parent_confirmation";
  }
  if (status.externalAuditSummary?.needsReview) {
    return "external_audit";
  }
  if (status.signoffState === "counselor_reviewed") {
    return "counselor_review";
  }
  return "status_snapshot";
}

function resolveMissingBeforeLockFromPayload(payload: DeliveryCaseStoreEventPayload): string[] {
  const missing: string[] = [];
  if (payload.status !== "ready") {
    missing.push("all delivery checklist items must be ready");
  }
  if (payload.signoffState !== "family_confirmed" && payload.signoffState !== "locked") {
    missing.push("counselor signoff is not complete");
  }
  if (payload.parentConfirmationState !== "confirmed") {
    missing.push("family confirmation is not complete");
  }
  if (payload.externalAuditNeedsReview) {
    missing.push("external plan audit still needs review");
  }
  return missing;
}

function buildChecksum(caseId: string, sequence: number, payload: DeliveryCaseStoreEventPayload): string {
  const checksumSource = [
    caseId,
    sequence,
    payload.status,
    payload.workflowStage,
    payload.signoffState,
    payload.parentConfirmationState,
    payload.blockedCount,
    payload.reviewCount,
    payload.readyCount,
    payload.externalAuditNeedsReview,
    payload.reviewRecordVersion,
  ].join("|");
  let hash = 0;
  for (let index = 0; index < checksumSource.length; index += 1) {
    hash = (hash * 31 + checksumSource.charCodeAt(index)) >>> 0;
  }
  return `${caseId}:${sequence}:${hash.toString(16).padStart(8, "0")}`;
}

function formatIsoTimestamp(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "invalid-date";
  }
  return date.toISOString();
}

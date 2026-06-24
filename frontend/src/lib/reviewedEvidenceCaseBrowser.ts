import type { DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { ReviewedEvidenceRecord } from "./evidenceAutopilotApi";

type ReviewedEvidenceCardWithClaim = ReviewedEvidenceRecord["reviewedEvidenceCard"] & {
  claim?: string;
};

export type ReviewedEvidenceTaskGroupStatus =
  | "ready_for_report"
  | "needs_capture"
  | "missing";

export interface ReviewedEvidenceCaseBrowserRecord {
  reviewId: string;
  taskId: string;
  claim: string;
  sourceTitle: string;
  sourceId: string;
  excerpt: string;
  reviewer: string;
  recordedAt: string;
  capturedAt: string;
  confidence: string;
  reviewAction: string;
  attachmentCount: number;
  redactionStatus: string;
  reviewerIdentity: string;
  attachmentAuditStatus: string;
  attachmentAuditDetail: string;
  readyForReport: boolean;
}

export interface ReviewedEvidenceTaskGroup {
  taskId: string;
  claim: string;
  title: string;
  priority: string;
  status: ReviewedEvidenceTaskGroupStatus;
  records: ReviewedEvidenceCaseBrowserRecord[];
}

export interface ReviewedEvidenceCaseBrowserView {
  protocol: "reviewed_evidence_case_browser_v1";
  caseId: string;
  totalRecords: number;
  capturedCount: number;
  pendingCount: number;
  readyForReportCount: number;
  missingP0TaskIds: string[];
  counterEvidenceHit: boolean;
  reviewRequired: boolean;
  taskGroups: ReviewedEvidenceTaskGroup[];
  claimBoundary: string;
}

interface PlanLike {
  tasks?: Array<{
    id: string;
    priority?: string;
    claim?: string;
    title?: string;
  }>;
}

export function buildReviewedEvidenceCaseBrowser({
  caseId,
  records,
  plan,
}: {
  caseId: string;
  records: ReviewedEvidenceRecord[];
  plan?: DeepEvidenceCollectionPlan | PlanLike;
}): ReviewedEvidenceCaseBrowserView {
  const caseRecords = records.filter((record) => record.caseId === caseId);
  const taskMetaById = new Map(
    (plan?.tasks ?? []).map((task) => [task.id, task]),
  );
  const groupsByTask = new Map<string, ReviewedEvidenceTaskGroup>();

  for (const record of caseRecords) {
    const card = record.reviewedEvidenceCard as ReviewedEvidenceCardWithClaim;
    const task = taskMetaById.get(card.taskId);
    const group = ensureTaskGroup(groupsByTask, {
      taskId: card.taskId,
      claim: card.claim ?? task?.claim ?? card.taskId,
      title: task?.title ?? card.sourceTitle,
      priority: task?.priority ?? "unplanned",
    });
    group.records.push(toBrowserRecord(record, card));
  }

  for (const task of plan?.tasks ?? []) {
    if (!groupsByTask.has(task.id)) {
      groupsByTask.set(task.id, {
        taskId: task.id,
        claim: task.claim ?? task.id,
        title: task.title ?? task.id,
        priority: task.priority ?? "unplanned",
        status: "missing",
        records: [],
      });
    }
  }

  const taskGroups = [...groupsByTask.values()].map((group) => ({
    ...group,
    status: statusFor(group),
  }));
  const capturedCount = taskGroups.flatMap((group) =>
    group.records.filter((record) => record.readyForReport),
  ).length;
  const pendingCount = caseRecords.length - capturedCount;
  const missingP0TaskIds = taskGroups
    .filter((group) => group.priority === "P0" && group.status !== "ready_for_report")
    .map((group) => group.taskId);
  const counterEvidenceHit = taskGroups.some((group) =>
    group.claim === "counter_evidence"
    && group.records.some((record) => record.readyForReport),
  );

  return {
    protocol: "reviewed_evidence_case_browser_v1",
    caseId,
    totalRecords: caseRecords.length,
    capturedCount,
    pendingCount,
    readyForReportCount: capturedCount,
    missingP0TaskIds,
    counterEvidenceHit,
    reviewRequired: missingP0TaskIds.length > 0 || counterEvidenceHit || pendingCount > 0,
    taskGroups,
    claimBoundary:
      "Case-scoped reviewed evidence browser only organizes captured ledger records; it does not prove admission probability or employment outcomes.",
  };
}

function ensureTaskGroup(
  groupsByTask: Map<string, ReviewedEvidenceTaskGroup>,
  task: {
    taskId: string;
    claim: string;
    title: string;
    priority: string;
  },
): ReviewedEvidenceTaskGroup {
  const existing = groupsByTask.get(task.taskId);
  if (existing) return existing;
  const group: ReviewedEvidenceTaskGroup = {
    ...task,
    status: "missing",
    records: [],
  };
  groupsByTask.set(task.taskId, group);
  return group;
}

function toBrowserRecord(
  record: ReviewedEvidenceRecord,
  card: ReviewedEvidenceCardWithClaim,
): ReviewedEvidenceCaseBrowserRecord {
  const attachmentAuditStatus = record.attachmentAudit?.status ?? "not_checked";
  const attachmentAuditDetail = record.attachmentAudit?.findings
    ?.find((finding) => !finding.valid)
    ?.detail ?? "attachment audit not checked";
  const readyForReport = (
    card.status === "captured_candidate"
    && Boolean(card.excerpt.trim())
    && attachmentAuditStatus !== "invalid"
  );
  return {
    reviewId: record.reviewId,
    taskId: card.taskId,
    claim: card.claim ?? card.taskId,
    sourceTitle: card.sourceTitle,
    sourceId: card.sourceUrl.trim() || `operator-review://${record.reviewId}`,
    excerpt: card.excerpt,
    reviewer: record.reviewer,
    recordedAt: record.recordedAt,
    capturedAt: card.capturedAt,
    confidence: card.confidence,
    reviewAction: card.reviewAction,
    attachmentCount: card.attachments?.length ?? 0,
    redactionStatus: card.redactionStatus ?? "pending",
    reviewerIdentity: formatReviewerIdentity(card.reviewerIdentity),
    attachmentAuditStatus,
    attachmentAuditDetail,
    readyForReport,
  };
}

function formatReviewerIdentity(identity: ReviewedEvidenceCardWithClaim["reviewerIdentity"]): string {
  if (!identity) return "unverified reviewer";
  return `${identity.displayName} (${identity.role})`;
}

function statusFor(group: ReviewedEvidenceTaskGroup): ReviewedEvidenceTaskGroupStatus {
  if (group.records.some((record) => record.readyForReport)) return "ready_for_report";
  if (group.records.length > 0) return "needs_capture";
  return "missing";
}

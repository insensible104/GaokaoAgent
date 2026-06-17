import type { EvidenceCollectionTaskRow, EvidenceCollectionWorkspace } from "./evidenceCollectionWorkspace";
import type { WebEvidenceSearchResult } from "./webEvidenceIntake";
import type { EvidenceClaimSupport, WebEvidenceSourceTier, WebEvidenceTaskType } from "./webEvidencePlanner";

export interface WebEvidenceCaptureSubmission {
  taskId: string;
  sourceTitle: string;
  sourceUrl: string;
  sourceTier?: WebEvidenceSourceTier;
  excerpts: string[] | string;
  claimedSupports?: EvidenceClaimSupport[];
  capturedAt?: string;
}

export interface WebEvidenceCaptureRow {
  taskId: string;
  taskType: WebEvidenceTaskType;
  priority: EvidenceCollectionTaskRow["priority"];
  currentStatus: EvidenceCollectionTaskRow["status"];
  primaryQuery: string;
  preferredDomains: string[];
  operatorChecklist: string[];
  mustReject: string[];
  resultTemplate: EvidenceCollectionTaskRow["resultTemplate"];
  copyableSubmission: WebEvidenceCaptureSubmission;
}

export interface WebEvidenceCaptureWorksheet {
  protocol: "web_evidence_capture_worksheet_v1";
  status: "ready_to_capture" | "complete" | "blocked";
  captureRows: WebEvidenceCaptureRow[];
  pendingRows: WebEvidenceCaptureRow[];
  claimBoundary: string;
}

export interface RejectedWebEvidenceCaptureSubmission {
  taskId: string;
  sourceTitle?: string;
  reason: string;
}

export interface WebEvidenceCaptureNormalizationResult {
  protocol: "web_evidence_capture_normalization_v1";
  evidenceResults: WebEvidenceSearchResult[];
  rejectedSubmissions: RejectedWebEvidenceCaptureSubmission[];
  claimBoundary: string;
}

const WORKSHEET_BOUNDARY =
  "Capture worksheet prepares operator source collection. It is not evidence by itself and cannot support final recommendations.";

const NORMALIZATION_BOUNDARY =
  "Capture normalization normalizes operator captures into evidence results; evidence still must pass intake before claims are supported.";

export function buildWebEvidenceCaptureWorksheet({
  workspace,
}: {
  workspace: EvidenceCollectionWorkspace;
}): WebEvidenceCaptureWorksheet {
  const captureRows = workspace.taskRows.map(toCaptureRow);
  const pendingRows = captureRows.filter((row) => row.currentStatus !== "accepted");

  return {
    protocol: "web_evidence_capture_worksheet_v1",
    status: workspace.status === "upstream_blocked"
      ? "blocked"
      : pendingRows.length === 0
        ? "complete"
        : "ready_to_capture",
    captureRows,
    pendingRows,
    claimBoundary: WORKSHEET_BOUNDARY,
  };
}

export function normalizeWebEvidenceCaptureSubmissions({
  workspace,
  submissions,
  capturedAt,
}: {
  workspace: EvidenceCollectionWorkspace;
  submissions: WebEvidenceCaptureSubmission[];
  capturedAt: string;
}): WebEvidenceCaptureNormalizationResult {
  const rowsById = new Map(workspace.taskRows.map((row) => [row.taskId, row]));
  const evidenceResults: WebEvidenceSearchResult[] = [];
  const rejectedSubmissions: RejectedWebEvidenceCaptureSubmission[] = [];

  for (const submission of submissions) {
    const taskRow = rowsById.get(submission.taskId);
    const rejection = validateSubmission(submission, taskRow);
    if (rejection) {
      rejectedSubmissions.push({
        taskId: submission.taskId,
        sourceTitle: submission.sourceTitle,
        reason: rejection,
      });
      continue;
    }

    const row = taskRow as EvidenceCollectionTaskRow;
    evidenceResults.push({
      taskId: submission.taskId,
      sourceTitle: submission.sourceTitle.trim(),
      sourceUrl: submission.sourceUrl.trim(),
      sourceTier: submission.sourceTier ?? row.resultTemplate.sourceTier,
      capturedAt: submission.capturedAt ?? capturedAt,
      excerpts: normalizeExcerpts(submission.excerpts),
      claimedSupports: submission.claimedSupports ?? row.resultTemplate.claimedSupports,
    });
  }

  return {
    protocol: "web_evidence_capture_normalization_v1",
    evidenceResults,
    rejectedSubmissions,
    claimBoundary: NORMALIZATION_BOUNDARY,
  };
}

function toCaptureRow(taskRow: EvidenceCollectionTaskRow): WebEvidenceCaptureRow {
  return {
    taskId: taskRow.taskId,
    taskType: taskRow.taskType,
    priority: taskRow.priority,
    currentStatus: taskRow.status,
    primaryQuery: taskRow.primaryQuery,
    preferredDomains: taskRow.preferredDomains,
    operatorChecklist: taskRow.operatorChecklist,
    mustReject: taskRow.mustReject,
    resultTemplate: taskRow.resultTemplate,
    copyableSubmission: {
      taskId: taskRow.taskId,
      sourceTitle: "",
      sourceUrl: "",
      sourceTier: taskRow.resultTemplate.sourceTier,
      excerpts: [],
      claimedSupports: taskRow.resultTemplate.claimedSupports,
    },
  };
}

function validateSubmission(
  submission: WebEvidenceCaptureSubmission,
  taskRow: EvidenceCollectionTaskRow | undefined,
): string | null {
  if (!taskRow) {
    return "Submission does not match any evidence collection task.";
  }
  if (!submission.sourceTitle?.trim()) {
    return "Submission requires a source title.";
  }
  if (!submission.sourceUrl?.trim()) {
    return "Submission requires a source URL.";
  }
  if (normalizeExcerpts(submission.excerpts).length === 0) {
    return "Submission requires at least one excerpt.";
  }

  const sourceTier = submission.sourceTier ?? taskRow.resultTemplate.sourceTier;
  if (sourceTier !== taskRow.resultTemplate.sourceTier) {
    return `Submission source tier ${sourceTier} does not match required ${taskRow.resultTemplate.sourceTier}.`;
  }

  const allowedClaims = new Set(taskRow.resultTemplate.claimedSupports);
  const claimedSupports = submission.claimedSupports ?? taskRow.resultTemplate.claimedSupports;
  const invalidClaim = claimedSupports.find((claim) => !allowedClaims.has(claim));
  if (invalidClaim) {
    return `Claim ${invalidClaim} is not allowed for ${taskRow.taskType}.`;
  }
  return null;
}

function normalizeExcerpts(excerpts: string[] | string): string[] {
  const raw = Array.isArray(excerpts) ? excerpts : excerpts.split("\n");
  return raw.map((excerpt) => excerpt.trim()).filter(Boolean);
}

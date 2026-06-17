import type { EvidenceCollectionTaskRow, EvidenceCollectionWorkspace } from "./evidenceCollectionWorkspace";
import {
  normalizeWebEvidenceCaptureSubmissions,
  type WebEvidenceCaptureNormalizationResult,
  type WebEvidenceCaptureSubmission,
} from "./webEvidenceCaptureWorksheet";
import type { EvidenceClaimSupport, WebEvidenceSourceTier, WebEvidenceTaskType } from "./webEvidencePlanner";

export interface WebEvidenceSearchAdapterRequest {
  requestId: string;
  taskId: string;
  taskType: WebEvidenceTaskType;
  query: string;
  domains: string[];
  sourceTier: WebEvidenceSourceTier;
  allowedClaims: EvidenceClaimSupport[];
  maxResults: number;
  searchIntent?: PublicOpinionSearchIntent;
  evidenceQuestion?: string;
  rejectsAsProof?: string[];
}

export interface WebEvidenceSearchRequestBatch {
  protocol: "web_evidence_search_requests_v1";
  requests: WebEvidenceSearchAdapterRequest[];
  claimBoundary: string;
}

export interface WebEvidenceAdapterResult {
  title: string;
  url: string;
  snippet: string;
  sourceTier?: WebEvidenceSourceTier;
  excerpts?: string[];
  claimedSupports?: EvidenceClaimSupport[];
}

export interface WebEvidenceAdapterResponse {
  taskId: string;
  requestId?: string;
  provider: string;
  results: WebEvidenceAdapterResult[];
}

export interface RejectedWebEvidenceAdapterResult {
  taskId: string;
  title: string;
  provider: string;
  reason: string;
}

export interface WebEvidenceSearchAdapterNormalizationResult {
  protocol: "web_evidence_search_adapter_normalization_v1";
  captureNormalization: WebEvidenceCaptureNormalizationResult;
  rejectedAdapterResults: RejectedWebEvidenceAdapterResult[];
  claimBoundary: string;
}

export type PublicOpinionSearchIntent =
  | "low_attention_signal"
  | "counter_evidence"
  | "hype_pressure"
  | "regional_preference"
  | "source_diversity";

const REQUEST_BOUNDARY =
  "Search requests do not support claims. They tell a search provider what evidence to retrieve for later capture and intake.";

const NORMALIZATION_BOUNDARY =
  "Search adapter normalization maps provider results into capture submissions. Claims are supported only after capture normalization and evidence intake.";

export function buildWebEvidenceSearchRequests({
  workspace,
  maxResultsPerTask = 3,
}: {
  workspace: Pick<EvidenceCollectionWorkspace, "taskRows"> & Partial<Pick<EvidenceCollectionWorkspace, "evidenceGapSearchPlan">>;
  maxResultsPerTask?: number;
}): WebEvidenceSearchRequestBatch {
  const normalRequests = workspace.taskRows
    .filter((row) => row.status !== "accepted")
    .flatMap((row) => buildRequestsForTaskRow(row, maxResultsPerTask));
  const normalRequestTaskIds = new Set(normalRequests.map((request) => request.taskId));
  const gapRequests = workspace.evidenceGapSearchPlan?.followUps
    .filter((followUp) => followUp.gapStatus !== "unsupported" || !followUp.taskId || !normalRequestTaskIds.has(followUp.taskId))
    .map((followUp) => ({
      requestId: followUp.id,
      taskId: followUp.taskId ?? followUp.id,
      taskType: followUp.taskType ?? "public_opinion_scan",
      query: followUp.query,
      domains: followUp.domains,
      sourceTier: followUp.sourceTier,
      allowedClaims: [followUp.claim],
      maxResults: maxResultsPerTask,
    })) ?? [];

  return {
    protocol: "web_evidence_search_requests_v1",
    requests: [...normalRequests, ...gapRequests],
    claimBoundary: REQUEST_BOUNDARY,
  };
}

function buildRequestsForTaskRow(
  row: EvidenceCollectionTaskRow,
  maxResults: number,
): WebEvidenceSearchAdapterRequest[] {
  if (row.taskType === "public_opinion_scan") {
    return buildPublicOpinionSearchRequests(row, maxResults);
  }
  return [baseRequestForTaskRow(row, maxResults)];
}

function baseRequestForTaskRow(
  row: EvidenceCollectionTaskRow,
  maxResults: number,
): WebEvidenceSearchAdapterRequest {
  return {
    requestId: row.taskId,
    taskId: row.taskId,
    taskType: row.taskType,
    query: row.primaryQuery,
    domains: row.preferredDomains,
    sourceTier: row.resultTemplate.sourceTier,
    allowedClaims: row.resultTemplate.claimedSupports,
    maxResults,
  };
}

function buildPublicOpinionSearchRequests(
  row: EvidenceCollectionTaskRow,
  maxResults: number,
): WebEvidenceSearchAdapterRequest[] {
  const base = row.primaryQuery.trim();
  const domains = publicOpinionDomains(row.preferredDomains);
  const proofBoundary = [
    "official plan",
    "admission probability",
    "final recommendation",
  ];
  const variants: Array<{
    searchIntent: PublicOpinionSearchIntent;
    query: string;
    evidenceQuestion: string;
  }> = [
    {
      searchIntent: "low_attention_signal",
      query: `${base} low attention overlooked cold discussion parent concern`,
      evidenceQuestion: "Does dated public discussion show low attention or avoidance around this school and major?",
    },
    {
      searchIntent: "counter_evidence",
      query: `${base} counter-evidence widely discussed mainstream attention popular`,
      evidenceQuestion: "What evidence would disprove the low-attention hypothesis or show broad recognition?",
    },
    {
      searchIntent: "hype_pressure",
      query: `${base} hype pressure hot major high salary everyone applying`,
      evidenceQuestion: "Is the topic crowded or hyped enough to block hidden-opportunity wording?",
    },
    {
      searchIntent: "regional_preference",
      query: `${base} local preference distance concern family discussion non-local`,
      evidenceQuestion: "Do family discussions show regional preference, distance fear, or adjustment avoidance?",
    },
    {
      searchIntent: "source_diversity",
      query: `${base} forum article social media search snippet admissions discussion`,
      evidenceQuestion: "Can the same trend be checked across different source kinds instead of one anecdote?",
    },
  ];

  return variants.map((variant) => ({
    requestId: `${row.taskId}-${variant.searchIntent}`,
    taskId: row.taskId,
    taskType: row.taskType,
    query: variant.query,
    domains,
    sourceTier: row.resultTemplate.sourceTier,
    allowedClaims: row.resultTemplate.claimedSupports,
    maxResults,
    searchIntent: variant.searchIntent,
    evidenceQuestion: variant.evidenceQuestion,
    rejectsAsProof: proofBoundary,
  }));
}

function publicOpinionDomains(preferredDomains: string[]): string[] {
  return unique([
    ...preferredDomains,
    "zhihu.com",
    "xiaohongshu.com",
    "weibo.com",
    "baidu.com",
  ]);
}

function unique<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

export function normalizeWebEvidenceSearchAdapterResults({
  workspace,
  responses,
  capturedAt,
}: {
  workspace: Pick<EvidenceCollectionWorkspace, "taskRows">;
  responses: WebEvidenceAdapterResponse[];
  capturedAt: string;
}): WebEvidenceSearchAdapterNormalizationResult {
  const rowsById = new Map(workspace.taskRows.map((row) => [row.taskId, row]));
  const submissions: WebEvidenceCaptureSubmission[] = [];
  const rejectedAdapterResults: RejectedWebEvidenceAdapterResult[] = [];

  for (const response of responses) {
    const taskRow = rowsById.get(response.taskId);
    for (const result of response.results) {
      const rejection = validateAdapterResult(taskRow, result);
      if (rejection) {
        rejectedAdapterResults.push({
          taskId: response.taskId,
          title: result.title,
          provider: response.provider,
          reason: rejection,
        });
        continue;
      }

      const row = taskRow as EvidenceCollectionTaskRow;
      submissions.push({
        taskId: response.taskId,
        sourceTitle: result.title,
        sourceUrl: result.url,
        sourceTier: result.sourceTier ?? row.resultTemplate.sourceTier,
        excerpts: result.excerpts && result.excerpts.length > 0 ? result.excerpts : [result.snippet],
        claimedSupports: result.claimedSupports ?? row.resultTemplate.claimedSupports,
        capturedAt,
      });
    }
  }

  return {
    protocol: "web_evidence_search_adapter_normalization_v1",
    captureNormalization: normalizeWebEvidenceCaptureSubmissions({
      workspace: workspace as EvidenceCollectionWorkspace,
      submissions,
      capturedAt,
    }),
    rejectedAdapterResults,
    claimBoundary: NORMALIZATION_BOUNDARY,
  };
}

function validateAdapterResult(
  taskRow: EvidenceCollectionTaskRow | undefined,
  result: WebEvidenceAdapterResult,
): string | null {
  if (!taskRow) {
    return "Adapter result does not match any evidence task.";
  }
  if (!result.title?.trim()) {
    return "Adapter result requires a title.";
  }
  if (!result.url?.trim()) {
    return "Adapter result requires a URL.";
  }
  const excerpts = result.excerpts && result.excerpts.length > 0 ? result.excerpts : [result.snippet];
  if (excerpts.map((excerpt) => excerpt.trim()).filter(Boolean).length === 0) {
    return "Adapter result requires a snippet or excerpt.";
  }
  const sourceTier = result.sourceTier ?? taskRow.resultTemplate.sourceTier;
  if (sourceTier !== taskRow.resultTemplate.sourceTier) {
    return `Adapter result source tier ${sourceTier} does not match required ${taskRow.resultTemplate.sourceTier}.`;
  }

  const allowedClaims = new Set(taskRow.resultTemplate.claimedSupports);
  const claimedSupports = result.claimedSupports ?? taskRow.resultTemplate.claimedSupports;
  const invalidClaim = claimedSupports.find((claim) => !allowedClaims.has(claim));
  if (invalidClaim) {
    return `Claim ${invalidClaim} is not allowed for ${taskRow.taskType}.`;
  }
  return null;
}

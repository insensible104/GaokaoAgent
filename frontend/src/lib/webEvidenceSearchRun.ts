import type { EvidenceCollectionWorkspace } from "./evidenceCollectionWorkspace";
import type { WebEvidenceSearchResult } from "./webEvidenceIntake";
import {
  buildWebEvidenceSearchRequests,
  normalizeWebEvidenceSearchAdapterResults,
  type RejectedWebEvidenceAdapterResult,
  type WebEvidenceAdapterResult,
  type WebEvidenceAdapterResponse,
  type WebEvidenceSearchAdapterRequest,
  type WebEvidenceSearchAdapterNormalizationResult,
  type WebEvidenceSearchRequestBatch,
} from "./webEvidenceSearchAdapter";

export type WebEvidenceSearchRunStatus =
  | "completed"
  | "partial_success"
  | "needs_manual_review"
  | "no_results";

export interface WebEvidenceSearchRun {
  protocol: "web_evidence_search_run_v1";
  status: WebEvidenceSearchRunStatus;
  requestBatch: WebEvidenceSearchRequestBatch;
  searchTrace: WebEvidenceSearchTrace;
  providerResponseCount: number;
  acceptedEvidenceResults: WebEvidenceSearchResult[];
  rejectedAdapterResults: RejectedWebEvidenceAdapterResult[];
  rejectedCaptureSubmissions: WebEvidenceSearchAdapterNormalizationResult["captureNormalization"]["rejectedSubmissions"];
  unreturnedTaskIds: string[];
  nextActions: string[];
  claimBoundary: string;
}

export type WebEvidenceSearchTraceOutcome = "accepted" | "rejected" | "unreturned";

export interface WebEvidenceSearchTraceRow {
  requestId: string;
  taskId: string;
  taskType: WebEvidenceSearchAdapterRequest["taskType"];
  query: string;
  domains: string[];
  searchIntent?: WebEvidenceSearchAdapterRequest["searchIntent"];
  evidenceQuestion?: string;
  rejectsAsProof: string[];
  provider: string | null;
  outcome: WebEvidenceSearchTraceOutcome;
  sourceTitle: string | null;
  sourceUrl: string | null;
  sourceTier: WebEvidenceSearchAdapterRequest["sourceTier"] | null;
  claimedSupports: WebEvidenceSearchAdapterRequest["allowedClaims"];
  rejectionReason: string | null;
}

export interface WebEvidenceSearchTrace {
  protocol: "web_evidence_search_trace_v1";
  rows: WebEvidenceSearchTraceRow[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Search runs collect candidate evidence and normalize it for intake. They do not support claims or make final recommendations by themselves.";

const TRACE_CLAIM_BOUNDARY =
  "Search trace rows show query and provider provenance only. They do not support claims until evidence intake accepts the captured excerpts.";

export function buildWebEvidenceSearchRun({
  workspace,
  responses,
  capturedAt,
}: {
  workspace: Pick<EvidenceCollectionWorkspace, "taskRows"> & Partial<Pick<EvidenceCollectionWorkspace, "evidenceGapSearchPlan">>;
  responses: WebEvidenceAdapterResponse[];
  capturedAt: string;
}): WebEvidenceSearchRun {
  const requestBatch = buildWebEvidenceSearchRequests({ workspace });
  const normalization = normalizeWebEvidenceSearchAdapterResults({
    workspace,
    responses,
    capturedAt,
  });
  const acceptedEvidenceResults = normalization.captureNormalization.evidenceResults;
  const rejectedAdapterResults = normalization.rejectedAdapterResults;
  const rejectedCaptureSubmissions = normalization.captureNormalization.rejectedSubmissions;
  const unreturnedRequests = findUnreturnedRequests(requestBatch, responses);
  const unreturnedTaskIds = unique(unreturnedRequests.map((request) => request.taskId));

  return {
    protocol: "web_evidence_search_run_v1",
    status: resolveStatus({
      acceptedCount: acceptedEvidenceResults.length,
      rejectedCount: rejectedAdapterResults.length + rejectedCaptureSubmissions.length,
      unreturnedCount: unreturnedTaskIds.length,
      requestedCount: requestBatch.requests.length,
    }),
    requestBatch,
    searchTrace: buildSearchTrace({
      requestBatch,
      responses,
      acceptedEvidenceResults,
      rejectedAdapterResults,
      unreturnedRequests,
    }),
    providerResponseCount: responses.length,
    acceptedEvidenceResults,
    rejectedAdapterResults,
    rejectedCaptureSubmissions,
    unreturnedTaskIds,
    nextActions: buildNextActions({
      acceptedEvidenceResults,
      rejectedAdapterResults,
      rejectedCaptureSubmissions,
      unreturnedTaskIds,
    }),
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildSearchTrace({
  requestBatch,
  responses,
  acceptedEvidenceResults,
  rejectedAdapterResults,
  unreturnedRequests,
}: {
  requestBatch: WebEvidenceSearchRequestBatch;
  responses: WebEvidenceAdapterResponse[];
  acceptedEvidenceResults: WebEvidenceSearchResult[];
  rejectedAdapterResults: RejectedWebEvidenceAdapterResult[];
  unreturnedRequests: WebEvidenceSearchAdapterRequest[];
}): WebEvidenceSearchTrace {
  const requestsByRequestId = new Map(requestBatch.requests.map((request) => [request.requestId, request]));
  const requestsByTaskId = groupByTaskId(requestBatch.requests);
  const rejectedByTaskTitle = new Map(
    rejectedAdapterResults.map((result) => [`${result.taskId}\u0000${result.title}`, result]),
  );
  const acceptedByTaskTitle = new Map(
    acceptedEvidenceResults.map((result) => [`${result.taskId}\u0000${result.sourceTitle}`, result]),
  );
  const rows: WebEvidenceSearchTraceRow[] = [];

  for (const response of responses) {
    const request = response.requestId
      ? requestsByRequestId.get(response.requestId)
      : requestsByTaskId.get(response.taskId)?.[0];
    if (!request) {
      continue;
    }

    for (const result of response.results) {
      const rejected = rejectedByTaskTitle.get(`${response.taskId}\u0000${result.title}`);
      const accepted = acceptedByTaskTitle.get(`${response.taskId}\u0000${result.title}`);
      rows.push(traceRowForResult({
        request,
        response,
        result,
        outcome: rejected ? "rejected" : accepted ? "accepted" : "rejected",
        rejectionReason: rejected?.reason ?? (accepted ? null : "Provider result did not pass normalization."),
      }));
    }
  }

  for (const request of unreturnedRequests) {
    rows.push({
      requestId: request.requestId,
      taskId: request.taskId,
      taskType: request.taskType,
      query: request.query,
      domains: request.domains,
      searchIntent: request.searchIntent,
      evidenceQuestion: request.evidenceQuestion,
      rejectsAsProof: request.rejectsAsProof ?? [],
      provider: null,
      outcome: "unreturned",
      sourceTitle: null,
      sourceUrl: null,
      sourceTier: request.sourceTier,
      claimedSupports: request.allowedClaims,
      rejectionReason: "No provider response returned for this request.",
    });
  }

  return {
    protocol: "web_evidence_search_trace_v1",
    rows,
    claimBoundary: TRACE_CLAIM_BOUNDARY,
  };
}

function traceRowForResult({
  request,
  response,
  result,
  outcome,
  rejectionReason,
}: {
  request: WebEvidenceSearchAdapterRequest;
  response: WebEvidenceAdapterResponse;
  result: WebEvidenceAdapterResult;
  outcome: Exclude<WebEvidenceSearchTraceOutcome, "unreturned">;
  rejectionReason: string | null;
}): WebEvidenceSearchTraceRow {
  return {
    requestId: request.requestId,
    taskId: response.taskId,
    taskType: request.taskType,
    query: request.query,
    domains: request.domains,
    searchIntent: request.searchIntent,
    evidenceQuestion: request.evidenceQuestion,
    rejectsAsProof: request.rejectsAsProof ?? [],
    provider: response.provider,
    outcome,
    sourceTitle: result.title,
    sourceUrl: result.url,
    sourceTier: result.sourceTier ?? request.sourceTier,
    claimedSupports: result.claimedSupports ?? request.allowedClaims,
    rejectionReason,
  };
}

function findUnreturnedRequests(
  requestBatch: WebEvidenceSearchRequestBatch,
  responses: WebEvidenceAdapterResponse[],
): WebEvidenceSearchAdapterRequest[] {
  const returnedTaskIds = new Set(
    responses.filter((response) => !response.requestId).map((response) => response.taskId),
  );
  const returnedRequestIds = new Set(
    responses.map((response) => response.requestId).filter((requestId): requestId is string => Boolean(requestId)),
  );
  return requestBatch.requests
    .filter((request) => !returnedTaskIds.has(request.taskId) && !returnedRequestIds.has(request.requestId));
}

function groupByTaskId(
  requests: WebEvidenceSearchAdapterRequest[],
): Map<string, WebEvidenceSearchAdapterRequest[]> {
  const grouped = new Map<string, WebEvidenceSearchAdapterRequest[]>();
  for (const request of requests) {
    grouped.set(request.taskId, [...(grouped.get(request.taskId) ?? []), request]);
  }
  return grouped;
}

function resolveStatus({
  acceptedCount,
  rejectedCount,
  unreturnedCount,
  requestedCount,
}: {
  acceptedCount: number;
  rejectedCount: number;
  unreturnedCount: number;
  requestedCount: number;
}): WebEvidenceSearchRunStatus {
  if (acceptedCount === 0 && requestedCount > 0) {
    return "no_results";
  }
  if (rejectedCount > 0 || unreturnedCount > 0) {
    return "partial_success";
  }
  if (requestedCount === 0) {
    return "completed";
  }
  return "completed";
}

function unique<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

function buildNextActions({
  acceptedEvidenceResults,
  rejectedAdapterResults,
  rejectedCaptureSubmissions,
  unreturnedTaskIds,
}: {
  acceptedEvidenceResults: WebEvidenceSearchResult[];
  rejectedAdapterResults: RejectedWebEvidenceAdapterResult[];
  rejectedCaptureSubmissions: WebEvidenceSearchAdapterNormalizationResult["captureNormalization"]["rejectedSubmissions"];
  unreturnedTaskIds: string[];
}): string[] {
  const actions: string[] = [];
  if (acceptedEvidenceResults.length > 0) {
    actions.push(`Attach ${acceptedEvidenceResults.length} normalized evidence results to evidence intake.`);
  }
  if (unreturnedTaskIds.length > 0) {
    actions.push(`Manually capture or rerun search for ${unreturnedTaskIds.join(", ")}.`);
  }
  if (rejectedAdapterResults.length + rejectedCaptureSubmissions.length > 0) {
    actions.push("Review rejected provider results before using them as evidence.");
  }
  if (actions.length === 0) {
    actions.push("No search results were accepted. Revise queries, domains, or provider settings before counselor review.");
  }
  actions.push("Keep final recommendation blocked until evidence intake and triangulation pass.");
  return actions;
}

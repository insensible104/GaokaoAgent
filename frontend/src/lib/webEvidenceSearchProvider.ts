import type { EvidenceCollectionWorkspace } from "./evidenceCollectionWorkspace";
import {
  buildWebEvidenceSearchRequests,
  type WebEvidenceAdapterResponse,
  type WebEvidenceAdapterResult,
  type WebEvidenceSearchAdapterRequest,
  type WebEvidenceSearchRequestBatch,
} from "./webEvidenceSearchAdapter";
import {
  buildWebEvidenceSearchRun,
  type WebEvidenceSearchRun,
} from "./webEvidenceSearchRun";

export interface WebEvidenceSearchProvider {
  id: string;
  search: (request: WebEvidenceSearchAdapterRequest) => Promise<WebEvidenceAdapterResult[]>;
}

export interface FailedWebEvidenceProviderRequest {
  requestId: string;
  taskId: string;
  providerId: string;
  reason: string;
}

export interface WebEvidenceSearchProviderExecution {
  protocol: "web_evidence_search_provider_execution_v1";
  providerId: string;
  status: "completed" | "partial_success" | "failed";
  requestBatch: WebEvidenceSearchRequestBatch;
  providerResponses: WebEvidenceAdapterResponse[];
  failedRequests: FailedWebEvidenceProviderRequest[];
  searchRun: WebEvidenceSearchRun;
  nextActions: string[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Provider execution retrieves candidate evidence for audit. Claims are supported only after capture normalization, evidence intake, triangulation, and counselor review.";

export async function executeWebEvidenceSearchProvider({
  workspace,
  provider,
  capturedAt,
}: {
  workspace: Pick<EvidenceCollectionWorkspace, "taskRows"> & Partial<Pick<EvidenceCollectionWorkspace, "evidenceGapSearchPlan">>;
  provider: WebEvidenceSearchProvider;
  capturedAt: string;
}): Promise<WebEvidenceSearchProviderExecution> {
  const requestBatch = buildWebEvidenceSearchRequests({ workspace });
  const providerResponses: WebEvidenceAdapterResponse[] = [];
  const failedRequests: FailedWebEvidenceProviderRequest[] = [];

  for (const request of requestBatch.requests) {
    try {
      const results = await provider.search(request);
      providerResponses.push({
        requestId: request.requestId,
        taskId: request.taskId,
        provider: provider.id,
        results,
      });
    } catch (error) {
      failedRequests.push({
        requestId: request.requestId,
        taskId: request.taskId,
        providerId: provider.id,
        reason: error instanceof Error ? error.message : String(error),
      });
    }
  }

  const searchRun = buildWebEvidenceSearchRun({
    workspace,
    responses: providerResponses,
    capturedAt,
  });

  return {
    protocol: "web_evidence_search_provider_execution_v1",
    providerId: provider.id,
    status: resolveExecutionStatus({
      requestCount: requestBatch.requests.length,
      responseCount: providerResponses.length,
      failureCount: failedRequests.length,
      acceptedCount: searchRun.acceptedEvidenceResults.length,
      rejectedCount: searchRun.rejectedAdapterResults.length + searchRun.rejectedCaptureSubmissions.length,
      unreturnedCount: searchRun.unreturnedTaskIds.length,
    }),
    requestBatch,
    providerResponses,
    failedRequests,
    searchRun,
    nextActions: buildProviderNextActions({ failedRequests, searchRun }),
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function resolveExecutionStatus({
  requestCount,
  responseCount,
  failureCount,
  acceptedCount,
  rejectedCount,
  unreturnedCount,
}: {
  requestCount: number;
  responseCount: number;
  failureCount: number;
  acceptedCount: number;
  rejectedCount: number;
  unreturnedCount: number;
}): WebEvidenceSearchProviderExecution["status"] {
  if (requestCount > 0 && responseCount === 0 && acceptedCount === 0) {
    return "failed";
  }
  if (failureCount > 0 || rejectedCount > 0 || unreturnedCount > 0 || acceptedCount < requestCount) {
    return "partial_success";
  }
  return "completed";
}

function buildProviderNextActions({
  failedRequests,
  searchRun,
}: {
  failedRequests: FailedWebEvidenceProviderRequest[];
  searchRun: WebEvidenceSearchRun;
}): string[] {
  const actions: string[] = [];
  if (failedRequests.length > 0) {
    actions.push(`Retry failed provider requests for ${failedRequests.map((request) => request.taskId).join(", ")}.`);
  }
  actions.push(...searchRun.nextActions);
  return actions;
}

import { buildApiUrl } from "./api";
import type { DeepEvidenceCollectionContext, DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { EvidenceAutopilotSearchTask } from "./evidenceAutopilot";
import type { EvidenceAutopilotProviderResult } from "./evidenceAutopilotProvider";
import { buildEvidenceAutopilotSnapshotProviderResults } from "./evidenceAutopilotSnapshotProvider";

export type EvidenceAutopilotBackendStatus =
  | "demo_snapshot"
  | "backend_connected"
  | "backend_failed_snapshot_fallback";

interface BackendEvidenceCard {
  taskId: string;
  sourceTitle: string;
  sourceUrl: string;
  sourceType: EvidenceAutopilotProviderResult["sourceType"];
  excerpt: string;
  capturedAt: string;
  confidence: EvidenceAutopilotProviderResult["confidence"];
}

export interface EvidenceAutopilotBackendResponse {
  success: boolean;
  targetLabel: string;
  tasks: unknown[];
  searchQueries: string[];
  evidenceCards: BackendEvidenceCard[];
  claimBoundary: string;
}

export interface EvidenceAutopilotApiState {
  status: EvidenceAutopilotBackendStatus;
  providerResults: EvidenceAutopilotProviderResult[];
  claimBoundary: string;
  backendResponse?: EvidenceAutopilotBackendResponse;
  error?: string;
}

type FetchLike = (url: string, init: RequestInit) => Promise<{
  ok: boolean;
  status?: number;
  json(): Promise<unknown>;
}>;

export function buildEvidenceAutopilotResearchPayload(
  context: DeepEvidenceCollectionContext,
) {
  return {
    province: context.province,
    schoolName: context.schoolName,
    majorName: context.majorName,
    targetYear: context.targetYear,
  };
}

export function mapBackendEvidenceCardsToProviderResults(
  response: EvidenceAutopilotBackendResponse,
): EvidenceAutopilotProviderResult[] {
  return response.evidenceCards
    .filter((card) => card.sourceUrl.trim() && card.excerpt.trim())
    .map((card, index) => ({
      requestId: `backend-${card.taskId}-${index + 1}`,
      taskId: card.taskId,
      sourceTitle: card.sourceTitle,
      sourceUrl: card.sourceUrl,
      sourceType: card.sourceType,
      excerpt: card.excerpt,
      capturedAt: card.capturedAt || "backend_runtime",
      confidence: card.confidence,
    }));
}

export function buildEvidenceAutopilotSnapshotFallback({
  plan,
  searchTasks,
  targetLabel,
  reason,
}: {
  plan: DeepEvidenceCollectionPlan;
  searchTasks: EvidenceAutopilotSearchTask[];
  targetLabel: string;
  reason: string;
}): EvidenceAutopilotApiState {
  return {
    status: "backend_failed_snapshot_fallback",
    providerResults: buildEvidenceAutopilotSnapshotProviderResults({ plan, searchTasks, targetLabel }),
    claimBoundary: `Using demo snapshot fallback: ${reason}. Live backend evidence still requires source URL, excerpt, capture time, and confidence.`,
    error: reason,
  };
}

export async function fetchEvidenceAutopilotResearch({
  context,
  fetchImpl = fetch,
  fallback,
}: {
  context: DeepEvidenceCollectionContext;
  fetchImpl?: FetchLike;
  fallback?: {
    plan: DeepEvidenceCollectionPlan;
    searchTasks: EvidenceAutopilotSearchTask[];
    targetLabel: string;
  };
}): Promise<EvidenceAutopilotApiState> {
  try {
    const response = await fetchImpl(buildApiUrl("/api/evidence-autopilot/research"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildEvidenceAutopilotResearchPayload(context)),
    });
    if (!response.ok) {
      throw new Error(`backend returned HTTP ${response.status ?? "error"}`);
    }
    const backendResponse = responseFromJson(await response.json());
    const providerResults = mapBackendEvidenceCardsToProviderResults(backendResponse);
    if (providerResults.length === 0 && fallback) {
      return buildEvidenceAutopilotSnapshotFallback({
        ...fallback,
        reason: "backend returned task placeholders without captured evidence",
      });
    }
    return {
      status: "backend_connected",
      providerResults,
      claimBoundary: backendResponse.claimBoundary,
      backendResponse,
    };
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    if (fallback) {
      return buildEvidenceAutopilotSnapshotFallback({ ...fallback, reason });
    }
    return {
      status: "backend_failed_snapshot_fallback",
      providerResults: [],
      claimBoundary: `Using demo snapshot fallback: ${reason}.`,
      error: reason,
    };
  }
}

function responseFromJson(value: unknown): EvidenceAutopilotBackendResponse {
  if (!value || typeof value !== "object") {
    throw new Error("backend response was not an object");
  }
  return value as EvidenceAutopilotBackendResponse;
}

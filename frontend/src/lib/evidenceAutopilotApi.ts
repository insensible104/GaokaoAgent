import { buildApiUrl } from "./api";
import type { DeepEvidenceCollectionContext, DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { EvidenceAutopilotSearchTask } from "./evidenceAutopilot";
import type { EvidenceAutopilotProviderResult } from "./evidenceAutopilotProvider";
import { buildEvidenceAutopilotSnapshotProviderResults } from "./evidenceAutopilotSnapshotProvider";

export type EvidenceAutopilotBackendStatus =
  | "demo_snapshot"
  | "backend_connected"
  | "backend_failed_snapshot_fallback"
  | "real_case_fixture";

type BackendEvidenceCardStatus = "requires_capture" | "operator_review" | "captured_candidate";

interface BackendEvidenceCard {
  taskId: string;
  status: BackendEvidenceCardStatus;
  sourceTitle: string;
  sourceUrl: string;
  sourceType: EvidenceAutopilotProviderResult["sourceType"];
  excerpt: string;
  capturedAt: string;
  confidence: EvidenceAutopilotProviderResult["confidence"];
}

const VALID_CARD_STATUSES = new Set(["requires_capture", "operator_review", "captured_candidate"]);
const VALID_SOURCE_TYPES = new Set(["official", "school", "paper", "job", "wechat", "discussion", "other"]);
const VALID_CONFIDENCE_LEVELS = new Set(["high", "medium", "low"]);

export interface EvidenceAutopilotBackendResponse {
  success: boolean;
  targetLabel: string;
  tasks: unknown[];
  searchQueries: string[];
  evidenceCards: BackendEvidenceCard[];
  evidenceCoverage: EvidenceAutopilotBackendCoverage;
  claimBoundary: string;
}

export interface EvidenceAutopilotBackendCoverage {
  totalTasks: number;
  capturedTaskIds: string[];
  missingP0TaskIds: string[];
  operatorTaskIds: string[];
  readyForCounselorReview: boolean;
  reviewBlockers: string[];
}

export interface EvidenceAutopilotApiState {
  status: EvidenceAutopilotBackendStatus;
  providerResults: EvidenceAutopilotProviderResult[];
  claimBoundary: string;
  evidenceCoverage?: EvidenceAutopilotBackendCoverage;
  backendResponse?: EvidenceAutopilotBackendResponse;
  error?: string;
}

type FetchLike = (url: string, init: RequestInit) => Promise<{
  ok: boolean;
  status?: number;
  json(): Promise<unknown>;
}>;

export interface EvidenceAutopilotResearchPayloadOptions {
  caseId?: string;
  enableReviewedEvidenceLedger?: boolean;
}

export function buildEvidenceAutopilotResearchPayload(
  context: DeepEvidenceCollectionContext,
  options: EvidenceAutopilotResearchPayloadOptions = {},
) {
  const payload: {
    province: string;
    schoolName: string;
    majorName: string;
    targetYear: number;
    caseId?: string;
    enableReviewedEvidenceLedger?: boolean;
  } = {
    province: context.province,
    schoolName: context.schoolName,
    majorName: context.majorName,
    targetYear: context.targetYear,
  };
  if (options.caseId) {
    payload.caseId = options.caseId;
  }
  if (options.enableReviewedEvidenceLedger) {
    payload.enableReviewedEvidenceLedger = true;
  }
  return payload;
}

export function mapBackendEvidenceCardsToProviderResults(
  response: EvidenceAutopilotBackendResponse,
): EvidenceAutopilotProviderResult[] {
  return response.evidenceCards
    .filter((card, index) => {
      assertValidBackendEvidenceCard(card, index);
      return card.status === "captured_candidate" && card.sourceUrl.trim() && card.excerpt.trim();
    })
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

export function buildEvidenceAutopilotRealCaseState({
  providerResults,
  claimBoundary,
}: {
  providerResults: EvidenceAutopilotProviderResult[];
  claimBoundary: string;
}): EvidenceAutopilotApiState {
  return {
    status: "real_case_fixture",
    providerResults,
    claimBoundary,
  };
}

export async function fetchEvidenceAutopilotResearch({
  context,
  caseId,
  enableReviewedEvidenceLedger,
  fetchImpl = fetch,
  fallback,
}: {
  context: DeepEvidenceCollectionContext;
  caseId?: string;
  enableReviewedEvidenceLedger?: boolean;
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
      body: JSON.stringify(buildEvidenceAutopilotResearchPayload(context, {
        caseId,
        enableReviewedEvidenceLedger,
      })),
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
      evidenceCoverage: backendResponse.evidenceCoverage,
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
  const response = value as EvidenceAutopilotBackendResponse;
  if (!Array.isArray(response.evidenceCards)) {
    throw new Error("backend response evidenceCards was not an array");
  }
  assertValidBackendCoverage(response.evidenceCoverage);
  return response;
}

function assertValidBackendEvidenceCard(card: BackendEvidenceCard, index: number): void {
  if (!VALID_CARD_STATUSES.has(card.status)) {
    throw new Error(`invalid backend evidence card ${index + 1}: status ${card.status}`);
  }
  if (!VALID_SOURCE_TYPES.has(card.sourceType)) {
    throw new Error(`invalid backend evidence card ${index + 1}: sourceType ${card.sourceType}`);
  }
  if (!VALID_CONFIDENCE_LEVELS.has(card.confidence)) {
    throw new Error(`invalid backend evidence card ${index + 1}: confidence ${card.confidence}`);
  }
}

function assertValidBackendCoverage(coverage: EvidenceAutopilotBackendCoverage): void {
  if (!coverage || typeof coverage !== "object") {
    throw new Error("backend response evidenceCoverage was not an object");
  }
  if (typeof coverage.totalTasks !== "number") {
    throw new Error("backend response evidenceCoverage totalTasks was not a number");
  }
  if (!Array.isArray(coverage.capturedTaskIds)) {
    throw new Error("backend response evidenceCoverage capturedTaskIds was not an array");
  }
  if (!Array.isArray(coverage.missingP0TaskIds)) {
    throw new Error("backend response evidenceCoverage missingP0TaskIds was not an array");
  }
  if (!Array.isArray(coverage.operatorTaskIds)) {
    throw new Error("backend response evidenceCoverage operatorTaskIds was not an array");
  }
  if (typeof coverage.readyForCounselorReview !== "boolean") {
    throw new Error("backend response evidenceCoverage readyForCounselorReview was not a boolean");
  }
  if (!Array.isArray(coverage.reviewBlockers)) {
    throw new Error("backend response evidenceCoverage reviewBlockers was not an array");
  }
}

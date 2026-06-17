import type {
  EvidenceClaimSupport,
  WebEvidenceResearchPlan,
  WebEvidenceResearchTask,
  WebEvidenceSourceTier,
} from "./webEvidencePlanner";

export interface WebEvidenceSearchResult {
  taskId: string;
  sourceTitle: string;
  sourceUrl: string;
  sourceTier: WebEvidenceSourceTier;
  capturedAt: string;
  excerpts: string[];
  claimedSupports: EvidenceClaimSupport[];
}

export interface AcceptedWebEvidence {
  taskId: string;
  claim: EvidenceClaimSupport;
  sourceTitle: string;
  sourceUrl: string;
  capturedAt: string;
  excerpts: string[];
}

export interface RejectedWebEvidence {
  taskId: string;
  claim: EvidenceClaimSupport;
  sourceTitle: string;
  reason: string;
}

export interface ClaimSupportStatus {
  status: "supported" | "unsupported";
  evidenceCount: number;
}

export interface WebEvidenceIntakeResult {
  protocol: "web_evidence_intake_v1";
  status: "review_ready" | "blocked";
  acceptedEvidence: AcceptedWebEvidence[];
  rejectedEvidence: RejectedWebEvidence[];
  blockedTasks: string[];
  claimSupport: Record<EvidenceClaimSupport, ClaimSupportStatus>;
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Evidence intake can make a case review-ready, not final. Final recommendation still requires counselor review and attached row-level artifacts.";

const CLAIMS: EvidenceClaimSupport[] = [
  "official_diff",
  "rank_delta",
  "risk_guard",
  "competitor_missed",
  "hypothesis_only",
  "parent_understanding",
  "final_recommendation",
];

export function evaluateWebEvidenceResults({
  evidencePlan,
  results,
}: {
  evidencePlan: WebEvidenceResearchPlan;
  results: WebEvidenceSearchResult[];
}): WebEvidenceIntakeResult {
  const tasksById = new Map(evidencePlan.tasks.map((task) => [task.id, task]));
  const acceptedEvidence: AcceptedWebEvidence[] = [];
  const rejectedEvidence: RejectedWebEvidence[] = [];
  const acceptedTaskIds = new Set<string>();

  for (const result of results) {
    const task = tasksById.get(result.taskId);
    if (!task) {
      for (const claim of result.claimedSupports) {
        rejectedEvidence.push({
          taskId: result.taskId,
          claim,
          sourceTitle: result.sourceTitle,
          reason: "Result does not match any planned evidence task.",
        });
      }
      continue;
    }

    for (const claim of result.claimedSupports) {
      const rejection = validateClaimSupport(task, result, claim);
      if (rejection) {
        rejectedEvidence.push({
          taskId: result.taskId,
          claim,
          sourceTitle: result.sourceTitle,
          reason: rejection,
        });
      } else {
        acceptedTaskIds.add(task.id);
        acceptedEvidence.push({
          taskId: result.taskId,
          claim,
          sourceTitle: result.sourceTitle,
          sourceUrl: result.sourceUrl,
          capturedAt: result.capturedAt,
          excerpts: result.excerpts,
        });
      }
    }
  }

  const blockedTasks = evidencePlan.tasks
    .filter((task) => task.blocksRecommendationReadiness && !acceptedTaskIds.has(task.id))
    .map((task) => `${task.taskType}:${task.id}`);
  const claimSupport = buildClaimSupport(acceptedEvidence);

  return {
    protocol: "web_evidence_intake_v1",
    status: blockedTasks.length === 0 ? "review_ready" : "blocked",
    acceptedEvidence,
    rejectedEvidence,
    blockedTasks,
    claimSupport,
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function validateClaimSupport(
  task: WebEvidenceResearchTask,
  result: WebEvidenceSearchResult,
  claim: EvidenceClaimSupport,
): string | null {
  if (claim === "final_recommendation") {
    return "Search evidence cannot support final_recommendation directly.";
  }
  if (!task.canSupportClaims.includes(claim)) {
    return `Task ${task.taskType} does not allow ${result.sourceTier} evidence to support ${claim}.`;
  }
  if (result.sourceTier !== task.sourceTier) {
    return `${claim} requires ${task.sourceTier} evidence, but this result is ${result.sourceTier}.`;
  }
  if (result.excerpts.length === 0) {
    return `${claim} requires at least one captured excerpt.`;
  }
  return null;
}

function buildClaimSupport(acceptedEvidence: AcceptedWebEvidence[]): WebEvidenceIntakeResult["claimSupport"] {
  return CLAIMS.reduce<WebEvidenceIntakeResult["claimSupport"]>((acc, claim) => {
    const evidenceCount = acceptedEvidence.filter((item) => item.claim === claim).length;
    acc[claim] = {
      status: evidenceCount > 0 ? "supported" : "unsupported",
      evidenceCount,
    };
    return acc;
  }, {} as WebEvidenceIntakeResult["claimSupport"]);
}

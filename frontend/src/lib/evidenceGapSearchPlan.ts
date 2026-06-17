import type { EvidenceCollectionTaskRow } from "./evidenceCollectionWorkspace";
import type {
  EvidenceTriangulationClaim,
  EvidenceTriangulationClaimStatus,
  EvidenceTriangulationReport,
} from "./evidenceTriangulationReport";
import type { EvidenceClaimSupport, WebEvidenceSourceTier, WebEvidenceTaskType } from "./webEvidencePlanner";

export type EvidenceGapStatus = Extract<
  EvidenceTriangulationClaimStatus,
  "unsupported" | "needs_second_source" | "conflicted"
>;

export interface EvidenceGapSearchFollowUp {
  id: string;
  claim: EvidenceClaimSupport;
  taskId?: string;
  taskType?: WebEvidenceTaskType;
  gapStatus: EvidenceGapStatus;
  priority: "blocking" | "context";
  sourceTier: WebEvidenceSourceTier;
  query: string;
  domains: string[];
  existingSourceHosts: string[];
  reason: string;
  nextActions: string[];
  blocksCounselorReview: boolean;
}

export interface EvidenceGapSearchPlan {
  protocol: "evidence_gap_search_plan_v1";
  status: "ready_to_search" | "no_gaps";
  followUps: EvidenceGapSearchFollowUp[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Evidence gap search plans turn triangulation gaps into follow-up searches. Search plans do not prove claims until captured sources pass intake and triangulation.";

export function buildEvidenceGapSearchPlan({
  triangulationReport,
  taskRows,
}: {
  triangulationReport: EvidenceTriangulationReport;
  taskRows: EvidenceCollectionTaskRow[];
}): EvidenceGapSearchPlan {
  const followUps = triangulationReport.claims
    .filter((claim): claim is EvidenceTriangulationClaim & { status: EvidenceGapStatus } => isEvidenceGapStatus(claim.status))
    .map((claim) => buildFollowUp(claim, taskRows))
    .filter(Boolean) as EvidenceGapSearchFollowUp[];

  return {
    protocol: "evidence_gap_search_plan_v1",
    status: followUps.length > 0 ? "ready_to_search" : "no_gaps",
    followUps,
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildFollowUp(
  claim: EvidenceTriangulationClaim & { status: EvidenceGapStatus },
  taskRows: EvidenceCollectionTaskRow[],
): EvidenceGapSearchFollowUp | null {
  const taskRow = taskRows.find((row) => row.resultTemplate.claimedSupports.includes(claim.claim));
  if (!taskRow) {
    return null;
  }
  const reason = claim.issues[0] ?? claim.nextActions[0] ?? `${claim.claim} needs more evidence.`;

  return {
    id: `${taskRow.taskId}-${claim.status}-follow-up`,
    claim: claim.claim,
    taskId: taskRow.taskId,
    taskType: taskRow.taskType,
    gapStatus: claim.status,
    priority: taskRow.priority,
    sourceTier: taskRow.resultTemplate.sourceTier,
    query: buildFollowUpQuery(taskRow.primaryQuery, claim),
    domains: taskRow.preferredDomains,
    existingSourceHosts: claim.sourceHosts,
    reason,
    nextActions: claim.nextActions.length > 0 ? claim.nextActions : [`Capture additional evidence for ${claim.claim}.`],
    blocksCounselorReview: taskRow.priority === "blocking",
  };
}

function buildFollowUpQuery(
  primaryQuery: string,
  claim: EvidenceTriangulationClaim & { status: EvidenceGapStatus },
): string {
  if (claim.status === "needs_second_source") {
    const excludedHosts = claim.sourceHosts.map((host) => `-site:${host}`).join(" ");
    return `${primaryQuery} second independent source ${excludedHosts}`.trim();
  }
  if (claim.status === "conflicted") {
    return `${primaryQuery} counter evidence conflict ${claim.claim}`;
  }
  return primaryQuery;
}

function isEvidenceGapStatus(status: EvidenceTriangulationClaimStatus): status is EvidenceGapStatus {
  return status === "unsupported" || status === "needs_second_source" || status === "conflicted";
}

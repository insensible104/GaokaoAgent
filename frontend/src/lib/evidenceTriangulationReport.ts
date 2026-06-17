import type { AcceptedWebEvidence, RejectedWebEvidence, WebEvidenceIntakeResult } from "./webEvidenceIntake";
import type { EvidenceClaimSupport } from "./webEvidencePlanner";

export type EvidenceTriangulationClaimStatus =
  | "authoritative"
  | "triangulated"
  | "needs_second_source"
  | "unsupported"
  | "conflicted"
  | "hypothesis_only"
  | "explained"
  | "forbidden";

export interface EvidenceTriangulationClaim {
  claim: EvidenceClaimSupport;
  status: EvidenceTriangulationClaimStatus;
  acceptedEvidenceCount: number;
  distinctSourceHosts: number;
  sourceHosts: string[];
  sourceTitles: string[];
  issues: string[];
  nextActions: string[];
}

export interface EvidenceTriangulationSummary {
  totalAcceptedEvidence: number;
  conflictedClaims: number;
  claimsNeedingMoreEvidence: number;
  authoritativeClaims: number;
  triangulatedClaims: number;
}

export interface EvidenceTriangulationReport {
  protocol: "evidence_triangulation_report_v1";
  status: "triangulated" | "needs_more_evidence" | "conflict_review";
  summary: EvidenceTriangulationSummary;
  claims: EvidenceTriangulationClaim[];
  claimBoundary: string;
}

const CLAIMS: EvidenceClaimSupport[] = [
  "official_diff",
  "rank_delta",
  "risk_guard",
  "competitor_missed",
  "hypothesis_only",
  "parent_understanding",
  "final_recommendation",
];

const AUTHORITATIVE_SINGLE_SOURCE_CLAIMS = new Set<EvidenceClaimSupport>([
  "official_diff",
  "risk_guard",
  "parent_understanding",
]);

const TRIANGULATED_CLAIMS = new Set<EvidenceClaimSupport>([
  "rank_delta",
  "competitor_missed",
]);

const CLAIM_BOUNDARY =
  "Evidence triangulation audits source diversity, conflicts, and claim boundaries. It does not make final recommendations.";

export function buildEvidenceTriangulationReport({
  intakeResult,
}: {
  intakeResult: WebEvidenceIntakeResult;
}): EvidenceTriangulationReport {
  const claims = CLAIMS.map((claim) => buildClaimReport(claim, intakeResult));
  const summary = buildSummary(claims, intakeResult.acceptedEvidence.length);
  const status = summary.conflictedClaims > 0
    ? "conflict_review"
    : summary.claimsNeedingMoreEvidence > 0
      ? "needs_more_evidence"
      : "triangulated";

  return {
    protocol: "evidence_triangulation_report_v1",
    status,
    summary,
    claims,
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildClaimReport(
  claim: EvidenceClaimSupport,
  intakeResult: WebEvidenceIntakeResult,
): EvidenceTriangulationClaim {
  const accepted = intakeResult.acceptedEvidence.filter((item) => item.claim === claim);
  const rejected = intakeResult.rejectedEvidence.filter((item) => item.claim === claim);
  const sourceHosts = unique(accepted.map((item) => sourceHost(item.sourceUrl)));
  const sourceTitles = unique(accepted.map((item) => item.sourceTitle));
  const conflictReasons = rejected
    .map((item) => item.reason)
    .filter((reason) => isConflictReason(reason));
  const issues: string[] = [];
  const nextActions: string[] = [];
  const status = resolveClaimStatus({
    claim,
    accepted,
    sourceHosts,
    conflictReasons,
    issues,
    nextActions,
  });

  if (status === "unsupported") {
    issues.push(`No accepted evidence supports ${claim}.`);
    nextActions.push(`Capture accepted evidence for ${claim} before using it in an interpretation package.`);
  }
  for (const reason of conflictReasons) {
    issues.push(reason);
  }
  if (conflictReasons.length > 0) {
    nextActions.push(`Resolve conflicting evidence for ${claim} before counselor review.`);
  }

  return {
    claim,
    status,
    acceptedEvidenceCount: accepted.length,
    distinctSourceHosts: sourceHosts.length,
    sourceHosts,
    sourceTitles,
    issues,
    nextActions,
  };
}

function resolveClaimStatus({
  claim,
  accepted,
  sourceHosts,
  conflictReasons,
  issues,
  nextActions,
}: {
  claim: EvidenceClaimSupport;
  accepted: AcceptedWebEvidence[];
  sourceHosts: string[];
  conflictReasons: string[];
  issues: string[];
  nextActions: string[];
}): EvidenceTriangulationClaimStatus {
  if (claim === "final_recommendation") {
    issues.push("final_recommendation cannot be supported by search evidence.");
    nextActions.push("Keep final filing decisions behind counselor signoff.");
    return "forbidden";
  }
  if (conflictReasons.length > 0) {
    return "conflicted";
  }
  if (accepted.length === 0) {
    return "unsupported";
  }
  if (claim === "hypothesis_only") {
    nextActions.push("Keep public-opinion evidence as hypothesis-only and look for counter-evidence.");
    return "hypothesis_only";
  }
  if (claim === "parent_understanding") {
    return "explained";
  }
  if (AUTHORITATIVE_SINGLE_SOURCE_CLAIMS.has(claim)) {
    return "authoritative";
  }
  if (TRIANGULATED_CLAIMS.has(claim) && sourceHosts.length < 2) {
    issues.push(`${claim} has only one independent source host.`);
    nextActions.push(`Attach a second independent source for ${claim}.`);
    return "needs_second_source";
  }
  return "triangulated";
}

function buildSummary(
  claims: EvidenceTriangulationClaim[],
  totalAcceptedEvidence: number,
): EvidenceTriangulationSummary {
  return {
    totalAcceptedEvidence,
    conflictedClaims: claims.filter((claim) => claim.status === "conflicted").length,
    claimsNeedingMoreEvidence: claims.filter((claim) => (
      claim.status === "needs_second_source" || claim.status === "unsupported" || claim.status === "conflicted"
    )).length,
    authoritativeClaims: claims.filter((claim) => claim.status === "authoritative").length,
    triangulatedClaims: claims.filter((claim) => claim.status === "triangulated").length,
  };
}

function isConflictReason(reason: RejectedWebEvidence["reason"]): boolean {
  return /contradict|counter-evidence|conflict|反证|冲突/i.test(reason);
}

function sourceHost(url: string): string {
  if (url.startsWith("internal://")) {
    return "internal";
  }
  try {
    return new URL(url).hostname;
  } catch {
    return "unknown";
  }
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean)));
}

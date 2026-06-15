export type CompetitiveDimensionStatus = "ready" | "partial" | "blocked";

export interface CompetitiveDimensionScore {
  key:
    | "evidence_coverage"
    | "external_challenge"
    | "delivery_trace"
    | "preference_fidelity"
    | "official_boundary"
    | "plan_change_alpha";
  label: string;
  score: number;
  maxScore: number;
  status: CompetitiveDimensionStatus;
  evidence: string;
  action: string;
}

export interface CompetitiveDifferentiationScore {
  protocol: "competitive_differentiation_score_v1";
  score: number;
  band: "flagship" | "credible" | "thin" | "blocked";
  dimensions: Record<CompetitiveDimensionScore["key"], CompetitiveDimensionScore>;
  advantageClaims: string[];
  blockedClaims: string[];
  benchmarkPositioning: {
    qianwenGap: string;
    tencentGap: string;
    claimBoundary: string;
  };
  nextAction: string;
}

interface GameMatrixLike {
  major_group_rows?: Array<{
    quant_evidence?: string[];
    decision_trace?: {
      supporting_factors?: unknown[];
      supporting_evidence?: unknown[];
    };
    is_key_prefix?: boolean;
    prefix_role?: string;
    plan_change_explanation?: {
      status?: string;
      ranking_impact?: string;
      official_changes?: Array<{
        evidence?: string;
        source_tier?: string;
        applied_to_ranking?: boolean;
      }>;
      review_items?: string[];
    };
  }>;
  rows?: unknown[];
  volunteer_plan?: {
    key_prefix_count?: number;
    shadowed_choice_count?: number;
  } | null;
  plan_audit_summary?: {
    coverage?: {
      coverage_sufficient?: boolean;
      deficits?: Record<string, number>;
    };
    data_boundary?: {
      formal_recommendation_ready?: boolean;
      limitations?: string[];
    };
  } | null;
  data_vintage?: {
    formal_recommendation_ready?: boolean;
    limitations?: string[];
  } | null;
}

interface ProfileLike {
  field_provenance?: Record<string, string>;
  riasec_top_codes?: string[];
  career_values?: string[];
  career_assessment_status?: string;
}

interface ExternalAuditLike {
  parsedCount?: number;
  matchedCount?: number;
  overlapRate?: number;
  unmatchedEntries?: unknown[];
  duplicateEntries?: unknown[];
  findings?: Array<{ severity?: string }> | unknown[];
}

interface EventReplayLike {
  eventCount?: number;
  lockReady?: boolean;
  currentStage?: string;
}

export interface CompetitiveDifferentiationInput {
  gameMatrix?: GameMatrixLike | null;
  userProfile?: ProfileLike | null;
  externalPlanAuditSummary?: ExternalAuditLike | null;
  eventReplay?: EventReplayLike | null;
}

export const COMPETITIVE_BENCHMARK_BOUNDARY =
  "This score compares PathFinder's auditable delivery evidence against generic AI/report workflows. It does not claim Qianwen, Tencent, or any external plan is wrong, and it cannot claim 2026 plan-change alpha without official plan evidence.";

export function buildCompetitiveDifferentiationScore(
  input: CompetitiveDifferentiationInput,
): CompetitiveDifferentiationScore {
  const dimensions = {
    evidence_coverage: scoreEvidenceCoverage(input.gameMatrix),
    external_challenge: scoreExternalChallenge(input.externalPlanAuditSummary),
    delivery_trace: scoreDeliveryTrace(input.eventReplay),
    preference_fidelity: scorePreferenceFidelity(input.userProfile),
    official_boundary: scoreOfficialBoundary(input.gameMatrix),
    plan_change_alpha: scorePlanChangeAlpha(input.gameMatrix),
  } satisfies Record<CompetitiveDimensionScore["key"], CompetitiveDimensionScore>;

  const score = clamp(
    Math.round(Object.values(dimensions).reduce((sum, dimension) => sum + dimension.score, 0)),
    0,
    100,
  );
  const advantageClaims = buildAdvantageClaims(dimensions);
  const blockedClaims = buildBlockedClaims(dimensions);

  return {
    protocol: "competitive_differentiation_score_v1",
    score,
    band: score >= 90 ? "flagship" : score >= 75 ? "credible" : score >= 55 ? "thin" : "blocked",
    dimensions,
    advantageClaims,
    blockedClaims,
    benchmarkPositioning: {
      qianwenGap:
        "Qianwen-style report/calendar/Q&A flows are strong at broad guidance; PathFinder must win by turning any report into auditable evidence, disagreement handling, and delivery readiness.",
      tencentGap:
        "Tencent-style AI entry workflows are strong at access and speed; PathFinder must win by preserving case workflow, event replay, and counselor-grade lock conditions.",
      claimBoundary: COMPETITIVE_BENCHMARK_BOUNDARY,
    },
    nextAction: blockedClaims[0] ?? "Use the score in counselor review and keep collecting official plan-change evidence.",
  };
}

function scoreEvidenceCoverage(gameMatrix?: GameMatrixLike | null): CompetitiveDimensionScore {
  const rows = gameMatrix?.major_group_rows ?? [];
  const rowCount = rows.length || gameMatrix?.rows?.length || 0;
  const evidenceCount = rows.reduce((sum, row) => sum + (row.quant_evidence?.length ?? 0), 0);
  const traceCount = rows.filter(
    (row) => (row.decision_trace?.supporting_factors?.length ?? 0) > 0 || (row.decision_trace?.supporting_evidence?.length ?? 0) > 0,
  ).length;
  const evidenceRatio = rowCount > 0 ? Math.min(1, evidenceCount / Math.max(rowCount, 1)) : 0;
  const traceRatio = rowCount > 0 ? traceCount / rowCount : 0;
  const score = Math.round(20 * (0.7 * evidenceRatio + 0.3 * traceRatio));

  return {
    key: "evidence_coverage",
    label: "Evidence coverage",
    score,
    maxScore: 20,
    status: score >= 16 ? "ready" : score >= 8 ? "partial" : "blocked",
    evidence: `${evidenceCount} evidence items across ${rowCount} rows; ${traceCount} rows have decision trace.`,
    action: score >= 16 ? "Keep evidence attached to each delivered row." : "Add quant_evidence and decision_trace to every selected row.",
  };
}

function scoreExternalChallenge(externalAudit?: ExternalAuditLike | null): CompetitiveDimensionScore {
  const parsed = externalAudit?.parsedCount ?? 0;
  const unmatched = externalAudit?.unmatchedEntries?.length ?? 0;
  const duplicates = externalAudit?.duplicateEntries?.length ?? 0;
  const hasReviewFinding = Boolean(
    externalAudit?.findings?.some((finding) => {
      if (!finding || typeof finding !== "object") return false;
      const severity = (finding as { severity?: unknown }).severity;
      return severity === "review" || severity === "blocker";
    }),
  );
  const clean = parsed > 0 && unmatched === 0 && duplicates === 0 && !hasReviewFinding;
  const score = parsed === 0 ? 0 : clean ? 15 : Math.max(5, Math.round(15 * (externalAudit?.overlapRate ?? 0)));

  return {
    key: "external_challenge",
    label: "External plan challenge",
    score,
    maxScore: 15,
    status: clean ? "ready" : parsed > 0 ? "partial" : "blocked",
    evidence: parsed > 0 ? `${parsed} pasted rows, ${unmatched} unmatched, ${duplicates} duplicate.` : "No external Qianwen/Tencent/teacher plan has been audited.",
    action: clean ? "Keep external audit attached to review record." : "Paste and reconcile the external plan before claiming comparative advantage.",
  };
}

function scoreDeliveryTrace(eventReplay?: EventReplayLike | null): CompetitiveDimensionScore {
  const eventCount = eventReplay?.eventCount ?? 0;
  const lockReady = eventReplay?.lockReady === true;
  const stage = eventReplay?.currentStage ?? "empty";
  const score = lockReady ? 20 : eventCount > 0 ? 12 : 0;

  return {
    key: "delivery_trace",
    label: "Delivery trace",
    score,
    maxScore: 20,
    status: lockReady ? "ready" : eventCount > 0 ? "partial" : "blocked",
    evidence: `${eventCount} event(s), current stage ${stage}, lockReady=${String(lockReady)}.`,
    action: lockReady ? "Use event replay as delivery audit evidence." : "Record counselor review, family confirmation, and lock events.",
  };
}

function scorePreferenceFidelity(profile?: ProfileLike | null): CompetitiveDimensionScore {
  const provenance = profile?.field_provenance ?? {};
  const explicitCount = ["risk_tolerance", "preferred_cities", "preferred_majors", "blacklist_majors"].filter(
    (field) => provenance[field] === "user_explicit",
  ).length;
  const careerSignal =
    profile?.career_assessment_status === "completed" ||
    Boolean(profile?.riasec_top_codes?.length) ||
    Boolean(profile?.career_values?.length);
  const score = Math.min(15, explicitCount * 3 + (careerSignal ? 6 : 0));

  return {
    key: "preference_fidelity",
    label: "Preference fidelity",
    score,
    maxScore: 15,
    status: score >= 12 ? "ready" : score >= 6 ? "partial" : "blocked",
    evidence: `${explicitCount} explicit preference fields; careerSignal=${String(careerSignal)}.`,
    action: score >= 12 ? "Use preference fidelity in family explanation." : "Collect explicit risk, city, major, blacklist, and career signals.",
  };
}

function scoreOfficialBoundary(gameMatrix?: GameMatrixLike | null): CompetitiveDimensionScore {
  const boundary = gameMatrix?.plan_audit_summary?.data_boundary ?? gameMatrix?.data_vintage;
  const formalReady = boundary?.formal_recommendation_ready === true;
  const limitations = boundary?.limitations ?? [];
  const disclosed = limitations.length > 0;
  const score = formalReady ? 15 : disclosed ? 8 : 2;

  return {
    key: "official_boundary",
    label: "Official data boundary",
    score,
    maxScore: 15,
    status: formalReady ? "ready" : disclosed ? "partial" : "blocked",
    evidence: formalReady ? "Official data boundary is ready." : limitations[0] ?? "Official data boundary is missing.",
    action: formalReady ? "Formal delivery can continue after review." : "Keep student-facing language in review mode until 2026 official data is ingested.",
  };
}

function scorePlanChangeAlpha(gameMatrix?: GameMatrixLike | null): CompetitiveDimensionScore {
  const rows = gameMatrix?.major_group_rows ?? [];
  const officialChanges = rows.flatMap((row) => row.plan_change_explanation?.official_changes ?? []);
  const appliedOfficialChanges = officialChanges.filter(
    (change) => change.source_tier === "official" && change.applied_to_ranking === true && Boolean(change.evidence),
  );
  const reviewItems = rows.flatMap((row) => row.plan_change_explanation?.review_items ?? []);
  const score = appliedOfficialChanges.length > 0 ? 15 : officialChanges.length > 0 ? 9 : reviewItems.length > 0 ? 6 : 0;

  return {
    key: "plan_change_alpha",
    label: "Plan-change alpha",
    score,
    maxScore: 15,
    status: score >= 12 ? "ready" : score > 0 ? "partial" : "blocked",
    evidence:
      appliedOfficialChanges.length > 0
        ? `${appliedOfficialChanges.length} official plan-change signal(s) applied to ranking.`
        : officialChanges.length > 0
          ? `${officialChanges.length} plan-change signal(s) found but not fully applied.`
          : "No official 2026 plan-change opportunity evidence is attached.",
    action:
      score >= 12
        ? "Expose plan-change opportunity and downside guard in counselor review."
        : "Wait for official 2026 plan, then score quota changes, group splits, selection requirement changes, and comparable-history reliability.",
  };
}

function buildAdvantageClaims(
  dimensions: Record<CompetitiveDimensionScore["key"], CompetitiveDimensionScore>,
): string[] {
  const claims: string[] = [];
  if (dimensions.delivery_trace.status === "ready") {
    claims.push("PathFinder has an auditable delivery trace rather than a one-shot answer.");
  }
  if (dimensions.external_challenge.status === "ready") {
    claims.push("External Qianwen/Tencent/teacher plans were reconciled against the current structure.");
  }
  if (dimensions.plan_change_alpha.status === "ready") {
    claims.push("plan-change opportunity is supported by official evidence and applied to ranking.");
  }
  if (dimensions.evidence_coverage.status === "ready" && dimensions.preference_fidelity.status === "ready") {
    claims.push("Recommendation rows have both quantitative evidence and student-specific fidelity signals.");
  }
  return claims;
}

function buildBlockedClaims(
  dimensions: Record<CompetitiveDimensionScore["key"], CompetitiveDimensionScore>,
): string[] {
  const blocked: string[] = [];
  if (dimensions.plan_change_alpha.status !== "ready") {
    blocked.push("Do not claim 2026 official plan changes create a true opportunity until official change evidence is attached.");
  }
  if (dimensions.external_challenge.status !== "ready") {
    blocked.push("Do not claim superiority over Qianwen or Tencent until their generated plan has been audited as an external input.");
  }
  if (dimensions.official_boundary.status !== "ready") {
    blocked.push("Do not present the case as final formal delivery while the official data boundary is incomplete.");
  }
  if (dimensions.delivery_trace.status !== "ready") {
    blocked.push("Do not lock delivery without event replay, counselor signoff, and family confirmation.");
  }
  return blocked;
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

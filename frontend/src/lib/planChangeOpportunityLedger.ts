import type { HiddenOpportunityAudit } from "./hiddenOpportunityAudit";

export type PlanChangeLedgerStatus = "ready" | "partial" | "blocked";
export type PlanChangeDiffType =
  | "quota_expansion"
  | "quota_reduction"
  | "new_major"
  | "discontinued_major"
  | "group_split"
  | "group_merge"
  | "subject_requirement_change"
  | "major_structure_change"
  | "unknown";

export interface PlanChangeAffectedRow {
  choiceIndex?: number | null;
  schoolName?: string;
  schoolCode?: string;
  majorGroupCode?: string;
  strategyTag?: string;
}

export interface PlanChangeRankDeltaEstimate {
  direction: "easier" | "harder" | "uncertain";
  rankDelta?: number;
  explanation: string;
}

export interface PlanChangeCompetitorMissed {
  status: "missed" | "covered" | "unknown";
  checkedSources: string[];
  evidence: string;
}

export interface PlanChangeRiskGuard {
  level: "low" | "medium" | "high";
  checks: string[];
}

export interface PlanChangeOpportunity {
  id: string;
  officialSource: string;
  diffType: PlanChangeDiffType;
  affectedRows: PlanChangeAffectedRow[];
  before?: unknown;
  after?: unknown;
  rankDeltaEstimate: PlanChangeRankDeltaEstimate;
  competitorMissed: PlanChangeCompetitorMissed;
  recommendationAction: "promote" | "guard" | "avoid" | "review";
  riskGuard: PlanChangeRiskGuard;
  hiddenOpportunityAudit?: PlanChangeHiddenOpportunityAuditSnapshot;
  auditScore: number;
  status: PlanChangeLedgerStatus;
  evidence: string;
  auditTrail: string[];
}

export interface PlanChangeHiddenOpportunityAuditSnapshot {
  protocol: HiddenOpportunityAudit["protocol"];
  status: HiddenOpportunityAudit["status"];
  labelPermission: HiddenOpportunityAudit["labelPermission"];
  score: number;
  canEnterLedger: boolean;
  mustStayHypothesisOnly: boolean;
  claimBoundary: string;
}

export interface PlanChangeHiddenOpportunityGate {
  status: "not_supplied" | "candidate_cleared" | "hypothesis_only" | "blocked";
  canEnterLedger: boolean;
  labelPermission: HiddenOpportunityAudit["labelPermission"] | "not_supplied";
  score: number | null;
  reasons: string[];
  claimBoundary: string;
}

export interface PlanChangeOpportunityLedger {
  protocol: "plan_change_opportunity_ledger_v1";
  targetYear?: number;
  score: number;
  status: PlanChangeLedgerStatus;
  opportunities: PlanChangeOpportunity[];
  hiddenOpportunityGate: PlanChangeHiddenOpportunityGate;
  blockedClaims: string[];
  summary: string;
  nextAction: string;
  claimBoundary: string;
}

interface GameMatrixLike {
  major_group_rows?: Array<{
    school_name?: string;
    school_code?: string;
    major_group_code?: string;
    choice_index?: number | null;
    strategy_tag?: string;
    admission_prob?: number;
    min_rank_pred?: number;
    major_list?: string[];
    plan_change_explanation?: {
      status?: string;
      ranking_impact?: string;
      official_changes?: PlanChangeChangeLike[];
      review_items?: string[];
    };
  }>;
  data_vintage?: {
    target_year?: number;
    formal_recommendation_ready?: boolean;
    limitations?: string[];
  } | null;
  plan_audit_summary?: {
    data_boundary?: {
      target_year?: number;
      formal_recommendation_ready?: boolean;
      limitations?: string[];
    };
  } | null;
}

interface PlanChangeChangeLike {
  change_type?: string;
  before?: unknown;
  after?: unknown;
  evidence?: string;
  official_source?: string;
  source?: string;
  source_tier?: string;
  applied_to_ranking?: boolean;
  rank_delta_estimate?: {
    direction?: string;
    rank_delta?: number;
    explanation?: string;
  };
  external_plan_coverage?: {
    competitor_missed?: boolean;
    checked_sources?: string[];
    evidence?: string;
  };
  recommendation_action?: string;
  risk_guard?: {
    level?: string;
    checks?: string[];
  };
}

interface ExternalAuditLike {
  parsedCount?: number;
}

export interface PlanChangeOpportunityLedgerInput {
  gameMatrix?: GameMatrixLike | null;
  externalPlanAuditSummary?: ExternalAuditLike | null;
  hiddenOpportunityAudit?: HiddenOpportunityAudit | null;
}

export const PLAN_CHANGE_LEDGER_CLAIM_BOUNDARY =
  "Plan change opportunity ledger is an audit object for official enrollment-plan differences. It cannot claim hidden opportunity without official source, rank-impact estimate, competitor-miss check, recommendation action, and risk guard.";

export function buildPlanChangeOpportunityLedger(
  input: PlanChangeOpportunityLedgerInput,
): PlanChangeOpportunityLedger {
  const rows = input.gameMatrix?.major_group_rows ?? [];
  const hiddenOpportunityGate = buildHiddenOpportunityGate(input.hiddenOpportunityAudit);
  const rawOpportunities = rows.flatMap((row, rowIndex) =>
    (row.plan_change_explanation?.official_changes ?? [])
      .filter((change) => isOfficialChange(change))
      .map((change, changeIndex) => buildOpportunity(
        row,
        rowIndex,
        change,
        changeIndex,
        input.externalPlanAuditSummary,
        input.hiddenOpportunityAudit,
      )),
  );
  const opportunities = hiddenOpportunityGate.canEnterLedger ? rawOpportunities : [];
  const score = opportunities.length > 0 ? Math.max(...opportunities.map((opportunity) => opportunity.auditScore)) : 0;
  const boundary = input.gameMatrix?.plan_audit_summary?.data_boundary ?? input.gameMatrix?.data_vintage;
  const formalReady = boundary?.formal_recommendation_ready === true;
  const status = hiddenOpportunityGate.canEnterLedger
    ? score >= 85 && formalReady ? "ready" : score >= 55 ? "partial" : "blocked"
    : "blocked";
  const blockedClaims = buildBlockedClaims({
    opportunities,
    rawOpportunityCount: rawOpportunities.length,
    score,
    formalReady,
    hiddenOpportunityGate,
  });

  return {
    protocol: "plan_change_opportunity_ledger_v1",
    targetYear: boundary?.target_year ?? input.gameMatrix?.data_vintage?.target_year,
    score,
    status,
    opportunities,
    hiddenOpportunityGate,
    blockedClaims,
    summary:
      !hiddenOpportunityGate.canEnterLedger && rawOpportunities.length > 0
        ? `${rawOpportunities.length} official plan-change opportunity object(s) blocked by hidden opportunity audit.`
        :
      opportunities.length > 0
        ? `${opportunities.length} official plan-change opportunity object(s), top audit score ${score}.`
        : "No official plan-change opportunity object is audit-ready.",
    nextAction:
      blockedClaims[0] ??
      "Promote the top audited opportunity into counselor review, while keeping the risk guard attached.",
    claimBoundary: PLAN_CHANGE_LEDGER_CLAIM_BOUNDARY,
  };
}

function buildOpportunity(
  row: NonNullable<GameMatrixLike["major_group_rows"]>[number],
  rowIndex: number,
  change: PlanChangeChangeLike,
  changeIndex: number,
  externalAudit?: ExternalAuditLike | null,
  hiddenOpportunityAudit?: HiddenOpportunityAudit | null,
): PlanChangeOpportunity {
  const diffType = normalizeDiffType(change.change_type);
  const officialSource = String(change.official_source || change.source || change.evidence || "official enrollment plan row");
  const affectedRows = [buildAffectedRow(row)];
  const rankDeltaEstimate = buildRankDeltaEstimate(change);
  const competitorMissed = buildCompetitorMissed(change, externalAudit);
  const recommendationAction = normalizeAction(change.recommendation_action);
  const riskGuard = buildRiskGuard(change);
  const auditScore = scoreOpportunity({
    officialSource,
    diffType,
    affectedRows,
    rankDeltaEstimate,
    competitorMissed,
    recommendationAction,
    riskGuard,
  });
  const hiddenOpportunityAuditSnapshot = hiddenOpportunityAudit
    ? buildHiddenOpportunityAuditSnapshot(hiddenOpportunityAudit)
    : undefined;

  return {
    id: `${row.school_code ?? row.school_name ?? "school"}-${row.major_group_code ?? rowIndex}-${diffType}-${changeIndex}`,
    officialSource,
    diffType,
    affectedRows,
    before: change.before,
    after: change.after,
    rankDeltaEstimate,
    competitorMissed,
    recommendationAction,
    riskGuard,
    hiddenOpportunityAudit: hiddenOpportunityAuditSnapshot,
    auditScore,
    status: auditScore >= 85 ? "ready" : auditScore >= 55 ? "partial" : "blocked",
    evidence: String(change.evidence || officialSource),
    auditTrail: [
      "official_source -> diff_type -> affected_rows -> rank_delta_estimate -> competitor_missed -> recommendation_action -> risk_guard",
      `official_source=${officialSource}`,
      `diff_type=${diffType}`,
      `rank_delta_estimate=${rankDeltaEstimate.direction}:${rankDeltaEstimate.rankDelta ?? "unknown"}`,
      `competitor_missed=${competitorMissed.status}`,
      `recommendation_action=${recommendationAction}`,
      `risk_guard=${riskGuard.level}`,
      hiddenOpportunityAuditSnapshot
        ? `hidden_opportunity_audit=${hiddenOpportunityAuditSnapshot.canEnterLedger ? "can_enter_ledger" : "blocked"}:${hiddenOpportunityAuditSnapshot.status}`
        : "hidden_opportunity_audit=not_supplied",
    ],
  };
}

function isOfficialChange(change: PlanChangeChangeLike): boolean {
  return change.source_tier === "official" && Boolean(change.evidence || change.official_source || change.source);
}

function buildAffectedRow(row: NonNullable<GameMatrixLike["major_group_rows"]>[number]): PlanChangeAffectedRow {
  return {
    choiceIndex: row.choice_index,
    schoolName: row.school_name,
    schoolCode: row.school_code,
    majorGroupCode: row.major_group_code,
    strategyTag: row.strategy_tag,
  };
}

function buildRankDeltaEstimate(change: PlanChangeChangeLike): PlanChangeRankDeltaEstimate {
  const estimate = change.rank_delta_estimate;
  if (estimate?.direction) {
    return {
      direction: normalizeDirection(estimate.direction),
      rankDelta: estimate.rank_delta,
      explanation: estimate.explanation || "Explicit rank delta estimate attached to the official plan diff.",
    };
  }

  if (typeof change.before === "number" && typeof change.after === "number" && change.before !== change.after) {
    const direction = change.after > change.before ? "easier" : "harder";
    return {
      direction,
      explanation: `Quota changed from ${change.before} to ${change.after}; use as a directional estimate until calibrated.`,
    };
  }

  return {
    direction: change.applied_to_ranking ? "uncertain" : "uncertain",
    explanation: change.applied_to_ranking
      ? "Official diff is applied to ranking, but numeric rank delta is not attached."
      : "Official diff is not yet translated into ranking impact.",
  };
}

function buildCompetitorMissed(
  change: PlanChangeChangeLike,
  externalAudit?: ExternalAuditLike | null,
): PlanChangeCompetitorMissed {
  const coverage = change.external_plan_coverage;
  if (coverage?.competitor_missed === true) {
    return {
      status: "missed",
      checkedSources: coverage.checked_sources ?? [],
      evidence: coverage.evidence || "External plan was checked and did not include this plan-change signal.",
    };
  }
  if (coverage?.competitor_missed === false) {
    return {
      status: "covered",
      checkedSources: coverage.checked_sources ?? [],
      evidence: coverage.evidence || "External plan already covered this plan-change signal.",
    };
  }
  return {
    status: "unknown",
    checkedSources: externalAudit?.parsedCount ? ["external_plan_audit"] : [],
    evidence: externalAudit?.parsedCount
      ? "External plan was parsed, but row-level coverage for this change is not attached."
      : "No external Qianwen, Tencent, teacher, or family plan was checked for this opportunity.",
  };
}

function buildRiskGuard(change: PlanChangeChangeLike): PlanChangeRiskGuard {
  const guard = change.risk_guard;
  const checks = guard?.checks?.filter(Boolean) ?? [];
  return {
    level: normalizeRiskLevel(guard?.level),
    checks,
  };
}

function scoreOpportunity(opportunity: {
  officialSource: string;
  diffType: PlanChangeDiffType;
  affectedRows: PlanChangeAffectedRow[];
  rankDeltaEstimate: PlanChangeRankDeltaEstimate;
  competitorMissed: PlanChangeCompetitorMissed;
  recommendationAction: PlanChangeOpportunity["recommendationAction"];
  riskGuard: PlanChangeRiskGuard;
}): number {
  let score = 0;
  if (opportunity.officialSource) score += 25;
  if (opportunity.diffType !== "unknown") score += 10;
  if (opportunity.affectedRows.some((row) => row.schoolName && row.majorGroupCode)) score += 15;
  if (typeof opportunity.rankDeltaEstimate.rankDelta === "number") {
    score += 20;
  } else if (opportunity.rankDeltaEstimate.direction !== "uncertain") {
    score += 12;
  }
  if (opportunity.competitorMissed.status === "missed") {
    score += 15;
  }
  if (opportunity.recommendationAction !== "review") score += 7;
  if (opportunity.riskGuard.checks.length > 0) score += 8;
  return clamp(score, 0, 100);
}

function buildBlockedClaims({
  opportunities,
  rawOpportunityCount,
  score,
  formalReady,
  hiddenOpportunityGate,
}: {
  opportunities: PlanChangeOpportunity[];
  rawOpportunityCount: number;
  score: number;
  formalReady: boolean;
  hiddenOpportunityGate: PlanChangeHiddenOpportunityGate;
}): string[] {
  const blocked: string[] = [];
  if (!hiddenOpportunityGate.canEnterLedger && rawOpportunityCount > 0) {
    blocked.push(
      `Hidden opportunity audit blocked ledger entry: ${hiddenOpportunityGate.reasons.join(" ") || "audit gate did not clear."}`,
    );
    blocked.push("Do not claim hidden opportunity or under-attention candidate until the hidden opportunity audit clears.");
    return blocked;
  }
  if (opportunities.length === 0) {
    blocked.push("Attach official 2026 plan diff before claiming any paid plan-change opportunity.");
    blocked.push("Do not claim official 2026 plan diff opportunity until an official 2026 plan diff is attached.");
    return blocked;
  }
  if (score < 85) {
    blocked.push("Do not claim discovered plan-change alpha until rank delta, competitor miss, action, and risk guard are audited.");
  }
  if (!formalReady) {
    blocked.push("Do not final-sign plan-change opportunity while the official data boundary is not ready.");
  }
  return blocked;
}

function buildHiddenOpportunityGate(
  audit?: HiddenOpportunityAudit | null,
): PlanChangeHiddenOpportunityGate {
  if (!audit) {
    return {
      status: "not_supplied",
      canEnterLedger: true,
      labelPermission: "not_supplied",
      score: null,
      reasons: [],
      claimBoundary: "No hidden opportunity audit was supplied; ledger status reflects official plan-change audit only.",
    };
  }
  const canEnterLedger = audit.reviewGate.canEnterLedger === true;
  const status = canEnterLedger
    ? "candidate_cleared"
    : audit.status === "blocked" ? "blocked" : "hypothesis_only";
  return {
    status,
    canEnterLedger,
    labelPermission: audit.labelPermission,
    score: audit.score,
    reasons: audit.reviewGate.reasons,
    claimBoundary: audit.claimBoundary,
  };
}

function buildHiddenOpportunityAuditSnapshot(
  audit: HiddenOpportunityAudit,
): PlanChangeHiddenOpportunityAuditSnapshot {
  return {
    protocol: audit.protocol,
    status: audit.status,
    labelPermission: audit.labelPermission,
    score: audit.score,
    canEnterLedger: audit.reviewGate.canEnterLedger,
    mustStayHypothesisOnly: audit.reviewGate.mustStayHypothesisOnly,
    claimBoundary: audit.claimBoundary,
  };
}

function normalizeDiffType(value?: string): PlanChangeDiffType {
  const allowed = new Set<PlanChangeDiffType>([
    "quota_expansion",
    "quota_reduction",
    "new_major",
    "discontinued_major",
    "group_split",
    "group_merge",
    "subject_requirement_change",
    "major_structure_change",
    "unknown",
  ]);
  return allowed.has(value as PlanChangeDiffType) ? (value as PlanChangeDiffType) : "unknown";
}

function normalizeDirection(value: string): PlanChangeRankDeltaEstimate["direction"] {
  return value === "easier" || value === "harder" ? value : "uncertain";
}

function normalizeAction(value?: string): PlanChangeOpportunity["recommendationAction"] {
  return value === "promote" || value === "guard" || value === "avoid" ? value : "review";
}

function normalizeRiskLevel(value?: string): PlanChangeRiskGuard["level"] {
  return value === "low" || value === "high" ? value : "medium";
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

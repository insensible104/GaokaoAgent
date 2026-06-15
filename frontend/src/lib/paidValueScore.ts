export type PaidValueStatus = "ready" | "partial" | "blocked";

export interface PaidValueDimension {
  key:
    | "plan_change_opportunity"
    | "withdrawal_risk_avoidance"
    | "external_plan_audit"
    | "executable_volunteer_draft"
    | "counselor_signoff_boundary";
  label: string;
  score: number;
  maxScore: number;
  status: PaidValueStatus;
  evidence: string;
  action: string;
}

export interface PaidValueScore {
  protocol: "paid_value_score_v1";
  score: number;
  band: "premium" | "credible_paid" | "advisory_only" | "free_tier";
  dimensions: Record<PaidValueDimension["key"], PaidValueDimension>;
  payReasons: string[];
  blockedRevenueClaims: string[];
  claimBoundary: string;
  nextAction: string;
}

interface GameMatrixLike {
  major_group_rows?: Array<{
    school_name?: string;
    school_code?: string;
    major_group_code?: string;
    strategy_tag?: string;
    choice_index?: number | null;
    major_list?: string[];
    suggested_major_choices?: Array<{
      major_code?: string;
      major_name?: string;
      is_blacklisted?: boolean;
      user_utility?: number;
    }>;
    obey_adjustment_recommendation?: boolean;
    quant_evidence?: string[];
    is_key_prefix?: boolean;
    prefix_role?: string;
    tail_assignment_risk?: number;
    adjustment_risk?: number;
    is_blacklist_risk?: boolean;
    worst_case_major?: string | null;
    plan_change_explanation?: {
      status?: string;
      ranking_impact?: string;
      official_changes?: Array<{
        change_type?: string;
        before?: unknown;
        after?: unknown;
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
    blacklist_violation_count?: number;
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

export interface PaidValueInput {
  gameMatrix?: GameMatrixLike | null;
  externalPlanAuditSummary?: ExternalAuditLike | null;
  eventReplay?: EventReplayLike | null;
}

export const PAID_VALUE_CLAIM_BOUNDARY =
  "Paid value score estimates whether this case contains evidence a family could reasonably pay for. It does not sell admission certainty, and it cannot claim plan-change opportunity without official-source evidence.";

export function buildPaidValueScore(input: PaidValueInput): PaidValueScore {
  const dimensions = {
    plan_change_opportunity: scorePlanChangeOpportunity(input.gameMatrix),
    withdrawal_risk_avoidance: scoreWithdrawalRiskAvoidance(input.gameMatrix),
    external_plan_audit: scoreExternalPlanAudit(input.externalPlanAuditSummary),
    executable_volunteer_draft: scoreExecutableVolunteerDraft(input.gameMatrix),
    counselor_signoff_boundary: scoreCounselorSignoffBoundary(input.eventReplay, input.gameMatrix),
  } satisfies Record<PaidValueDimension["key"], PaidValueDimension>;

  const score = clamp(
    Math.round(Object.values(dimensions).reduce((sum, dimension) => sum + dimension.score, 0)),
    0,
    100,
  );
  const payReasons = buildPayReasons(dimensions);
  const blockedRevenueClaims = buildBlockedRevenueClaims(dimensions);

  return {
    protocol: "paid_value_score_v1",
    score,
    band: score >= 90 ? "premium" : score >= 75 ? "credible_paid" : score >= 50 ? "advisory_only" : "free_tier",
    dimensions,
    payReasons,
    blockedRevenueClaims,
    claimBoundary: PAID_VALUE_CLAIM_BOUNDARY,
    nextAction: blockedRevenueClaims[0] ?? "Package this case as paid counselor delivery with explicit evidence and signoff.",
  };
}

function scorePlanChangeOpportunity(gameMatrix?: GameMatrixLike | null): PaidValueDimension {
  const rows = gameMatrix?.major_group_rows ?? [];
  const officialChanges = rows.flatMap((row) => row.plan_change_explanation?.official_changes ?? []);
  const applied = officialChanges.filter(
    (change) => change.source_tier === "official" && change.applied_to_ranking === true && Boolean(change.evidence),
  );
  const score = applied.length > 0 ? 25 : officialChanges.length > 0 ? 14 : 0;

  return {
    key: "plan_change_opportunity",
    label: "Plan-change opportunity",
    score,
    maxScore: 25,
    status: score >= 20 ? "ready" : score > 0 ? "partial" : "blocked",
    evidence:
      applied.length > 0
        ? `${applied.length} official plan-change signal(s) applied to ranking.`
        : officialChanges.length > 0
          ? `${officialChanges.length} official-looking change signal(s) need ranking validation.`
          : "No official plan-change opportunity is attached.",
    action:
      score >= 20
        ? "Use this as the primary paid value proof, with downside guard."
        : "Do not sell paid plan-change opportunity until official 2026 plan diff is attached.",
  };
}

function scoreWithdrawalRiskAvoidance(gameMatrix?: GameMatrixLike | null): PaidValueDimension {
  const rows = gameMatrix?.major_group_rows ?? [];
  const riskyRows = rows.filter(
    (row) => row.is_blacklist_risk || Number(row.tail_assignment_risk ?? row.adjustment_risk ?? 0) >= 0.1,
  );
  const safetyAnchors = rows.filter((row) => row.prefix_role === "safety_anchor" || row.strategy_tag === "safe");
  const blacklistViolations = gameMatrix?.volunteer_plan?.blacklist_violation_count ?? 0;
  const hasEvidence = rows.some((row) => (row.quant_evidence?.length ?? 0) > 0);
  const coverageReady = gameMatrix?.plan_audit_summary?.coverage?.coverage_sufficient === true;

  let score = 0;
  if (blacklistViolations === 0) score += 6;
  if (safetyAnchors.length > 0) score += 7;
  if (hasEvidence) score += 5;
  if (coverageReady) score += 5;
  if (riskyRows.length === 0) score += 2;

  return {
    key: "withdrawal_risk_avoidance",
    label: "Adjustment and withdrawal risk avoided",
    score: clamp(score, 0, 25),
    maxScore: 25,
    status: score >= 20 ? "ready" : score >= 10 ? "partial" : "blocked",
    evidence: `${riskyRows.length} risky row(s), ${safetyAnchors.length} safety anchor(s), blacklist violations ${blacklistViolations}.`,
    action:
      score >= 20
        ? "Use risk avoidance as a paid delivery reason."
        : "Add safety anchors, blacklist checks, tail-assignment evidence, and coverage repair.",
  };
}

function scoreExternalPlanAudit(externalAudit?: ExternalAuditLike | null): PaidValueDimension {
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
  const score = parsed === 0 ? 0 : clean ? 15 : Math.max(5, Math.round((externalAudit?.overlapRate ?? 0) * 15));

  return {
    key: "external_plan_audit",
    label: "External plan audit",
    score,
    maxScore: 15,
    status: clean ? "ready" : parsed > 0 ? "partial" : "blocked",
    evidence: parsed > 0 ? `${parsed} external row(s), ${unmatched} unmatched, ${duplicates} duplicate.` : "No Qianwen/teacher/family plan has been audited.",
    action: clean ? "Use this as proof that external advice was reconciled." : "Audit the external plan before charging for comparative review.",
  };
}

function scoreExecutableVolunteerDraft(gameMatrix?: GameMatrixLike | null): PaidValueDimension {
  const rows = gameMatrix?.major_group_rows ?? [];
  const executableRows = rows.filter((row) => {
    const hasSchoolIdentity = Boolean(row.school_code || row.school_name);
    const hasGroup = Boolean(row.major_group_code);
    const choices = row.suggested_major_choices ?? [];
    const hasMajorChoices =
      choices.length > 0
        ? choices.every((choice) => Boolean(choice.major_code || choice.major_name) && !choice.is_blacklisted)
        : (row.major_list?.length ?? 0) > 0;
    return hasSchoolIdentity && hasGroup && typeof row.choice_index === "number" && hasMajorChoices;
  });
  const ratio = rows.length > 0 ? executableRows.length / rows.length : 0;
  const hasAdjustmentAdvice = rows.some((row) => typeof row.obey_adjustment_recommendation === "boolean");
  const score = Math.round(16 * ratio + (hasAdjustmentAdvice ? 4 : 0));

  return {
    key: "executable_volunteer_draft",
    label: "Executable volunteer draft",
    score: clamp(score, 0, 20),
    maxScore: 20,
    status: score >= 16 ? "ready" : score >= 8 ? "partial" : "blocked",
    evidence: `${executableRows.length}/${rows.length} rows have school/group/choice/major structure; adjustment advice=${String(hasAdjustmentAdvice)}.`,
    action:
      score >= 16
        ? "Package as an executable volunteer draft."
        : "Add school identity, group code, row order, 1-6 major choices, and adjustment recommendation.",
  };
}

function scoreCounselorSignoffBoundary(
  eventReplay?: EventReplayLike | null,
  gameMatrix?: GameMatrixLike | null,
): PaidValueDimension {
  const lockReady = eventReplay?.lockReady === true;
  const eventCount = eventReplay?.eventCount ?? 0;
  const formalReady =
    (gameMatrix?.plan_audit_summary?.data_boundary ?? gameMatrix?.data_vintage)?.formal_recommendation_ready === true;
  const score = lockReady && formalReady ? 15 : eventCount > 0 ? 8 : 0;

  return {
    key: "counselor_signoff_boundary",
    label: "Counselor signoff boundary",
    score,
    maxScore: 15,
    status: score >= 12 ? "ready" : score > 0 ? "partial" : "blocked",
    evidence: `${eventCount} event(s), lockReady=${String(lockReady)}, formalReady=${String(formalReady)}.`,
    action:
      score >= 12
        ? "Use signoff and claim boundary in the paid handoff."
        : "Do not charge for final delivery until counselor signoff, family confirmation, and official boundary are ready.",
  };
}

function buildPayReasons(dimensions: Record<PaidValueDimension["key"], PaidValueDimension>): string[] {
  const reasons: string[] = [];
  if (dimensions.plan_change_opportunity.status === "ready") {
    reasons.push("official plan-change opportunity is attached and applied to ranking.");
  }
  if (dimensions.withdrawal_risk_avoidance.status === "ready") {
    reasons.push("adjustment, withdrawal, blacklist, and safety-anchor risks are explicitly controlled.");
  }
  if (dimensions.external_plan_audit.status === "ready") {
    reasons.push("Qianwen, teacher, or family plan has been audited rather than ignored.");
  }
  if (dimensions.executable_volunteer_draft.status === "ready") {
    reasons.push("executable volunteer draft is structured enough for counselor handoff.");
  }
  if (dimensions.counselor_signoff_boundary.status === "ready") {
    reasons.push("counselor signoff and family confirmation boundary are ready.");
  }
  return reasons;
}

function buildBlockedRevenueClaims(dimensions: Record<PaidValueDimension["key"], PaidValueDimension>): string[] {
  const blocked: string[] = [];
  if (dimensions.plan_change_opportunity.status !== "ready") {
    blocked.push("Do not sell paid plan-change opportunity without official 2026 plan-change evidence.");
  }
  if (dimensions.withdrawal_risk_avoidance.status !== "ready") {
    blocked.push("Do not sell risk avoidance until adjustment, withdrawal, blacklist, and safety-anchor checks are complete.");
  }
  if (dimensions.external_plan_audit.status !== "ready") {
    blocked.push("Do not sell external-plan review until the Qianwen/teacher/family plan is audited.");
  }
  if (dimensions.executable_volunteer_draft.status !== "ready") {
    blocked.push("Do not sell final delivery without an executable volunteer draft.");
  }
  if (dimensions.counselor_signoff_boundary.status !== "ready") {
    blocked.push("Do not sell final signoff until counselor and family confirmation boundaries are ready.");
  }
  return blocked;
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

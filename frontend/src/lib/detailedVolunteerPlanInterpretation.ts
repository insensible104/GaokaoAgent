import type { CounselorReviewDossier } from "./counselorReviewDossier";
import type { EvidenceClaimSupport } from "./webEvidencePlanner";

export type DetailedVolunteerPlanInterpretationStatus =
  | "ready_for_family_review"
  | "needs_counselor_review"
  | "blocked";

export type DetailedVolunteerPlanClaim =
  | EvidenceClaimSupport
  | "trend_wording"
  | "concept_readiness"
  | "search_provenance";

export type DetailedVolunteerPlanClaimStance =
  | "can_explain"
  | "hypothesis_only"
  | "cannot_claim"
  | "needs_review";

export interface DetailedVolunteerPlanClaimRow {
  claim: DetailedVolunteerPlanClaim;
  stance: DetailedVolunteerPlanClaimStance;
  familyWording: string;
  evidenceBasis: string[];
  sourceRefs: string[];
  counterChecks: string[];
  claimBoundary: string;
}

export interface DetailedVolunteerPlanInterpretation {
  protocol: "detailed_volunteer_plan_interpretation_v1";
  status: DetailedVolunteerPlanInterpretationStatus;
  headline: string;
  summary: string;
  claimRows: DetailedVolunteerPlanClaimRow[];
  familyDecisionPath: {
    conceptReadinessProtocol: string;
    conceptReadinessStatus: string;
    requiredQuestions: string[];
    hardStops: string[];
  };
  planPosition: {
    rowUse: "candidate_for_counselor_review" | "family_discussion_only" | "blocked";
    notARecommendationReasons: string[];
    counselorSignoffChecklist: string[];
  };
  nextActions: string[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "This detailed interpretation is not a final filing recommendation. It translates the counselor dossier into family-readable reasoning, while preserving evidence limits, counter-checks, and counselor signoff gates.";

export function buildDetailedVolunteerPlanInterpretation(
  dossier: CounselorReviewDossier,
): DetailedVolunteerPlanInterpretation {
  const status = resolveStatus(dossier);
  const conceptReadiness = dossier.decisionBrief?.conceptReadiness;
  const claimRows = [
    ...buildEvidenceClaimRows(dossier, status),
    buildTrendClaimRow(dossier, status),
    buildSearchProvenanceClaimRow(dossier, status),
    buildConceptReadinessClaimRow(dossier, status),
  ];

  return {
    protocol: "detailed_volunteer_plan_interpretation_v1",
    status,
    headline: buildHeadline(dossier, status),
    summary: buildSummary(dossier, status),
    claimRows,
    familyDecisionPath: {
      conceptReadinessProtocol: conceptReadiness?.protocol ?? "family_concept_readiness_v1",
      conceptReadinessStatus: conceptReadiness?.status ?? "missing",
      requiredQuestions: unique([
        ...(dossier.familyQuestions ?? []),
        ...(conceptReadiness?.checkpoints ?? [])
          .filter((checkpoint) => checkpoint.status !== "understood")
          .map((checkpoint) => checkpoint.familyQuestion),
      ]),
      hardStops: unique([
        ...(dossier.decisionBrief?.hardBoundaries ?? []),
        ...(dossier.evidenceQuality.blockingConcerns ?? []),
      ]),
    },
    planPosition: {
      rowUse: rowUseFor(status),
      notARecommendationReasons: buildNotARecommendationReasons(dossier),
      counselorSignoffChecklist: dossier.counselorReviewChecklist,
    },
    nextActions: buildNextActions(dossier, status),
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function resolveStatus(dossier: CounselorReviewDossier): DetailedVolunteerPlanInterpretationStatus {
  if (dossier.evidenceQuality.status === "blocked") {
    return "blocked";
  }
  if (
    dossier.status !== "ready_for_counselor_review" ||
    dossier.evidenceQuality.status !== "review_ready" ||
    dossier.decisionBrief?.conceptReadiness.status === "needs_concept_clarification"
  ) {
    return "needs_counselor_review";
  }
  return "ready_for_family_review";
}

function buildHeadline(
  dossier: CounselorReviewDossier,
  status: DetailedVolunteerPlanInterpretationStatus,
): string {
  if (status === "ready_for_family_review") {
    return `${dossier.caseSummary.studentName}: evidence-backed plan interpretation ready for family review`;
  }
  if (status === "blocked") {
    return `${dossier.caseSummary.studentName}: interpretation blocked until evidence issues are resolved`;
  }
  return `${dossier.caseSummary.studentName}: counselor review still required before family presentation`;
}

function buildSummary(
  dossier: CounselorReviewDossier,
  status: DetailedVolunteerPlanInterpretationStatus,
): string {
  const gate = dossier.evidenceQuality.familyPresentationGate;
  if (status === "ready_for_family_review") {
    return `${dossier.opportunityThesis} ${gate}`;
  }
  if (status === "blocked") {
    return `${gate} Resolve blockers before presenting the opportunity as a family-facing interpretation.`;
  }
  return `${dossier.caseSummary.summary} ${gate}`;
}

function buildEvidenceClaimRows(
  dossier: CounselorReviewDossier,
  status: DetailedVolunteerPlanInterpretationStatus,
): DetailedVolunteerPlanClaimRow[] {
  const claimOrder: EvidenceClaimSupport[] = [
    "official_diff",
    "rank_delta",
    "risk_guard",
    "competitor_missed",
    "parent_understanding",
  ];
  return claimOrder
    .filter((claim) => dossier.evidenceTrail.some((item) => item.claim === claim))
    .map((claim) => {
      const evidenceItems = dossier.evidenceTrail.filter((item) => item.claim === claim);
      return {
        claim,
        stance: status === "blocked" && claim !== "official_diff" ? "needs_review" : "can_explain",
        familyWording: familyWordingForEvidenceClaim(claim),
        evidenceBasis: evidenceItems.flatMap((item) => item.excerpts).slice(0, 3),
        sourceRefs: evidenceItems.map((item) => `${item.sourceTitle} (${item.sourceTier})`),
        counterChecks: counterChecksForClaim(dossier, claim),
        claimBoundary: boundaryForEvidenceClaim(claim),
      };
    });
}

function buildTrendClaimRow(
  dossier: CounselorReviewDossier,
  status: DetailedVolunteerPlanInterpretationStatus,
): DetailedVolunteerPlanClaimRow {
  const position = dossier.publicOpinionPosition;
  const stance: DetailedVolunteerPlanClaimStance =
    status === "blocked" || !position.canUseHiddenOpportunityLabel ? "cannot_claim" : "hypothesis_only";
  return {
    claim: "trend_wording",
    stance,
    familyWording:
      stance === "cannot_claim"
        ? `Do not use hidden-opportunity wording. Current trend gate: ${position.wordingGateStatus}.`
        : position.familySafeWording,
    evidenceBasis: [
      position.familySafeSummary,
      `Trend language gate: ${position.wordingGateStatus}; score ${position.wordingGateScore}.`,
      ...position.requiredEvidence,
    ],
    sourceRefs: sourceRefsForClaim(dossier, "hypothesis_only"),
    counterChecks: publicOpinionCounterChecks(dossier),
    claimBoundary:
      "Public-opinion evidence can frame a low-attention hypothesis only. It cannot prove demand, score movement, admission probability, or final recommendation quality.",
  };
}

function buildSearchProvenanceClaimRow(
  dossier: CounselorReviewDossier,
  status: DetailedVolunteerPlanInterpretationStatus,
): DetailedVolunteerPlanClaimRow {
  return {
    claim: "search_provenance",
    stance: status === "blocked" ? "needs_review" : "can_explain",
    familyWording:
      "The search record shows what was checked, what was accepted, and what was rejected or missing before any family-facing claim is made.",
    evidenceBasis: [
      `${dossier.searchProvenance.runCount} search runs across ${dossier.searchProvenance.providerIds.join(", ") || "no provider"}.`,
      `${dossier.searchProvenance.summary.acceptedRows} accepted rows, ${dossier.searchProvenance.summary.rejectedRows} rejected rows, ${dossier.searchProvenance.summary.unreturnedRows} unreturned rows.`,
    ],
    sourceRefs: dossier.searchProvenance.providerIds,
    counterChecks: publicOpinionCounterChecks(dossier),
    claimBoundary: dossier.searchProvenance.claimBoundary,
  };
}

function buildConceptReadinessClaimRow(
  dossier: CounselorReviewDossier,
  status: DetailedVolunteerPlanInterpretationStatus,
): DetailedVolunteerPlanClaimRow {
  const conceptReadiness = dossier.decisionBrief?.conceptReadiness;
  const conceptStatus = conceptReadiness?.status ?? "missing";
  return {
    claim: "concept_readiness",
    stance:
      status === "blocked"
        ? "needs_review"
        : conceptStatus === "ready"
          ? "can_explain"
          : "needs_review",
    familyWording:
      conceptReadiness?.nextAction ??
      "Professional group, adjustment, safe-anchor, and interest tradeoff concepts must be clarified before row-level discussion.",
    evidenceBasis: conceptReadiness?.checkpoints.map((checkpoint) => (
      `${checkpoint.concept}: ${checkpoint.status}; ${checkpoint.evidenceNeeded}`
    )) ?? [],
    sourceRefs: sourceRefsForClaim(dossier, "parent_understanding"),
    counterChecks: conceptReadiness?.checkpoints
      .filter((checkpoint) => checkpoint.status !== "understood")
      .map((checkpoint) => checkpoint.familyQuestion) ?? [],
    claimBoundary: conceptReadiness?.claimBoundary ?? "Concept readiness is a communication gate, not a recommendation.",
  };
}

function familyWordingForEvidenceClaim(claim: EvidenceClaimSupport): string {
  if (claim === "official_diff") {
    return "The official plan change is attached and can be used as the factual starting point.";
  }
  if (claim === "rank_delta") {
    return "Rank impact can be discussed directionally with current evidence, but it is not a score guarantee.";
  }
  if (claim === "risk_guard") {
    return "Adjustment, school rules, and worst-case outcomes must be checked before treating this row as safe.";
  }
  if (claim === "competitor_missed") {
    return "External plans appear to miss or underweight the official change, subject to counselor review.";
  }
  return "The family has concept-clarification evidence attached before row-level discussion.";
}

function boundaryForEvidenceClaim(claim: EvidenceClaimSupport): string {
  if (claim === "official_diff") {
    return "Official diff supports that the plan row changed; it does not by itself prove admission probability.";
  }
  if (claim === "rank_delta") {
    return "Rank evidence supports directional interpretation only and must not replace current-year admission results.";
  }
  if (claim === "risk_guard") {
    return "Risk guard evidence limits unsafe claims; it does not make the row acceptable for every family.";
  }
  if (claim === "competitor_missed") {
    return "External omission can support a candidate opportunity thesis, not a guarantee that others will miss it.";
  }
  return "Concept evidence supports communication readiness only.";
}

function counterChecksForClaim(
  dossier: CounselorReviewDossier,
  claim: EvidenceClaimSupport,
): string[] {
  if (claim === "official_diff") {
    return ["Recheck school code, group code, major code, quota, subject requirements, and official URL before filing."];
  }
  if (claim === "rank_delta") {
    return ["Compare at least two historical-data sources and keep quota context attached."];
  }
  if (claim === "competitor_missed") {
    return ["Look for external plans that already incorporated the 2026 change before calling it underweighted."];
  }
  if (claim === "risk_guard") {
    return ["Confirm worst-case adjusted major, campus, fee, city, physical-exam, and transfer constraints."];
  }
  return dossier.familyQuestions;
}

function sourceRefsForClaim(dossier: CounselorReviewDossier, claim: EvidenceClaimSupport): string[] {
  return dossier.evidenceTrail
    .filter((item) => item.claim === claim)
    .map((item) => `${item.sourceTitle} (${item.sourceTier})`);
}

function publicOpinionCounterChecks(dossier: CounselorReviewDossier): string[] {
  return dossier.searchProvenance.queryRows
    .filter((row) => row.taskType === "public_opinion_scan")
    .map((row) => {
      const question = row.evidenceQuestion ? `: ${row.evidenceQuestion}` : "";
      const rejects = row.rejectsAsProof.length > 0 ? `; rejects as proof: ${row.rejectsAsProof.join(", ")}` : "";
      return `${row.searchIntent ?? row.taskType}${question}${rejects}`;
    });
}

function rowUseFor(status: DetailedVolunteerPlanInterpretationStatus) {
  if (status === "ready_for_family_review") {
    return "candidate_for_counselor_review";
  }
  if (status === "blocked") {
    return "blocked";
  }
  return "family_discussion_only";
}

function buildNotARecommendationReasons(dossier: CounselorReviewDossier): string[] {
  return unique([
    "This is not a final recommendation.",
    "This is not an admission guarantee.",
    ...dossier.whatWeCannotSay.filter((item) => /recommendation|guarantee|cannot prove/i.test(item)),
    dossier.claimBoundary,
  ]);
}

function buildNextActions(
  dossier: CounselorReviewDossier,
  status: DetailedVolunteerPlanInterpretationStatus,
): string[] {
  if (status === "blocked") {
    return unique([
      "Resolve evidence quality blockers before family presentation.",
      ...dossier.evidenceQuality.blockingConcerns,
      ...dossier.publicOpinionPosition.requiredFollowUps,
    ]);
  }
  if (status === "needs_counselor_review") {
    return unique([
      "Finish counselor review before turning this into family-facing wording.",
      ...dossier.familyQuestions,
      ...dossier.publicOpinionPosition.requiredFollowUps,
    ]);
  }
  return unique([
    "Use this as a family-review explanation only after counselor signoff.",
    ...dossier.familyQuestions,
    "Keep public-opinion wording hypothesis-only and preserve counter-evidence checks.",
  ]);
}

function unique<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

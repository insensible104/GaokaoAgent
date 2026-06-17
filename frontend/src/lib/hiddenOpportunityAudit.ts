import type { CounselorReviewDossier } from "./counselorReviewDossier";
import type { DetailedVolunteerPlanInterpretation } from "./detailedVolunteerPlanInterpretation";
import type { FamilyDecisionClarityRoadmap } from "./familyDecisionClarityRoadmap";
import type { WebEvidenceResearchStrategy } from "./webEvidenceResearchStrategy";

export type HiddenOpportunityAuditStatus =
  | "candidate_for_counselor_review"
  | "hypothesis_only"
  | "blocked";

export type HiddenOpportunityLabelPermission =
  | "under_attention_candidate_only"
  | "do_not_use_hidden_opportunity"
  | "internal_watchlist_only";

export type HiddenOpportunityAuditFactor =
  | "official_change"
  | "rank_direction"
  | "external_plan_gap"
  | "low_attention_signal"
  | "counter_evidence_clearance"
  | "hype_pressure_clearance"
  | "source_diversity"
  | "evidence_quality"
  | "family_readiness";

export interface HiddenOpportunityAuditScoreBand {
  factor: HiddenOpportunityAuditFactor;
  points: number;
  maxPoints: number;
  rationale: string;
}

export interface HiddenOpportunityAudit {
  protocol: "hidden_opportunity_audit_v1";
  status: HiddenOpportunityAuditStatus;
  labelPermission: HiddenOpportunityLabelPermission;
  score: number;
  scoreBands: HiddenOpportunityAuditScoreBand[];
  positiveSignals: string[];
  negativeSignals: string[];
  requiredBeforeFamilyWording: string[];
  forbiddenClaims: string[];
  reviewGate: {
    canEnterLedger: boolean;
    canUseHiddenOpportunityLabel: boolean;
    mustStayHypothesisOnly: boolean;
    counselorSignoffRequired: boolean;
    reasons: string[];
  };
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Hidden opportunity audit is a counselor-review gate only. Public-opinion evidence must stay hypothesis-only; the audit cannot prove admission probability, final recommendation, or demand.";

export function buildHiddenOpportunityAudit({
  dossier,
  detailedInterpretation,
  researchStrategy,
  familyClarityRoadmap,
}: {
  dossier: CounselorReviewDossier;
  detailedInterpretation: DetailedVolunteerPlanInterpretation;
  researchStrategy: WebEvidenceResearchStrategy;
  familyClarityRoadmap: FamilyDecisionClarityRoadmap;
}): HiddenOpportunityAudit {
  const scoreBands = buildScoreBands({
    dossier,
    detailedInterpretation,
    familyClarityRoadmap,
  });
  const score = Math.min(100, scoreBands.reduce((sum, band) => sum + band.points, 0));
  const blockers = blockingReasons({
    dossier,
    detailedInterpretation,
    researchStrategy,
    familyClarityRoadmap,
  });
  const missingRequirements = requiredBeforeFamilyWording({
    dossier,
    detailedInterpretation,
    researchStrategy,
    familyClarityRoadmap,
  });
  const candidateReady = blockers.length === 0 && score >= 75 && missingRequirements.length === 0;
  const status: HiddenOpportunityAuditStatus =
    blockers.length > 0 ? "blocked" : candidateReady ? "candidate_for_counselor_review" : "hypothesis_only";
  const canUseHiddenOpportunityLabel =
    status === "candidate_for_counselor_review" &&
    dossier.publicOpinionPosition.canUseHiddenOpportunityLabel &&
    dossier.publicOpinionPosition.wordingGateStatus === "hypothesis_only";

  return {
    protocol: "hidden_opportunity_audit_v1",
    status,
    labelPermission: labelPermissionFor(status, canUseHiddenOpportunityLabel),
    score,
    scoreBands,
    positiveSignals: positiveSignalsFor(scoreBands, dossier, familyClarityRoadmap),
    negativeSignals: negativeSignalsFor(blockers, scoreBands, dossier),
    requiredBeforeFamilyWording: unique([
      ...missingRequirements,
      ...(status === "blocked" ? blockers.map((reason) => `Resolve blocker: ${reason}`) : []),
    ]),
    forbiddenClaims: forbiddenClaimsFor(dossier, researchStrategy),
    reviewGate: {
      canEnterLedger: status === "candidate_for_counselor_review",
      canUseHiddenOpportunityLabel,
      mustStayHypothesisOnly: true,
      counselorSignoffRequired: true,
      reasons: unique([
        ...blockers,
        ...missingRequirements,
        "Public-opinion signals remain hypothesis-only even when the row enters the opportunity ledger.",
      ]),
    },
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildScoreBands({
  dossier,
  detailedInterpretation,
  familyClarityRoadmap,
}: {
  dossier: CounselorReviewDossier;
  detailedInterpretation: DetailedVolunteerPlanInterpretation;
  familyClarityRoadmap: FamilyDecisionClarityRoadmap;
}): HiddenOpportunityAuditScoreBand[] {
  return [
    scoreClaimFactor(
      "official_change",
      15,
      hasEvidenceClaim(dossier, "official_diff"),
      hasExplainableClaim(detailedInterpretation, "official_diff"),
      "Official plan diff is attached and can be explained.",
      "Official plan diff is missing or not explainable.",
    ),
    scoreClaimFactor(
      "rank_direction",
      10,
      hasEvidenceClaim(dossier, "rank_delta"),
      hasExplainableClaim(detailedInterpretation, "rank_delta"),
      "Rank direction evidence is attached and can be explained.",
      "Rank direction evidence is missing or not explainable.",
    ),
    scoreClaimFactor(
      "external_plan_gap",
      15,
      hasEvidenceClaim(dossier, "competitor_missed"),
      hasExplainableClaim(detailedInterpretation, "competitor_missed"),
      "External plan comparison supports the omission/gap hypothesis.",
      "External plan comparison has not cleared the evidence gate.",
    ),
    scoreSimpleFactor(
      "low_attention_signal",
      10,
      hasSearchIntent(dossier, "low_attention_signal") &&
        dossier.publicOpinionPosition.canUseHiddenOpportunityLabel &&
        dossier.publicOpinionPosition.wordingGateStatus === "hypothesis_only",
      "Low-attention signal exists and wording gate allows under-attention framing.",
      "Low-attention signal or wording gate is not sufficient.",
    ),
    scoreSimpleFactor(
      "counter_evidence_clearance",
      10,
      hasSearchIntent(dossier, "counter_evidence") && intentClear(dossier, "counter_evidence"),
      "Counter-evidence search has been run without rejected or unreturned rows.",
      "Counter-evidence search is missing, rejected, or unreturned.",
    ),
    scoreSimpleFactor(
      "hype_pressure_clearance",
      10,
      hasSearchIntent(dossier, "hype_pressure") && intentClear(dossier, "hype_pressure"),
      "Hype-pressure search has been run without rejected or unreturned rows.",
      "Hype-pressure search is missing, rejected, or unreturned.",
    ),
    sourceDiversityScore(dossier),
    evidenceQualityScore(dossier),
    familyReadinessScore(familyClarityRoadmap),
  ];
}

function scoreClaimFactor(
  factor: HiddenOpportunityAuditFactor,
  maxPoints: number,
  hasEvidence: boolean,
  canExplain: boolean,
  success: string,
  failure: string,
): HiddenOpportunityAuditScoreBand {
  const points = hasEvidence && canExplain ? maxPoints : hasEvidence ? Math.floor(maxPoints / 2) : 0;
  return {
    factor,
    points,
    maxPoints,
    rationale: points === maxPoints ? success : failure,
  };
}

function scoreSimpleFactor(
  factor: HiddenOpportunityAuditFactor,
  maxPoints: number,
  passes: boolean,
  success: string,
  failure: string,
): HiddenOpportunityAuditScoreBand {
  return {
    factor,
    points: passes ? maxPoints : 0,
    maxPoints,
    rationale: passes ? success : failure,
  };
}

function sourceDiversityScore(dossier: CounselorReviewDossier): HiddenOpportunityAuditScoreBand {
  const intents = new Set(dossier.searchProvenance.queryRows.map((row) => row.searchIntent ?? row.taskType));
  const providers = dossier.searchProvenance.providerIds.length;
  const passes = intents.size >= 4 && providers >= 1;
  return {
    factor: "source_diversity",
    points: passes ? 10 : intents.size >= 3 ? 5 : 0,
    maxPoints: 10,
    rationale: passes
      ? `Search plan spans ${intents.size} intents across ${providers} provider(s).`
      : `Search plan spans only ${intents.size} intent(s) across ${providers} provider(s).`,
  };
}

function evidenceQualityScore(dossier: CounselorReviewDossier): HiddenOpportunityAuditScoreBand {
  const points =
    dossier.evidenceQuality.status === "review_ready" ? 10 :
      dossier.evidenceQuality.status === "needs_review" ? 4 :
        0;
  return {
    factor: "evidence_quality",
    points,
    maxPoints: 10,
    rationale:
      dossier.evidenceQuality.status === "review_ready"
        ? "Evidence quality is review-ready."
        : `Evidence quality is ${dossier.evidenceQuality.status}.`,
  };
}

function familyReadinessScore(roadmap: FamilyDecisionClarityRoadmap): HiddenOpportunityAuditScoreBand {
  const passes = roadmap.status === "ready_for_row_discussion" && roadmap.rowDiscussionGate.canDiscussRows;
  return {
    factor: "family_readiness",
    points: passes ? 10 : roadmap.status === "needs_concept_repair" ? 4 : 0,
    maxPoints: 10,
    rationale: passes
      ? "Family concept readiness allows row-level discussion."
      : `Family clarity roadmap is ${roadmap.status}.`,
  };
}

function blockingReasons({
  dossier,
  detailedInterpretation,
  researchStrategy,
  familyClarityRoadmap,
}: {
  dossier: CounselorReviewDossier;
  detailedInterpretation: DetailedVolunteerPlanInterpretation;
  researchStrategy: WebEvidenceResearchStrategy;
  familyClarityRoadmap: FamilyDecisionClarityRoadmap;
}): string[] {
  const reasons: string[] = [];
  if (dossier.evidenceQuality.status === "blocked") {
    reasons.push(...dossier.evidenceQuality.blockingConcerns, "Evidence quality is blocked.");
  }
  if (detailedInterpretation.status === "blocked") {
    reasons.push("Detailed volunteer-plan interpretation is blocked.");
  }
  if (researchStrategy.status === "blocked_by_evidence_quality") {
    reasons.push("Web evidence research strategy is blocked.");
  }
  if (familyClarityRoadmap.status === "blocked") {
    reasons.push(...familyClarityRoadmap.rowDiscussionGate.blockedReasons, "Family row discussion is blocked.");
  }
  if (/^blocked/.test(dossier.publicOpinionPosition.wordingGateStatus)) {
    reasons.push(`Trend wording gate is ${dossier.publicOpinionPosition.wordingGateStatus}.`);
  }
  for (const intent of ["counter_evidence", "hype_pressure"] as const) {
    if (hasRejectedOrUnreturnedIntent(dossier, intent)) {
      reasons.push(`${intent} search has rejected or unreturned rows.`);
    }
  }
  return unique(reasons);
}

function requiredBeforeFamilyWording({
  dossier,
  detailedInterpretation,
  researchStrategy,
  familyClarityRoadmap,
}: {
  dossier: CounselorReviewDossier;
  detailedInterpretation: DetailedVolunteerPlanInterpretation;
  researchStrategy: WebEvidenceResearchStrategy;
  familyClarityRoadmap: FamilyDecisionClarityRoadmap;
}): string[] {
  const requirements: string[] = [];
  if (!hasSearchIntent(dossier, "counter_evidence")) {
    requirements.push("Run counter-evidence search before family wording.");
  }
  if (!hasSearchIntent(dossier, "hype_pressure")) {
    requirements.push("Run hype-pressure search before family wording.");
  }
  if (!hasEvidenceClaim(dossier, "competitor_missed") || !hasExplainableClaim(detailedInterpretation, "competitor_missed")) {
    requirements.push("Attach external-plan comparison before ledger entry.");
  }
  if (researchStrategy.status !== "ready_to_run") {
    requirements.push("Resolve web evidence research strategy status before presenting the audit.");
  }
  if (!familyClarityRoadmap.rowDiscussionGate.canDiscussRows) {
    requirements.push("Repair family concept readiness before row-level discussion.");
  }
  return unique(requirements);
}

function positiveSignalsFor(
  scoreBands: HiddenOpportunityAuditScoreBand[],
  dossier: CounselorReviewDossier,
  familyClarityRoadmap: FamilyDecisionClarityRoadmap,
): string[] {
  return unique([
    ...scoreBands.filter((band) => band.points === band.maxPoints).map((band) => band.rationale),
    ...dossier.whatWeCanSay,
    familyClarityRoadmap.rowDiscussionGate.nextAction,
  ]);
}

function negativeSignalsFor(
  blockers: string[],
  scoreBands: HiddenOpportunityAuditScoreBand[],
  dossier: CounselorReviewDossier,
): string[] {
  return unique([
    ...blockers,
    ...scoreBands.filter((band) => band.points < band.maxPoints).map((band) => band.rationale),
    ...dossier.evidenceQuality.blockingConcerns,
  ]);
}

function forbiddenClaimsFor(
  dossier: CounselorReviewDossier,
  researchStrategy: WebEvidenceResearchStrategy,
): string[] {
  return unique([
    "Do not claim admission guarantee.",
    "Do not claim final recommendation.",
    "Do not claim public opinion proves demand.",
    ...dossier.whatWeCannotSay,
    ...dossier.publicOpinionPosition.forbiddenWording,
    ...researchStrategy.minimumEvidenceRules.filter((rule) => /forbidden|hypothesis-only|final recommendation/i.test(rule)),
  ]);
}

function labelPermissionFor(
  status: HiddenOpportunityAuditStatus,
  canUseHiddenOpportunityLabel: boolean,
): HiddenOpportunityLabelPermission {
  if (status === "blocked") {
    return "do_not_use_hidden_opportunity";
  }
  if (status === "candidate_for_counselor_review" && canUseHiddenOpportunityLabel) {
    return "under_attention_candidate_only";
  }
  return "internal_watchlist_only";
}

function hasEvidenceClaim(dossier: CounselorReviewDossier, claim: string): boolean {
  return dossier.evidenceTrail.some((item) => item.claim === claim);
}

function hasExplainableClaim(
  detailedInterpretation: DetailedVolunteerPlanInterpretation,
  claim: string,
): boolean {
  return detailedInterpretation.claimRows.some((row) => row.claim === claim && row.stance === "can_explain");
}

function hasSearchIntent(dossier: CounselorReviewDossier, intent: string): boolean {
  return dossier.searchProvenance.queryRows.some((row) => row.searchIntent === intent);
}

function intentClear(dossier: CounselorReviewDossier, intent: string): boolean {
  return hasSearchIntent(dossier, intent) && !hasRejectedOrUnreturnedIntent(dossier, intent);
}

function hasRejectedOrUnreturnedIntent(dossier: CounselorReviewDossier, intent: string): boolean {
  return dossier.searchProvenance.resultRows.some((row) => (
    row.searchIntent === intent &&
    (row.outcome === "rejected" || row.outcome === "unreturned")
  ));
}

function unique(items: string[]): string[] {
  return Array.from(new Set(items.filter(Boolean)));
}

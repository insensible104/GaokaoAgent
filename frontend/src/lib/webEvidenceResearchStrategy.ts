import type { CounselorReviewDossier } from "./counselorReviewDossier";
import type { DetailedVolunteerPlanInterpretation } from "./detailedVolunteerPlanInterpretation";
import type { WebEvidenceSourceTier, WebEvidenceTaskType } from "./webEvidencePlanner";
import type { PublicOpinionSearchIntent } from "./webEvidenceSearchAdapter";

export type WebEvidenceResearchStrategyStatus =
  | "ready_to_run"
  | "needs_query_repair"
  | "blocked_by_evidence_quality";

export type WebEvidenceResearchPillar =
  | "official_plan"
  | "rank_calibration"
  | "public_opinion_trend"
  | "external_plan_omission"
  | "family_concept";

export interface WebEvidenceResearchPillarRow {
  pillar: WebEvidenceResearchPillar;
  status: "covered" | "needs_counter_check" | "needs_second_source" | "blocked" | "missing";
  evidenceCount: number;
  nextCheck: string;
}

export interface WebEvidenceResearchPriorityQuery {
  id: string;
  status: "ready" | "must_rerun" | "keep_for_audit";
  priority: "critical" | "high" | "medium" | "low";
  taskType: WebEvidenceTaskType;
  searchIntent?: PublicOpinionSearchIntent;
  query: string;
  sourceTier: WebEvidenceSourceTier;
  evidenceQuestion: string;
  allowedClaims: string[];
  rejectsAsProof: string[];
  escalationRule: string;
}

export interface WebEvidenceResearchStrategy {
  protocol: "web_evidence_research_strategy_v1";
  status: WebEvidenceResearchStrategyStatus;
  researchPillars: WebEvidenceResearchPillarRow[];
  priorityQueries: WebEvidenceResearchPriorityQuery[];
  contradictionTests: string[];
  minimumEvidenceRules: string[];
  presentationGate: string;
  operatorBrief: string[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "This research strategy does not support claims or make recommendations. It converts dossier provenance into an auditable search plan; claims still require accepted evidence intake, triangulation, and counselor signoff.";

export function buildWebEvidenceResearchStrategy({
  dossier,
  detailedInterpretation,
}: {
  dossier: CounselorReviewDossier;
  detailedInterpretation: DetailedVolunteerPlanInterpretation;
}): WebEvidenceResearchStrategy {
  const status = resolveStatus(dossier, detailedInterpretation);
  const priorityQueries = buildPriorityQueries(dossier, status);

  return {
    protocol: "web_evidence_research_strategy_v1",
    status,
    researchPillars: buildResearchPillars(dossier),
    priorityQueries,
    contradictionTests: buildContradictionTests(dossier, detailedInterpretation),
    minimumEvidenceRules: buildMinimumEvidenceRules(),
    presentationGate: buildPresentationGate(dossier, detailedInterpretation),
    operatorBrief: buildOperatorBrief(dossier, detailedInterpretation, status),
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function resolveStatus(
  dossier: CounselorReviewDossier,
  detailedInterpretation: DetailedVolunteerPlanInterpretation,
): WebEvidenceResearchStrategyStatus {
  if (dossier.evidenceQuality.status === "blocked" || detailedInterpretation.status === "blocked") {
    return "blocked_by_evidence_quality";
  }
  if (
    dossier.searchProvenance.queryRows.length === 0 ||
    dossier.searchProvenance.summary.unreturnedRows > 0 ||
    dossier.searchProvenance.summary.rejectedRows > 0
  ) {
    return "needs_query_repair";
  }
  return "ready_to_run";
}

function buildResearchPillars(dossier: CounselorReviewDossier): WebEvidenceResearchPillarRow[] {
  return [
    pillarRow({
      dossier,
      pillar: "official_plan",
      sourceTier: "official",
      nextCheck: "Verify official school code, group code, major code, quota, subject requirements, and source URL.",
    }),
    pillarRow({
      dossier,
      pillar: "rank_calibration",
      sourceTier: "historical_data",
      nextCheck: "Compare at least two independent rank-history sources and keep quota context attached.",
    }),
    publicOpinionPillarRow(dossier),
    pillarRow({
      dossier,
      pillar: "external_plan_omission",
      sourceTier: "competitor_plan",
      nextCheck: "Search whether external plans already incorporated the 2026 official change before calling it omitted.",
    }),
    pillarRow({
      dossier,
      pillar: "family_concept",
      sourceTier: "concept",
      nextCheck: "Confirm the family can explain professional group, adjustment, safe anchor, and interest tradeoff.",
    }),
  ];
}

function pillarRow({
  dossier,
  pillar,
  sourceTier,
  nextCheck,
}: {
  dossier: CounselorReviewDossier;
  pillar: WebEvidenceResearchPillar;
  sourceTier: WebEvidenceSourceTier;
  nextCheck: string;
}): WebEvidenceResearchPillarRow {
  const evidenceCount = dossier.evidenceTrail.filter((item) => item.sourceTier === sourceTier).length;
  const unresolvedForTier = dossier.gapPosition.unresolvedClaims.filter((claim) => (
    dossier.evidenceTrail.some((item) => item.claim === claim && item.sourceTier === sourceTier)
  ));
  return {
    pillar,
    status: evidenceCount === 0 ? "missing" : unresolvedForTier.length > 0 ? "needs_second_source" : "covered",
    evidenceCount,
    nextCheck,
  };
}

function publicOpinionPillarRow(dossier: CounselorReviewDossier): WebEvidenceResearchPillarRow {
  const evidenceCount = dossier.evidenceTrail.filter((item) => item.sourceTier === "public_opinion").length;
  const hasCounterSearch = dossier.searchProvenance.queryRows.some((row) => row.searchIntent === "counter_evidence");
  const hasHypeSearch = dossier.searchProvenance.queryRows.some((row) => row.searchIntent === "hype_pressure");
  const status =
    dossier.evidenceQuality.status === "blocked"
      ? "blocked"
      : evidenceCount === 0
        ? "missing"
        : hasCounterSearch && hasHypeSearch
          ? "needs_counter_check"
          : "needs_second_source";
  return {
    pillar: "public_opinion_trend",
    status,
    evidenceCount,
    nextCheck:
      "Run low-attention, counter-evidence, hype-pressure, regional-preference, and source-diversity searches; keep all trend language hypothesis-only.",
  };
}

function buildPriorityQueries(
  dossier: CounselorReviewDossier,
  status: WebEvidenceResearchStrategyStatus,
): WebEvidenceResearchPriorityQuery[] {
  return dossier.searchProvenance.queryRows
    .map((row) => {
      const unreturned = dossier.searchProvenance.resultRows.some((result) => (
        result.requestId === row.requestId && result.outcome === "unreturned"
      ));
      return {
        id: row.requestId,
        status: status === "blocked_by_evidence_quality" || unreturned ? "must_rerun" : statusForQuery(row.taskType),
        priority: priorityForQuery(row.taskType, row.searchIntent),
        taskType: row.taskType,
        searchIntent: row.searchIntent,
        query: row.query,
        sourceTier: row.sourceTier,
        evidenceQuestion: row.evidenceQuestion ?? defaultEvidenceQuestion(row.taskType),
        allowedClaims: row.allowedClaims,
        rejectsAsProof: row.rejectsAsProof,
        escalationRule: escalationRuleForQuery(row.taskType, row.searchIntent),
      };
    })
    .sort((a, b) => priorityRank(a.priority) - priorityRank(b.priority));
}

function statusForQuery(taskType: WebEvidenceTaskType): WebEvidenceResearchPriorityQuery["status"] {
  if (taskType === "public_opinion_scan") {
    return "ready";
  }
  return "keep_for_audit";
}

function priorityForQuery(
  taskType: WebEvidenceTaskType,
  searchIntent?: PublicOpinionSearchIntent,
): WebEvidenceResearchPriorityQuery["priority"] {
  if (searchIntent === "counter_evidence") {
    return "critical";
  }
  if (searchIntent === "hype_pressure") {
    return "high";
  }
  if (taskType === "official_plan_verification" || taskType === "rank_history_calibration") {
    return "high";
  }
  if (taskType === "external_plan_comparison") {
    return "medium";
  }
  return "low";
}

function priorityRank(priority: WebEvidenceResearchPriorityQuery["priority"]): number {
  if (priority === "critical") return 0;
  if (priority === "high") return 1;
  if (priority === "medium") return 2;
  return 3;
}

function defaultEvidenceQuestion(taskType: WebEvidenceTaskType): string {
  if (taskType === "official_plan_verification") {
    return "Does the official row exactly match the opportunity being discussed?";
  }
  if (taskType === "rank_history_calibration") {
    return "Does rank history support only a directional interpretation with quota context retained?";
  }
  if (taskType === "external_plan_comparison") {
    return "Do external plans omit, underweight, include, or contradict the official change?";
  }
  if (taskType === "family_concept_clarification") {
    return "Can the family explain the concept before row-level discussion?";
  }
  return "What dated public-opinion signal is being tested?";
}

function escalationRuleForQuery(
  taskType: WebEvidenceTaskType,
  searchIntent?: PublicOpinionSearchIntent,
): string {
  if (searchIntent === "counter_evidence") {
    return "If broad recognition appears, block low-attention or hidden-opportunity wording and keep the claim as hypothesis-only.";
  }
  if (searchIntent === "hype_pressure") {
    return "If hype pressure appears, block hidden-opportunity wording and require counselor review before family presentation.";
  }
  if (searchIntent === "low_attention_signal") {
    return "If signals are anecdotal, require source diversity before using trend language.";
  }
  if (taskType === "official_plan_verification") {
    return "If the official row does not match, stop the opportunity thesis.";
  }
  if (taskType === "rank_history_calibration") {
    return "If rank sources conflict, downgrade rank impact to needs review.";
  }
  if (taskType === "external_plan_comparison") {
    return "If external plans already include the change, remove competitor-missed wording.";
  }
  return "If the family cannot answer the concept question, pause row-level recommendation discussion.";
}

function buildContradictionTests(
  dossier: CounselorReviewDossier,
  detailedInterpretation: DetailedVolunteerPlanInterpretation,
): string[] {
  const trendRow = detailedInterpretation.claimRows.find((row) => row.claim === "trend_wording");
  return unique([
    "Search for official-row mismatch before discussing any opportunity.",
    "Search for rank-history conflict before using directional rank impact.",
    "Search for external plans that already include the 2026 change before claiming omission.",
    "Search for broad recognition, hype pressure, or mainstream attention before using under-attention wording.",
    ...(trendRow?.counterChecks ?? []),
    ...dossier.publicOpinionPosition.forbiddenWording.map((item) => `Forbidden wording test: ${item}`),
  ]);
}

function buildMinimumEvidenceRules(): string[] {
  return [
    "Official plan diff must be attached before opportunity language is used.",
    "Rank calibration needs at least two independent historical-data checks before directional rank impact is family-facing.",
    "Public-opinion trend language requires low-attention evidence, counter-evidence search, hype-pressure search, and source diversity; it remains hypothesis-only.",
    "External-plan omission needs row-level comparison against the official diff and at least one counter-search for plans that already include the change.",
    "Family concept readiness must cover professional group, adjustment, safe anchor, and interest tradeoff before row-level discussion.",
    "Final recommendation remains forbidden until counselor signoff.",
  ];
}

function buildPresentationGate(
  dossier: CounselorReviewDossier,
  detailedInterpretation: DetailedVolunteerPlanInterpretation,
): string {
  if (dossier.evidenceQuality.status === "blocked" || detailedInterpretation.status === "blocked") {
    return "Do not present this research strategy to the family until evidence quality blockers are resolved.";
  }
  if (detailedInterpretation.status === "ready_for_family_review") {
    return "Use as a family-review explanation only after counselor signoff; keep public-opinion wording hypothesis-only.";
  }
  return "Use internally until counselor review confirms evidence quality and concept readiness.";
}

function buildOperatorBrief(
  dossier: CounselorReviewDossier,
  detailedInterpretation: DetailedVolunteerPlanInterpretation,
  status: WebEvidenceResearchStrategyStatus,
): string[] {
  const brief: string[] = [];
  if (status === "blocked_by_evidence_quality") {
    brief.push("Resolve evidence quality blockers before family presentation.");
    brief.push(...dossier.evidenceQuality.blockingConcerns);
  }
  brief.push("Verify official plan row before interpreting demand, rank movement, or external-plan omission.");
  brief.push("Run counter-evidence and hype-pressure searches before using trend wording.");
  brief.push("Keep public-opinion evidence as hypothesis-only; never use it as admission probability or final recommendation proof.");
  brief.push(...detailedInterpretation.planPosition.notARecommendationReasons);
  return unique(brief);
}

function unique<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

import type { AdmissionsOpportunityWorkflow } from "./admissionsOpportunityWorkflow";
import type { EvidenceCollectionWorkspace } from "./evidenceCollectionWorkspace";
import type { FamilyDecisionBrief } from "./evidenceBackedInterpretationPackage";
import type { EvidenceClaimSupport, WebEvidenceSourceTier, WebEvidenceTaskType } from "./webEvidencePlanner";
import type { WebEvidenceSearchRun, WebEvidenceSearchTraceRow } from "./webEvidenceSearchRun";

export interface CounselorReviewDossierInput {
  workflow: AdmissionsOpportunityWorkflow;
  workspace: EvidenceCollectionWorkspace;
  studentName?: string;
  searchRuns?: WebEvidenceSearchRun[];
  assessedAt?: string;
}

export interface CounselorReviewEvidenceTrailItem {
  taskId: string;
  taskType?: WebEvidenceTaskType;
  claim: EvidenceClaimSupport;
  sourceTitle: string;
  sourceUrl: string;
  sourceTier: WebEvidenceSourceTier | "unknown";
  capturedAt: string;
  excerpts: string[];
}

export interface CounselorReviewDossier {
  protocol: "counselor_review_dossier_v1";
  status: EvidenceCollectionWorkspace["status"];
  caseSummary: {
    studentName: string;
    summary: string;
  };
  opportunityThesis: string;
  evidenceTrail: CounselorReviewEvidenceTrailItem[];
  publicOpinionPosition: {
    guardStatus: string;
    opportunitySignal: string;
    confidence: string;
    evidenceRole: "hypothesis_only";
    familySafeSummary: string;
    requiredFollowUps: string[];
    wordingGateStatus: string;
    wordingGateScore: number;
    canUseHiddenOpportunityLabel: boolean;
    familySafeWording: string;
    requiredEvidence: string[];
    forbiddenWording: string[];
  };
  gapPosition: {
    status: EvidenceCollectionWorkspace["evidenceGapSearchPlan"]["status"];
    triangulationStatus: EvidenceCollectionWorkspace["triangulationReport"]["status"];
    followUpCount: number;
    unresolvedClaims: EvidenceClaimSupport[];
  };
  searchProvenance: CounselorSearchProvenance;
  evidenceQuality: CounselorEvidenceQuality;
  decisionBrief: FamilyDecisionBrief | null;
  whatWeCanSay: string[];
  whatWeCannotSay: string[];
  counselorReviewChecklist: string[];
  familyQuestions: string[];
  claimBoundary: string;
}

export type CounselorEvidenceQualityStatus = "review_ready" | "needs_review" | "blocked";
export type CounselorEvidenceAuthorityLevel = "authoritative" | "specialized" | "context" | "weak";
export type CounselorEvidenceFreshness = "current_cycle" | "recent" | "stale" | "undated";

export interface CounselorEvidenceQualitySourceRow {
  taskId: string;
  claim: EvidenceClaimSupport;
  sourceTitle: string;
  sourceTier: WebEvidenceSourceTier | "unknown";
  capturedAt: string;
  authorityLevel: CounselorEvidenceAuthorityLevel;
  freshness: CounselorEvidenceFreshness;
  riskFlags: string[];
}

export interface CounselorEvidenceQuality {
  protocol: "counselor_evidence_quality_v1";
  status: CounselorEvidenceQualityStatus;
  assessedAt: string;
  summary: {
    authoritativeSources: number;
    currentCycleSources: number;
    staleSources: number;
    conflictedClaims: number;
    rejectedSearchRows: number;
    unreturnedSearchRows: number;
  };
  sourceRows: CounselorEvidenceQualitySourceRow[];
  blockingConcerns: string[];
  familyPresentationGate: string;
  claimBoundary: string;
}

export interface CounselorSearchProvenance {
  protocol: "counselor_search_provenance_v1";
  runCount: number;
  providerIds: string[];
  summary: {
    acceptedRows: number;
    rejectedRows: number;
    unreturnedRows: number;
  };
  queryRows: Array<{
    requestId: string;
    taskId: string;
    taskType: WebEvidenceTaskType;
    query: string;
    sourceTier: WebEvidenceSourceTier;
    allowedClaims: EvidenceClaimSupport[];
    searchIntent?: WebEvidenceSearchTraceRow["searchIntent"];
    evidenceQuestion?: string;
    rejectsAsProof: string[];
  }>;
  resultRows: WebEvidenceSearchTraceRow[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "This dossier is not a final filing recommendation. It organizes auditable evidence, claim limits, and counselor-review questions.";

const SEARCH_PROVENANCE_BOUNDARY =
  "Search provenance is provider provenance only. It shows what was searched and returned, but claim support still depends on evidence intake and triangulation.";

const EVIDENCE_QUALITY_BOUNDARY =
  "Evidence quality scores source authority, freshness, conflicts, and search gaps. It gates presentation quality but does not make final recommendations.";

export function buildCounselorReviewDossier(input: CounselorReviewDossierInput): CounselorReviewDossier {
  const insight = input.workflow.discoveryLedger.insights[0];
  const card = input.workspace.completion.interpretationPackage?.opportunityCards[0] ?? null;
  const decisionBrief = card?.familyDecisionBrief ?? null;
  const evidenceTrail: CounselorReviewEvidenceTrailItem[] = input.workspace.completion.intakeResult.acceptedEvidence.map((item) => {
    const taskRow = input.workspace.taskRows.find((row) => row.taskId === item.taskId);
    const sourceTier: WebEvidenceSourceTier | "unknown" = taskRow?.resultTemplate.sourceTier ?? "unknown";
    return {
      taskId: item.taskId,
      taskType: taskRow?.taskType,
      claim: item.claim,
      sourceTitle: item.sourceTitle,
      sourceUrl: item.sourceUrl,
      sourceTier,
      capturedAt: item.capturedAt,
      excerpts: item.excerpts,
    };
  });
  const unresolvedClaims = input.workspace.triangulationReport.claims
    .filter((claim) => (
      claim.status === "unsupported" || claim.status === "needs_second_source" || claim.status === "conflicted"
    ))
    .map((claim) => claim.claim);
  const searchProvenance = buildSearchProvenance(input.searchRuns ?? []);

  return {
    protocol: "counselor_review_dossier_v1",
    status: input.workspace.status,
    caseSummary: {
      studentName: input.studentName ?? "Student",
      summary: buildCaseSummary(input.workspace),
    },
    opportunityThesis: buildOpportunityThesis(insight),
    evidenceTrail,
    publicOpinionPosition: buildPublicOpinionPosition(insight, input.workflow.trendAnalysis.trendLanguageGate),
    gapPosition: {
      status: input.workspace.evidenceGapSearchPlan.status,
      triangulationStatus: input.workspace.triangulationReport.status,
      followUpCount: input.workspace.evidenceGapSearchPlan.followUps.length,
      unresolvedClaims,
    },
    searchProvenance,
    evidenceQuality: buildEvidenceQuality({
      evidenceTrail,
      workspace: input.workspace,
      searchProvenance,
      assessedAt: input.assessedAt ?? "2026-06-16",
    }),
    decisionBrief,
    whatWeCanSay: buildWhatWeCanSay(input, evidenceTrail),
    whatWeCannotSay: buildWhatWeCannotSay(input.workflow.trendAnalysis.trendLanguageGate),
    counselorReviewChecklist: buildCounselorReviewChecklist(input),
    familyQuestions: decisionBrief?.decisionQuestions ?? defaultFamilyQuestions(),
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildEvidenceQuality({
  evidenceTrail,
  workspace,
  searchProvenance,
  assessedAt,
}: {
  evidenceTrail: CounselorReviewEvidenceTrailItem[];
  workspace: EvidenceCollectionWorkspace;
  searchProvenance: CounselorSearchProvenance;
  assessedAt: string;
}): CounselorEvidenceQuality {
  const sourceRows = evidenceTrail.map((item) => buildEvidenceQualitySourceRow(item, assessedAt));
  const staleSources = sourceRows.filter((row) => row.freshness === "stale" || row.freshness === "undated").length;
  const conflictingSearchRows = searchProvenance.resultRows.filter((row) => /counter-evidence|conflict|contradict/i.test(row.rejectionReason ?? ""));
  const blockingConcerns = [
    ...workspace.triangulationReport.claims
      .filter((claim) => claim.status === "conflicted")
      .flatMap((claim) => claim.issues.map((issue) => `${claim.claim}: ${issue}`)),
    ...conflictingSearchRows.map((row) => `${row.taskId}: ${row.rejectionReason}`),
    ...searchProvenance.resultRows
      .filter((row) => row.outcome === "unreturned")
      .map((row) => `${row.taskId}: unreturned search result for ${row.query}`),
  ];
  const status = resolveEvidenceQualityStatus({
    workspace,
    searchProvenance,
    staleSources,
    blockingConcerns,
  });

  return {
    protocol: "counselor_evidence_quality_v1",
    status,
    assessedAt,
    summary: {
      authoritativeSources: sourceRows.filter((row) => row.authorityLevel === "authoritative").length,
      currentCycleSources: sourceRows.filter((row) => row.freshness === "current_cycle").length,
      staleSources,
      conflictedClaims: workspace.triangulationReport.summary.conflictedClaims,
      rejectedSearchRows: searchProvenance.summary.rejectedRows,
      unreturnedSearchRows: searchProvenance.summary.unreturnedRows,
    },
    sourceRows,
    blockingConcerns,
    familyPresentationGate: buildFamilyPresentationGate(status),
    claimBoundary: EVIDENCE_QUALITY_BOUNDARY,
  };
}

function buildEvidenceQualitySourceRow(
  item: CounselorReviewEvidenceTrailItem,
  assessedAt: string,
): CounselorEvidenceQualitySourceRow {
  const authorityLevel = authorityLevelFor(item.sourceTier, item.claim);
  const freshness = freshnessFor(item.capturedAt, assessedAt);
  const riskFlags = [
    ...(authorityLevel === "weak" ? ["weak_source_tier"] : []),
    ...(freshness === "stale" || freshness === "undated" ? [`${freshness}_evidence`] : []),
    ...(item.claim === "hypothesis_only" ? ["hypothesis_only_not_demand_proof"] : []),
  ];

  return {
    taskId: item.taskId,
    claim: item.claim,
    sourceTitle: item.sourceTitle,
    sourceTier: item.sourceTier,
    capturedAt: item.capturedAt,
    authorityLevel,
    freshness,
    riskFlags,
  };
}

function authorityLevelFor(
  sourceTier: WebEvidenceSourceTier | "unknown",
  claim: EvidenceClaimSupport,
): CounselorEvidenceAuthorityLevel {
  if (sourceTier === "official") {
    return "authoritative";
  }
  if (sourceTier === "historical_data" || sourceTier === "competitor_plan") {
    return "specialized";
  }
  if (sourceTier === "public_opinion" || sourceTier === "concept" || claim === "hypothesis_only") {
    return "context";
  }
  return "weak";
}

function freshnessFor(capturedAt: string, assessedAt: string): CounselorEvidenceFreshness {
  const capturedYear = yearFromDate(capturedAt);
  const assessedYear = yearFromDate(assessedAt);
  if (!capturedYear || !assessedYear) {
    return "undated";
  }
  if (capturedYear === assessedYear) {
    return "current_cycle";
  }
  if (assessedYear - capturedYear <= 1) {
    return "recent";
  }
  return "stale";
}

function resolveEvidenceQualityStatus({
  workspace,
  searchProvenance,
  staleSources,
  blockingConcerns,
}: {
  workspace: EvidenceCollectionWorkspace;
  searchProvenance: CounselorSearchProvenance;
  staleSources: number;
  blockingConcerns: string[];
}): CounselorEvidenceQualityStatus {
  if (
    workspace.triangulationReport.status === "conflict_review" ||
    searchProvenance.summary.unreturnedRows > 0 ||
    blockingConcerns.length > 0
  ) {
    return "blocked";
  }
  if (
    workspace.status !== "ready_for_counselor_review" ||
    searchProvenance.summary.rejectedRows > 0 ||
    staleSources > 0
  ) {
    return "needs_review";
  }
  return "review_ready";
}

function buildFamilyPresentationGate(status: CounselorEvidenceQualityStatus): string {
  if (status === "review_ready") {
    return "This dossier can be shown as a counselor-review explanation, with final filing still gated by counselor signoff.";
  }
  if (status === "needs_review") {
    return "Use internally only until stale evidence, rejected search rows, or readiness gaps are reviewed.";
  }
  return "Do not show this as a family-facing interpretation until conflicts, missing searches, and blocking concerns are resolved.";
}

function buildSearchProvenance(searchRuns: WebEvidenceSearchRun[]): CounselorSearchProvenance {
  const traceRows = searchRuns.flatMap((run) => run.searchTrace.rows);
  const queryRowsByKey = new Map<string, CounselorSearchProvenance["queryRows"][number]>();

  for (const run of searchRuns) {
    for (const request of run.requestBatch.requests) {
      const key = `${request.requestId ?? request.taskId}\u0000${request.query}`;
      if (!queryRowsByKey.has(key)) {
        queryRowsByKey.set(key, {
          requestId: request.requestId ?? request.taskId,
          taskId: request.taskId,
          taskType: request.taskType,
          query: request.query,
          sourceTier: request.sourceTier,
          allowedClaims: request.allowedClaims,
          searchIntent: request.searchIntent,
          evidenceQuestion: request.evidenceQuestion,
          rejectsAsProof: request.rejectsAsProof ?? [],
        });
      }
    }
  }

  return {
    protocol: "counselor_search_provenance_v1",
    runCount: searchRuns.length,
    providerIds: unique(traceRows.map((row) => row.provider).filter((provider): provider is string => Boolean(provider))),
    summary: {
      acceptedRows: traceRows.filter((row) => row.outcome === "accepted").length,
      rejectedRows: traceRows.filter((row) => row.outcome === "rejected").length,
      unreturnedRows: traceRows.filter((row) => row.outcome === "unreturned").length,
    },
    queryRows: Array.from(queryRowsByKey.values()),
    resultRows: traceRows,
    claimBoundary: SEARCH_PROVENANCE_BOUNDARY,
  };
}

function buildCaseSummary(workspace: EvidenceCollectionWorkspace): string {
  if (workspace.status === "ready_for_counselor_review") {
    return "This case is review-ready: blocking evidence passed intake, triangulation has no remaining gaps, and counselor signoff is still required.";
  }
  if (workspace.status === "collecting_evidence") {
    return "This case is still collecting evidence and cannot be presented as review-ready.";
  }
  return "This case is blocked by upstream workflow gates.";
}

function buildOpportunityThesis(insight?: AdmissionsOpportunityWorkflow["discoveryLedger"]["insights"][number]): string {
  if (!insight) {
    return "No opportunity thesis is available until official diff and discovery ledger pass upstream gates.";
  }
  const diffType = insight.officialEvidence.diffType;
  return [
    `${diffType}: ${insight.officialEvidence.auditKey}.`,
    `Official change suggests a candidate opportunity; public opinion remains a hypothesis, not demand proof.`,
    `Rank direction is ${insight.rankImpact.direction} with ${insight.rankImpact.confidence} confidence.`,
  ].join(" ");
}

function buildPublicOpinionPosition(
  insight?: AdmissionsOpportunityWorkflow["discoveryLedger"]["insights"][number],
  trendLanguageGate?: AdmissionsOpportunityWorkflow["trendAnalysis"]["trendLanguageGate"],
): CounselorReviewDossier["publicOpinionPosition"] {
  const guard = insight?.publicOpinionGuard;
  return {
    guardStatus: guard?.status ?? "insufficient_signal",
    opportunitySignal: guard?.opportunitySignal ?? "insufficient",
    confidence: guard?.confidence ?? "low",
    evidenceRole: "hypothesis_only",
    familySafeSummary: guard?.summary ?? "Public-opinion evidence is missing or insufficient, so it remains a hypothesis only.",
    requiredFollowUps: guard?.nextActions ?? ["Collect dated public-opinion and counter-evidence before using trend language."],
    wordingGateStatus: trendLanguageGate?.status ?? "missing",
    wordingGateScore: trendLanguageGate?.score ?? 0,
    canUseHiddenOpportunityLabel: trendLanguageGate?.canUseHiddenOpportunityLabel ?? false,
    familySafeWording:
      trendLanguageGate?.familySafeWording ??
      "Trend wording is unavailable; keep public-opinion language hypothesis-only until evidence is reviewed.",
    requiredEvidence: trendLanguageGate?.requiredEvidence ?? [
      "Attach official plan diff, rank calibration, external-plan comparison, and counter-evidence review before using trend language.",
    ],
    forbiddenWording: trendLanguageGate?.forbiddenWording ?? [
      "Do not use hidden-opportunity wording without a trend language gate.",
    ],
  };
}

function buildWhatWeCanSay(
  input: CounselorReviewDossierInput,
  evidenceTrail: CounselorReviewEvidenceTrailItem[],
): string[] {
  const insight = input.workflow.discoveryLedger.insights[0];
  const statements: string[] = [];
  if (insight && hasClaim(evidenceTrail, "official_diff")) {
    statements.push(
      `Official ${readableDiffType(insight.officialEvidence.diffType)} evidence is attached for ${insight.officialEvidence.auditKey}.`,
    );
  }
  if (insight && hasClaim(evidenceTrail, "rank_delta")) {
    statements.push(
      `Rank impact can be discussed directionally as ${insight.rankImpact.direction}, with ${insight.rankImpact.confidence} confidence and attached rank history.`,
    );
  }
  if (hasClaim(evidenceTrail, "risk_guard")) {
    statements.push("School rule and adjustment risk guard evidence is attached for counselor review.");
  }
  if (hasClaim(evidenceTrail, "competitor_missed")) {
    statements.push("External plans appear to omit or underweight the official change, based on attached comparison evidence.");
  }
  if (hasClaim(evidenceTrail, "parent_understanding")) {
    statements.push("Professional group, adjustment, safe anchor, and interest tradeoff concepts have been explained before row-level discussion.");
  }
  const trendLanguageGate = input.workflow.trendAnalysis.trendLanguageGate;
  if (trendLanguageGate.canUseHiddenOpportunityLabel) {
    statements.push(
      "Public-opinion wording may say under-attention candidate only as hypothesis-only after official, rank, external-plan, and counter-evidence review.",
    );
  } else {
    statements.push(
      `Public-opinion trend wording is blocked (${trendLanguageGate.status}); resolve the language gate before using opportunity wording.`,
    );
  }
  return statements;
}

function buildWhatWeCannotSay(
  trendLanguageGate: AdmissionsOpportunityWorkflow["trendAnalysis"]["trendLanguageGate"],
): string[] {
  return [
    "This is not a final recommendation.",
    "This is not an admission guarantee.",
    "Public-opinion evidence cannot prove demand, admission probability, or score movement.",
    "Rank history can support direction and calibration, but it cannot replace the current-year official admission result.",
    "Interest fit cannot override blacklist majors, subject requirements, physical-exam restrictions, tuition, campus, or adjustment rules.",
    ...trendLanguageGate.forbiddenWording,
  ];
}

function buildCounselorReviewChecklist(input: CounselorReviewDossierInput): string[] {
  const trendLanguageGate = input.workflow.trendAnalysis.trendLanguageGate;
  return [
    "Verify the official source row: school code, major group code, major code, quota, subject requirements, and source URL.",
    "Recheck rank history and quota context against at least two independent historical-data sources when available.",
    "Review adjustment rules, transfer rules, campus, fee, tuition, and physical-exam restrictions before signoff.",
    "Confirm the family accepts the worst-case adjusted major, campus, fee, and city outcome before treating this as a safe anchor.",
    "Keep public-opinion language hypothesis-only and look for dated counter-evidence before presenting hidden-opportunity wording.",
    ...trendLanguageGate.requiredEvidence.map((item) => `Trend language evidence gate: ${item}`),
    ...input.workspace.nextSearchActions.filter((action) => !/final recommendation/i.test(action)),
  ];
}

function defaultFamilyQuestions(): string[] {
  return [
    "Would you still accept this group if the final major is not the student's first-choice major?",
    "Which worst-case major, campus, fee, city, or adjustment result would make this row unacceptable?",
    "Is this row still a real safe anchor after adjustment and blacklist boundaries are considered?",
  ];
}

function hasClaim(evidenceTrail: CounselorReviewEvidenceTrailItem[], claim: EvidenceClaimSupport): boolean {
  return evidenceTrail.some((item) => item.claim === claim);
}

function readableDiffType(diffType: string): string {
  return diffType.replace(/_/g, " ");
}

function yearFromDate(value: string): number | null {
  const match = value.match(/^(\d{4})/);
  return match ? Number(match[1]) : null;
}

function unique<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

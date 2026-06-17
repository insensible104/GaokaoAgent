import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const libDir = path.join(here, "..", "lib");

function loadTsModule(filePath, mocks = {}) {
  const source = fs.readFileSync(filePath, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      esModuleInterop: true,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (mocks[specifier]) return mocks[specifier];
    throw new Error(`Unexpected require: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const strategyModule = loadTsModule(path.join(libDir, "webEvidenceResearchStrategy.ts"), {
  "./counselorReviewDossier": {},
  "./detailedVolunteerPlanInterpretation": {},
});

const dossier = {
  protocol: "counselor_review_dossier_v1",
  status: "ready_for_counselor_review",
  caseSummary: {
    studentName: "Student A",
    summary: "This case is review-ready.",
  },
  opportunityThesis:
    "quota_expansion: 10561-201-080901-quota_expansion. Public opinion remains a hypothesis, not demand proof.",
  evidenceTrail: [
    {
      taskId: "official-plan",
      taskType: "official_plan_verification",
      claim: "official_diff",
      sourceTitle: "Guangdong official 2026 enrollment plan",
      sourceUrl: "https://eea.gd.gov.cn/2026-plan",
      sourceTier: "official",
      capturedAt: "2026-06-16",
      excerpts: ["10561 group 201 Computer Science quota 36."],
    },
    {
      taskId: "rank-history",
      taskType: "rank_history_calibration",
      claim: "rank_delta",
      sourceTitle: "CHSI rank history second source",
      sourceUrl: "https://gaokao.chsi.com.cn/rank-history-second-source",
      sourceTier: "historical_data",
      capturedAt: "2026-06-16",
      excerpts: ["2025 rank 42000 and 2024 rank 43800 with quota context."],
    },
    {
      taskId: "public-opinion",
      taskType: "public_opinion_scan",
      claim: "hypothesis_only",
      sourceTitle: "Search summary for non-local engineering attention",
      sourceUrl: "https://search.example/non-local-engineering",
      sourceTier: "public_opinion",
      capturedAt: "2026-06-16",
      excerpts: ["Search snippets emphasize local schools and rarely mention the quota expansion."],
    },
    {
      taskId: "external-plan",
      taskType: "external_plan_comparison",
      claim: "competitor_missed",
      sourceTitle: "Teacher plan comparison second source",
      sourceUrl: "https://teacher-plan.example/review-second-source",
      sourceTier: "competitor_plan",
      capturedAt: "2026-06-16",
      excerpts: ["A second external plan still keeps the 2025 quota assumption."],
    },
    {
      taskId: "family-concept",
      taskType: "family_concept_clarification",
      claim: "parent_understanding",
      sourceTitle: "Family concept checklist",
      sourceUrl: "internal://concept-brief",
      sourceTier: "concept",
      capturedAt: "2026-06-16",
      excerpts: ["Professional group, adjustment, safe anchor, and interest tradeoff explained."],
    },
  ],
  publicOpinionPosition: {
    guardStatus: "supports_hypothesis",
    opportunitySignal: "under_attention_candidate",
    confidence: "medium",
    evidenceRole: "hypothesis_only",
    familySafeSummary: "Low-attention pattern is still a hypothesis.",
    requiredFollowUps: ["Keep dated counter-evidence review attached."],
    wordingGateStatus: "hypothesis_only",
    wordingGateScore: 76,
    canUseHiddenOpportunityLabel: true,
    familySafeWording:
      "South China Tech Computer Science can be described only as an under-attention candidate.",
    requiredEvidence: ["Attach official plan diff before using trend language."],
    forbiddenWording: ["Do not say public opinion proves demand.", "Do not say guaranteed admission."],
  },
  gapPosition: {
    status: "no_gaps",
    triangulationStatus: "triangulated",
    followUpCount: 0,
    unresolvedClaims: [],
  },
  searchProvenance: {
    protocol: "counselor_search_provenance_v1",
    runCount: 2,
    providerIds: ["demo-search-provider", "demo-gap-search-provider"],
    summary: {
      acceptedRows: 6,
      rejectedRows: 0,
      unreturnedRows: 0,
    },
    queryRows: [
      {
        requestId: "official-plan",
        taskId: "official-plan",
        taskType: "official_plan_verification",
        query: "Guangdong 2026 official enrollment plan 10561 201 Computer Science quota_expansion",
        sourceTier: "official",
        allowedClaims: ["official_diff"],
        rejectsAsProof: ["final recommendation"],
      },
      {
        requestId: "public-opinion-low",
        taskId: "public-opinion",
        taskType: "public_opinion_scan",
        query: "South China Tech Computer Science low attention overlooked cold discussion parent concern",
        sourceTier: "public_opinion",
        allowedClaims: ["hypothesis_only"],
        searchIntent: "low_attention_signal",
        evidenceQuestion: "Does dated public discussion show low attention or avoidance around this school and major?",
        rejectsAsProof: ["official plan", "admission probability", "final recommendation"],
      },
      {
        requestId: "public-opinion-counter",
        taskId: "public-opinion",
        taskType: "public_opinion_scan",
        query: "South China Tech Computer Science counter-evidence widely discussed mainstream attention popular",
        sourceTier: "public_opinion",
        allowedClaims: ["hypothesis_only"],
        searchIntent: "counter_evidence",
        evidenceQuestion: "What evidence would disprove the low-attention hypothesis?",
        rejectsAsProof: ["official plan", "admission probability", "final recommendation"],
      },
      {
        requestId: "public-opinion-hype",
        taskId: "public-opinion",
        taskType: "public_opinion_scan",
        query: "South China Tech Computer Science hype pressure hot major high salary everyone applying",
        sourceTier: "public_opinion",
        allowedClaims: ["hypothesis_only"],
        searchIntent: "hype_pressure",
        evidenceQuestion: "Is the topic crowded enough to block hidden-opportunity wording?",
        rejectsAsProof: ["official plan", "admission probability", "final recommendation"],
      },
      {
        requestId: "external-plan",
        taskId: "external-plan",
        taskType: "external_plan_comparison",
        query: "qianwen tencent teacher family plan comparison South China Tech 201 Computer Science quota_expansion",
        sourceTier: "competitor_plan",
        allowedClaims: ["competitor_missed"],
        rejectsAsProof: ["final recommendation"],
      },
    ],
    resultRows: [
      {
        requestId: "public-opinion-counter",
        taskId: "public-opinion",
        taskType: "public_opinion_scan",
        query: "South China Tech Computer Science counter-evidence widely discussed mainstream attention popular",
        provider: "demo-search-provider",
        outcome: "accepted",
        sourceTitle: "Search summary for non-local engineering attention",
        sourceUrl: "https://search.example/non-local-engineering",
        sourceTier: "public_opinion",
        claimedSupports: ["hypothesis_only"],
        rejectionReason: null,
      },
    ],
    claimBoundary: "Search provenance is provider provenance only, not claim support.",
  },
  evidenceQuality: {
    protocol: "counselor_evidence_quality_v1",
    status: "review_ready",
    assessedAt: "2026-06-16",
    summary: {
      authoritativeSources: 1,
      currentCycleSources: 5,
      staleSources: 0,
      conflictedClaims: 0,
      rejectedSearchRows: 0,
      unreturnedSearchRows: 0,
    },
    sourceRows: [],
    blockingConcerns: [],
    familyPresentationGate:
      "This dossier can be shown as a counselor-review explanation, with final filing still gated by counselor signoff.",
    claimBoundary: "Evidence quality scores source authority, freshness, conflicts, and search gaps.",
  },
  decisionBrief: {
    protocol: "family_decision_brief_v1",
    status: "ready_for_family_discussion",
    interestFitSummary: "Primary interest direction: Computer Science. Student fit is fit.",
    riskPosture: "Interest brief is ready_for_plan_discussion; risk tolerance is balanced.",
    hardBoundaries: ["Do not recommend majors matching blacklist: Civil Engineering."],
    conceptCheckpoints: ["Professional group: the unit of filing is a school major group."],
    conceptReadiness: {
      protocol: "family_concept_readiness_v1",
      status: "ready",
      checkpoints: [
        {
          concept: "professional_group",
          status: "understood",
          familyQuestion: "Can the family explain that filing is by school major group?",
          evidenceNeeded: "Family accepts group-level uncertainty.",
        },
      ],
      nextAction: "Concept readiness supports row-level discussion.",
      claimBoundary: "Concept readiness is a communication gate.",
    },
    decisionQuestions: ["Would you still accept the group if the final major is not Computer Science?"],
    cannotClaim: ["This is not a final recommendation."],
  },
  whatWeCanSay: [
    "Official quota expansion evidence is attached.",
    "Public-opinion wording may say under-attention candidate only as hypothesis-only.",
  ],
  whatWeCannotSay: [
    "This is not a final recommendation.",
    "This is not an admission guarantee.",
    "Public-opinion evidence cannot prove demand.",
  ],
  counselorReviewChecklist: ["Verify the official source row."],
  familyQuestions: ["Would you still accept the group if the final major is not Computer Science?"],
  claimBoundary:
    "This dossier is not a final filing recommendation. It organizes auditable evidence, claim limits, and counselor-review questions.",
};

const detailedInterpretation = {
  protocol: "detailed_volunteer_plan_interpretation_v1",
  status: "ready_for_family_review",
  headline: "Student A: evidence-backed plan interpretation ready for family review",
  summary: dossier.opportunityThesis,
  claimRows: [
    {
      claim: "trend_wording",
      stance: "hypothesis_only",
      familyWording:
        "South China Tech Computer Science can be described only as an under-attention candidate.",
      evidenceBasis: ["Trend language gate: hypothesis_only; score 76."],
      sourceRefs: ["Search summary for non-local engineering attention (public_opinion)"],
      counterChecks: [
        "counter_evidence: What evidence would disprove the low-attention hypothesis?; rejects as proof: official plan, admission probability, final recommendation",
        "hype_pressure: Is the topic crowded enough to block hidden-opportunity wording?; rejects as proof: official plan, admission probability, final recommendation",
      ],
      claimBoundary: "Public-opinion evidence can frame a low-attention hypothesis only.",
    },
  ],
  familyDecisionPath: {
    conceptReadinessProtocol: "family_concept_readiness_v1",
    conceptReadinessStatus: "ready",
    requiredQuestions: ["Would you still accept the group if the final major is not Computer Science?"],
    hardStops: ["Do not recommend majors matching blacklist: Civil Engineering."],
  },
  planPosition: {
    rowUse: "candidate_for_counselor_review",
    notARecommendationReasons: [
      "This is not a final recommendation.",
      "This is not an admission guarantee.",
    ],
    counselorSignoffChecklist: ["Verify the official source row."],
  },
  nextActions: ["Keep public-opinion wording hypothesis-only and preserve counter-evidence checks."],
  claimBoundary: "This detailed interpretation is not a final filing recommendation.",
};

const strategy = strategyModule.buildWebEvidenceResearchStrategy({
  dossier,
  detailedInterpretation,
});

assert.equal(strategy.protocol, "web_evidence_research_strategy_v1");
assert.equal(strategy.status, "ready_to_run");
assert.equal(strategy.researchPillars.some((pillar) => pillar.pillar === "official_plan" && pillar.status === "covered"), true);
assert.equal(strategy.researchPillars.some((pillar) => pillar.pillar === "public_opinion_trend" && pillar.status === "needs_counter_check"), true);
assert.equal(strategy.priorityQueries.some((row) => row.searchIntent === "counter_evidence" && row.priority === "critical"), true);
assert.equal(strategy.priorityQueries.some((row) => row.searchIntent === "hype_pressure" && /hidden-opportunity wording/i.test(row.escalationRule)), true);
assert.equal(strategy.priorityQueries.some((row) => row.rejectsAsProof.includes("admission probability")), true);
assert.match(strategy.minimumEvidenceRules.join("\n"), /official plan diff/i);
assert.match(strategy.minimumEvidenceRules.join("\n"), /counter-evidence/i);
assert.match(strategy.presentationGate, /family-review explanation/i);
assert.match(strategy.operatorBrief.join("\n"), /Run counter-evidence and hype-pressure searches before using trend wording/i);
assert.match(strategy.claimBoundary, /research strategy does not support claims/i);

const blockedStrategy = strategyModule.buildWebEvidenceResearchStrategy({
  dossier: {
    ...dossier,
    evidenceQuality: {
      ...dossier.evidenceQuality,
      status: "blocked",
      blockingConcerns: ["public-opinion: unreturned search result for counter-evidence query"],
    },
    searchProvenance: {
      ...dossier.searchProvenance,
      summary: {
        ...dossier.searchProvenance.summary,
        unreturnedRows: 1,
      },
    },
  },
  detailedInterpretation: {
    ...detailedInterpretation,
    status: "blocked",
  },
});

assert.equal(blockedStrategy.status, "blocked_by_evidence_quality");
assert.equal(blockedStrategy.priorityQueries.some((row) => row.status === "must_rerun"), true);
assert.match(blockedStrategy.operatorBrief.join("\n"), /Resolve evidence quality blockers/i);

console.log("Web evidence research strategy behavior test passed");

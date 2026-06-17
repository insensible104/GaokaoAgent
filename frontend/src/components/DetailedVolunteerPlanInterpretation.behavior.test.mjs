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

const detailed = loadTsModule(path.join(libDir, "detailedVolunteerPlanInterpretation.ts"), {
  "./counselorReviewDossier": {},
});

const reviewReadyDossier = {
  protocol: "counselor_review_dossier_v1",
  status: "ready_for_counselor_review",
  caseSummary: {
    studentName: "Student A",
    summary: "This case is review-ready: blocking evidence passed intake and counselor signoff is still required.",
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
      excerpts: ["Professional group, adjustment, safe anchor, and interest tradeoff explained before final rows."],
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
    ],
    resultRows: [
      {
        taskId: "public-opinion",
        taskType: "public_opinion_scan",
        query: "South China Tech Computer Science counter-evidence widely discussed mainstream attention popular",
        provider: "demo-search-provider",
        outcome: "accepted",
        sourceTitle: "Search summary for non-local engineering attention",
        claimedSupports: ["hypothesis_only"],
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
    conceptCheckpoints: [
      "Professional group: the unit of filing is a school major group, not a single favorite major.",
      "Adjustment: accepting adjustment protects admission chance, but the final major may change.",
    ],
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
        {
          concept: "safe_anchor",
          status: "understood",
          familyQuestion: "Can the family define safe by worst acceptable outcome?",
          evidenceNeeded: "Family checks worst-case major, campus, fee, and city.",
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
    "Rank impact can be discussed directionally.",
    "Public-opinion wording may say under-attention candidate only as hypothesis-only.",
  ],
  whatWeCannotSay: [
    "This is not a final recommendation.",
    "This is not an admission guarantee.",
    "Public-opinion evidence cannot prove demand.",
  ],
  counselorReviewChecklist: [
    "Verify the official source row.",
    "Confirm the family accepts the worst-case adjusted major.",
  ],
  familyQuestions: ["Would you still accept the group if the final major is not Computer Science?"],
  claimBoundary:
    "This dossier is not a final filing recommendation. It organizes auditable evidence, claim limits, and counselor-review questions.",
};

const interpretation = detailed.buildDetailedVolunteerPlanInterpretation(reviewReadyDossier);

assert.equal(interpretation.protocol, "detailed_volunteer_plan_interpretation_v1");
assert.equal(interpretation.status, "ready_for_family_review");
assert.match(interpretation.headline, /Student A/);
assert.equal(interpretation.claimRows.some((row) => row.claim === "official_diff" && row.stance === "can_explain"), true);
assert.equal(interpretation.claimRows.some((row) => row.claim === "rank_delta" && row.stance === "can_explain"), true);
assert.equal(interpretation.claimRows.some((row) => row.claim === "trend_wording" && row.stance === "hypothesis_only"), true);
assert.equal(interpretation.claimRows.some((row) => row.claim === "concept_readiness" && row.stance === "can_explain"), true);
assert.equal(interpretation.claimRows.some((row) => row.sourceRefs.some((ref) => /official 2026/.test(ref))), true);
assert.equal(interpretation.claimRows.some((row) => row.counterChecks.some((item) => /counter_evidence/.test(item))), true);
assert.equal(interpretation.claimRows.some((row) => row.counterChecks.some((item) => /hype_pressure/.test(item))), true);
assert.match(interpretation.familyDecisionPath.conceptReadinessProtocol, /family_concept_readiness_v1/);
assert.equal(interpretation.familyDecisionPath.conceptReadinessStatus, "ready");
assert.equal(interpretation.planPosition.rowUse, "candidate_for_counselor_review");
assert.match(interpretation.planPosition.notARecommendationReasons.join("\n"), /not a final recommendation/i);
assert.match(interpretation.planPosition.notARecommendationReasons.join("\n"), /admission guarantee/i);
assert.match(interpretation.claimBoundary, /not a final filing recommendation/i);

const blockedInterpretation = detailed.buildDetailedVolunteerPlanInterpretation({
  ...reviewReadyDossier,
  status: "collecting_evidence",
  evidenceQuality: {
    ...reviewReadyDossier.evidenceQuality,
    status: "blocked",
    blockingConcerns: ["public-opinion: unreturned search result for counter-evidence query"],
  },
});

assert.equal(blockedInterpretation.status, "blocked");
assert.equal(blockedInterpretation.planPosition.rowUse, "blocked");
assert.equal(blockedInterpretation.claimRows.some((row) => row.stance === "cannot_claim"), true);
assert.match(blockedInterpretation.nextActions.join("\n"), /Resolve evidence quality blockers/i);

console.log("Detailed volunteer plan interpretation behavior test passed");

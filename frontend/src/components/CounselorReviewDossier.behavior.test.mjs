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

const diffEngine = loadTsModule(path.join(libDir, "planChangeDiffEngine.ts"));
const trendAnalyzer = loadTsModule(path.join(libDir, "publicOpinionTrendAnalyzer.ts"), {
  "./opportunityDiscoveryEngine": {},
});
const discovery = loadTsModule(path.join(libDir, "opportunityDiscoveryEngine.ts"), {
  "./planChangeDiffEngine": diffEngine,
});
const planner = loadTsModule(path.join(libDir, "webEvidencePlanner.ts"), {
  "./opportunityDiscoveryEngine": discovery,
});
const clarification = loadTsModule(path.join(libDir, "studentInterestClarification.ts"), {
  "./careerAssessment": {},
});
const workflowModule = loadTsModule(path.join(libDir, "admissionsOpportunityWorkflow.ts"), {
  "./planChangeDiffEngine": diffEngine,
  "./publicOpinionTrendAnalyzer": trendAnalyzer,
  "./opportunityDiscoveryEngine": discovery,
  "./webEvidencePlanner": planner,
  "./studentInterestClarification": clarification,
});
const intake = loadTsModule(path.join(libDir, "webEvidenceIntake.ts"), {
  "./webEvidencePlanner": planner,
});
const interpretation = loadTsModule(path.join(libDir, "evidenceBackedInterpretationPackage.ts"), {
  "./opportunityDiscoveryEngine": discovery,
  "./webEvidencePlanner": planner,
  "./webEvidenceIntake": intake,
});
const completion = loadTsModule(path.join(libDir, "admissionsOpportunityWorkflowCompletion.ts"), {
  "./admissionsOpportunityWorkflow": workflowModule,
  "./webEvidenceIntake": intake,
  "./evidenceBackedInterpretationPackage": interpretation,
});
const searchBrief = loadTsModule(path.join(libDir, "webEvidenceSearchBrief.ts"), {
  "./webEvidencePlanner": planner,
});
const triangulation = loadTsModule(path.join(libDir, "evidenceTriangulationReport.ts"), {
  "./webEvidenceIntake": intake,
  "./webEvidencePlanner": planner,
});
const gapPlan = loadTsModule(path.join(libDir, "evidenceGapSearchPlan.ts"), {
  "./evidenceCollectionWorkspace": {},
  "./evidenceTriangulationReport": triangulation,
  "./webEvidencePlanner": planner,
});
const workspace = loadTsModule(path.join(libDir, "evidenceCollectionWorkspace.ts"), {
  "./admissionsOpportunityWorkflow": workflowModule,
  "./admissionsOpportunityWorkflowCompletion": completion,
  "./webEvidenceSearchBrief": searchBrief,
  "./evidenceTriangulationReport": triangulation,
  "./evidenceGapSearchPlan": gapPlan,
  "./webEvidenceIntake": intake,
  "./webEvidencePlanner": planner,
});
const worksheet = loadTsModule(path.join(libDir, "webEvidenceCaptureWorksheet.ts"), {
  "./evidenceCollectionWorkspace": workspace,
  "./webEvidenceIntake": intake,
  "./webEvidencePlanner": planner,
});
const searchAdapter = loadTsModule(path.join(libDir, "webEvidenceSearchAdapter.ts"), {
  "./evidenceCollectionWorkspace": workspace,
  "./webEvidenceCaptureWorksheet": worksheet,
});
const searchRun = loadTsModule(path.join(libDir, "webEvidenceSearchRun.ts"), {
  "./webEvidenceSearchAdapter": searchAdapter,
  "./webEvidenceIntake": intake,
});
const gapRerun = loadTsModule(path.join(libDir, "evidenceGapSearchRerun.ts"), {
  "./admissionsOpportunityWorkflow": workflowModule,
  "./evidenceCollectionWorkspace": workspace,
  "./webEvidenceIntake": intake,
  "./webEvidenceSearchAdapter": searchAdapter,
  "./webEvidenceSearchRun": searchRun,
});
const dossierModule = loadTsModule(path.join(libDir, "counselorReviewDossier.ts"), {
  "./admissionsOpportunityWorkflow": workflowModule,
  "./evidenceCollectionWorkspace": workspace,
});
const detailedInterpretation = loadTsModule(path.join(libDir, "detailedVolunteerPlanInterpretation.ts"), {
  "./counselorReviewDossier": dossierModule,
  "./webEvidencePlanner": planner,
});
const researchStrategy = loadTsModule(path.join(libDir, "webEvidenceResearchStrategy.ts"), {
  "./counselorReviewDossier": dossierModule,
  "./detailedVolunteerPlanInterpretation": detailedInterpretation,
  "./webEvidencePlanner": planner,
  "./webEvidenceSearchAdapter": searchAdapter,
});
const clarityRoadmap = loadTsModule(path.join(libDir, "familyDecisionClarityRoadmap.ts"), {
  "./evidenceBackedInterpretationPackage": interpretation,
  "./detailedVolunteerPlanInterpretation": detailedInterpretation,
  "./studentInterestClarification": clarification,
});
const hiddenOpportunityAudit = loadTsModule(path.join(libDir, "hiddenOpportunityAudit.ts"));
const planChangeLedger = loadTsModule(path.join(libDir, "planChangeOpportunityLedger.ts"), {
  "./hiddenOpportunityAudit": hiddenOpportunityAudit,
});
const narrativePackage = loadTsModule(path.join(libDir, "volunteerPlanNarrativePackage.ts"), {
  "./detailedVolunteerPlanInterpretation": detailedInterpretation,
  "./webEvidenceResearchStrategy": researchStrategy,
  "./familyDecisionClarityRoadmap": clarityRoadmap,
  "./hiddenOpportunityAudit": hiddenOpportunityAudit,
  "./planChangeOpportunityLedger": planChangeLedger,
});
const demoModule = loadTsModule(path.join(libDir, "admissionsOpportunityDemoCase.ts"), {
  "./admissionsOpportunityWorkflow": workflowModule,
  "./evidenceCollectionWorkspace": workspace,
  "./webEvidenceCaptureWorksheet": worksheet,
  "./webEvidenceSearchRun": searchRun,
  "./evidenceGapSearchRerun": gapRerun,
  "./counselorReviewDossier": dossierModule,
  "./detailedVolunteerPlanInterpretation": detailedInterpretation,
  "./webEvidenceResearchStrategy": researchStrategy,
  "./familyDecisionClarityRoadmap": clarityRoadmap,
  "./hiddenOpportunityAudit": hiddenOpportunityAudit,
  "./planChangeOpportunityLedger": planChangeLedger,
  "./volunteerPlanNarrativePackage": narrativePackage,
  "./webEvidenceIntake": intake,
});

const demo = demoModule.buildAdmissionsOpportunityDemoCase();
const dossier = dossierModule.buildCounselorReviewDossier({
  workflow: demo.workflow,
  workspace: demo.gapSearchRerun.refreshedWorkspace,
  studentName: demo.studentName,
  searchRuns: [demo.operatorSearchRun, demo.gapSearchRerun.searchRun],
  assessedAt: "2026-06-16",
});

assert.equal(dossier.protocol, "counselor_review_dossier_v1");
assert.equal(dossier.status, "ready_for_counselor_review");
assert.equal(dossier.caseSummary.studentName, "Student A");
assert.match(dossier.caseSummary.summary, /review-ready/i);
assert.match(dossier.opportunityThesis, /quota_expansion/);
assert.match(dossier.opportunityThesis, /hypothesis/i);
assert.equal(dossier.evidenceTrail.length >= 6, true);
assert.equal(dossier.evidenceTrail.some((item) => item.claim === "official_diff" && /official/.test(item.sourceTier)), true);
assert.equal(dossier.evidenceTrail.some((item) => item.claim === "rank_delta"), true);
assert.equal(dossier.evidenceTrail.some((item) => item.claim === "competitor_missed"), true);
assert.equal(dossier.publicOpinionPosition.guardStatus, "supports_hypothesis");
assert.equal(dossier.publicOpinionPosition.evidenceRole, "hypothesis_only");
assert.match(dossier.publicOpinionPosition.familySafeSummary, /hypothesis/i);
assert.equal(dossier.publicOpinionPosition.wordingGateStatus, "hypothesis_only");
assert.equal(dossier.publicOpinionPosition.canUseHiddenOpportunityLabel, true);
assert.equal(dossier.publicOpinionPosition.wordingGateScore >= 70, true);
assert.match(dossier.publicOpinionPosition.familySafeWording, /under-attention candidate/i);
assert.equal(dossier.gapPosition.status, "no_gaps");
assert.equal(dossier.gapPosition.triangulationStatus, "triangulated");
assert.equal(dossier.searchProvenance.protocol, "counselor_search_provenance_v1");
assert.equal(dossier.searchProvenance.runCount, 2);
assert.equal(dossier.searchProvenance.providerIds.includes("demo-search-provider"), true);
assert.equal(dossier.searchProvenance.providerIds.includes("demo-gap-search-provider"), true);
assert.equal(dossier.searchProvenance.summary.acceptedRows >= 6, true);
assert.equal(dossier.searchProvenance.summary.rejectedRows, 0);
assert.equal(dossier.searchProvenance.queryRows.some((row) => row.taskType === "rank_history_calibration"), true);
assert.equal(dossier.searchProvenance.queryRows.some((row) => /second independent source/.test(row.query)), true);
assert.equal(dossier.searchProvenance.queryRows.some((row) => row.searchIntent === "counter_evidence"), true);
assert.equal(dossier.searchProvenance.queryRows.some((row) => /disprove/i.test(row.evidenceQuestion ?? "")), true);
assert.equal(dossier.searchProvenance.queryRows.some((row) => row.rejectsAsProof?.includes("admission probability")), true);
assert.equal(dossier.searchProvenance.resultRows.some((row) => row.provider === "demo-gap-search-provider" && row.outcome === "accepted"), true);
assert.match(dossier.searchProvenance.claimBoundary, /provider provenance only/i);
assert.equal(dossier.evidenceQuality.protocol, "counselor_evidence_quality_v1");
assert.equal(dossier.evidenceQuality.status, "review_ready");
assert.equal(dossier.evidenceQuality.summary.authoritativeSources >= 2, true);
assert.equal(dossier.evidenceQuality.summary.currentCycleSources >= 6, true);
assert.equal(dossier.evidenceQuality.summary.conflictedClaims, 0);
assert.equal(dossier.evidenceQuality.summary.rejectedSearchRows, 0);
assert.equal(dossier.evidenceQuality.sourceRows.some((row) => row.claim === "official_diff" && row.authorityLevel === "authoritative"), true);
assert.equal(dossier.evidenceQuality.sourceRows.some((row) => row.claim === "hypothesis_only" && row.authorityLevel === "context"), true);
assert.match(dossier.evidenceQuality.familyPresentationGate, /can be shown/i);
assert.match(dossier.whatWeCanSay.join("\n"), /official.*quota expansion/i);
assert.match(dossier.whatWeCanSay.join("\n"), /rank.*direction/i);
assert.match(dossier.whatWeCanSay.join("\n"), /external plans.*omit/i);
assert.match(dossier.whatWeCanSay.join("\n"), /under-attention candidate/i);
assert.match(dossier.whatWeCanSay.join("\n"), /hypothesis-only/i);
assert.match(dossier.whatWeCannotSay.join("\n"), /final recommendation/i);
assert.match(dossier.whatWeCannotSay.join("\n"), /admission guarantee/i);
assert.match(dossier.whatWeCannotSay.join("\n"), /public-opinion.*prove/i);
assert.match(dossier.whatWeCannotSay.join("\n"), /guaranteed admission/i);
assert.match(dossier.counselorReviewChecklist.join("\n"), /official source row/i);
assert.match(dossier.counselorReviewChecklist.join("\n"), /rank history/i);
assert.match(dossier.counselorReviewChecklist.join("\n"), /adjustment/i);
assert.match(dossier.counselorReviewChecklist.join("\n"), /worst-case/i);
assert.match(dossier.counselorReviewChecklist.join("\n"), /trend language/i);
assert.match(dossier.familyQuestions.join("\n"), /Would you still accept/i);
assert.equal(dossier.decisionBrief.protocol, "family_decision_brief_v1");
assert.match(dossier.claimBoundary, /not a final filing recommendation/i);

const conflictedWorkflow = {
  ...demo.workflow,
  trendAnalysis: {
    ...demo.workflow.trendAnalysis,
    trendLanguageGate: {
      protocol: "public_opinion_trend_language_gate_v1",
      status: "blocked_by_conflict",
      score: 18,
      canUseHiddenOpportunityLabel: false,
      familySafeWording:
        "Conflicted trend evidence blocks hidden-opportunity wording until dated counter-evidence is resolved.",
      requiredEvidence: [
        "Resolve dated counter-evidence before using trend language.",
        "Run counter-evidence review with source dates and source kinds.",
      ],
      forbiddenWording: [
        "Do not call this a hidden opportunity.",
        "Do not describe this as an under-attention candidate.",
      ],
      claimBoundary: "Trend language gates decide wording only.",
    },
  },
};

const conflictedDossier = dossierModule.buildCounselorReviewDossier({
  workflow: conflictedWorkflow,
  workspace: demo.gapSearchRerun.refreshedWorkspace,
  studentName: demo.studentName,
  searchRuns: [demo.operatorSearchRun, demo.gapSearchRerun.searchRun],
  assessedAt: "2026-06-16",
});

assert.equal(conflictedDossier.publicOpinionPosition.wordingGateStatus, "blocked_by_conflict");
assert.equal(conflictedDossier.publicOpinionPosition.canUseHiddenOpportunityLabel, false);
assert.match(conflictedDossier.publicOpinionPosition.familySafeWording, /Conflicted trend evidence/i);
assert.doesNotMatch(conflictedDossier.whatWeCanSay.join("\n"), /hidden opportunity|under-attention candidate/i);
assert.match(conflictedDossier.whatWeCanSay.join("\n"), /trend wording is blocked/i);
assert.match(conflictedDossier.whatWeCanSay.join("\n"), /blocked_by_conflict/i);
assert.match(conflictedDossier.whatWeCannotSay.join("\n"), /Do not call this a hidden opportunity/i);
assert.match(conflictedDossier.whatWeCannotSay.join("\n"), /Do not describe this as an under-attention candidate/i);
assert.match(conflictedDossier.counselorReviewChecklist.join("\n"), /counter-evidence review/i);

const degradedDossier = dossierModule.buildCounselorReviewDossier({
  workflow: demo.workflow,
  workspace: demo.readyWorkspace,
  studentName: demo.studentName,
  searchRuns: [
    {
      protocol: "web_evidence_search_run_v1",
      status: "partial_success",
      requestBatch: {
        protocol: "web_evidence_search_requests_v1",
        requests: [
          {
            taskId: "external-plan",
            taskType: "external_plan_comparison",
            query: "external plan comparison query",
            domains: ["example.com"],
            sourceTier: "competitor_plan",
            allowedClaims: ["competitor_missed"],
            maxResults: 3,
          },
          {
            taskId: "rank-history",
            taskType: "rank_history_calibration",
            query: "rank history query",
            domains: ["gaokao.chsi.com.cn"],
            sourceTier: "historical_data",
            allowedClaims: ["rank_delta"],
            maxResults: 3,
          },
        ],
        claimBoundary: "request boundary",
      },
      searchTrace: {
        protocol: "web_evidence_search_trace_v1",
        rows: [
          {
            taskId: "external-plan",
            taskType: "external_plan_comparison",
            query: "external plan comparison query",
            domains: ["example.com"],
            provider: "browser-search",
            outcome: "rejected",
            sourceTitle: "Forum guarantee",
            sourceUrl: "https://example.com/forum",
            sourceTier: "competitor_plan",
            claimedSupports: ["competitor_missed"],
            rejectionReason: "counter-evidence conflicts with external-plan omission.",
          },
          {
            taskId: "rank-history",
            taskType: "rank_history_calibration",
            query: "rank history query",
            domains: ["gaokao.chsi.com.cn"],
            provider: null,
            outcome: "unreturned",
            sourceTitle: null,
            sourceUrl: null,
            sourceTier: "historical_data",
            claimedSupports: ["rank_delta"],
            rejectionReason: "No provider response returned for this request.",
          },
        ],
        claimBoundary: "trace boundary",
      },
      providerResponseCount: 1,
      acceptedEvidenceResults: [],
      rejectedAdapterResults: [],
      rejectedCaptureSubmissions: [],
      unreturnedTaskIds: ["rank-history"],
      nextActions: [],
      claimBoundary: "search run boundary",
    },
  ],
  assessedAt: "2026-06-16",
});

assert.equal(degradedDossier.evidenceQuality.status, "blocked");
assert.equal(degradedDossier.evidenceQuality.summary.rejectedSearchRows, 1);
assert.equal(degradedDossier.evidenceQuality.summary.unreturnedSearchRows, 1);
assert.match(degradedDossier.evidenceQuality.blockingConcerns.join("\n"), /counter-evidence conflicts/i);
assert.match(degradedDossier.evidenceQuality.blockingConcerns.join("\n"), /unreturned/i);
assert.match(degradedDossier.evidenceQuality.familyPresentationGate, /Do not show/i);

console.log("Counselor review dossier behavior test passed");

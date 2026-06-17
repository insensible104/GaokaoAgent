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
const workspaceModule = loadTsModule(path.join(libDir, "evidenceCollectionWorkspace.ts"), {
  "./admissionsOpportunityWorkflow": workflowModule,
  "./admissionsOpportunityWorkflowCompletion": completion,
  "./webEvidenceSearchBrief": searchBrief,
  "./evidenceTriangulationReport": triangulation,
  "./evidenceGapSearchPlan": gapPlan,
  "./webEvidenceIntake": intake,
  "./webEvidencePlanner": planner,
});
const worksheet = loadTsModule(path.join(libDir, "webEvidenceCaptureWorksheet.ts"), {
  "./evidenceCollectionWorkspace": workspaceModule,
  "./webEvidenceIntake": intake,
  "./webEvidencePlanner": planner,
});
const searchAdapter = loadTsModule(path.join(libDir, "webEvidenceSearchAdapter.ts"), {
  "./evidenceCollectionWorkspace": workspaceModule,
  "./webEvidenceCaptureWorksheet": worksheet,
});
const searchRun = loadTsModule(path.join(libDir, "webEvidenceSearchRun.ts"), {
  "./webEvidenceSearchAdapter": searchAdapter,
  "./webEvidenceIntake": intake,
});
const rerunModule = loadTsModule(path.join(libDir, "evidenceGapSearchRerun.ts"), {
  "./admissionsOpportunityWorkflow": workflowModule,
  "./evidenceCollectionWorkspace": workspaceModule,
  "./webEvidenceIntake": intake,
  "./webEvidenceSearchAdapter": searchAdapter,
  "./webEvidenceSearchRun": searchRun,
});
const dossier = loadTsModule(path.join(libDir, "counselorReviewDossier.ts"), {
  "./admissionsOpportunityWorkflow": workflowModule,
  "./evidenceCollectionWorkspace": workspaceModule,
});
const detailedInterpretation = loadTsModule(path.join(libDir, "detailedVolunteerPlanInterpretation.ts"), {
  "./counselorReviewDossier": dossier,
  "./webEvidencePlanner": planner,
});
const researchStrategy = loadTsModule(path.join(libDir, "webEvidenceResearchStrategy.ts"), {
  "./counselorReviewDossier": dossier,
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
  "./evidenceCollectionWorkspace": workspaceModule,
  "./webEvidenceCaptureWorksheet": worksheet,
  "./webEvidenceSearchRun": searchRun,
  "./evidenceGapSearchRerun": rerunModule,
  "./counselorReviewDossier": dossier,
  "./detailedVolunteerPlanInterpretation": detailedInterpretation,
  "./webEvidenceResearchStrategy": researchStrategy,
  "./familyDecisionClarityRoadmap": clarityRoadmap,
  "./hiddenOpportunityAudit": hiddenOpportunityAudit,
  "./planChangeOpportunityLedger": planChangeLedger,
  "./volunteerPlanNarrativePackage": narrativePackage,
  "./webEvidenceIntake": intake,
});

const demo = demoModule.buildAdmissionsOpportunityDemoCase();
const currentEvidenceResults = [...demo.partialEvidenceResults, ...demo.operatorSearchRun.acceptedEvidenceResults];

assert.equal(demo.readyWorkspace.status, "collecting_evidence");
assert.equal(demo.readyWorkspace.evidenceGapSearchPlan.status, "ready_to_search");
assert.equal(
  demo.readyWorkspace.evidenceGapSearchPlan.followUps.filter((followUp) => followUp.gapStatus === "needs_second_source").length,
  2,
);
const rankFollowUp = demo.readyWorkspace.evidenceGapSearchPlan.followUps.find((followUp) => followUp.claim === "rank_delta");
const competitorFollowUp = demo.readyWorkspace.evidenceGapSearchPlan.followUps.find((followUp) => followUp.claim === "competitor_missed");
assert.ok(rankFollowUp);
assert.ok(competitorFollowUp);

const rerun = rerunModule.rerunEvidenceGapSearch({
  workflow: demo.workflow,
  workspace: demo.readyWorkspace,
  currentEvidenceResults,
  responses: [
    {
      taskId: rankFollowUp.taskId,
      provider: "second-source-search",
      results: [
        {
          title: "CHSI rank history mirror",
          url: "https://gaokao.chsi.com.cn/rank-history-second-source",
          snippet: "The same school group has 2025 rank 42000 and 2024 rank 43800 with quota context.",
          sourceTier: "historical_data",
          claimedSupports: ["rank_delta"],
        },
      ],
    },
    {
      taskId: competitorFollowUp.taskId,
      provider: "second-source-search",
      results: [
        {
          title: "Teacher plan comparison second source",
          url: "https://teacher-plan.example/review-second-source",
          snippet: "A second external plan still keeps the 2025 quota assumption and omits the 2026 expansion.",
          sourceTier: "competitor_plan",
          claimedSupports: ["competitor_missed"],
        },
      ],
    },
  ],
  capturedAt: "2026-06-16",
  studentName: "Student A",
});

assert.equal(rerun.protocol, "evidence_gap_search_rerun_v1");
assert.equal(rerun.searchRun.status, "completed");
assert.equal(rerun.searchRun.acceptedEvidenceResults.length, 2);
assert.equal(rerun.mergedEvidenceResults.length, currentEvidenceResults.length + 2);
assert.equal(rerun.refreshedWorkspace.status, "ready_for_counselor_review");
assert.equal(rerun.refreshedWorkspace.evidenceGapSearchPlan.status, "no_gaps");
assert.equal(
  rerun.refreshedWorkspace.triangulationReport.claims.find((claim) => claim.claim === "rank_delta").status,
  "triangulated",
);
assert.equal(
  rerun.refreshedWorkspace.triangulationReport.claims.find((claim) => claim.claim === "competitor_missed").status,
  "triangulated",
);
assert.match(rerun.nextActions.join("\n"), /Counselor review can start/);
assert.match(rerun.claimBoundary, /do not make final recommendations/);

console.log("Evidence gap search rerun behavior test passed");

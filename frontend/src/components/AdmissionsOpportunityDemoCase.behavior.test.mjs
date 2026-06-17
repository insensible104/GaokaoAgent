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
const dossier = loadTsModule(path.join(libDir, "counselorReviewDossier.ts"), {
  "./admissionsOpportunityWorkflow": workflowModule,
  "./evidenceCollectionWorkspace": workspace,
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
  "./evidenceCollectionWorkspace": workspace,
  "./webEvidenceCaptureWorksheet": worksheet,
  "./webEvidenceSearchRun": searchRun,
  "./evidenceGapSearchRerun": gapRerun,
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

assert.equal(demo.protocol, "admissions_opportunity_demo_case_v1");
assert.equal(demo.studentName, "Student A");
assert.equal(demo.workflow.status, "needs_evidence_research");
assert.equal(demo.workflow.discoveryLedger.insights.length, 1);
assert.equal(demo.partialWorkspace.status, "collecting_evidence");
assert.equal(demo.partialWorkspace.coverageSummary.completedBlockingTasks, 1);
assert.equal(demo.captureWorksheet.status, "ready_to_capture");
assert.equal(demo.captureWorksheet.pendingRows.some((row) => row.taskType === "rank_history_calibration"), true);
assert.equal(demo.captureWorksheet.pendingRows.some((row) => row.taskType === "public_opinion_scan"), true);
assert.equal(demo.operatorSearchRun.protocol, "web_evidence_search_run_v1");
assert.equal(demo.operatorSearchRun.status, "completed");
assert.equal(demo.operatorSearchRun.acceptedEvidenceResults.length, 5);
assert.equal(demo.operatorSearchRun.rejectedAdapterResults.length, 0);
assert.equal(demo.operatorCaptureNormalization.evidenceResults.length, 5);
assert.equal(demo.operatorCaptureNormalization.rejectedSubmissions.length, 0);
assert.equal(demo.readyWorkspace.status, "collecting_evidence");
assert.equal(demo.readyWorkspace.coverageSummary.completedBlockingTasks, 4);
assert.deepEqual(demo.readyWorkspace.coverageSummary.missingClaims, ["final_recommendation"]);
assert.equal(demo.readyWorkspace.evidenceGapSearchPlan.status, "ready_to_search");
assert.equal(
  demo.readyWorkspace.evidenceGapSearchPlan.followUps.some((followUp) => followUp.gapStatus === "needs_second_source"),
  true,
);
assert.equal(demo.readyWorkspace.completion.status, "interpretation_ready");
assert.equal(demo.readyWorkspace.completion.interpretationPackage.status, "counselor_review_ready");
assert.equal(demo.readyWorkspace.completion.intakeResult.claimSupport.hypothesis_only.status, "supported");
assert.equal(demo.readyWorkspace.completion.intakeResult.claimSupport.final_recommendation.status, "unsupported");
assert.equal(demo.readyWorkspace.completion.interpretationPackage.opportunityCards[0].familyConcepts.status, "explained");
assert.equal(demo.gapSearchRerun.protocol, "evidence_gap_search_rerun_v1");
assert.equal(demo.gapSearchRerun.searchRun.acceptedEvidenceResults.length, 2);
assert.equal(demo.gapSearchRerun.refreshedWorkspace.status, "ready_for_counselor_review");
assert.equal(demo.gapSearchRerun.refreshedWorkspace.evidenceGapSearchPlan.status, "no_gaps");
assert.equal(demo.counselorReviewDossier.protocol, "counselor_review_dossier_v1");
assert.equal(demo.counselorReviewDossier.status, "ready_for_counselor_review");
assert.equal(demo.counselorReviewDossier.evidenceTrail.length >= 6, true);
assert.equal(demo.counselorReviewDossier.searchProvenance.runCount, 2);
assert.equal(demo.counselorReviewDossier.searchProvenance.providerIds.includes("demo-search-provider"), true);
assert.equal(demo.counselorReviewDossier.searchProvenance.providerIds.includes("demo-gap-search-provider"), true);
assert.equal(demo.counselorReviewDossier.searchProvenance.queryRows.some((row) => /second independent source/.test(row.query)), true);
assert.equal(demo.counselorReviewDossier.searchProvenance.queryRows.some((row) => row.searchIntent === "counter_evidence"), true);
assert.equal(demo.counselorReviewDossier.searchProvenance.queryRows.some((row) => /admission probability/.test(row.rejectsAsProof.join("\n"))), true);
assert.equal(demo.counselorReviewDossier.evidenceQuality.status, "review_ready");
assert.equal(demo.counselorReviewDossier.evidenceQuality.summary.currentCycleSources >= 6, true);
assert.match(demo.counselorReviewDossier.evidenceQuality.familyPresentationGate, /can be shown/i);
assert.equal(demo.detailedInterpretation.protocol, "detailed_volunteer_plan_interpretation_v1");
assert.equal(demo.detailedInterpretation.status, "ready_for_family_review");
assert.equal(demo.detailedInterpretation.planPosition.rowUse, "candidate_for_counselor_review");
assert.equal(demo.detailedInterpretation.claimRows.some((row) => row.claim === "trend_wording" && row.stance === "hypothesis_only"), true);
assert.equal(demo.detailedInterpretation.claimRows.some((row) => row.claim === "concept_readiness" && row.stance === "can_explain"), true);
assert.equal(demo.detailedInterpretation.claimRows.some((row) => row.counterChecks.some((item) => /counter_evidence/.test(item))), true);
assert.equal(demo.researchStrategy.protocol, "web_evidence_research_strategy_v1");
assert.equal(demo.researchStrategy.status, "ready_to_run");
assert.equal(demo.researchStrategy.researchPillars.some((pillar) => pillar.pillar === "public_opinion_trend"), true);
assert.equal(demo.researchStrategy.priorityQueries.some((row) => row.searchIntent === "counter_evidence" && row.priority === "critical"), true);
assert.match(demo.researchStrategy.minimumEvidenceRules.join("\n"), /Final recommendation remains forbidden/i);
assert.equal(demo.familyClarityRoadmap.protocol, "family_decision_clarity_roadmap_v1");
assert.equal(demo.familyClarityRoadmap.status, "ready_for_row_discussion");
assert.equal(demo.familyClarityRoadmap.rowDiscussionGate.canDiscussRows, true);
assert.equal(demo.familyClarityRoadmap.conceptCards.length, 4);
assert.equal(demo.familyClarityRoadmap.interestAxes.some((axis) => axis.axis === "course_content"), true);
assert.match(demo.familyClarityRoadmap.parentStudentAlignment.hardStops.join("\n"), /final recommendation/i);
assert.equal(demo.hiddenOpportunityAudit.protocol, "hidden_opportunity_audit_v1");
assert.equal(demo.hiddenOpportunityAudit.status, "candidate_for_counselor_review");
assert.equal(demo.hiddenOpportunityAudit.labelPermission, "under_attention_candidate_only");
assert.equal(demo.hiddenOpportunityAudit.score >= 75, true);
assert.equal(demo.hiddenOpportunityAudit.reviewGate.canEnterLedger, true);
assert.equal(demo.hiddenOpportunityAudit.reviewGate.mustStayHypothesisOnly, true);
assert.equal(demo.hiddenOpportunityAudit.scoreBands.some((band) => band.factor === "source_diversity"), true);
assert.match(demo.hiddenOpportunityAudit.forbiddenClaims.join("\n"), /admission guarantee/i);
assert.match(demo.hiddenOpportunityAudit.forbiddenClaims.join("\n"), /final recommendation/i);
assert.equal(demo.planChangeOpportunityLedger.protocol, "plan_change_opportunity_ledger_v1");
assert.equal(demo.planChangeOpportunityLedger.status, "ready");
assert.equal(demo.planChangeOpportunityLedger.hiddenOpportunityGate.status, "candidate_cleared");
assert.equal(demo.planChangeOpportunityLedger.hiddenOpportunityGate.canEnterLedger, true);
assert.equal(demo.planChangeOpportunityLedger.opportunities.length, 1);
assert.equal(demo.planChangeOpportunityLedger.opportunities[0].hiddenOpportunityAudit.status, "candidate_for_counselor_review");
assert.equal(demo.planChangeOpportunityLedger.opportunities[0].hiddenOpportunityAudit.labelPermission, "under_attention_candidate_only");
assert.match(demo.planChangeOpportunityLedger.opportunities[0].auditTrail.join("\n"), /hidden_opportunity_audit=can_enter_ledger/);
assert.equal(demo.volunteerPlanNarrativePackage.protocol, "volunteer_plan_narrative_package_v1");
assert.equal(demo.volunteerPlanNarrativePackage.status, "ready_for_family_delivery");
assert.equal(demo.volunteerPlanNarrativePackage.planRows[0].position, "audited_opportunity_candidate");
assert.equal(demo.volunteerPlanNarrativePackage.planRows[0].evidencePillars.some((pillar) => pillar.claim === "trend_wording"), true);
assert.equal(demo.volunteerPlanNarrativePackage.planRows[0].searchFollowUps.some((item) => /counter-evidence/i.test(item)), true);
assert.equal(demo.volunteerPlanNarrativePackage.planRows[0].interestPrompts.some((item) => /course/i.test(item)), true);
assert.match(demo.volunteerPlanNarrativePackage.forbiddenClaims.join("\n"), /admission guarantee/i);
assert.match(demo.counselorReviewDossier.whatWeCanSay.join("\n"), /official.*quota expansion/i);
assert.match(demo.counselorReviewDossier.whatWeCannotSay.join("\n"), /admission guarantee/i);
assert.match(demo.counselorReviewDossier.counselorReviewChecklist.join("\n"), /worst-case/i);
assert.match(demo.operatorRunbook.join("\n"), /Search official plan rows/);
assert.match(demo.operatorRunbook.join("\n"), /Paste excerpts into capture submissions/);
assert.match(demo.familyExplanationPreview, /Professional group/);
assert.match(demo.familyExplanationPreview, /Adjustment/);
assert.match(demo.claimBoundary, /demo case is not a final recommendation/i);

console.log("Admissions opportunity demo case behavior test passed");

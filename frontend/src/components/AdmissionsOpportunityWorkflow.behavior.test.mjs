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
const workflow = loadTsModule(path.join(libDir, "admissionsOpportunityWorkflow.ts"), {
  "./planChangeDiffEngine": diffEngine,
  "./publicOpinionTrendAnalyzer": trendAnalyzer,
  "./opportunityDiscoveryEngine": discovery,
  "./webEvidencePlanner": planner,
  "./studentInterestClarification": clarification,
});

const completeWorkflow = workflow.buildAdmissionsOpportunityWorkflow({
  priorYear: 2025,
  currentYear: 2026,
  province: "Guangdong",
  officialSource: "Guangdong Education Exam Authority 2026 enrollment plan",
  priorRows: [
    row({ year: 2025, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080901", majorName: "Computer Science", quota: 20 }),
  ],
  currentRows: [
    row({ year: 2026, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080901", majorName: "Computer Science", quota: 36 }),
  ],
  publicOpinionObservations: [
    {
      id: "search-1",
      sourceKind: "search_snippet",
      title: "Parents focus on local schools",
      capturedAt: "2026-06-16",
      text: "Discussion snippets mostly mention local brands and rarely mention South China Tech Computer Science.",
    },
    {
      id: "social-1",
      sourceKind: "social_summary",
      title: "Distance concern thread",
      capturedAt: "2026-06-16",
      text: "Families avoid non-local engineering options because of distance and adjustment concern.",
    },
  ],
  studentProfile: {
    preferredMajors: ["Computer Science", "Software Engineering"],
    blacklistMajors: ["Civil Engineering", "Materials"],
    riskTolerance: "balanced",
    acceptableTradeoffs: ["can_accept_medium_adjustment_risk"],
    careerAssessment: {
      mode: "quick",
      answers: { I1: 5, I2: 5, R1: 4, R2: 4, A1: 2, A2: 2, S1: 2, S2: 2, E1: 3, E2: 3, C1: 3, C2: 3 },
      career_values: ["growth"],
    },
  },
  rankDeltaEstimates: {
    "10561-201-080901-quota_expansion": {
      direction: "easier",
      rankDelta: 1800,
      confidence: "medium",
      explanation: "Quota expands from 20 to 36 seats; demand calibration is still required.",
    },
  },
  externalPlanSources: ["qianwen", "tencent", "teacher", "family"],
});

assert.equal(completeWorkflow.protocol, "admissions_opportunity_workflow_v1");
assert.equal(completeWorkflow.status, "needs_evidence_research");
assert.equal(completeWorkflow.interestBrief.status, "ready_for_plan_discussion");
assert.equal(completeWorkflow.planDiffResult.diffs[0].diffType, "quota_expansion");
assert.equal(completeWorkflow.trendAnalysis.status, "signals_detected");
assert.equal(completeWorkflow.discoveryLedger.insights[0].opportunityKind, "under_attention_opportunity");
assert.equal(completeWorkflow.evidencePlan.status, "needs_research");
assert.equal(completeWorkflow.evidencePlan.tasks.some((task) => task.taskType === "official_plan_verification"), true);
assert.equal(completeWorkflow.evidencePlan.tasks.some((task) => task.taskType === "public_opinion_scan"), true);
assert.match(completeWorkflow.nextAction, /Run evidence research tasks/);
assert.match(completeWorkflow.claimBoundary, /orchestrates/);
assert.equal(completeWorkflow.gateReasons.includes("Evidence research is required before counselor review."), true);

const unclearWorkflow = workflow.buildAdmissionsOpportunityWorkflow({
  priorYear: 2025,
  currentYear: 2026,
  province: "Guangdong",
  officialSource: "Guangdong Education Exam Authority 2026 enrollment plan",
  priorRows: completeWorkflow.inputEcho.priorRows,
  currentRows: completeWorkflow.inputEcho.currentRows,
  publicOpinionObservations: [],
  studentProfile: {
    preferredMajors: [],
    blacklistMajors: [],
    riskTolerance: "unknown",
    acceptableTradeoffs: [],
    careerAssessment: { mode: "skip", answers: {}, career_values: [] },
  },
  externalPlanSources: ["qianwen"],
});

assert.equal(unclearWorkflow.status, "needs_student_clarification");
assert.equal(unclearWorkflow.interestBrief.status, "needs_clarification");
assert.match(unclearWorkflow.nextAction, /Clarify student interest/);
assert.equal(unclearWorkflow.gateReasons.includes("Student interest and tradeoff inputs are incomplete."), true);
assert.equal(unclearWorkflow.evidencePlan.tasks.length, 0);

function row({ year, schoolCode, schoolName, groupCode, majorCode, majorName, quota }) {
  return {
    year,
    officialSource: "Guangdong Education Exam Authority 2026 enrollment plan",
    province: "Guangdong",
    batch: "undergraduate",
    schoolCode,
    schoolName,
    majorGroupCode: groupCode,
    majorCode,
    majorName,
    quota,
    subjectRequirements: ["physics", "chemistry"],
  };
}

console.log("Admissions opportunity workflow behavior test passed");

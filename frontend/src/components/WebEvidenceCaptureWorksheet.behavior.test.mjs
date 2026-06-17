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
const worksheetModule = loadTsModule(path.join(libDir, "webEvidenceCaptureWorksheet.ts"), {
  "./evidenceCollectionWorkspace": workspaceModule,
  "./webEvidenceIntake": intake,
});

const workflow = buildWorkflow();
const initialEvidence = [
  resultForTask(task("official_plan_verification")),
  resultForTask(task("public_opinion_scan")),
];
const workspace = workspaceModule.buildEvidenceCollectionWorkspace({
  workflow,
  evidenceResults: initialEvidence,
  studentName: "Student A",
});
const worksheet = worksheetModule.buildWebEvidenceCaptureWorksheet({ workspace });

assert.equal(worksheet.protocol, "web_evidence_capture_worksheet_v1");
assert.equal(worksheet.status, "ready_to_capture");
assert.equal(worksheet.captureRows.length, workflow.evidencePlan.tasks.length);
assert.equal(worksheet.pendingRows.some((row) => row.taskType === "rank_history_calibration"), true);
assert.equal(worksheet.pendingRows.some((row) => row.taskType === "external_plan_comparison"), true);
assert.match(worksheet.claimBoundary, /capture worksheet/i);

const rankCapture = captureRow("rank_history_calibration");
assert.equal(rankCapture.currentStatus, "needs_capture");
assert.equal(rankCapture.resultTemplate.sourceTier, "historical_data");
assert.deepEqual(rankCapture.resultTemplate.claimedSupports, ["rank_delta"]);
assert.equal(rankCapture.copyableSubmission.taskId, rankCapture.taskId);
assert.equal(rankCapture.copyableSubmission.sourceTier, "historical_data");
assert.deepEqual(rankCapture.copyableSubmission.claimedSupports, ["rank_delta"]);
assert.deepEqual(rankCapture.copyableSubmission.excerpts, []);
assert.equal(rankCapture.operatorChecklist.some((item) => /rank/i.test(item)), true);

const normalized = worksheetModule.normalizeWebEvidenceCaptureSubmissions({
  workspace,
  submissions: [
    {
      taskId: rankCapture.taskId,
      sourceTitle: "Guangdong rank history table",
      sourceUrl: "https://data.example/rank-history",
      excerpts: ["2025 rank 42000; 2024 rank 43800 for the same school group."],
    },
    {
      taskId: captureRow("school_rule_verification").taskId,
      sourceTitle: "Admission charter without excerpt",
      sourceUrl: "https://admission.example/charter",
      excerpts: [],
    },
    {
      taskId: captureRow("public_opinion_scan").taskId,
      sourceTitle: "Forum post overclaiming admission result",
      sourceUrl: "https://example.com/forum",
      excerpts: ["A parent says this row is guaranteed."],
      claimedSupports: ["final_recommendation"],
    },
  ],
  capturedAt: "2026-06-16",
});

assert.equal(normalized.protocol, "web_evidence_capture_normalization_v1");
assert.equal(normalized.evidenceResults.length, 1);
assert.equal(normalized.evidenceResults[0].taskId, rankCapture.taskId);
assert.equal(normalized.evidenceResults[0].sourceTier, "historical_data");
assert.deepEqual(normalized.evidenceResults[0].claimedSupports, ["rank_delta"]);
assert.equal(normalized.rejectedSubmissions.length, 2);
assert.match(normalized.rejectedSubmissions.map((item) => item.reason).join("\n"), /at least one excerpt/);
assert.match(normalized.rejectedSubmissions.map((item) => item.reason).join("\n"), /not allowed/);
assert.match(normalized.claimBoundary, /normalizes operator captures/i);

const updatedWorkspace = workspaceModule.buildEvidenceCollectionWorkspace({
  workflow,
  evidenceResults: [...initialEvidence, ...normalized.evidenceResults],
  studentName: "Student A",
});

assert.equal(updatedWorkspace.taskRows.find((row) => row.taskType === "rank_history_calibration").status, "accepted");
assert.equal(updatedWorkspace.coverageSummary.completedBlockingTasks, 2);
assert.equal(updatedWorkspace.coverageSummary.missingClaims.includes("rank_delta"), false);
assert.equal(updatedWorkspace.coverageSummary.missingClaims.includes("risk_guard"), true);

function captureRow(taskType) {
  const found = worksheet.captureRows.find((candidate) => candidate.taskType === taskType);
  assert.ok(found, `Expected capture row ${taskType}`);
  return found;
}

function task(taskType) {
  const found = workflow.evidencePlan.tasks.find((candidate) => candidate.taskType === taskType);
  assert.ok(found, `Expected ${taskType}`);
  return found;
}

function resultForTask(taskItem) {
  assert.ok(taskItem, "Expected task item");
  const base = {
    taskId: taskItem.id,
    capturedAt: "2026-06-16",
  };
  if (taskItem.taskType === "official_plan_verification") {
    return {
      ...base,
      sourceTitle: "Guangdong official 2026 enrollment plan",
      sourceUrl: "https://eea.gd.gov.cn/2026-plan",
      sourceTier: "official",
      excerpts: ["10561 major group 201 Computer Science quota 36"],
      claimedSupports: ["official_diff"],
    };
  }
  if (taskItem.taskType === "public_opinion_scan") {
    return {
      ...base,
      sourceTitle: "Search summary for non-local engineering attention",
      sourceUrl: "https://search.example/non-local-engineering",
      sourceTier: "public_opinion",
      excerpts: ["Search snippets emphasize local schools and rarely mention the quota expansion."],
      claimedSupports: ["hypothesis_only"],
    };
  }
  throw new Error(`Unexpected fixture task: ${taskItem.taskType}`);
}

function buildWorkflow() {
  return workflowModule.buildAdmissionsOpportunityWorkflow({
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
}

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

console.log("Web evidence capture worksheet behavior test passed");

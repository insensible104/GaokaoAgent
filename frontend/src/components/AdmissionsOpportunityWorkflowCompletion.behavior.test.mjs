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

const workflow = buildWorkflow();
const readyCompletion = completion.completeAdmissionsOpportunityWorkflow({
  workflow,
  evidenceResults: workflow.evidencePlan.tasks.map((task) => resultForTask(task)),
  studentName: "Student A",
});

assert.equal(readyCompletion.protocol, "admissions_opportunity_workflow_completion_v1");
assert.equal(readyCompletion.status, "interpretation_ready");
assert.equal(readyCompletion.intakeResult.status, "review_ready");
assert.equal(readyCompletion.interpretationPackage.status, "counselor_review_ready");
assert.equal(readyCompletion.interpretationPackage.opportunityCards[0].officialEvidence.status, "supported");
assert.equal(readyCompletion.interpretationPackage.opportunityCards[0].publicOpinionEvidence.status, "hypothesis_only");
assert.equal(readyCompletion.interpretationPackage.opportunityCards[0].sourceLinks.length >= 5, true);
assert.match(readyCompletion.nextAction, /Counselor review/);
assert.match(readyCompletion.claimBoundary, /not a final recommendation/i);
assert.doesNotMatch(readyCompletion.interpretationPackage.executiveSummary, /final recommendation/i);

const blockedCompletion = completion.completeAdmissionsOpportunityWorkflow({
  workflow,
  evidenceResults: [
    resultForTask(task("public_opinion_scan")),
    resultForTask(task("family_concept_clarification")),
  ],
  studentName: "Student A",
});

assert.equal(blockedCompletion.status, "blocked");
assert.equal(blockedCompletion.intakeResult.status, "blocked");
assert.equal(blockedCompletion.interpretationPackage.status, "blocked");
assert.match(blockedCompletion.blockedReasons.join("\n"), /official_plan_verification/);
assert.match(blockedCompletion.blockedReasons.join("\n"), /rank_history_calibration/);
assert.match(blockedCompletion.nextAction, /Attach blocking evidence/);
assert.equal(blockedCompletion.interpretationPackage.opportunityCards[0].officialEvidence.status, "missing");
assert.equal(blockedCompletion.interpretationPackage.opportunityCards[0].familyConcepts.status, "explained");

const upstreamBlockedWorkflow = workflowModule.buildAdmissionsOpportunityWorkflow({
  ...baseWorkflowInput(),
  studentProfile: {
    preferredMajors: [],
    blacklistMajors: [],
    riskTolerance: "unknown",
    acceptableTradeoffs: [],
    careerAssessment: { mode: "skip", answers: {}, career_values: [] },
  },
});
const upstreamBlockedCompletion = completion.completeAdmissionsOpportunityWorkflow({
  workflow: upstreamBlockedWorkflow,
  evidenceResults: [],
  studentName: "Student B",
});

assert.equal(upstreamBlockedCompletion.status, "blocked");
assert.equal(upstreamBlockedCompletion.interpretationPackage, null);
assert.match(upstreamBlockedCompletion.blockedReasons.join("\n"), /Student interest/);
assert.match(upstreamBlockedCompletion.nextAction, /Clarify student interest/);

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
  if (taskItem.taskType === "school_rule_verification") {
    return {
      ...base,
      sourceTitle: "South China Tech 2026 admission charter",
      sourceUrl: "https://admission.example/charter-2026",
      sourceTier: "official",
      excerpts: ["Adjustment stays inside eligible majors in the same group."],
      claimedSupports: ["risk_guard"],
    };
  }
  if (taskItem.taskType === "rank_history_calibration") {
    return {
      ...base,
      sourceTitle: "Guangdong historical admission rank table",
      sourceUrl: "https://data.example/rank-history",
      sourceTier: "historical_data",
      excerpts: ["2025 rank 42000; 2024 rank 43800; quota context retained."],
      claimedSupports: ["rank_delta"],
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
  if (taskItem.taskType === "external_plan_comparison") {
    return {
      ...base,
      sourceTitle: "Qianwen and teacher plan comparison",
      sourceUrl: "https://example.com/external-plan-review",
      sourceTier: "competitor_plan",
      excerpts: ["External plans keep the 2025 quota assumption and omit the expansion."],
      claimedSupports: ["competitor_missed"],
    };
  }
  return {
    ...base,
    sourceTitle: "Family concept checklist",
    sourceUrl: "internal://concept-brief",
    sourceTier: "concept",
    excerpts: ["Professional group, adjustment, safe anchor, and interest tradeoff explained."],
    claimedSupports: ["parent_understanding"],
  };
}

function buildWorkflow() {
  return workflowModule.buildAdmissionsOpportunityWorkflow(baseWorkflowInput());
}

function baseWorkflowInput() {
  return {
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
  };
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

console.log("Admissions opportunity workflow completion behavior test passed");

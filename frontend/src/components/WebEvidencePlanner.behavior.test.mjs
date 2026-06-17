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
const discovery = loadTsModule(path.join(libDir, "opportunityDiscoveryEngine.ts"), {
  "./planChangeDiffEngine": diffEngine,
});
const planner = loadTsModule(path.join(libDir, "webEvidencePlanner.ts"), {
  "./opportunityDiscoveryEngine": discovery,
});

const officialSource = "Guangdong Education Exam Authority 2026 enrollment plan";
const diffResult = diffEngine.diffEnrollmentPlans({
  priorYear: 2025,
  currentYear: 2026,
  officialSource,
  priorRows: [
    row({ year: 2025, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080901", majorName: "Computer Science", quota: 20, subjects: ["physics", "chemistry"] }),
  ],
  currentRows: [
    row({ year: 2026, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080901", majorName: "Computer Science", quota: 36, subjects: ["physics", "chemistry"] }),
  ],
});

function row({ year, schoolCode, schoolName, groupCode, majorCode, majorName, quota, subjects }) {
  return {
    year,
    officialSource,
    province: "Guangdong",
    batch: "本科批",
    schoolCode,
    schoolName,
    majorGroupCode: groupCode,
    majorCode,
    majorName,
    quota,
    subjectRequirements: subjects,
  };
}

const discoveryLedger = discovery.buildOpportunityDiscoveryLedger({
  trendSignals: [
    {
      id: "trend-low-attention-tech",
      topic: "low attention to non-local engineering groups",
      sourceKind: "social_summary",
      attention: "low",
      sentiment: "avoidance",
      schoolCode: "10561",
      majorKeywords: ["Computer"],
      evidence: "Search and discussion summaries focus on local brands, not the quota expansion.",
    },
  ],
  planDiffs: diffResult.diffs,
  rankDeltaEstimates: {
    "10561-201-080901-quota_expansion": {
      direction: "easier",
      rankDelta: 1800,
      confidence: "medium",
      explanation: "Quota expands from 20 to 36 seats; demand calibration is still required.",
    },
  },
  studentProfile: {
    preferredMajorKeywords: ["Computer", "Software"],
    blacklistMajorKeywords: ["Civil", "Materials"],
    riskTolerance: "balanced",
    acceptableTradeoffs: ["can_accept_medium_risk"],
  },
});

const evidencePlan = planner.buildWebEvidenceResearchPlan({
  discoveryLedger,
  targetYear: 2026,
  province: "Guangdong",
  externalPlanSources: ["qianwen", "tencent", "teacher", "family"],
});

assert.equal(evidencePlan.protocol, "web_evidence_research_plan_v1");
assert.equal(evidencePlan.status, "needs_research");
assert.match(evidencePlan.claimBoundary, /Search tasks do not prove claims/);
assert.equal(evidencePlan.tasks.length >= 6, true);

assertTask("official_plan_verification", {
  sourceTier: "official",
  canSupport: "official_diff",
  mustBlock: true,
  queryIncludes: ["Guangdong", "2026", "10561", "201"],
});
assertTask("school_rule_verification", {
  sourceTier: "official",
  canSupport: "risk_guard",
  mustBlock: true,
  queryIncludes: ["South China Tech", "admission charter", "adjustment"],
});
assertTask("rank_history_calibration", {
  sourceTier: "historical_data",
  canSupport: "rank_delta",
  mustBlock: true,
  queryIncludes: ["2025", "2024", "Computer Science"],
});
assertTask("public_opinion_scan", {
  sourceTier: "public_opinion",
  canSupport: "hypothesis_only",
  mustBlock: false,
  queryIncludes: ["low attention to non-local engineering groups"],
});
assertTask("external_plan_comparison", {
  sourceTier: "competitor_plan",
  canSupport: "competitor_missed",
  mustBlock: true,
  queryIncludes: ["qianwen", "tencent", "teacher", "family"],
});
assertTask("family_concept_clarification", {
  sourceTier: "concept",
  canSupport: "parent_understanding",
  mustBlock: false,
  queryIncludes: ["professional group", "safe anchor", "adjustment"],
});

const publicOpinionTask = evidencePlan.tasks.find((task) => task.taskType === "public_opinion_scan");
assert.equal(publicOpinionTask.canSupportClaims.includes("official_diff"), false);
assert.equal(publicOpinionTask.canSupportClaims.includes("final_recommendation"), false);
assert.match(publicOpinionTask.claimBoundary, /hypothesis/);

assert.match(evidencePlan.interpretationChecklist.join("\n"), /Do not call this a hidden opportunity until official plan, rank calibration, external omission, and risk guard evidence are all attached/);
assert.match(evidencePlan.interpretationChecklist.join("\n"), /Explain professional group, adjustment, safe-anchor failure, and interest tradeoff before showing final rows/);

function assertTask(taskType, { sourceTier, canSupport, mustBlock, queryIncludes }) {
  const task = evidencePlan.tasks.find((candidate) => candidate.taskType === taskType);
  assert.ok(task, `Expected task ${taskType}`);
  assert.equal(task.sourceTier, sourceTier);
  assert.equal(task.canSupportClaims.includes(canSupport), true);
  assert.equal(task.blocksRecommendationReadiness, mustBlock);
  for (const fragment of queryIncludes) {
    assert.match(task.query, new RegExp(escapeRegExp(fragment), "i"));
  }
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

console.log("Web evidence planner behavior test passed");

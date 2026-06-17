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
const intake = loadTsModule(path.join(libDir, "webEvidenceIntake.ts"), {
  "./webEvidencePlanner": planner,
});

const evidencePlan = buildEvidencePlan();
const fullIntake = intake.evaluateWebEvidenceResults({
  evidencePlan,
  results: evidencePlan.tasks.map((task) => resultForTask(task)),
});

assert.equal(fullIntake.protocol, "web_evidence_intake_v1");
assert.equal(fullIntake.status, "review_ready");
assert.equal(fullIntake.acceptedEvidence.length, evidencePlan.tasks.length);
assert.equal(fullIntake.blockedTasks.length, 0);
assert.equal(fullIntake.claimSupport.official_diff.status, "supported");
assert.equal(fullIntake.claimSupport.rank_delta.status, "supported");
assert.equal(fullIntake.claimSupport.risk_guard.status, "supported");
assert.equal(fullIntake.claimSupport.competitor_missed.status, "supported");
assert.equal(fullIntake.claimSupport.hypothesis_only.status, "supported");
assert.equal(fullIntake.claimSupport.parent_understanding.status, "supported");
assert.equal(fullIntake.claimSupport.final_recommendation.status, "unsupported");
assert.match(fullIntake.claimBoundary, /Evidence intake can make a case review-ready/);

const publicOpinionOnly = intake.evaluateWebEvidenceResults({
  evidencePlan,
  results: [
    {
      taskId: task("public_opinion_scan").id,
      sourceTitle: "Discussion summary about low attention",
      sourceUrl: "https://example.com/discussion-summary",
      sourceTier: "public_opinion",
      capturedAt: "2026-06-16",
      excerpts: ["Families talk about local brands and miss the quota expansion."],
      claimedSupports: ["hypothesis_only", "official_diff", "final_recommendation"],
    },
  ],
});

assert.equal(publicOpinionOnly.status, "blocked");
assert.equal(publicOpinionOnly.claimSupport.hypothesis_only.status, "supported");
assert.equal(publicOpinionOnly.claimSupport.official_diff.status, "unsupported");
assert.equal(publicOpinionOnly.claimSupport.final_recommendation.status, "unsupported");
assert.equal(publicOpinionOnly.rejectedEvidence.length, 2);
assert.match(publicOpinionOnly.rejectedEvidence.map((item) => item.reason).join("\n"), /does not allow public_opinion evidence to support official_diff/);
assert.match(publicOpinionOnly.blockedTasks.join("\n"), /official_plan_verification/);

const wrongTierOfficial = intake.evaluateWebEvidenceResults({
  evidencePlan,
  results: [
    {
      taskId: task("official_plan_verification").id,
      sourceTitle: "Blog repost of a plan table",
      sourceUrl: "https://example.com/blog-plan",
      sourceTier: "public_opinion",
      capturedAt: "2026-06-16",
      excerpts: ["10561 201 Computer Science 36"],
      claimedSupports: ["official_diff"],
    },
  ],
});

assert.equal(wrongTierOfficial.status, "blocked");
assert.equal(wrongTierOfficial.acceptedEvidence.length, 0);
assert.equal(wrongTierOfficial.rejectedEvidence[0].claim, "official_diff");
assert.match(wrongTierOfficial.rejectedEvidence[0].reason, /requires official evidence/);

function task(taskType) {
  const found = evidencePlan.tasks.find((candidate) => candidate.taskType === taskType);
  assert.ok(found, `Expected ${taskType}`);
  return found;
}

function resultForTask(taskItem) {
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
      sourceUrl: "https://admission.scut.example/charter-2026",
      sourceTier: "official",
      excerpts: ["Major assignment follows group rules; adjustment is limited to eligible majors in the group."],
      claimedSupports: ["risk_guard"],
    };
  }
  if (taskItem.taskType === "rank_history_calibration") {
    return {
      ...base,
      sourceTitle: "Guangdong historical admission rank table",
      sourceUrl: "https://data.example.com/rank-history",
      sourceTier: "historical_data",
      excerpts: ["2025 minimum rank 42000; 2024 minimum rank 43800; quota context retained."],
      claimedSupports: ["rank_delta"],
    };
  }
  if (taskItem.taskType === "public_opinion_scan") {
    return {
      ...base,
      sourceTitle: "Search summary for non-local engineering attention",
      sourceUrl: "https://search.example.com/non-local-engineering",
      sourceTier: "public_opinion",
      excerpts: ["Search snippets emphasize local schools and rarely mention South China Tech quota expansion."],
      claimedSupports: ["hypothesis_only", "official_diff"],
    };
  }
  if (taskItem.taskType === "external_plan_comparison") {
    return {
      ...base,
      sourceTitle: "Qianwen and teacher plan comparison",
      sourceUrl: "https://example.com/external-plan-review",
      sourceTier: "competitor_plan",
      excerpts: ["External plans keep the 2025 quota assumption and do not mention the 2026 expansion."],
      claimedSupports: ["competitor_missed"],
    };
  }
  return {
    ...base,
    sourceTitle: "Family concept explanation checklist",
    sourceUrl: "internal://concept-brief",
    sourceTier: "concept",
    excerpts: ["Professional group, adjustment, safe anchor, and interest tradeoff explained before final rows."],
    claimedSupports: ["parent_understanding"],
  };
}

function buildEvidencePlan() {
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

  return planner.buildWebEvidenceResearchPlan({
    discoveryLedger,
    targetYear: 2026,
    province: "Guangdong",
    externalPlanSources: ["qianwen", "tencent", "teacher", "family"],
  });
}

function row({ year, schoolCode, schoolName, groupCode, majorCode, majorName, quota, subjects }) {
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
    subjectRequirements: subjects,
  };
}

console.log("Web evidence intake behavior test passed");

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
const searchBrief = loadTsModule(path.join(libDir, "webEvidenceSearchBrief.ts"), {
  "./webEvidencePlanner": planner,
});

const evidencePlan = buildEvidencePlan();
const brief = searchBrief.buildWebEvidenceSearchBrief({
  evidencePlan,
  locale: "zh-CN",
});

assert.equal(brief.protocol, "web_evidence_search_brief_v1");
assert.equal(brief.status, "ready_to_search");
assert.equal(brief.taskBriefs.length, evidencePlan.tasks.length);
assert.match(brief.claimBoundary, /Search briefs prepare evidence collection/);

const officialBrief = taskBrief("official_plan_verification");
assert.equal(officialBrief.priority, "blocking");
assert.equal(officialBrief.evidenceResultTemplate.sourceTier, "official");
assert.deepEqual(officialBrief.evidenceResultTemplate.claimedSupports, ["official_diff"]);
assert.equal(officialBrief.preferredDomains.includes("eea.gd.gov.cn"), true);
assert.equal(officialBrief.searchQueries.some((query) => query.includes("site:eea.gd.gov.cn")), true);
assert.equal(officialBrief.acceptanceCriteria.some((item) => /row-level/i.test(item)), true);
assert.equal(officialBrief.mustReject.some((item) => /public-opinion/i.test(item)), true);

const publicBrief = taskBrief("public_opinion_scan");
assert.equal(publicBrief.priority, "context");
assert.equal(publicBrief.evidenceResultTemplate.sourceTier, "public_opinion");
assert.deepEqual(publicBrief.evidenceResultTemplate.claimedSupports, ["hypothesis_only"]);
assert.equal(publicBrief.preferredDomains.includes("zhihu.com"), true);
assert.equal(publicBrief.searchQueries.some((query) => query.includes("low attention") || query.includes("avoidance")), true);
assert.match(publicBrief.claimBoundary, /hypothesis/i);

const externalBrief = taskBrief("external_plan_comparison");
assert.equal(externalBrief.priority, "blocking");
assert.equal(externalBrief.acceptanceCriteria.some((item) => /row-level/i.test(item)), true);
assert.equal(externalBrief.mustReject.some((item) => /without row-level matching/i.test(item)), true);

function taskBrief(taskType) {
  const found = brief.taskBriefs.find((candidate) => candidate.taskType === taskType);
  assert.ok(found, `Expected ${taskType}`);
  return found;
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

console.log("Web evidence search brief behavior test passed");

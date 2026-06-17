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

const officialSource = "Guangdong Education Exam Authority 2026 enrollment plan";
const planDiffResult = diffEngine.diffEnrollmentPlans({
  priorYear: 2025,
  currentYear: 2026,
  officialSource,
  priorRows: [
    row({ year: 2025, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080901", majorName: "Computer Science", quota: 20, subjects: ["physics", "chemistry"] }),
    row({ year: 2025, schoolCode: "10561", schoolName: "South China Tech", groupCode: "202", majorCode: "080904", majorName: "Artificial Intelligence", quota: 12, subjects: ["physics", "chemistry"] }),
    row({ year: 2025, schoolCode: "11845", schoolName: "Pearl River Normal", groupCode: "205", majorCode: "050201", majorName: "English", quota: 12, subjects: ["history"] }),
  ],
  currentRows: [
    row({ year: 2026, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080901", majorName: "Computer Science", quota: 36, subjects: ["physics", "chemistry"] }),
    row({ year: 2026, schoolCode: "10561", schoolName: "South China Tech", groupCode: "202", majorCode: "080904", majorName: "Artificial Intelligence", quota: 12, subjects: ["physics", "chemistry", "biology"] }),
    row({ year: 2026, schoolCode: "10561", schoolName: "South China Tech", groupCode: "203", majorCode: "080905", majorName: "Data Science", quota: 10, subjects: ["physics", "chemistry"] }),
    row({ year: 2026, schoolCode: "11845", schoolName: "Pearl River Normal", groupCode: "205", majorCode: "050201", majorName: "English", quota: 12, subjects: ["history"] }),
    row({ year: 2026, schoolCode: "11845", schoolName: "Pearl River Normal", groupCode: "208", majorCode: "050201", majorName: "English", quota: 6, subjects: ["history"] }),
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

const trendOnly = discovery.buildOpportunityDiscoveryLedger({
  trendSignals: [
    {
      id: "trend-low-attention-remote-tech",
      topic: "省外工科组关注不足",
      sourceKind: "search_snippet",
      attention: "low",
      sentiment: "avoidance",
      schoolCode: "10561",
      majorKeywords: ["Computer Science"],
      evidence: "Search snippets focus on local schools and rarely mention the quota expansion.",
    },
  ],
  planDiffs: [],
  studentProfile: {
    preferredMajorKeywords: ["Computer", "Software"],
    blacklistMajorKeywords: ["Civil"],
    riskTolerance: "balanced",
    acceptableTradeoffs: ["can_accept_outprovince", "can_accept_medium_risk"],
  },
});

assert.equal(trendOnly.status, "blocked");
assert.equal(trendOnly.insights.length, 0);
assert.match(trendOnly.blockedClaims.join("\n"), /Trend signals cannot become official opportunity evidence/);

const ledger = discovery.buildOpportunityDiscoveryLedger({
  trendSignals: [
    {
      id: "trend-low-attention-remote-tech",
      topic: "省外工科组关注不足",
      sourceKind: "social_summary",
      attention: "low",
      sentiment: "avoidance",
      schoolCode: "10561",
      majorKeywords: ["Computer", "Software"],
      evidence: "Family discussions over-index local brands and miss the expanded plan.",
    },
    {
      id: "trend-ai-hype",
      topic: "AI 专业热度过高",
      sourceKind: "article_summary",
      attention: "high",
      sentiment: "hype",
      schoolCode: "10561",
      majorKeywords: ["Data Science"],
      evidence: "Articles frame data science as a universal high-salary major.",
    },
  ],
  planDiffs: planDiffResult.diffs,
  rankDeltaEstimates: {
    "10561-201-080901-quota_expansion": {
      direction: "easier",
      rankDelta: 1800,
      confidence: "medium",
      explanation: "Quota expands from 20 to 36 seats; only a directional estimate until historical demand is calibrated.",
    },
  },
  studentProfile: {
    preferredMajorKeywords: ["Computer", "Software"],
    blacklistMajorKeywords: ["Civil", "Materials"],
    riskTolerance: "balanced",
    acceptableTradeoffs: ["can_accept_outprovince", "can_accept_medium_risk"],
  },
});

assert.equal(ledger.protocol, "opportunity_discovery_engine_v1");
assert.equal(ledger.status, "partial");
assert.match(ledger.claimBoundary, /hypotheses/);
assert.equal(ledger.insights.length >= 2, true);

const underAttention = ledger.insights.find((insight) => insight.opportunityKind === "under_attention_opportunity");
assert.ok(underAttention);
assert.equal(underAttention.status, "research_ready");
assert.equal(underAttention.publicOpinionGuard.status, "supports_hypothesis");
assert.equal(underAttention.publicOpinionGuard.opportunitySignal, "under_attention_candidate");
assert.equal(underAttention.officialEvidence.diffType, "quota_expansion");
assert.equal(underAttention.trendHypotheses[0].role, "hypothesis_only");
assert.equal(underAttention.rankImpact.confidence, "medium");
assert.equal(underAttention.studentFit.status, "fit");
assert.deepEqual(underAttention.requiredConcepts, ["professional_group", "adjustment_tradeoff", "safe_anchor_failure", "interest_tradeoff"]);
assert.match(underAttention.parentExplanation.summary, /可能是机会/);
assert.match(underAttention.parentExplanation.concepts.join("\n"), /保底不是只看能不能进组/);
assert.doesNotMatch(underAttention.parentExplanation.summary, /diffType|auditKey|sourceTier/);

const hypeGuard = ledger.insights.find((insight) => insight.opportunityKind === "overheated_attention_guard");
assert.ok(hypeGuard);
assert.equal(hypeGuard.status, "guarded");
assert.equal(hypeGuard.trendHypotheses[0].role, "hypothesis_only");
assert.match(hypeGuard.parentExplanation.summary, /热度/);

const subjectGuard = ledger.insights.find((insight) => insight.officialEvidence.diffType === "subject_requirement_change");
assert.ok(subjectGuard);
assert.equal(subjectGuard.status, "guarded");
assert.match(subjectGuard.parentExplanation.concepts.join("\n"), /选科要求/);

const conflictedLedger = discovery.buildOpportunityDiscoveryLedger({
  trendSignals: [
    {
      id: "trend-low-attention-remote-tech",
      topic: "conflicted low attention",
      sourceKind: "social_summary",
      attention: "low",
      sentiment: "avoidance",
      schoolCode: "10561",
      majorKeywords: ["Computer Science"],
      evidence: "Some snippets rarely mention the group, but mainstream articles dispute the pattern.",
    },
  ],
  trendProfiles: [
    {
      schoolCode: "10561",
      majorKeywords: ["Computer Science"],
      opportunitySignal: "conflicted",
      confidence: "low",
      familySafeSummary: "Counter-evidence exists; do not treat this as a hidden opportunity yet.",
      requiredFollowUps: ["Search for dated counter-evidence before presenting this as a hidden opportunity."],
    },
  ],
  planDiffs: planDiffResult.diffs,
  rankDeltaEstimates: {
    "10561-201-080901-quota_expansion": {
      direction: "easier",
      rankDelta: 1800,
      confidence: "medium",
      explanation: "Quota expands from 20 to 36 seats; only a directional estimate until historical demand is calibrated.",
    },
  },
  studentProfile: {
    preferredMajorKeywords: ["Computer", "Software"],
    blacklistMajorKeywords: ["Civil", "Materials"],
    riskTolerance: "balanced",
    acceptableTradeoffs: ["can_accept_outprovince", "can_accept_medium_risk"],
  },
});

const conflictedComputer = conflictedLedger.insights.find(
  (insight) => insight.officialEvidence.auditKey === "10561-201-080901-quota_expansion",
);
assert.ok(conflictedComputer);
assert.equal(conflictedComputer.opportunityKind, "official_change_guard");
assert.equal(conflictedComputer.status, "guarded");
assert.equal(conflictedComputer.publicOpinionGuard.status, "needs_counterevidence_review");
assert.equal(conflictedComputer.publicOpinionGuard.opportunitySignal, "conflicted");
assert.match(conflictedComputer.publicOpinionGuard.nextActions.join("\n"), /counter-evidence/);
assert.equal(conflictedLedger.insights.some((insight) => insight.id.endsWith("-under-attention")), false);

console.log("Opportunity discovery engine behavior test passed");

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

const ledger = loadTsModule(path.join(libDir, "planChangeOpportunityLedger.ts"));

const weakLedger = ledger.buildPlanChangeOpportunityLedger({
  gameMatrix: {
    major_group_rows: [
      {
        school_name: "Generic U",
        school_code: "10001",
        major_group_code: "101",
        choice_index: 1,
        strategy_tag: "safe",
        plan_change_explanation: {
          status: "rumor",
          ranking_impact: "not_applied",
          official_changes: [
            {
              change_type: "quota_expansion",
              before: 12,
              after: 18,
              evidence: "parent screenshot",
              source_tier: "unverified",
              applied_to_ranking: false,
            },
          ],
          review_items: ["Need official 2026 plan row."],
        },
      },
    ],
    data_vintage: {
      target_year: 2026,
      formal_recommendation_ready: false,
      limitations: ["2026 official plan is missing"],
    },
  },
  externalPlanAuditSummary: null,
});

assert.equal(weakLedger.protocol, "plan_change_opportunity_ledger_v1");
assert.equal(weakLedger.status, "blocked");
assert.equal(weakLedger.score < 50, true);
assert.equal(weakLedger.opportunities.length, 0);
assert.match(weakLedger.blockedClaims.join("\n"), /official 2026 plan diff/);
assert.match(weakLedger.nextAction, /Attach official 2026/);

const strongLedger = ledger.buildPlanChangeOpportunityLedger({
  gameMatrix: {
    major_group_rows: [
      {
        school_name: "South China Tech",
        school_code: "10561",
        major_group_code: "202",
        choice_index: 3,
        strategy_tag: "target",
        admission_prob: 0.68,
        min_rank_pred: 42000,
        major_list: ["Computer Science", "Software Engineering"],
        plan_change_explanation: {
          status: "official_diff",
          ranking_impact: "official_diff_applied",
          official_changes: [
            {
              change_type: "quota_expansion",
              before: 20,
              after: 36,
              evidence: "Guangdong 2026 official plan row 10561-202",
              official_source: "Guangdong Education Exam Authority 2026 enrollment plan",
              source_tier: "official",
              applied_to_ranking: true,
              rank_delta_estimate: {
                direction: "easier",
                rank_delta: 1800,
                explanation: "Quota expands 80%, so comparable cutoff can loosen after demand guard.",
              },
              external_plan_coverage: {
                competitor_missed: true,
                checked_sources: ["qianwen", "teacher"],
                evidence: "External plan kept last year's rank anchor and did not mention quota expansion.",
              },
              recommendation_action: "promote",
              risk_guard: {
                level: "medium",
                checks: ["do not use as safety anchor", "verify group code before final signoff"],
              },
            },
          ],
        },
      },
    ],
    data_vintage: {
      target_year: 2026,
      formal_recommendation_ready: true,
      limitations: [],
    },
  },
  externalPlanAuditSummary: {
    parsedCount: 2,
    matchedCount: 2,
    overlapRate: 1,
    unmatchedEntries: [],
    duplicateEntries: [],
    findings: [],
  },
});

assert.equal(strongLedger.status, "ready");
assert.equal(strongLedger.score >= 85, true);
assert.equal(strongLedger.opportunities.length, 1);

const [opportunity] = strongLedger.opportunities;
assert.equal(opportunity.officialSource, "Guangdong Education Exam Authority 2026 enrollment plan");
assert.equal(opportunity.diffType, "quota_expansion");
assert.deepEqual(opportunity.affectedRows, [
  {
    choiceIndex: 3,
    schoolName: "South China Tech",
    schoolCode: "10561",
    majorGroupCode: "202",
    strategyTag: "target",
  },
]);
assert.equal(opportunity.rankDeltaEstimate.direction, "easier");
assert.equal(opportunity.rankDeltaEstimate.rankDelta, 1800);
assert.equal(opportunity.competitorMissed.status, "missed");
assert.equal(opportunity.recommendationAction, "promote");
assert.equal(opportunity.riskGuard.level, "medium");
assert.match(opportunity.auditTrail.join("\n"), /official_source -> diff_type -> affected_rows -> rank_delta_estimate -> competitor_missed -> recommendation_action -> risk_guard/);
assert.deepEqual(strongLedger.blockedClaims, []);

console.log("Plan change opportunity ledger behavior test passed");

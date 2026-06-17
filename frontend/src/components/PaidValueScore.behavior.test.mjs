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

const paidValue = loadTsModule(path.join(libDir, "paidValueScore.ts"));

const genericMatrix = {
  major_group_rows: [
    {
      school_name: "Generic U",
      major_group_code: "101",
      strategy_tag: "safe",
      major_list: ["Generic major"],
      quant_evidence: [],
      is_blacklist_risk: false,
    },
  ],
  rows: [],
  data_vintage: {
    formal_recommendation_ready: false,
    limitations: ["2026 official plan is missing"],
  },
  volunteer_plan: {
    key_prefix_count: 0,
    shadowed_choice_count: 0,
  },
  plan_audit_summary: {
    coverage: { coverage_sufficient: false, deficits: { safe: 2 } },
    data_boundary: {
      formal_recommendation_ready: false,
      limitations: ["2026 official plan is missing"],
    },
  },
};

const genericScore = paidValue.buildPaidValueScore({
  gameMatrix: genericMatrix,
  externalPlanAuditSummary: null,
  eventReplay: { eventCount: 0, lockReady: false, currentStage: "empty" },
});

assert.equal(genericScore.protocol, "paid_value_score_v1");
assert.equal(genericScore.score < 45, true);
assert.equal(genericScore.dimensions.plan_change_opportunity.status, "blocked");
assert.equal(genericScore.dimensions.executable_volunteer_draft.status, "blocked");
assert.match(genericScore.blockedRevenueClaims.join("\n"), /paid plan-change opportunity/);
assert.match(genericScore.blockedRevenueClaims.join("\n"), /executable volunteer draft/);

const paidMatrix = {
  major_group_rows: [
    {
      school_name: "South China Tech",
      school_code: "10561",
      major_group_code: "202",
      strategy_tag: "target",
      choice_index: 1,
      is_key_prefix: true,
      major_list: ["Computer Science", "Software Engineering"],
      suggested_major_choices: [
        { major_code: "080901", major_name: "Computer Science", is_blacklisted: false, user_utility: 0.92 },
        { major_code: "080902", major_name: "Software Engineering", is_blacklisted: false, user_utility: 0.87 },
      ],
      obey_adjustment_recommendation: true,
      quant_evidence: ["rank evidence", "plan change evidence"],
      tail_assignment_risk: 0.06,
      is_blacklist_risk: false,
      plan_change_explanation: {
        status: "official_diff",
        ranking_impact: "official_diff_applied",
        official_changes: [
          {
            change_type: "quota_expansion",
            before: 20,
            after: 35,
            evidence: "official plan row",
            source_tier: "official",
            applied_to_ranking: true,
          },
        ],
      },
    },
    {
      school_name: "Guangdong Industry",
      school_code: "11845",
      major_group_code: "205",
      strategy_tag: "safe",
      choice_index: 2,
      prefix_role: "safety_anchor",
      major_list: ["Automation", "Instrumentation"],
      suggested_major_choices: [
        { major_code: "080801", major_name: "Automation", is_blacklisted: false, user_utility: 0.78 },
        { major_code: "080301", major_name: "Instrumentation", is_blacklisted: false, user_utility: 0.73 },
      ],
      obey_adjustment_recommendation: true,
      quant_evidence: ["safety evidence", "assignment evidence"],
      tail_assignment_risk: 0.08,
      is_blacklist_risk: false,
    },
  ],
  rows: [],
  data_vintage: {
    formal_recommendation_ready: true,
    limitations: [],
  },
  volunteer_plan: {
    key_prefix_count: 1,
    shadowed_choice_count: 0,
    blacklist_violation_count: 0,
  },
  plan_audit_summary: {
    coverage: { coverage_sufficient: true, deficits: {} },
    data_boundary: {
      formal_recommendation_ready: true,
      limitations: [],
    },
  },
};

const paidScore = paidValue.buildPaidValueScore({
  gameMatrix: paidMatrix,
  externalPlanAuditSummary: {
    parsedCount: 2,
    matchedCount: 2,
    overlapRate: 1,
    unmatchedEntries: [],
    duplicateEntries: [],
    findings: [],
  },
  eventReplay: { eventCount: 3, lockReady: true, currentStage: "locked" },
});

assert.equal(paidScore.score >= 90, true);
assert.equal(paidScore.dimensions.plan_change_opportunity.status, "ready");
assert.equal(paidScore.dimensions.withdrawal_risk_avoidance.status, "ready");
assert.equal(paidScore.dimensions.external_plan_audit.status, "ready");
assert.equal(paidScore.dimensions.executable_volunteer_draft.status, "ready");
assert.equal(paidScore.dimensions.counselor_signoff_boundary.status, "ready");
assert.match(paidScore.payReasons.join("\n"), /official plan-change/);
assert.match(paidScore.payReasons.join("\n"), /executable volunteer draft/);
assert.deepEqual(paidScore.blockedRevenueClaims, []);

console.log("Paid value score behavior test passed");

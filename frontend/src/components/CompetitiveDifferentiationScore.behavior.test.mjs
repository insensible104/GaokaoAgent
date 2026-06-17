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

const benchmark = loadTsModule(path.join(libDir, "competitiveDifferentiationScore.ts"));

const weakMatrix = {
  major_group_rows: [
    {
      school_name: "Weak Evidence U",
      major_group_code: "101",
      strategy_tag: "safe",
      quant_evidence: [],
    },
  ],
  rows: [],
  data_vintage: {
    formal_recommendation_ready: false,
    limitations: ["2026 official admission plan is not ingested"],
  },
  volunteer_plan: {
    key_prefix_count: 0,
    shadowed_choice_count: 0,
  },
  plan_audit_summary: {
    coverage: { coverage_sufficient: false, deficits: { safe: 2 } },
    data_boundary: {
      formal_recommendation_ready: false,
      limitations: ["2026 official admission plan is not ingested"],
    },
  },
};

const weakScore = benchmark.buildCompetitiveDifferentiationScore({
  gameMatrix: weakMatrix,
  userProfile: {
    field_provenance: {},
  },
  externalPlanAuditSummary: null,
  eventReplay: { eventCount: 0, lockReady: false, currentStage: "empty" },
});

assert.equal(weakScore.protocol, "competitive_differentiation_score_v1");
assert.equal(weakScore.score < 60, true);
assert.equal(weakScore.dimensions.plan_change_alpha.status, "blocked");
assert.match(weakScore.blockedClaims.join("\n"), /2026 official plan changes/);
assert.match(weakScore.blockedClaims.join("\n"), /Qianwen|Tencent/);

const strongMatrix = {
  major_group_rows: [
    {
      school_name: "South China Tech",
      major_group_code: "202",
      strategy_tag: "target",
      is_key_prefix: true,
      quant_evidence: ["rank evidence", "plan change evidence"],
      decision_trace: { supporting_factors: [{ code: "fit", label: "fit", value: 0.82 }] },
      plan_change_explanation: {
        status: "official_diff",
        summary: "2026 quota expands and comparable history is adjusted.",
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
      major_group_code: "205",
      strategy_tag: "safe",
      prefix_role: "safety_anchor",
      quant_evidence: ["safety evidence"],
      decision_trace: { supporting_factors: [{ code: "buffer", label: "buffer", value: 0.71 }] },
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
  },
  plan_audit_summary: {
    coverage: { coverage_sufficient: true, deficits: {} },
    data_boundary: {
      formal_recommendation_ready: true,
      limitations: [],
    },
  },
};

const strongScore = benchmark.buildCompetitiveDifferentiationScore({
  gameMatrix: strongMatrix,
  userProfile: {
    field_provenance: {
      preferred_cities: "user_explicit",
      blacklist_majors: "user_explicit",
    },
    riasec_top_codes: ["I", "C"],
    career_values: ["stability"],
    career_assessment_status: "completed",
  },
  externalPlanAuditSummary: {
    parsedCount: 2,
    matchedCount: 2,
    overlapRate: 1,
    unmatchedEntries: [],
    duplicateEntries: [],
    findings: [],
  },
  eventReplay: { eventCount: 2, lockReady: true, currentStage: "locked" },
});

assert.equal(strongScore.score >= 90, true);
assert.equal(strongScore.dimensions.plan_change_alpha.status, "ready");
assert.equal(strongScore.dimensions.external_challenge.score, 15);
assert.match(strongScore.advantageClaims.join("\n"), /auditable/);
assert.match(strongScore.advantageClaims.join("\n"), /plan-change opportunity/);
assert.match(strongScore.benchmarkPositioning.qianwenGap, /report/);
assert.match(strongScore.benchmarkPositioning.tencentGap, /workflow/);

console.log("Competitive differentiation score behavior test passed");

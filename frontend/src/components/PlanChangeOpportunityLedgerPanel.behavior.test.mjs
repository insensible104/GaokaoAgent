import assert from "node:assert/strict";
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const require = createRequire(import.meta.url);
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const here = path.dirname(fileURLToPath(import.meta.url));
const libDir = path.join(here, "..", "lib");

function loadTsModule(filePath, mocks = {}, jsx = ts.JsxEmit.React) {
  const source = fs.readFileSync(filePath, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      jsx,
      esModuleInterop: true,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (mocks[specifier]) return mocks[specifier];
    if (specifier === "react") return React;
    throw new Error(`Unexpected require: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const ledger = loadTsModule(path.join(libDir, "planChangeOpportunityLedger.ts"));
const panel = loadTsModule(path.join(here, "PlanChangeOpportunityLedgerPanel.tsx"), {
  "../lib/planChangeOpportunityLedger": ledger,
});

const gameMatrix = {
  major_group_rows: [
    {
      school_name: "South China Tech",
      school_code: "10561",
      major_group_code: "202",
      choice_index: 3,
      strategy_tag: "target",
      major_list: ["Computer Science"],
      plan_change_explanation: {
        status: "official_diff",
        ranking_impact: "official_diff_applied",
        official_changes: [
          {
            change_type: "quota_expansion",
            before: 20,
            after: 36,
            evidence: "Guangdong 2026 official plan row",
            official_source: "Guangdong Education Exam Authority 2026 enrollment plan",
            source_tier: "official",
            applied_to_ranking: true,
            rank_delta_estimate: {
              direction: "easier",
              rank_delta: 1800,
              explanation: "Quota expands after demand guard.",
            },
            external_plan_coverage: {
              competitor_missed: true,
              checked_sources: ["qianwen"],
              evidence: "External plan did not mention the expansion.",
            },
            recommendation_action: "promote",
            risk_guard: {
              level: "medium",
              checks: ["not a safety anchor"],
            },
          },
        ],
      },
    },
  ],
  rows: [],
  data_vintage: {
    target_year: 2026,
    formal_recommendation_ready: true,
    limitations: [],
  },
};

const markup = renderToStaticMarkup(
  React.createElement(panel.PlanChangeOpportunityLedgerPanel, {
    gameMatrix,
    externalPlanAuditSummary: {
      parsedCount: 1,
      matchedCount: 1,
      overlapRate: 1,
      unmatchedEntries: [],
      duplicateEntries: [],
      findings: [],
    },
  }),
);

assert.match(markup, /data-protocol="plan_change_opportunity_ledger_v1"/);
assert.match(markup, /Plan change opportunity ledger/);
assert.match(markup, /official source/i);
assert.match(markup, /diff type/i);
assert.match(markup, /affected rows/i);
assert.match(markup, /rank delta/i);
assert.match(markup, /competitor missed/i);
assert.match(markup, /recommendation action/i);
assert.match(markup, /risk guard/i);
assert.match(markup, /South China Tech/);
assert.match(markup, /quota_expansion/);

const gameMatrixSource = fs.readFileSync(path.join(here, "GameMatrixView.tsx"), "utf8");
assert.match(gameMatrixSource, /PlanChangeOpportunityLedgerPanel/);
assert.match(gameMatrixSource, /externalPlanAuditSummary=\{externalPlanAuditSummary\}/);

console.log("Plan change opportunity ledger panel behavior test passed");

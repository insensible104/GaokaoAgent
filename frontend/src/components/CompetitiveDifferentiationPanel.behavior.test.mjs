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

const checklist = loadTsModule(path.join(libDir, "counselorDeliveryChecklist.ts"));
const reviewRecord = loadTsModule(path.join(libDir, "deliveryReviewRecord.ts"), {
  "./counselorDeliveryChecklist": checklist,
});
const caseStatus = loadTsModule(path.join(libDir, "deliveryCaseStatus.ts"), {
  "./counselorDeliveryChecklist": checklist,
  "./deliveryReviewRecord": reviewRecord,
});
const eventStore = loadTsModule(path.join(libDir, "deliveryCaseEventStore.ts"), {
  "./deliveryCaseStatus": caseStatus,
});
const benchmark = loadTsModule(path.join(libDir, "competitiveDifferentiationScore.ts"));
const panel = loadTsModule(path.join(here, "CompetitiveDifferentiationPanel.tsx"), {
  "../lib/competitiveDifferentiationScore": benchmark,
  "../lib/deliveryCaseEventStore": eventStore,
  "../lib/deliveryCaseStatus": caseStatus,
});

const gameMatrix = {
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
        ranking_impact: "official_diff_applied",
        official_changes: [
          {
            source_tier: "official",
            applied_to_ranking: true,
            evidence: "official plan row",
          },
        ],
      },
    },
  ],
  rows: [],
  data_vintage: {
    formal_recommendation_ready: false,
    limitations: ["2026 official plan not fully ingested"],
  },
  volunteer_plan: {
    key_prefix_count: 1,
  },
  plan_audit_summary: {
    status: "review",
    coverage: { coverage_sufficient: true, deficits: {} },
    data_boundary: {
      formal_recommendation_ready: false,
      limitations: ["2026 official plan not fully ingested"],
    },
  },
};

const markup = renderToStaticMarkup(
  React.createElement(panel.CompetitiveDifferentiationPanel, {
    gameMatrix,
    userProfile: {
      field_provenance: {
        preferred_cities: "user_explicit",
        blacklist_majors: "user_explicit",
      },
      riasec_top_codes: ["I"],
      career_assessment_status: "completed",
    },
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

assert.match(markup, /data-protocol="competitive_differentiation_score_v1"/);
assert.match(markup, /Competitive benchmark/);
assert.match(markup, /Plan-change alpha/);
assert.match(markup, /Qianwen gap/);
assert.match(markup, /Tencent gap/);
assert.match(markup, /Claims not allowed yet/);
assert.match(markup, /official data boundary/i);

const gameMatrixSource = fs.readFileSync(path.join(here, "GameMatrixView.tsx"), "utf8");
assert.match(gameMatrixSource, /CompetitiveDifferentiationPanel/);
assert.match(gameMatrixSource, /externalPlanAuditSummary=\{externalPlanAuditSummary\}/);

console.log("Competitive differentiation panel behavior test passed");

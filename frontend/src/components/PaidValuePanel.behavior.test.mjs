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

const paidValue = loadTsModule(path.join(libDir, "paidValueScore.ts"));
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
const panel = loadTsModule(path.join(here, "PaidValuePanel.tsx"), {
  "../lib/paidValueScore": paidValue,
  "../lib/deliveryCaseEventStore": eventStore,
  "../lib/deliveryCaseStatus": caseStatus,
});

const markup = renderToStaticMarkup(
  React.createElement(panel.PaidValuePanel, {
    gameMatrix: {
      major_group_rows: [
        {
          school_name: "Generic U",
          major_group_code: "101",
          strategy_tag: "safe",
          major_list: ["Generic major"],
          quant_evidence: [],
        },
      ],
      rows: [],
      data_vintage: {
        formal_recommendation_ready: false,
        limitations: ["2026 official plan is missing"],
      },
      volunteer_plan: {
        key_prefix_count: 0,
      },
      plan_audit_summary: {
        status: "review",
        coverage: { coverage_sufficient: false, deficits: { safe: 2 } },
        data_boundary: {
          formal_recommendation_ready: false,
          limitations: ["2026 official plan is missing"],
        },
      },
    },
    userProfile: null,
    externalPlanAuditSummary: null,
  }),
);

assert.match(markup, /data-protocol="paid_value_score_v1"/);
assert.match(markup, /Paid value score/);
assert.match(markup, /Plan-change opportunity/);
assert.match(markup, /Adjustment and withdrawal risk avoided/);
assert.match(markup, /External plan audit/);
assert.match(markup, /Executable volunteer draft/);
assert.match(markup, /Counselor signoff boundary/);
assert.match(markup, /Revenue claims blocked/);

const gameMatrixSource = fs.readFileSync(path.join(here, "GameMatrixView.tsx"), "utf8");
assert.match(gameMatrixSource, /PaidValuePanel/);
assert.match(gameMatrixSource, /externalPlanAuditSummary=\{externalPlanAuditSummary\}/);

console.log("Paid value panel behavior test passed");

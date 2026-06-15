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
const caseHistory = loadTsModule(path.join(libDir, "deliveryCaseHistory.ts"), {
  "./deliveryCaseStatus": caseStatus,
});
const caseEventStore = loadTsModule(path.join(libDir, "deliveryCaseEventStore.ts"), {
  "./deliveryCaseStatus": caseStatus,
});
const panel = loadTsModule(path.join(here, "DeliveryCaseStatusPanel.tsx"), {
  "../lib/deliveryCaseEventStore": caseEventStore,
  "../lib/deliveryCaseHistory": caseHistory,
  "../lib/deliveryCaseStatus": caseStatus,
});

const gameMatrix = {
  major_group_rows: [
    {
      school_name: "South China Tech",
      major_group_code: "202",
      strategy_tag: "rush",
      is_key_prefix: true,
      quant_evidence: ["rank evidence"],
    },
  ],
  rows: [],
  data_vintage: {
    formal_recommendation_ready: false,
    limitations: ["2026 official admission data is incomplete"],
  },
  volunteer_plan: {
    key_prefix_count: 1,
    shadowed_choice_count: 0,
    blacklist_violation_count: 0,
  },
  plan_audit_summary: {
    status: "review",
    key_prefix: { count: 1 },
    coverage: { coverage_sufficient: true, deficits: {} },
    data_boundary: {
      formal_recommendation_ready: false,
      limitations: ["2026 official admission data is incomplete"],
    },
    student_facing_items: [{ title: "data boundary", severity: "review" }],
  },
};

const externalPlanAuditSummary = {
  protocol: "external_plan_audit_v1",
  metricKeys: {
    overlapRate: "overlap_rate",
    unmatchedEntries: "unmatched_entries",
    strategyMix: "strategy_mix",
  },
  parsedCount: 3,
  matchedCount: 1,
  overlapRate: 1 / 3,
  unmatchedEntries: [{ schoolName: "External U", normalizedKey: "externalu#999" }],
  duplicateEntries: [{ schoolName: "Duplicate U", normalizedKey: "duplicateu#111" }],
  strategyMix: { rush: 1, target: 0, safe: 0, unknown: 2 },
  findings: [{ severity: "review", type: "unmatched_entries", title: "unmatched", detail: "", action: "" }],
  claimBoundary: "External comparison is a review input only.",
};

const status = caseStatus.buildDeliveryCaseStatus({
  caseId: "pf-panel-001",
  gameMatrix,
  userProfile: null,
  externalPlanCompared: true,
  externalPlanAuditSummary,
  reportReady: true,
  signoffState: "locked",
  parentConfirmationState: "confirmed",
  generatedAt: "2026-06-15T10:30:00+08:00",
  updatedAt: "2026-06-15T10:45:00+08:00",
});

assert.equal(status.signoffState, "not_started");
assert.equal(status.parentConfirmationState, "requested");
assert.equal(status.externalAuditSummary.needsReview, true);

const markup = renderToStaticMarkup(
  React.createElement(panel.DeliveryCaseStatusPanel, {
    gameMatrix,
    userProfile: null,
    externalPlanCompared: true,
    externalPlanAuditSummary,
    caseId: "pf-panel-001",
    reviewer: "Lead Counselor",
    signoffState: "locked",
    parentConfirmationState: "confirmed",
    generatedAt: "2026-06-15T10:30:00+08:00",
    updatedAt: "2026-06-15T10:45:00+08:00",
  }),
);

assert.match(markup, /Delivery case status/);
assert.match(markup, /data-protocol="delivery_case_status_v1"/);
assert.match(markup, /not_started/);
assert.match(markup, /requested/);
assert.match(markup, /unmatched 1/);
assert.match(markup, /duplicates 1/);
assert.match(markup, /Review record metrics: blocked/);
assert.match(markup, /delivery_case_history_v1/);
assert.match(markup, /delivery_case_event_replay_v1/);
assert.match(markup, /Lock blocked/);
assert.match(markup, /Claim boundary:/);

const gameMatrixSource = fs.readFileSync(path.join(here, "GameMatrixView.tsx"), "utf8");
assert.match(gameMatrixSource, /DeliveryCaseStatusPanel/);
assert.match(gameMatrixSource, /externalPlanAuditSummary=\{externalPlanAuditSummary\}/);
assert.match(gameMatrixSource, /externalPlanCompared=\{Boolean\(externalPlanAuditSummary\)\}/);

console.log("Delivery case status panel behavior test passed");

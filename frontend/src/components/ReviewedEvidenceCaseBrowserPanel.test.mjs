import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const panelPath = path.join(here, "ReviewedEvidenceCaseBrowserPanel.tsx");
const summaryPath = path.join(here, "..", "lib", "reviewedEvidenceCaseBrowserPanelSummary.ts");

assert.equal(fs.existsSync(panelPath), true, "reviewed evidence case browser panel should exist");
assert.equal(fs.existsSync(summaryPath), true, "reviewed evidence case browser panel summary should exist");

const panelSource = fs.readFileSync(panelPath, "utf8");
const summarySource = fs.readFileSync(summaryPath, "utf8");
const combinedSource = `${panelSource}\n${summarySource}`;
for (const token of [
  "ReviewedEvidenceCaseBrowserPanel",
  "buildReviewedEvidenceCaseBrowser",
  "reviewRequired",
  "missingP0TaskIds",
  "counterEvidenceHit",
  "ready_for_report",
  "needs_capture",
  "sourceId",
  "attachmentCount",
  "redactionStatus",
  "reviewerIdentity",
  "reviewer",
  "reviewAction",
  "case-scoped reviewed evidence",
]) {
  assert.match(combinedSource, new RegExp(token), `panel should include ${token}`);
}

function loadTsxModule(source) {
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      jsx: ts.JsxEmit.ReactJSX,
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
  const module = { exports: {} };
  const require = (id) => {
    if (id === "react/jsx-runtime") {
      return {
        Fragment: "Fragment",
        jsx: (type, props) => ({ type, props }),
        jsxs: (type, props) => ({ type, props }),
      };
    }
    if (id === "../lib/reviewedEvidenceCaseBrowser") {
      return {
        buildReviewedEvidenceCaseBrowser: () => {
          throw new Error("component rendering is not exercised by this smoke test");
        },
      };
    }
    if (id === "../lib/reviewedEvidenceCaseBrowserPanelSummary") {
      return {
        buildReviewedEvidenceCaseBrowserPanelSummary: () => ({
          caseId: "mock",
          tone: "blocked",
          primaryAction: "mock",
          metrics: { captured: 0, readyForReport: 0, pending: 0, missingP0: 0 },
          readyTaskCount: 0,
          needsCaptureTaskCount: 0,
          reviewRequired: true,
          claimBoundary: "mock",
        }),
      };
    }
    throw new Error(`Unexpected import ${id}`);
  };
  new Function("require", "module", "exports", output)(require, module, module.exports);
  return module.exports;
}

const panel = loadTsxModule(panelSource);
assert.equal(typeof panel.ReviewedEvidenceCaseBrowserPanel, "function");

function loadTsModule(source) {
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
  const module = { exports: {} };
  new Function("require", "module", "exports", output)(() => {
    throw new Error("No runtime imports expected");
  }, module, module.exports);
  return module.exports;
}

const summary = loadTsModule(summarySource);
assert.equal(typeof summary.buildReviewedEvidenceCaseBrowserPanelSummary, "function");

const blockedView = {
  caseId: "scut-im-v0",
  capturedCount: 2,
  readyForReportCount: 2,
  pendingCount: 1,
  missingP0TaskIds: ["official-plan-charter"],
  counterEvidenceHit: true,
  reviewRequired: true,
  claimBoundary: "Case-scoped reviewed evidence browser only organizes captured ledger records.",
  taskGroups: [
    { taskId: "employment-market", status: "ready_for_report", records: [{ reviewId: "review-1" }] },
    { taskId: "wechat-public-account", status: "needs_capture", records: [{ reviewId: "review-2" }] },
  ],
};

const blockedSummary = summary.buildReviewedEvidenceCaseBrowserPanelSummary(blockedView);

assert.equal(blockedSummary.caseId, "scut-im-v0");
assert.equal(blockedSummary.tone, "blocked");
assert.equal(blockedSummary.primaryAction, "Review counter-evidence before counselor signoff.");
assert.deepEqual(blockedSummary.metrics, {
  captured: 2,
  readyForReport: 2,
  pending: 1,
  missingP0: 1,
});
assert.equal(blockedSummary.readyTaskCount, 1);
assert.equal(blockedSummary.needsCaptureTaskCount, 1);
assert.match(blockedSummary.claimBoundary, /case-scoped reviewed evidence/i);

const reviewSummary = summary.buildReviewedEvidenceCaseBrowserPanelSummary({
  ...blockedView,
  pendingCount: 1,
  missingP0TaskIds: [],
  counterEvidenceHit: false,
  reviewRequired: true,
});
assert.equal(reviewSummary.tone, "needs_review");
assert.equal(reviewSummary.primaryAction, "Complete pending evidence capture before report use.");

const readySummary = summary.buildReviewedEvidenceCaseBrowserPanelSummary({
  ...blockedView,
  pendingCount: 0,
  missingP0TaskIds: [],
  counterEvidenceHit: false,
  reviewRequired: false,
});
assert.equal(readySummary.tone, "ready");
assert.equal(readySummary.primaryAction, "Evidence package can enter report review.");

console.log("Reviewed evidence case browser panel test passed");

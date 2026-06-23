import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const lib = path.join(here, "..", "lib");
const browserPath = path.join(lib, "reviewedEvidenceCaseBrowser.ts");

assert.equal(fs.existsSync(browserPath), true, "reviewed evidence case browser helper should exist");

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

const browser = loadTsModule(fs.readFileSync(browserPath, "utf8"));
assert.equal(typeof browser.buildReviewedEvidenceCaseBrowser, "function");

const records = [
  reviewedRecord({
    reviewId: "review-live-001",
    caseId: "scut-im-v0",
    taskId: "employment-market",
    claim: "employment_market",
    status: "captured_candidate",
    sourceTitle: "Live job-market sample",
    sourceUrl: "operator-review://review-live-001",
    excerpt: "Robotics integration job sample asks for PLC and data-platform skills.",
    reviewAction: "Use as operator-captured job sample only.",
  }),
  reviewedRecord({
    reviewId: "review-live-002",
    caseId: "scut-im-v0",
    taskId: "counter-evidence",
    claim: "counter_evidence",
    status: "captured_candidate",
    sourceTitle: "Counter evidence note",
    sourceUrl: "operator-review://review-live-002",
    excerpt: "调剂风险提示：专业组内仍需复核黑名单专业。",
    reviewAction: "Escalate before counselor signoff.",
  }),
  reviewedRecord({
    reviewId: "review-live-003",
    caseId: "scut-im-v0",
    taskId: "wechat-public-account",
    claim: "wechat_public_account",
    status: "operator_review",
    sourceTitle: "Incomplete WeChat note",
    sourceUrl: "",
    excerpt: "",
    reviewAction: "Collect visible screenshot before use.",
  }),
  reviewedRecord({
    reviewId: "other-case-001",
    caseId: "other-case",
    taskId: "employment-market",
    claim: "employment_market",
    status: "captured_candidate",
    sourceTitle: "Wrong case record",
    sourceUrl: "operator-review://other-case-001",
    excerpt: "Should not appear.",
    reviewAction: "Ignore.",
  }),
];

const plan = {
  tasks: [
    { id: "official-plan-charter", priority: "P0", claim: "official_admission", title: "Official plan" },
    { id: "employment-market", priority: "P0", claim: "employment_market", title: "Employment market" },
    { id: "counter-evidence", priority: "P0", claim: "counter_evidence", title: "Counter evidence" },
    { id: "wechat-public-account", priority: "P1", claim: "wechat_public_account", title: "WeChat account" },
  ],
};

const view = browser.buildReviewedEvidenceCaseBrowser({
  caseId: "scut-im-v0",
  records,
  plan,
});

assert.equal(view.protocol, "reviewed_evidence_case_browser_v1");
assert.equal(view.caseId, "scut-im-v0");
assert.equal(view.totalRecords, 3, "only requested-case records should be counted");
assert.equal(view.capturedCount, 2);
assert.equal(view.pendingCount, 1);
assert.equal(view.readyForReportCount, 2);
assert.deepEqual(view.missingP0TaskIds, ["official-plan-charter"]);
assert.equal(view.counterEvidenceHit, true);
assert.equal(view.reviewRequired, true);
assert.match(view.claimBoundary, /case-scoped reviewed evidence/i);

const employment = view.taskGroups.find((group) => group.taskId === "employment-market");
assert.equal(employment.status, "ready_for_report");
assert.equal(employment.records[0].reviewId, "review-live-001");
assert.equal(employment.records[0].sourceId, "operator-review://review-live-001");
assert.match(employment.records[0].excerpt, /PLC/);

const wechat = view.taskGroups.find((group) => group.taskId === "wechat-public-account");
assert.equal(wechat.status, "needs_capture");
assert.equal(wechat.records[0].reviewAction, "Collect visible screenshot before use.");

console.log("Reviewed evidence case browser test passed");

function reviewedRecord({
  reviewId,
  caseId,
  taskId,
  claim,
  status,
  sourceTitle,
  sourceUrl,
  excerpt,
  reviewAction,
}) {
  return {
    reviewId,
    targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
    reviewedEvidenceCard: {
      taskId,
      claim,
      status,
      sourceTitle,
      sourceUrl,
      sourceType: taskId === "employment-market" ? "job" : "other",
      excerpt,
      capturedAt: "2026-06-24",
      confidence: status === "captured_candidate" ? "medium" : "low",
      reviewAction,
    },
    reviewer: "operator-a",
    caseId,
    recordedAt: "2026-06-24T00:00:00Z",
    ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
  };
}

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
    attachments: [
      {
        attachmentId: "attachment-job-001",
        kind: "screenshot",
        storageRef: "reviewed-evidence/job-001.png",
        capturedAt: "2026-06-24T00:00:00Z",
        redactionStatus: "redacted",
      },
    ],
    redactionStatus: "redacted",
    reviewerIdentity: {
      reviewerId: "operator-a",
      displayName: "Operator A",
      role: "operator",
    },
    attachmentAudit: { status: "valid", validAttachmentCount: 1, invalidAttachmentCount: 0, findings: [] },
  }),
  reviewedRecord({
    reviewId: "review-live-002",
    caseId: "scut-im-v0",
    taskId: "counter-evidence",
    claim: "counter_evidence",
    status: "captured_candidate",
    sourceTitle: "Counter evidence note",
    sourceUrl: "operator-review://review-live-002",
    excerpt: "Transfer-risk note: the professional group still needs a blacklist-major review.",
    reviewAction: "Escalate before counselor signoff.",
    attachments: [
      {
        attachmentId: "attachment-counter-001",
        kind: "screenshot",
        storageRef: "reviewed-evidence/counter-001.png",
        capturedAt: "2026-06-24T00:00:00Z",
        redactionStatus: "redacted",
      },
    ],
    attachmentAudit: { status: "valid", validAttachmentCount: 1, invalidAttachmentCount: 0, findings: [] },
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
  reviewedRecord({
    reviewId: "review-live-invalid-attachment",
    caseId: "scut-im-v0",
    taskId: "employment-market-invalid",
    claim: "employment_market",
    status: "captured_candidate",
    sourceTitle: "Tampered job-market sample",
    sourceUrl: "operator-review://review-live-invalid-attachment",
    excerpt: "This record has a stale attachment and must not become report-ready.",
    reviewAction: "Re-upload and re-review the attachment before report use.",
    attachmentAudit: {
      status: "invalid",
      validAttachmentCount: 0,
      invalidAttachmentCount: 1,
      findings: [
        {
          attachmentId: "attachment-job-invalid",
          storageRef: "reviewed-evidence/job-invalid.png",
          valid: false,
          detail: "attachment sha256 mismatch: reviewed-evidence/job-invalid.png",
        },
      ],
    },
  }),
  reviewedRecord({
    reviewId: "review-live-unaudited-operator",
    caseId: "scut-im-v0",
    taskId: "operator-unaudited",
    claim: "employment_market",
    status: "captured_candidate",
    sourceTitle: "Operator note without attachment proof",
    sourceUrl: "operator-review://review-live-unaudited-operator",
    excerpt: "This manual note has text but no attachment audit, so it must stay pending.",
    reviewAction: "Attach source proof before report use.",
  }),
];

const plan = {
  tasks: [
    { id: "official-plan-charter", priority: "P0", claim: "official_admission", title: "Official plan" },
    { id: "employment-market", priority: "P0", claim: "employment_market", title: "Employment market" },
    { id: "counter-evidence", priority: "P0", claim: "counter_evidence", title: "Counter evidence" },
    { id: "employment-market-invalid", priority: "P0", claim: "employment_market", title: "Invalid employment market" },
    { id: "operator-unaudited", priority: "P0", claim: "employment_market", title: "Unaudited operator evidence" },
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
assert.equal(view.totalRecords, 5, "only requested-case records should be counted");
assert.equal(view.capturedCount, 2);
assert.equal(view.pendingCount, 3);
assert.equal(view.readyForReportCount, 2);
assert.deepEqual(
  [...view.missingP0TaskIds].sort(),
  ["employment-market-invalid", "official-plan-charter", "operator-unaudited"],
);
assert.equal(view.counterEvidenceHit, true);
assert.equal(view.reviewRequired, true);
assert.match(view.claimBoundary, /case-scoped reviewed evidence/i);

const employment = view.taskGroups.find((group) => group.taskId === "employment-market");
assert.equal(employment.status, "ready_for_report");
assert.equal(employment.records[0].reviewId, "review-live-001");
assert.equal(employment.records[0].sourceId, "operator-review://review-live-001");
assert.equal(employment.records[0].attachmentCount, 1);
assert.equal(employment.records[0].redactionStatus, "redacted");
assert.equal(employment.records[0].reviewerIdentity, "Operator A (operator)");
assert.match(employment.records[0].excerpt, /PLC/);

const wechat = view.taskGroups.find((group) => group.taskId === "wechat-public-account");
assert.equal(wechat.status, "needs_capture");
assert.equal(wechat.records[0].reviewAction, "Collect visible screenshot before use.");

const invalidEmployment = view.taskGroups.find((group) => group.taskId === "employment-market-invalid");
assert.equal(invalidEmployment.status, "needs_capture");
assert.equal(invalidEmployment.records[0].readyForReport, false);
assert.equal(invalidEmployment.records[0].attachmentAuditStatus, "invalid");
assert.match(invalidEmployment.records[0].attachmentAuditDetail, /sha256 mismatch/);

const unauditedOperator = view.taskGroups.find((group) => group.taskId === "operator-unaudited");
assert.equal(unauditedOperator.status, "needs_capture");
assert.equal(unauditedOperator.records[0].readyForReport, false);
assert.equal(unauditedOperator.records[0].attachmentCount, 0);
assert.match(unauditedOperator.records[0].attachmentAuditDetail, /valid attachment audit or public URL/i);

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
  attachments,
  redactionStatus,
  reviewerIdentity,
  attachmentAudit,
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
      attachments,
      redactionStatus,
      reviewerIdentity,
    },
    reviewer: "operator-a",
    caseId,
    recordedAt: "2026-06-24T00:00:00Z",
    ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
    attachmentAudit,
  };
}

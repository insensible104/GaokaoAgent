import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const lib = path.join(here, "..", "lib");
const helperPath = path.join(lib, "operatorEvidenceCaptureWorklist.ts");
const browserPath = path.join(lib, "reviewedEvidenceCaseBrowser.ts");

assert.equal(fs.existsSync(helperPath), true, "operator evidence capture worklist helper should exist");

function loadTsModule(source, requireMap = {}) {
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (requireMap[specifier]) return requireMap[specifier];
    throw new Error(`Unexpected require: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const browser = loadTsModule(fs.readFileSync(browserPath, "utf8"));
const worklist = loadTsModule(fs.readFileSync(helperPath, "utf8"), {
  "./reviewedEvidenceCaseBrowser": browser,
});

assert.equal(typeof worklist.buildOperatorEvidenceCaptureWorklist, "function");
assert.equal(typeof worklist.buildOperatorEvidenceCaptureGate, "function");

const plan = {
  protocol: "deep_evidence_collection_plan_v1",
  targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
  tasks: [
    {
      id: "official-plan-charter",
      claim: "official_admission",
      title: "Official plan",
      priority: "P0",
      outputFields: ["sourceUrl", "excerpt"],
    },
    {
      id: "employment-market",
      claim: "employment_market",
      title: "Employment market",
      priority: "P0",
      outputFields: ["岗位名称", "城市", "学历要求", "技能栈", "原文摘录"],
    },
    {
      id: "wechat-public-account",
      claim: "wechat_public_account",
      title: "WeChat public account",
      priority: "P1",
      outputFields: ["公众号名称", "文章标题", "发布时间", "原文摘录"],
    },
    {
      id: "counter-evidence",
      claim: "counter_evidence",
      title: "Counter evidence",
      priority: "P0",
      outputFields: ["反证类型", "命中证据", "降权动作", "原文摘录"],
    },
  ],
};

const records = [
  reviewedRecord({
    taskId: "counter-evidence",
    claim: "counter_evidence",
    reviewId: "review-counter-ready",
    status: "captured_candidate",
    sourceUrl: "operator-review://review-counter-ready",
    excerpt: "Manual review found no blocking complaint hit.",
    attachmentAudit: { status: "valid", validAttachmentCount: 1, invalidAttachmentCount: 0, findings: [] },
  }),
  reviewedRecord({
    taskId: "employment-market",
    claim: "employment_market",
    reviewId: "review-job-invalid",
    status: "captured_candidate",
    sourceUrl: "operator-review://review-job-invalid",
    excerpt: "Job sample exists but attachment was tampered.",
    attachmentAudit: {
      status: "invalid",
      validAttachmentCount: 0,
      invalidAttachmentCount: 1,
      findings: [
        {
          attachmentId: "att-job-invalid",
          storageRef: "reviewed-evidence/scut-im-v0/att-job-invalid.png",
          valid: false,
          detail: "attachment sha256 mismatch",
        },
      ],
    },
  }),
];

const view = browser.buildReviewedEvidenceCaseBrowser({
  caseId: "scut-im-v0",
  records,
  plan,
});
const result = worklist.buildOperatorEvidenceCaptureWorklist({
  caseId: "scut-im-v0",
  plan,
  records,
});

assert.equal(result.protocol, "operator_evidence_capture_worklist_v1");
assert.equal(result.caseId, "scut-im-v0");
assert.equal(result.targetLabel, "Guangdong 2026 SCUT intelligent manufacturing");
assert.equal(result.totalItems, 2);
assert.equal(result.blockingItemCount, 1);
assert.match(result.claimBoundary, /does not collect evidence/i);
assert.deepEqual(
  result.items.map((item) => item.taskId),
  ["employment-market", "wechat-public-account"],
);

const employment = result.items.find((item) => item.taskId === "employment-market");
assert.equal(employment.priority, "P0");
assert.equal(employment.blocking, true);
assert.equal(employment.captureStatus, "needs_recapture");
assert.equal(employment.workflowFunction, "captureAndSubmitOperatorReviewedEvidence");
assert.equal(employment.redactionChecklistRequired, true);
assert.deepEqual(employment.requiredAttachmentKinds, ["screenshot", "page_capture", "pdf", "image"]);
assert.match(employment.reason, /attachment sha256 mismatch/);
assert.deepEqual(employment.outputFields.slice(0, 2), ["岗位名称", "城市"]);

const wechat = result.items.find((item) => item.taskId === "wechat-public-account");
assert.equal(wechat.priority, "P1");
assert.equal(wechat.blocking, false);
assert.equal(wechat.captureStatus, "missing");
assert.match(wechat.reviewAction, /capture/i);
assert.equal(wechat.redactionChecklistRequired, true);

assert.equal(
  result.items.some((item) => item.taskId === "official-plan-charter"),
  false,
  "official public tasks should not become operator capture work items",
);
assert.equal(
  result.items.some((item) => item.taskId === "counter-evidence"),
  false,
  "ready operator records should not become capture work items",
);
assert.deepEqual(view.missingP0TaskIds.sort(), ["employment-market", "official-plan-charter"]);

const gate = worklist.buildOperatorEvidenceCaptureGate(result);
assert.equal(gate.protocol, "operator_evidence_capture_gate_v1");
assert.equal(gate.status, "blocked");
assert.equal(gate.blocksClientDelivery, true);
assert.equal(gate.blockingItemCount, 1);
assert.match(gate.blockedReason, /employment-market/);
assert.match(gate.claimBoundary, /does not prove admission/i);

const nonBlockingGate = worklist.buildOperatorEvidenceCaptureGate({
  ...result,
  blockingItemCount: 0,
  items: result.items.filter((item) => !item.blocking),
});
assert.equal(nonBlockingGate.status, "needs_capture");
assert.equal(nonBlockingGate.blocksClientDelivery, false);
assert.match(nonBlockingGate.blockedReason, /non-blocking/i);

console.log("Operator evidence capture worklist test passed");

function reviewedRecord({
  taskId,
  claim,
  reviewId,
  status,
  sourceUrl,
  excerpt,
  attachmentAudit,
}) {
  return {
    reviewId,
    targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
    reviewedEvidenceCard: {
      taskId,
      claim,
      status,
      sourceTitle: `Reviewed source for ${taskId}`,
      sourceUrl,
      sourceType: taskId === "employment-market" ? "job" : "discussion",
      excerpt,
      capturedAt: "2026-06-24T00:00:00Z",
      confidence: "medium",
      reviewAction: "Use as operator-captured evidence only.",
      attachments: [
        {
          attachmentId: `att-${taskId}`,
          kind: "screenshot",
          storageRef: `reviewed-evidence/scut-im-v0/att-${taskId}.png`,
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
    },
    reviewer: "operator-a",
    caseId: "scut-im-v0",
    recordedAt: "2026-06-24T00:00:00Z",
    ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
    attachmentAudit,
  };
}

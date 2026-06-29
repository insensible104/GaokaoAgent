import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..", "..", "..");
const lib = path.join(here, "..", "lib");
const fixturePath = path.join(root, "data", "evidence_autopilot", "real_case_v0.json");
const browserPath = path.join(lib, "reviewedEvidenceCaseBrowser.ts");
const auditPacketPath = path.join(lib, "evidenceAutopilotRealCaseAuditPacket.ts");
const reportBriefPath = path.join(lib, "evidenceAutopilotRealCaseReportBrief.ts");
const operatorClosurePath = path.join(lib, "evidenceAutopilotRealCaseOperatorClosure.ts");

assert.equal(fs.existsSync(operatorClosurePath), true, "real case operator closure helper should exist");

function loadTsModule(filePath, requireMap = {}) {
  const output = ts.transpileModule(fs.readFileSync(filePath, "utf8"), {
    compilerOptions: {
      esModuleInterop: true,
      module: ts.ModuleKind.CommonJS,
      resolveJsonModule: true,
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

const browser = loadTsModule(browserPath);
const auditPacket = loadTsModule(auditPacketPath);
const reportBrief = loadTsModule(reportBriefPath);
const operatorClosure = loadTsModule(operatorClosurePath, {
  "./evidenceAutopilotRealCaseLedgerBootstrap": {
    bootstrapRealCaseReviewedEvidenceLedger: async () => {
      throw new Error("bootstrap should not run in build-only test");
    },
  },
  "./operatorEvidenceCaptureRoundtrip": {
    executeOperatorEvidenceCaptureRoundtrip: async () => {
      throw new Error("roundtrip should not run in build-only test");
    },
  },
  "./reviewedEvidenceCaseBrowser": browser,
  "./evidenceAutopilotRealCaseAuditPacket": auditPacket,
  "./evidenceAutopilotRealCaseReportBrief": reportBrief,
});

assert.equal(typeof operatorClosure.buildRealCaseOperatorClosureReview, "function");

const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
const caseId = fixture.caseId;
const plan = {
  protocol: "deep_evidence_collection_plan_v1",
  targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
  tasks: [
    { id: "official-plan-charter", priority: "P0", claim: "official_admission", title: "Official admission" },
    { id: "undergrad-access", priority: "P0", claim: "undergrad_access", title: "Undergraduate access" },
    { id: "employment-market", priority: "P0", claim: "employment_market", title: "Employment market" },
    { id: "counter-evidence", priority: "P0", claim: "counter_evidence", title: "Counter evidence" },
  ],
  reviewGates: [],
  claimBoundary: "test boundary",
};

const publicBootstrap = {
  protocol: "real_case_reviewed_evidence_bootstrap_v1",
  caseId,
  submittedCount: 3,
  recordCount: 3,
  submissions: [],
  listing: {
    success: true,
    caseId,
    recordCount: 3,
    records: [
      publicRecord({
        reviewId: "review-official",
        taskId: "official-plan-charter",
        claim: "official_admission",
        sourceTitle: "SCUT undergraduate admission plan",
        excerpt: "Official plan and charter evidence is ready for counselor review.",
      }),
      publicRecord({
        reviewId: "review-undergrad",
        taskId: "undergrad-access",
        claim: "undergrad_access",
        sourceTitle: "SCUT WUSIE undergraduate platform access",
        excerpt: "Research platforms are open to undergraduates.",
      }),
      publicRecord({
        reviewId: "review-counter",
        taskId: "counter-evidence",
        claim: "counter_evidence",
        sourceTitle: "SCUT adjacent policy risk",
        excerpt: "Cost, campus, or transfer constraints require counselor review.",
      }),
    ],
  },
  browser: { missingP0TaskIds: ["employment-market"] },
  claimBoundary: "public bootstrap boundary",
};

const operatorRoundtrip = {
  protocol: "operator_evidence_capture_roundtrip_v1",
  caseId,
  capture: {},
  submission: { reviewId: "review-job-market" },
  listing: {
    success: true,
    caseId,
    recordCount: 1,
    records: [
      operatorRecord({
        reviewId: "review-job-market",
        sourceTitle: "Public intelligent manufacturing job listing",
        excerpt: "The public listing asks for manufacturing data analysis, Python, and engineering workflow experience.",
      }),
    ],
  },
  worklist: { totalItems: 0 },
  gate: { status: "clear", blocksClientDelivery: false },
  claimBoundary: "operator roundtrip boundary",
};

const result = operatorClosure.buildRealCaseOperatorClosureReview({
  fixture,
  plan,
  publicBootstrap,
  operatorRoundtrip,
});

assert.equal(result.protocol, "real_case_operator_closure_review_v1");
assert.equal(result.caseId, caseId);
assert.equal(result.browser.missingP0TaskIds.length, 0);
assert.equal(result.browser.readyForReportCount, 4);
assert.equal(result.auditPacket.status, "requires_counter_evidence_review");
assert.equal(result.auditPacket.supportedClaims.some((claim) => claim.taskId === "employment-market"), true);
assert.equal(result.auditPacket.blockingGaps.length, 0);
assert.equal(result.reportBrief.status, "requires_counter_evidence_review");
assert.equal(result.reportBrief.familyFacingAllowed, false);
assert.match(result.reportBrief.statusLabel, /反证需要顾问复核/);
assert.match(result.claimBoundary, /does not prove admission probability/i);
assert.match(result.claimBoundary, /does not prove employment outcomes/i);
assert.doesNotMatch(JSON.stringify(result.reportBrief), /推荐报考/);

assert.throws(
  () => operatorClosure.buildRealCaseOperatorClosureReview({
    fixture,
    plan,
    publicBootstrap,
    operatorRoundtrip: { ...operatorRoundtrip, caseId: "other-case" },
  }),
  /caseId/i,
);

console.log("Evidence Autopilot real case operator closure test passed");

function publicRecord({
  reviewId,
  taskId,
  claim,
  sourceTitle,
  excerpt,
}) {
  return {
    reviewId,
    targetLabel: plan.targetLabel,
    caseId,
    reviewer: "real-case-public-fixture",
    recordedAt: "2026-06-24T08:00:00Z",
    ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
    reviewedEvidenceCard: {
      status: "captured_candidate",
      taskId,
      claim,
      sourceTitle,
      sourceUrl: `https://example.edu/${taskId}`,
      sourceType: "official",
      excerpt,
      capturedAt: "2026-06-24",
      confidence: "high",
      reviewAction: "Use as reviewed public evidence only.",
    },
  };
}

function operatorRecord({
  reviewId,
  sourceTitle,
  excerpt,
}) {
  return {
    reviewId,
    targetLabel: plan.targetLabel,
    caseId,
    reviewer: "operator-a",
    recordedAt: "2026-06-24T08:05:00Z",
    ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
    attachmentAudit: {
      status: "valid",
      validAttachmentCount: 1,
      invalidAttachmentCount: 0,
      findings: [],
    },
    reviewedEvidenceCard: {
      status: "captured_candidate",
      taskId: "employment-market",
      claim: "employment_market",
      sourceTitle,
      sourceUrl: "operator-review://review-job-market",
      sourceType: "job",
      excerpt,
      capturedAt: "2026-06-24T08:04:00Z",
      confidence: "medium",
      reviewAction: "Use only as operator-reviewed job-market evidence; verify source freshness before delivery.",
      attachments: [
        {
          attachmentId: "att-job-market",
          kind: "screenshot",
          storageRef: "reviewed-evidence/scut/att-job-market.png",
          capturedAt: "2026-06-24T08:04:00Z",
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
  };
}

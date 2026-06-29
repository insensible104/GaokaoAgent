import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const lib = path.join(here, "..", "lib");
const worklistPath = path.join(lib, "operatorEvidenceCaptureWorklist.ts");
const packetPath = path.join(lib, "operatorEvidenceCapturePacket.ts");

assert.equal(fs.existsSync(packetPath), true, "operator evidence capture packet helper should exist");

function loadTsModule(filePath, requireMap = {}) {
  const output = ts.transpileModule(fs.readFileSync(filePath, "utf8"), {
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

const worklistModule = loadTsModule(worklistPath, {
  "./reviewedEvidenceCaseBrowser": {
    buildReviewedEvidenceCaseBrowser: () => ({
      taskGroups: [
        {
          taskId: "employment-market",
          claim: "employment_market",
          title: "Employment market",
          priority: "P0",
          status: "needs_capture",
          records: [
            {
              attachmentAuditStatus: "invalid",
              attachmentAuditDetail: "attachment sha256 mismatch",
            },
          ],
        },
        {
          taskId: "wechat-public-account",
          claim: "wechat_public_account",
          title: "WeChat public account",
          priority: "P1",
          status: "missing",
          records: [],
        },
      ],
    }),
  },
});
const packetModule = loadTsModule(packetPath, {
  "./operatorEvidenceCaptureWorklist": worklistModule,
});

assert.equal(typeof packetModule.buildOperatorEvidenceCapturePacket, "function");

const worklist = worklistModule.buildOperatorEvidenceCaptureWorklist({
  caseId: "scut-im-v0",
  plan: {
    protocol: "deep_evidence_collection_plan_v1",
    targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
    tasks: [
      {
        id: "employment-market",
        claim: "employment_market",
        title: "Employment market",
        priority: "P0",
        outputFields: ["jobTitle", "city", "educationRequirement", "skills", "excerpt"],
      },
      {
        id: "wechat-public-account",
        claim: "wechat_public_account",
        title: "WeChat public account",
        priority: "P1",
        outputFields: ["accountName", "articleTitle", "publishedAt", "excerpt"],
      },
    ],
    reviewGates: [],
    claimBoundary: "test boundary",
  },
  records: [],
});

const packet = packetModule.buildOperatorEvidenceCapturePacket({ worklist });

assert.equal(packet.protocol, "operator_evidence_capture_packet_v1");
assert.equal(packet.caseId, "scut-im-v0");
assert.equal(packet.status, "blocked");
assert.equal(packet.workflowFunction, "captureAndSubmitOperatorReviewedEvidence");
assert.equal(packet.blockingItemCount, 1);
assert.equal(packet.items.length, 2);
assert.match(packet.claimBoundary, /does not collect evidence/i);
assert.match(packet.operatorRules.join("\n"), /Do not scrape/i);
assert.match(packet.operatorRules.join("\n"), /redaction checklist/i);

const employment = packet.items.find((item) => item.taskId === "employment-market");
assert.equal(employment.sourceType, "job");
assert.equal(employment.captureStatus, "needs_recapture");
assert.equal(employment.submissionTemplate.attachmentPayload.caseId, "scut-im-v0");
assert.equal(employment.submissionTemplate.attachmentPayload.taskId, "employment-market");
assert.equal(employment.submissionTemplate.attachmentPayload.kind, "screenshot");
assert.equal(employment.submissionTemplate.attachmentPayload.redactionStatus, "redacted");
assert.equal(employment.submissionTemplate.card.taskId, "employment-market");
assert.equal(employment.submissionTemplate.card.claim, "employment_market");
assert.equal(employment.submissionTemplate.card.sourceType, "job");
assert.equal(employment.submissionTemplate.card.confidence, "medium");
assert.equal(employment.submissionTemplate.card.reviewerIdentity.role, "operator");
assert.deepEqual(employment.requiredOutputFields.slice(0, 3), ["jobTitle", "city", "educationRequirement"]);
assert.match(employment.captureBrief, /job listing/i);
assert.match(employment.rejectionRules.join("\n"), /private/i);
assert.equal(employment.redactionChecklist.length >= 5, true);

const wechat = packet.items.find((item) => item.taskId === "wechat-public-account");
assert.equal(wechat.sourceType, "wechat");
assert.equal(wechat.blocking, false);
assert.match(wechat.captureBrief, /public account/i);
assert.match(wechat.rejectionRules.join("\n"), /login-only/i);

assert.equal(typeof packetModule.fillOperatorEvidenceCapturePacketItem, "function");

const filledInput = packetModule.fillOperatorEvidenceCapturePacketItem({
  packet,
  item: employment,
  reviewer: {
    reviewerId: "operator-a",
    displayName: "Operator A",
    role: "operator",
  },
  sourceTitle: "Public job listing for intelligent manufacturing engineer",
  excerpt: "The public listing requires manufacturing data analysis, Python, and engineering workflow experience.",
  capturedAt: "2026-06-24T08:00:00Z",
  contentType: "image/png",
  contentBase64: "c2NyZWVuc2hvdA==",
  originalFileName: "job-listing.png",
  redactionChecklist: {
    studentPersonalInfoRemoved: true,
    privateContactInfoRemoved: true,
    accountIdentifiersRemoved: true,
    thirdPartyPersonalInfoRemoved: true,
    reviewerConfirmed: true,
  },
});

assert.equal(filledInput.targetLabel, packet.targetLabel);
assert.equal(filledInput.caseId, packet.caseId);
assert.equal(filledInput.reviewer, "operator-a");
assert.equal(filledInput.attachmentPayload.taskId, "employment-market");
assert.equal(filledInput.attachmentPayload.reviewerId, "operator-a");
assert.equal(filledInput.attachmentPayload.contentBase64, "c2NyZWVuc2hvdA==");
assert.equal(filledInput.attachmentPayload.redactionChecklist.reviewerConfirmed, true);
assert.equal(filledInput.card.taskId, "employment-market");
assert.equal(filledInput.card.sourceTitle, "Public job listing for intelligent manufacturing engineer");
assert.equal(filledInput.card.sourceType, "job");
assert.equal(filledInput.card.excerpt.includes("Python"), true);
assert.equal(filledInput.card.reviewerIdentity.displayName, "Operator A");

assert.throws(
  () => packetModule.fillOperatorEvidenceCapturePacketItem({
    packet,
    item: employment,
    reviewer: { reviewerId: "operator-a", displayName: "Operator A", role: "operator" },
    sourceTitle: "Public job listing",
    excerpt: "",
    capturedAt: "2026-06-24T08:00:00Z",
    contentType: "image/png",
    contentBase64: "c2NyZWVuc2hvdA==",
    redactionChecklist: {
      studentPersonalInfoRemoved: true,
      privateContactInfoRemoved: true,
      accountIdentifiersRemoved: true,
      thirdPartyPersonalInfoRemoved: true,
      reviewerConfirmed: true,
    },
  }),
  /excerpt/i,
);

assert.throws(
  () => packetModule.fillOperatorEvidenceCapturePacketItem({
    packet,
    item: employment,
    reviewer: { reviewerId: "operator-a", displayName: "Operator A", role: "operator" },
    sourceTitle: "Public job listing",
    excerpt: "Valid public excerpt.",
    capturedAt: "2026-06-24T08:00:00Z",
    contentType: "image/png",
    contentBase64: "c2NyZWVuc2hvdA==",
    redactionChecklist: {
      studentPersonalInfoRemoved: true,
      privateContactInfoRemoved: true,
      accountIdentifiersRemoved: true,
      thirdPartyPersonalInfoRemoved: true,
      reviewerConfirmed: false,
    },
  }),
  /redaction checklist/i,
);

console.log("Operator evidence capture packet test passed");

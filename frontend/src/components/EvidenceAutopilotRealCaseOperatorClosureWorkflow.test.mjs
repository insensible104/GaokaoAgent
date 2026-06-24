import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..", "..", "..");
const lib = path.join(here, "..", "lib");
const fixturePath = path.join(root, "data", "evidence_autopilot", "real_case_v0.json");
const apiPath = path.join(lib, "evidenceAutopilotApi.ts");
const browserPath = path.join(lib, "reviewedEvidenceCaseBrowser.ts");
const reviewedAdapterPath = path.join(lib, "evidenceAutopilotRealCaseReviewedEvidence.ts");
const bootstrapPath = path.join(lib, "evidenceAutopilotRealCaseLedgerBootstrap.ts");
const worklistPath = path.join(lib, "operatorEvidenceCaptureWorklist.ts");
const roundtripPath = path.join(lib, "operatorEvidenceCaptureRoundtrip.ts");
const auditPacketPath = path.join(lib, "evidenceAutopilotRealCaseAuditPacket.ts");
const reportBriefPath = path.join(lib, "evidenceAutopilotRealCaseReportBrief.ts");
const operatorClosurePath = path.join(lib, "evidenceAutopilotRealCaseOperatorClosure.ts");

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

const api = loadTsModule(apiPath, {
  "./api": { buildApiUrl: (pathName) => `https://api.test${pathName}` },
  "./evidenceAutopilotSnapshotProvider": {
    buildEvidenceAutopilotSnapshotProviderResults: () => [],
  },
});
const browser = loadTsModule(browserPath);
const reviewedAdapter = loadTsModule(reviewedAdapterPath);
const bootstrap = loadTsModule(bootstrapPath, {
  "./evidenceAutopilotApi": api,
  "./evidenceAutopilotRealCaseReviewedEvidence": reviewedAdapter,
  "./reviewedEvidenceCaseBrowser": browser,
});
const worklist = loadTsModule(worklistPath, {
  "./reviewedEvidenceCaseBrowser": browser,
});
const roundtrip = loadTsModule(roundtripPath, {
  "./evidenceAutopilotApi": api,
  "./operatorEvidenceCaptureWorklist": worklist,
});
const auditPacket = loadTsModule(auditPacketPath);
const reportBrief = loadTsModule(reportBriefPath);
const operatorClosure = loadTsModule(operatorClosurePath, {
  "./evidenceAutopilotRealCaseLedgerBootstrap": bootstrap,
  "./operatorEvidenceCaptureRoundtrip": roundtrip,
  "./reviewedEvidenceCaseBrowser": browser,
  "./evidenceAutopilotRealCaseAuditPacket": auditPacket,
  "./evidenceAutopilotRealCaseReportBrief": reportBrief,
});

assert.equal(typeof operatorClosure.executeRealCaseOperatorClosureWorkflow, "function");

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
const operatorInput = {
  targetLabel: plan.targetLabel,
  caseId,
  reviewer: "operator-a",
  attachmentPayload: {
    caseId,
    taskId: "employment-market",
    reviewerId: "operator-a",
    kind: "screenshot",
    contentType: "image/png",
    contentBase64: "c2NyZWVuc2hvdA==",
    capturedAt: "2026-06-24T08:04:00Z",
    redactionStatus: "redacted",
    redactionChecklist: {
      studentPersonalInfoRemoved: true,
      privateContactInfoRemoved: true,
      accountIdentifiersRemoved: true,
      thirdPartyPersonalInfoRemoved: true,
      reviewerConfirmed: true,
    },
  },
  card: {
    taskId: "employment-market",
    claim: "employment_market",
    sourceTitle: "Public intelligent manufacturing job listing",
    sourceType: "job",
    excerpt: "The public listing asks for manufacturing data analysis, Python, and engineering workflow experience.",
    capturedAt: "2026-06-24T08:04:00Z",
    confidence: "medium",
    reviewAction: "Use only as operator-reviewed job-market evidence; verify source freshness before delivery.",
    redactionStatus: "redacted",
    reviewerIdentity: {
      reviewerId: "operator-a",
      displayName: "Operator A",
      role: "operator",
    },
  },
};

const ledger = [];
const calls = [];
let attachment = null;
const fetchImpl = async (url, init) => {
  calls.push(`${init.method} ${url.replace("https://api.test", "")}`);
  if (url.endsWith("/reviewed-evidence/attachments")) {
    const body = JSON.parse(init.body);
    attachment = {
      attachmentId: "att-job-market",
      kind: body.kind,
      storageRef: "reviewed-evidence/scut/att-job-market.png",
      capturedAt: body.capturedAt,
      redactionStatus: body.redactionStatus,
      redactionChecklist: body.redactionChecklist,
    };
    return jsonResponse({
      success: true,
      attachment,
      byteSize: 10,
      sha256: "a".repeat(64),
      metadataPath: "C:/PathFinder/backend/logs/evidence_autopilot/attachments/reviewed-evidence/scut/att-job-market.png.json",
    });
  }
  if (url.endsWith("/reviewed-evidence") && init.method === "POST") {
    const body = JSON.parse(init.body);
    const reviewId = body.card.taskId === "employment-market"
      ? "review-job-market"
      : `review-public-${ledger.length + 1}`;
    const reviewedEvidenceCard = body.card.taskId === "employment-market"
      ? { ...body.card, sourceUrl: `operator-review://${reviewId}` }
      : body.card;
    ledger.push({
      reviewId,
      targetLabel: body.targetLabel,
      caseId: body.caseId,
      reviewer: body.reviewer,
      recordedAt: "2026-06-24T08:05:00Z",
      ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
      reviewedEvidenceCard,
      attachmentAudit: body.card.taskId === "employment-market"
        ? {
            status: "valid",
            validAttachmentCount: 1,
            invalidAttachmentCount: 0,
            findings: [],
          }
        : undefined,
    });
    return jsonResponse({
      success: true,
      reviewId,
      reviewedEvidenceCard,
      ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
      recordedAt: "2026-06-24T08:05:00Z",
    });
  }
  if (url.endsWith(`/reviewed-evidence/${caseId}`) && init.method === "GET") {
    return jsonResponse({
      success: true,
      caseId,
      recordCount: ledger.length,
      records: ledger,
    });
  }
  throw new Error(`Unexpected fetch ${init.method} ${url}`);
};

const result = await operatorClosure.executeRealCaseOperatorClosureWorkflow({
  fixture,
  caseId,
  plan,
  operatorInput,
  fetchImpl,
});

assert.equal(result.protocol, "real_case_operator_closure_workflow_v1");
assert.equal(result.caseId, caseId);
assert.equal(result.publicBootstrap.protocol, "real_case_reviewed_evidence_bootstrap_v1");
assert.equal(result.operatorRoundtrip.protocol, "operator_evidence_capture_roundtrip_v1");
assert.equal(result.closureReview.protocol, "real_case_operator_closure_review_v1");
assert.equal(result.closureReview.listing.records.length, new Set(result.closureReview.listing.records.map((record) => record.reviewId)).size);
assert.equal(result.closureReview.listing.records.length, ledger.length);
assert.equal(result.closureReview.browser.missingP0TaskIds.length, 0);
assert.equal(result.closureReview.auditPacket.status, "requires_counter_evidence_review");
assert.equal(result.closureReview.reportBrief.familyFacingAllowed, false);
assert.match(result.claimBoundary, /does not prove admission probability/i);
assert.match(result.claimBoundary, /does not prove employment outcomes/i);
assert.deepEqual(
  calls.filter((call) => call.includes("/reviewed-evidence/attachments")),
  ["POST /api/evidence-autopilot/reviewed-evidence/attachments"],
);
assert.equal(calls.filter((call) => call === `GET /api/evidence-autopilot/reviewed-evidence/${caseId}`).length, 2);

await assert.rejects(
  () => operatorClosure.executeRealCaseOperatorClosureWorkflow({
    fixture,
    caseId: "other-case",
    plan,
    operatorInput,
    fetchImpl,
  }),
  /caseId/i,
);

console.log("Evidence Autopilot real case operator closure workflow test passed");

function jsonResponse(payload) {
  return {
    ok: true,
    status: 200,
    async json() {
      return payload;
    },
  };
}

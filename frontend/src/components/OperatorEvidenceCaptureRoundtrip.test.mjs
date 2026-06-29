import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const lib = path.join(here, "..", "lib");
const browserPath = path.join(lib, "reviewedEvidenceCaseBrowser.ts");
const worklistPath = path.join(lib, "operatorEvidenceCaptureWorklist.ts");
const packetPath = path.join(lib, "operatorEvidenceCapturePacket.ts");
const apiPath = path.join(lib, "evidenceAutopilotApi.ts");
const roundtripPath = path.join(lib, "operatorEvidenceCaptureRoundtrip.ts");

assert.equal(fs.existsSync(roundtripPath), true, "operator evidence capture roundtrip helper should exist");

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

const browser = loadTsModule(browserPath);
const worklist = loadTsModule(worklistPath, {
  "./reviewedEvidenceCaseBrowser": browser,
});
const packetModule = loadTsModule(packetPath, {
  "./operatorEvidenceCaptureWorklist": worklist,
});
const api = loadTsModule(apiPath, {
  "./api": { buildApiUrl: (pathName) => `https://api.test${pathName}` },
  "./evidenceAutopilotSnapshotProvider": {
    buildEvidenceAutopilotSnapshotProviderResults: () => [],
  },
});
const roundtrip = loadTsModule(roundtripPath, {
  "./evidenceAutopilotApi": api,
  "./operatorEvidenceCaptureWorklist": worklist,
});

assert.equal(typeof roundtrip.executeOperatorEvidenceCaptureRoundtrip, "function");

const plan = {
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
  ],
  reviewGates: [],
  claimBoundary: "test boundary",
};

const initialWorklist = worklist.buildOperatorEvidenceCaptureWorklist({
  caseId: "scut-im-v0",
  plan,
  records: [],
});
const initialGate = worklist.buildOperatorEvidenceCaptureGate(initialWorklist);
assert.equal(initialGate.blocksClientDelivery, true);

const packet = packetModule.buildOperatorEvidenceCapturePacket({ worklist: initialWorklist });
const item = packet.items[0];
const input = packetModule.fillOperatorEvidenceCapturePacketItem({
  packet,
  item,
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

const calls = [];
let submittedCard = null;
const fetchImpl = async (url, init) => {
  calls.push({ url, method: init.method });
  if (url.endsWith("/reviewed-evidence/attachments")) {
    const body = JSON.parse(init.body);
    assert.equal(body.taskId, "employment-market");
    assert.equal(body.redactionChecklist.reviewerConfirmed, true);
    return jsonResponse({
      success: true,
      attachment: {
        attachmentId: "att-job-001",
        kind: "screenshot",
        storageRef: "reviewed-evidence/scut-im-v0/att-job-001.png",
        capturedAt: body.capturedAt,
        redactionStatus: "redacted",
        redactionChecklist: body.redactionChecklist,
      },
      byteSize: 10,
      sha256: "a".repeat(64),
      metadataPath: "C:/PathFinder/backend/logs/evidence_autopilot/attachments/reviewed-evidence/scut-im-v0/att-job-001.png.json",
    });
  }
  if (url.endsWith("/reviewed-evidence") && init.method === "POST") {
    const body = JSON.parse(init.body);
    submittedCard = {
      ...body.card,
      sourceUrl: "operator-review://review-job-001",
    };
    return jsonResponse({
      success: true,
      reviewId: "review-job-001",
      reviewedEvidenceCard: submittedCard,
      ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
      recordedAt: "2026-06-24T08:01:00Z",
    });
  }
  if (url.endsWith("/reviewed-evidence/scut-im-v0") && init.method === "GET") {
    return jsonResponse({
      success: true,
      caseId: "scut-im-v0",
      recordCount: 1,
      records: [
        {
          reviewId: "review-job-001",
          targetLabel: plan.targetLabel,
          reviewedEvidenceCard: submittedCard,
          reviewer: "operator-a",
          caseId: "scut-im-v0",
          recordedAt: "2026-06-24T08:01:00Z",
          ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
          attachmentAudit: {
            status: "valid",
            validAttachmentCount: 1,
            invalidAttachmentCount: 0,
            findings: [],
          },
        },
      ],
    });
  }
  throw new Error(`Unexpected fetch ${init.method} ${url}`);
};

const result = await roundtrip.executeOperatorEvidenceCaptureRoundtrip({
  plan,
  input,
  fetchImpl,
});

assert.equal(result.protocol, "operator_evidence_capture_roundtrip_v1");
assert.equal(result.caseId, "scut-im-v0");
assert.equal(result.submission.reviewId, "review-job-001");
assert.equal(result.listing.recordCount, 1);
assert.equal(result.worklist.totalItems, 0);
assert.equal(result.gate.status, "clear");
assert.equal(result.gate.blocksClientDelivery, false);
assert.match(result.claimBoundary, /does not prove admission/i);
assert.deepEqual(
  calls.map((call) => `${call.method} ${call.url.replace("https://api.test", "")}`),
  [
    "POST /api/evidence-autopilot/reviewed-evidence/attachments",
    "POST /api/evidence-autopilot/reviewed-evidence",
    "GET /api/evidence-autopilot/reviewed-evidence/scut-im-v0",
  ],
);

await assert.rejects(
  () => roundtrip.executeOperatorEvidenceCaptureRoundtrip({
    plan,
    input: { ...input, caseId: undefined },
    fetchImpl,
  }),
  /caseId/i,
);

console.log("Operator evidence capture roundtrip test passed");

function jsonResponse(payload) {
  return {
    ok: true,
    status: 200,
    async json() {
      return payload;
    },
  };
}

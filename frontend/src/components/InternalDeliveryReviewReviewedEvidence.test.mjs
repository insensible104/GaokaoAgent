import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..");
const componentPath = path.join(here, "InternalDeliveryReview.tsx");
const helperPath = path.join(root, "lib", "deliveryReviewedEvidencePlan.ts");
const worklistPath = path.join(root, "lib", "operatorEvidenceCaptureWorklist.ts");
const packetPath = path.join(root, "lib", "operatorEvidenceCapturePacket.ts");
const roundtripPath = path.join(root, "lib", "operatorEvidenceCaptureRoundtrip.ts");

assert.equal(fs.existsSync(componentPath), true, "InternalDeliveryReview should exist");
assert.equal(fs.existsSync(helperPath), true, "delivery reviewed evidence plan helper should exist");
assert.equal(fs.existsSync(worklistPath), true, "operator evidence capture worklist helper should exist");
assert.equal(fs.existsSync(packetPath), true, "operator evidence capture packet helper should exist");
assert.equal(fs.existsSync(roundtripPath), true, "operator evidence capture roundtrip helper should exist");

const source = fs.readFileSync(componentPath, "utf8");
for (const token of [
  "ReviewedEvidenceCaseBrowserPanel",
  "fetchReviewedEvidenceRecords",
  "buildDeliveryReviewedEvidencePlan",
  "buildOperatorEvidenceCaptureWorklist",
  "buildOperatorEvidenceCaptureGate",
  "buildOperatorEvidenceCapturePacket",
  "captureAndSubmitOperatorReviewedEvidence",
  "operatorCaptureGate",
  "operatorCapturePacket",
  "blocksClientDelivery",
  "reviewedEvidenceRecords",
  "reviewedEvidenceError",
  "case-scoped reviewed evidence",
  "operator-review ledger unavailable",
]) {
  assert.match(source, new RegExp(token), `InternalDeliveryReview should wire ${token}`);
}

const helper = loadTsModule(fs.readFileSync(helperPath, "utf8"), {
  "./deepEvidenceCollectionPlan": {
    buildDeepEvidenceCollectionPlan: (context) => ({
      protocol: "deep_evidence_collection_plan_v1",
      targetLabel: `${context.province} ${context.targetYear} ${context.schoolName} ${context.majorName}`,
      tasks: [{ id: "official-plan-charter", priority: "P0" }],
      reviewGates: [],
      claimBoundary: "test boundary",
    }),
  },
});
const worklist = loadTsModule(fs.readFileSync(worklistPath, "utf8"), {
  "./reviewedEvidenceCaseBrowser": {
    buildReviewedEvidenceCaseBrowser: () => ({
      taskGroups: [
        {
          taskId: "employment-market",
          claim: "employment_market",
          title: "Employment market",
          priority: "P0",
          status: "missing",
          records: [],
        },
      ],
    }),
  },
});
const packet = loadTsModule(fs.readFileSync(packetPath, "utf8"), {
  "./operatorEvidenceCaptureWorklist": worklist,
  "./evidenceAutopilotApi": {},
  "./evidenceAutopilotProvider": {},
});
const roundtrip = loadTsModule(fs.readFileSync(roundtripPath, "utf8"), {
  "./evidenceAutopilotApi": {
    captureAndSubmitOperatorReviewedEvidence: async () => ({}),
    fetchReviewedEvidenceRecords: async () => ({ records: [] }),
  },
  "./operatorEvidenceCaptureWorklist": worklist,
});

assert.equal(typeof helper.buildDeliveryReviewedEvidencePlan, "function");
assert.equal(typeof worklist.buildOperatorEvidenceCaptureWorklist, "function");
assert.equal(typeof worklist.buildOperatorEvidenceCaptureGate, "function");
assert.equal(typeof packet.buildOperatorEvidenceCapturePacket, "function");
assert.equal(typeof packet.fillOperatorEvidenceCapturePacketItem, "function");
assert.equal(typeof roundtrip.executeOperatorEvidenceCaptureRoundtrip, "function");

const plan = helper.buildDeliveryReviewedEvidencePlan({
  profile: {
    score: 621,
    rank: 15000,
    subject_group: "physics",
    preferred_majors: ["智能制造"],
  },
  gameMatrix: {
    volunteer_plan: {
      province: "Guangdong",
      year: 2026,
      choices: [
        {
          school_name: "South China University of Technology",
          major_choices: [{ major_name: "Intelligent Manufacturing" }],
        },
      ],
    },
  },
});

assert.equal(plan.protocol, "deep_evidence_collection_plan_v1");
assert.match(plan.targetLabel, /Guangdong 2026 South China University of Technology Intelligent Manufacturing/);

const fallbackPlan = helper.buildDeliveryReviewedEvidencePlan({
  profile: {
    score: 621,
    subject_group: "physics",
    preferred_majors: ["数据工程"],
  },
  gameMatrix: null,
});

assert.match(fallbackPlan.targetLabel, /Guangdong 2026 delivery case target 数据工程/);

const captureWorklist = worklist.buildOperatorEvidenceCaptureWorklist({
  caseId: "delivery-case-001",
  plan: {
    protocol: "deep_evidence_collection_plan_v1",
    targetLabel: "Delivery target",
    tasks: [
      {
        id: "employment-market",
        claim: "employment_market",
        title: "Employment market",
        priority: "P0",
        outputFields: ["岗位名称", "城市"],
      },
    ],
    reviewGates: [],
    claimBoundary: "test boundary",
  },
  records: [],
});

assert.equal(captureWorklist.blockingItemCount, 1);
assert.equal(captureWorklist.items[0].workflowFunction, "captureAndSubmitOperatorReviewedEvidence");

const captureGate = worklist.buildOperatorEvidenceCaptureGate(captureWorklist);
assert.equal(captureGate.blocksClientDelivery, true);

const capturePacket = packet.buildOperatorEvidenceCapturePacket({ worklist: captureWorklist });
assert.equal(capturePacket.workflowFunction, "captureAndSubmitOperatorReviewedEvidence");
assert.equal(capturePacket.items[0].submissionTemplate.attachmentPayload.taskId, "employment-market");
assert.match(fs.readFileSync(packetPath, "utf8"), /fillOperatorEvidenceCapturePacketItem/);

console.log("Internal delivery reviewed evidence wiring test passed");

function loadTsModule(source, requires = {}) {
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
  const module = { exports: {} };
  const require = (id) => {
    if (requires[id]) return requires[id];
    throw new Error(`Unexpected import ${id}`);
  };
  new Function("require", "module", "exports", output)(require, module, module.exports);
  return module.exports;
}

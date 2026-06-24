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
const worklistPath = path.join(lib, "operatorEvidenceCaptureWorklist.ts");
const packetPath = path.join(lib, "operatorEvidenceCapturePacket.ts");
const handoffPath = path.join(lib, "evidenceAutopilotRealCaseReviewerHandoff.ts");

assert.equal(fs.existsSync(handoffPath), true, "real case reviewer handoff helper should exist");

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
const worklist = loadTsModule(worklistPath, {
  "./reviewedEvidenceCaseBrowser": browser,
});
const packet = loadTsModule(packetPath, {
  "./operatorEvidenceCaptureWorklist": worklist,
});
const handoffModule = loadTsModule(handoffPath, {
  "./operatorEvidenceCaptureWorklist": worklist,
  "./operatorEvidenceCapturePacket": packet,
});

assert.equal(typeof handoffModule.buildRealCaseReviewerHandoff, "function");

const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
const caseId = fixture.caseId;
const plan = {
  protocol: "deep_evidence_collection_plan_v1",
  targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
  tasks: [
    {
      id: "official-plan-charter",
      priority: "P0",
      claim: "official_admission",
      title: "Official admission",
      outputFields: ["sourceTitle", "excerpt"],
    },
    {
      id: "undergrad-access",
      priority: "P0",
      claim: "undergrad_access",
      title: "Undergraduate access",
      outputFields: ["sourceTitle", "excerpt"],
    },
    {
      id: "employment-market",
      priority: "P0",
      claim: "employment_market",
      title: "Employment market",
      outputFields: ["jobTitle", "city", "educationRequirement", "skills", "excerpt"],
    },
    {
      id: "counter-evidence",
      priority: "P0",
      claim: "counter_evidence",
      title: "Counter evidence",
      outputFields: ["sourceTitle", "risk", "excerpt"],
    },
  ],
  reviewGates: [],
  claimBoundary: "test boundary",
};

const records = [
  publicRecord({
    reviewId: "review-official",
    taskId: "official-plan-charter",
    claim: "official_admission",
    sourceTitle: "SCUT undergraduate admission plan",
  }),
  publicRecord({
    reviewId: "review-undergrad",
    taskId: "undergrad-access",
    claim: "undergrad_access",
    sourceTitle: "SCUT WUSIE undergraduate platform access",
  }),
  publicRecord({
    reviewId: "review-counter",
    taskId: "counter-evidence",
    claim: "counter_evidence",
    sourceTitle: "SCUT adjacent policy risk",
  }),
];

const handoff = handoffModule.buildRealCaseReviewerHandoff({
  fixture,
  caseId,
  plan,
  records,
});

assert.equal(handoff.protocol, "real_case_reviewer_handoff_v1");
assert.equal(handoff.caseId, caseId);
assert.equal(handoff.familyFacingAllowed, false);
assert.equal(handoff.status, "blocked_by_operator_capture");
assert.deepEqual(handoff.openTaskIds, ["employment-market"]);
assert.equal(handoff.capturePacket.protocol, "operator_evidence_capture_packet_v1");
assert.equal(handoff.capturePacket.items.length, 1);
assert.equal(handoff.capturePacket.items[0].taskId, "employment-market");
assert.equal(handoff.capturePacket.items[0].submissionTemplate.card.sourceType, "job");
assert.deepEqual(handoff.capturePacket.items[0].requiredOutputFields.slice(0, 4), [
  "jobTitle",
  "city",
  "educationRequirement",
  "skills",
]);
assert.equal(handoff.execution.workflowFunction, "executeRealCaseOperatorClosureWorkflow");
assert.equal(handoff.execution.inputContract, "OperatorReviewedEvidenceCaptureInput");
assert.equal(handoff.execution.expectedStatusAfterValidCapture, "requires_counter_evidence_review");
assert.match(handoff.execution.notes.join("\n"), /reviewId/);
assert.match(handoff.reviewerChecklist.join("\n"), /redaction checklist/i);
assert.match(handoff.reviewerChecklist.join("\n"), /source freshness/i);
assert.match(handoff.claimBoundary, /does not prove admission probability/i);
assert.match(handoff.claimBoundary, /does not prove employment outcomes/i);
assert.doesNotMatch(JSON.stringify(handoff), /推荐报考|保证录取|保证就业/);

assert.throws(
  () => handoffModule.buildRealCaseReviewerHandoff({
    fixture,
    caseId: "other-case",
    plan,
    records,
  }),
  /caseId/i,
);

console.log("Evidence Autopilot real case reviewer handoff test passed");

function publicRecord({
  reviewId,
  taskId,
  claim,
  sourceTitle,
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
      excerpt: "Reviewed public evidence excerpt.",
      capturedAt: "2026-06-24",
      confidence: "high",
      reviewAction: "Use as reviewed public evidence only.",
    },
  };
}

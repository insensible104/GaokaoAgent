import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..", "..", "..");
const lib = path.join(here, "..", "lib");
const fixturePath = path.join(root, "data", "evidence_autopilot", "real_case_v0.json");
const providerPath = path.join(lib, "evidenceAutopilotRealCaseProvider.ts");
const reviewedPath = path.join(lib, "evidenceAutopilotRealCaseReviewedEvidence.ts");

assert.equal(fs.existsSync(reviewedPath), true, "real case reviewed-evidence adapter should exist");

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

const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
const provider = loadTsModule(providerPath, {
  "../../../data/evidence_autopilot/real_case_v0.json": fixture,
});
const reviewed = loadTsModule(reviewedPath, {
  "./evidenceAutopilotRealCaseProvider": provider,
  "./evidenceAutopilotApi": {},
  "./evidenceAutopilotProvider": {},
});

assert.equal(typeof reviewed.buildRealCaseReviewedEvidenceSubmissions, "function");

const submissions = reviewed.buildRealCaseReviewedEvidenceSubmissions({
  fixture: provider.loadEvidenceAutopilotRealCaseFixture(),
  caseId: "scut-im-v0",
});

assert.equal(submissions.length >= 5, true);
assert.equal(submissions.every((submission) => submission.caseId === "scut-im-v0"), true);
assert.equal(submissions.every((submission) => submission.reviewer === "real-case-v0-source-log"), true);
assert.equal(submissions.every((submission) => submission.targetLabel.includes("South China University of Technology")), true);

const undergradAccess = submissions.find((submission) => submission.card.taskId === "undergrad-access");
assert.ok(undergradAccess, "undergrad-access should be converted from the real case fixture");
assert.equal(undergradAccess.card.claim, "undergrad_access");
assert.equal(undergradAccess.card.status, "captured_candidate");
assert.match(undergradAccess.card.sourceUrl, /^https?:\/\//);
assert.equal(undergradAccess.card.sourceType, "school");
assert.match(undergradAccess.card.excerpt, /undergraduate/i);
assert.deepEqual(undergradAccess.card.attachments, []);
assert.equal(undergradAccess.card.redactionStatus, "not_required");

const counterEvidence = submissions.find((submission) => submission.card.taskId === "counter-evidence");
assert.ok(counterEvidence, "counter-evidence should be converted from the real case fixture");
assert.equal(counterEvidence.card.claim, "counter_evidence");
assert.match(counterEvidence.card.reviewAction, /Flag cost/i);

const officialPlan = submissions.filter((submission) => submission.card.taskId === "official-plan-charter");
assert.equal(officialPlan.length, 2, "both official-plan-charter cards should be preserved");
assert.equal(officialPlan.every((submission) => submission.card.claim === "official_admission"), true);

const filtered = reviewed.buildRealCaseReviewedEvidenceSubmissions({
  fixture: {
    ...fixture,
    evidenceCards: [
      ...fixture.evidenceCards,
      {
        taskId: "employment-market",
        claim: "Incomplete job note",
        status: "operator_review",
        sourceTitle: "",
        sourceUrl: "",
        sourceType: "job",
        excerpt: "",
        capturedAt: "",
        confidence: "low",
        reviewAction: "Do not use.",
      },
    ],
  },
  caseId: "scut-im-v0",
});
assert.equal(filtered.some((submission) => submission.card.taskId === "employment-market"), false);

assert.throws(
  () => reviewed.buildRealCaseReviewedEvidenceSubmissions({
    fixture,
    caseId: "",
  }),
  /caseId/i,
);

console.log("Evidence Autopilot real case reviewed evidence test passed");

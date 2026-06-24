import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const lib = path.join(here, "..", "lib");
const decisionPath = path.join(lib, "evidenceAutopilotRealCaseCounselorReviewDecision.ts");

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

const decision = loadTsModule(decisionPath);

assert.equal(typeof decision.buildRealCaseCounselorReviewDecision, "function");

const closurePreview = {
  protocol: "real_case_operator_closure_delivery_preview_v1",
  caseId: "scut-intelligent-manufacturing-real-case-v0",
  workflow: {
    protocol: "real_case_operator_closure_workflow_v1",
    caseId: "scut-intelligent-manufacturing-real-case-v0",
    closureReview: {
      auditPacket: {
        protocol: "real_case_opportunity_audit_packet_v1",
        caseId: "scut-intelligent-manufacturing-real-case-v0",
        status: "requires_counter_evidence_review",
        missingP0TaskIds: [],
        counterEvidence: {
          requiresCounselorReview: true,
          records: [
            {
              taskId: "counter-evidence",
              sourceTitle: "Counter evidence source",
              sourceId: "https://example.edu/risk",
              excerpt: "The source flags adjustment and curriculum uncertainty.",
              reviewAction: "Counselor must decide whether this weakens the opportunity.",
            },
          ],
        },
        nextActions: ["Review counter-evidence with a counselor before any family-facing opportunity wording."],
      },
      browser: {
        missingP0TaskIds: [],
      },
      reportBrief: {
        familyFacingAllowed: false,
      },
    },
  },
  preview: {
    manifest: {
      client_delivery: {
        allowed: false,
      },
    },
  },
  clientFacingArtifacts: [],
  claimBoundary:
    "Real Case operator closure delivery preview does not prove admission probability or employment outcomes.",
};

const reviewer = {
  reviewerId: "counselor-a",
  displayName: "Counselor A",
  role: "senior_counselor",
};

const reject = decision.buildRealCaseCounselorReviewDecision({
  closurePreview,
  reviewer,
  decision: "reject",
  reasons: ["Counter-evidence directly weakens the opportunity hypothesis."],
  reviewedCounterEvidenceSourceIds: ["https://example.edu/risk"],
  sourceFreshnessChecked: true,
  representativenessChecked: true,
  claimBoundaryConfirmed: true,
});

assert.equal(reject.protocol, "real_case_counselor_review_decision_v1");
assert.equal(reject.decision, "reject");
assert.equal(reject.clientDeliveryAllowed, false);
assert.equal(reject.familyFacingAllowed, false);
assert.equal(reject.internalReportDraftAllowed, false);
assert.match(reject.statusReason, /reject/i);
assert.match(reject.claimBoundary, /does not prove admission probability/i);
assert.match(reject.claimBoundary, /does not prove employment outcomes/i);

const moreEvidence = decision.buildRealCaseCounselorReviewDecision({
  closurePreview,
  reviewer,
  decision: "needs_more_evidence",
  reasons: ["Job-market source needs fresher corroboration."],
  reviewedCounterEvidenceSourceIds: ["https://example.edu/risk"],
  sourceFreshnessChecked: false,
  representativenessChecked: true,
  claimBoundaryConfirmed: true,
});

assert.equal(moreEvidence.decision, "needs_more_evidence");
assert.equal(moreEvidence.internalReportDraftAllowed, false);
assert.equal(moreEvidence.clientDeliveryAllowed, false);
assert.deepEqual(moreEvidence.requiredNextActions, [
  "Collect fresher source evidence before internal report drafting.",
]);

const allowDraft = decision.buildRealCaseCounselorReviewDecision({
  closurePreview,
  reviewer,
  decision: "allow_internal_report_draft",
  reasons: ["Counter-evidence reviewed; use only as cautious internal draft input."],
  reviewedCounterEvidenceSourceIds: ["https://example.edu/risk"],
  sourceFreshnessChecked: true,
  representativenessChecked: true,
  claimBoundaryConfirmed: true,
});

assert.equal(allowDraft.decision, "allow_internal_report_draft");
assert.equal(allowDraft.internalReportDraftAllowed, true);
assert.equal(allowDraft.clientDeliveryAllowed, false);
assert.equal(allowDraft.familyFacingAllowed, false);
assert.deepEqual(allowDraft.requiredNextActions, [
  "Draft internal report language with counter-evidence caveats; keep client delivery blocked.",
]);
assert.doesNotMatch(JSON.stringify(allowDraft), /guaranteed admission|guaranteed employment|recommend applying/i);

assert.throws(
  () => decision.buildRealCaseCounselorReviewDecision({
    closurePreview,
    reviewer,
    decision: "allow_internal_report_draft",
    reasons: ["Skipping counter-evidence review."],
    reviewedCounterEvidenceSourceIds: [],
    sourceFreshnessChecked: true,
    representativenessChecked: true,
    claimBoundaryConfirmed: true,
  }),
  /counter-evidence/i,
);

assert.throws(
  () => decision.buildRealCaseCounselorReviewDecision({
    closurePreview,
    reviewer,
    decision: "allow_internal_report_draft",
    reasons: ["Missing representativeness check."],
    reviewedCounterEvidenceSourceIds: ["https://example.edu/risk"],
    sourceFreshnessChecked: true,
    representativenessChecked: false,
    claimBoundaryConfirmed: true,
  }),
  /representativeness/i,
);

console.log("Evidence Autopilot real case counselor review decision test passed");

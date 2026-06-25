import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const lib = path.join(here, "..", "lib");
const componentPath = path.join(here, "InternalDeliveryReview.tsx");
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
assert.equal(typeof decision.buildRealCaseCounselorDecisionDeliveryPreview, "function");
assert.equal(typeof decision.listRealCaseCounselorDecisionClientFacingArtifacts, "function");

const closurePreview = {
  protocol: "real_case_operator_closure_delivery_preview_v1",
  caseId: "scut-intelligent-manufacturing-real-case-v0",
  workflow: {
    protocol: "real_case_operator_closure_workflow_v1",
    closureReview: {
      browser: { missingP0TaskIds: [] },
      reportBrief: { familyFacingAllowed: false },
      auditPacket: {
        counterEvidence: {
          records: [
            {
              sourceId: "https://example.edu/risk",
              sourceTitle: "Counter evidence source",
            },
          ],
        },
      },
    },
  },
  preview: {
    success: true,
    message: "Real Case operator evidence is captured; internal preview is blocked for counselor review.",
    case_id: "scut-intelligent-manufacturing-real-case-v0",
    output_dir: "operator-closure://scut-intelligent-manufacturing-real-case-v0",
    manifest: {
      case_id: "scut-intelligent-manufacturing-real-case-v0",
      status: "requires_counter_evidence_review",
      client_delivery: {
        allowed: false,
        status: "blocked",
        artifact_audiences: ["client_confirmation", "client_final"],
        blocked_reason: "Client delivery remains blocked by counter-evidence and counselor review.",
      },
      artifacts: [
        {
          id: "real_case_operator_closure_brief",
          label: "Real Case operator closure brief",
          path: "operator-closure-brief.md",
          required: true,
          audience: "internal_review",
        },
        {
          id: "real_case_operator_closure_json",
          label: "Real Case operator closure JSON snapshot",
          path: "operator-closure.json",
          required: true,
          audience: "internal_review",
        },
      ],
      delivery_gates: [
        {
          gate: "counter_evidence_review",
          status: "blocked",
          requirement: "Counselor must review counter-evidence.",
        },
      ],
      next_actions: ["Review counter-evidence and source freshness before drafting any family-facing report language."],
    },
    artifacts: {
      real_case_operator_closure_brief: "# closure brief",
      real_case_operator_closure_json: "{\"status\":\"requires_counter_evidence_review\"}",
    },
  },
  clientFacingArtifacts: [],
  claimBoundary: "Closure preview does not prove admission probability or employment outcomes.",
};

const counselorDecision = decision.buildRealCaseCounselorReviewDecision({
  closurePreview,
  reviewer: {
    reviewerId: "counselor-a",
    displayName: "Counselor A",
    role: "senior_counselor",
  },
  decision: "allow_internal_report_draft",
  reasons: ["Counter-evidence reviewed; draft internally with caveats."],
  reviewedCounterEvidenceSourceIds: ["https://example.edu/risk"],
  sourceFreshnessChecked: true,
  representativenessChecked: true,
  claimBoundaryConfirmed: true,
});

const result = decision.buildRealCaseCounselorDecisionDeliveryPreview({
  closurePreview,
  counselorDecision,
});

assert.equal(result.protocol, "real_case_counselor_decision_delivery_preview_v1");
assert.equal(result.caseId, "scut-intelligent-manufacturing-real-case-v0");
assert.equal(result.counselorDecision.decision, "allow_internal_report_draft");
assert.equal(result.preview.manifest.status, "counselor_decision_recorded");
assert.equal(result.preview.manifest.client_delivery.allowed, false);
assert.match(result.preview.manifest.client_delivery.blocked_reason, /allow_internal_report_draft/);
assert.match(result.preview.manifest.client_delivery.blocked_reason, /client delivery remains blocked/i);
assert.equal(result.preview.manifest.artifacts.every((artifact) => artifact.audience === "internal_review"), true);
assert.deepEqual(
  result.preview.manifest.artifacts.map((artifact) => artifact.id),
  [
    "real_case_operator_closure_brief",
    "real_case_operator_closure_json",
    "real_case_counselor_decision_brief",
    "real_case_counselor_decision_json",
  ],
);
assert.match(result.preview.artifacts.real_case_counselor_decision_brief, /allow_internal_report_draft/);
assert.match(result.preview.artifacts.real_case_counselor_decision_brief, /client delivery remains blocked/i);
assert.match(result.preview.artifacts.real_case_counselor_decision_json, /Counter evidence source/);
assert.deepEqual(result.clientFacingArtifacts, []);
assert.match(result.claimBoundary, /does not prove admission probability/i);
assert.match(result.claimBoundary, /does not prove employment outcomes/i);
assert.doesNotMatch(JSON.stringify(result), /guaranteed admission|guaranteed employment|recommend applying/i);

assert.throws(
  () => decision.buildRealCaseCounselorDecisionDeliveryPreview({
    closurePreview: {
      ...closurePreview,
      caseId: "other-case",
    },
    counselorDecision,
  }),
  /caseId/i,
);

const source = fs.readFileSync(componentPath, "utf8");
for (const token of [
  "real_case_counselor_decision_brief",
  "real_case_counselor_decision_json",
  "Real Case counselor decision",
]) {
  assert.match(source, new RegExp(token), `InternalDeliveryReview should recognize ${token}`);
}

console.log("Evidence Autopilot real case counselor decision delivery preview test passed");

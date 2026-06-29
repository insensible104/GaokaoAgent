import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const lib = path.join(here, "..", "lib");
const bundlePath = path.join(lib, "evidenceAutopilotRealCaseReviewerHandoffDeliveryBundle.ts");

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

const bundle = loadTsModule(bundlePath);

assert.equal(typeof bundle.buildRealCaseReviewerHandoffDeliveryBundle, "function");
assert.equal(typeof bundle.buildRealCaseReviewerHandoffDeliveryPreview, "function");
assert.equal(typeof bundle.listRealCaseReviewerClientFacingArtifacts, "function");

const artifactManifest = {
  protocol: "real_case_reviewer_handoff_artifact_manifest_v1",
  caseId: "scut-intelligent-manufacturing-real-case-v0",
  artifactCount: 2,
  familyFacingAllowed: false,
  blockedReason:
    "Family-facing delivery is blocked until internal reviewer tasks are closed: employment-market.",
  claimBoundary:
    "Internal reviewer handoff only; does not prove admission probability and does not prove employment outcomes.",
  artifacts: [
    {
      id: "scut-intelligent-manufacturing-real-case-v0-reviewer-handoff-markdown",
      kind: "markdown",
      filename: "scut-intelligent-manufacturing-real-case-v0-reviewer-handoff.md",
      contentType: "text/markdown; charset=utf-8",
      audience: "internal_reviewer",
      familyFacingAllowed: false,
      content: [
        "# Internal reviewer handoff",
        "- employment-market",
        "- executeRealCaseOperatorClosureWorkflow",
      ].join("\n"),
      byteLength: 92,
      claimBoundary:
        "Internal reviewer handoff only; does not prove admission probability and does not prove employment outcomes.",
    },
    {
      id: "scut-intelligent-manufacturing-real-case-v0-reviewer-handoff-json",
      kind: "json",
      filename: "scut-intelligent-manufacturing-real-case-v0-reviewer-handoff.json",
      contentType: "application/json",
      audience: "internal_reviewer",
      familyFacingAllowed: false,
      content: JSON.stringify({ handoff: { openTaskIds: ["employment-market"] } }),
      byteLength: 51,
      claimBoundary:
        "Internal reviewer handoff only; does not prove admission probability and does not prove employment outcomes.",
    },
  ],
};

const deliveryBundle = bundle.buildRealCaseReviewerHandoffDeliveryBundle(artifactManifest);

assert.equal(deliveryBundle.protocol, "real_case_reviewer_handoff_delivery_bundle_v1");
assert.equal(deliveryBundle.caseId, "scut-intelligent-manufacturing-real-case-v0");
assert.equal(deliveryBundle.success, true);
assert.equal(deliveryBundle.manifest.case_id, "scut-intelligent-manufacturing-real-case-v0");
assert.equal(deliveryBundle.manifest.status, "blocked_by_operator_capture");
assert.equal(deliveryBundle.manifest.client_delivery.allowed, false);
assert.equal(deliveryBundle.manifest.client_delivery.status, "blocked");
assert.match(deliveryBundle.manifest.client_delivery.blocked_reason, /employment-market/);
assert.deepEqual(deliveryBundle.manifest.client_delivery.artifact_audiences, [
  "client_confirmation",
  "client_final",
]);
assert.equal(deliveryBundle.manifest.artifacts.length, 2);
assert.equal(
  deliveryBundle.manifest.artifacts.every((item) => item.audience === "internal_review"),
  true,
);
assert.deepEqual(
  deliveryBundle.manifest.artifacts.map((item) => item.id),
  [
    "real_case_reviewer_handoff_markdown",
    "real_case_reviewer_handoff_json",
  ],
);
assert.equal(deliveryBundle.artifacts.real_case_reviewer_handoff_markdown, artifactManifest.artifacts[0].content);
assert.equal(deliveryBundle.artifacts.real_case_reviewer_handoff_json, artifactManifest.artifacts[1].content);
assert.match(deliveryBundle.manifest.delivery_gates[0].gate, /real_case_reviewer_handoff/);
assert.equal(deliveryBundle.manifest.delivery_gates[0].status, "blocked");
assert.match(deliveryBundle.manifest.delivery_gates[0].requirement, /employment-market/);
assert.match(deliveryBundle.manifest.next_actions[0], /employment-market/);
assert.match(deliveryBundle.claimBoundary, /does not prove admission probability/i);
assert.match(deliveryBundle.claimBoundary, /does not prove employment outcomes/i);

const clientArtifacts = bundle.listRealCaseReviewerClientFacingArtifacts(deliveryBundle);
assert.deepEqual(clientArtifacts, []);

const deliveryPreview = bundle.buildRealCaseReviewerHandoffDeliveryPreview(deliveryBundle);
assert.equal(deliveryPreview.success, true);
assert.equal(deliveryPreview.case_id, "scut-intelligent-manufacturing-real-case-v0");
assert.equal(deliveryPreview.output_dir, "reviewer-handoff://scut-intelligent-manufacturing-real-case-v0");
assert.equal(deliveryPreview.manifest, deliveryBundle.manifest);
assert.equal(deliveryPreview.artifacts.real_case_reviewer_handoff_markdown, artifactManifest.artifacts[0].content);
assert.equal(deliveryPreview.artifacts.real_case_reviewer_handoff_json, artifactManifest.artifacts[1].content);
assert.equal(deliveryPreview.manifest.client_delivery.allowed, false);

assert.throws(
  () => bundle.buildRealCaseReviewerHandoffDeliveryBundle({
    ...artifactManifest,
    protocol: "wrong_protocol",
  }),
  /artifact manifest/i,
);

console.log("Evidence Autopilot real case reviewer handoff delivery bundle test passed");

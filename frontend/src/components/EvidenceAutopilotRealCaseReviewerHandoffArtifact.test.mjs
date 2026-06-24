import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const lib = path.join(here, "..", "lib");
const artifactPath = path.join(lib, "evidenceAutopilotRealCaseReviewerHandoffArtifact.ts");

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

const artifact = loadTsModule(artifactPath);

assert.equal(typeof artifact.buildRealCaseReviewerHandoffArtifactManifest, "function");

const bootstrapResult = {
  protocol: "real_case_reviewer_handoff_bootstrap_v1",
  caseId: "scut-intelligent-manufacturing-real-case-v0",
  publicBootstrap: {
    protocol: "real_case_reviewed_evidence_bootstrap_v1",
    caseId: "scut-intelligent-manufacturing-real-case-v0",
  },
  handoff: {
    protocol: "real_case_reviewer_handoff_v1",
    caseId: "scut-intelligent-manufacturing-real-case-v0",
    targetLabel: "SCUT intelligent manufacturing",
    status: "blocked_by_operator_capture",
    familyFacingAllowed: false,
    openTaskIds: ["employment-market"],
    capturePacket: {
      protocol: "operator_evidence_capture_packet_v1",
      caseId: "scut-intelligent-manufacturing-real-case-v0",
      items: [
        {
          taskId: "employment-market",
          captureBrief: "Capture a reviewer-verifiable job-market source.",
          requiredOutputFields: ["jobTitle", "city", "educationRequirement", "skills", "excerpt"],
        },
      ],
    },
    execution: {
      workflowFunction: "executeRealCaseOperatorClosureWorkflow",
      inputContract: "OperatorReviewedEvidenceCaptureInput",
      expectedStatusAfterValidCapture: "requires_counter_evidence_review",
      notes: ["Use only personally reviewable sources."],
    },
    reviewerChecklist: ["Reject unverifiable employment-market claims."],
    claimBoundary:
      "Internal reviewer work order only; does not prove admission probability or employment outcomes.",
  },
  brief: {
    protocol: "real_case_reviewer_handoff_brief_v1",
    caseId: "scut-intelligent-manufacturing-real-case-v0",
    title: "Internal reviewer handoff",
    familyFacingAllowed: false,
    sections: [],
    markdown: [
      "# Internal reviewer handoff",
      "",
      "- employment-market",
      "- executeRealCaseOperatorClosureWorkflow",
      "- does not prove admission probability",
      "- does not prove employment outcomes",
    ].join("\n"),
    claimBoundary:
      "Internal Markdown brief only; does not prove admission probability or employment outcomes.",
  },
  claimBoundary:
    "Bootstrap prepares an internal reviewer handoff only; it does not prove admission probability or employment outcomes.",
};

const manifest = artifact.buildRealCaseReviewerHandoffArtifactManifest(bootstrapResult);

assert.equal(manifest.protocol, "real_case_reviewer_handoff_artifact_manifest_v1");
assert.equal(manifest.caseId, "scut-intelligent-manufacturing-real-case-v0");
assert.equal(manifest.familyFacingAllowed, false);
assert.equal(manifest.artifactCount, 2);
assert.match(manifest.blockedReason, /employment-market/);
assert.match(manifest.claimBoundary, /does not prove admission probability/i);
assert.match(manifest.claimBoundary, /does not prove employment outcomes/i);

const markdownArtifact = manifest.artifacts.find((item) => item.kind === "markdown");
const jsonArtifact = manifest.artifacts.find((item) => item.kind === "json");

assert.ok(markdownArtifact);
assert.ok(jsonArtifact);
assert.equal(markdownArtifact.audience, "internal_reviewer");
assert.equal(jsonArtifact.audience, "internal_reviewer");
assert.equal(markdownArtifact.familyFacingAllowed, false);
assert.equal(jsonArtifact.familyFacingAllowed, false);
assert.match(markdownArtifact.filename, /^scut-intelligent-manufacturing-real-case-v0-/);
assert.match(markdownArtifact.filename, /\.md$/);
assert.match(jsonArtifact.filename, /^scut-intelligent-manufacturing-real-case-v0-/);
assert.match(jsonArtifact.filename, /\.json$/);
assert.match(markdownArtifact.content, /employment-market/);
assert.match(markdownArtifact.content, /executeRealCaseOperatorClosureWorkflow/);
assert.match(markdownArtifact.content, /does not prove admission probability/i);
assert.match(markdownArtifact.content, /does not prove employment outcomes/i);
assert.doesNotMatch(markdownArtifact.content, /recommend applying|guaranteed admission|guaranteed employment/i);

const parsed = JSON.parse(jsonArtifact.content);
assert.equal(parsed.protocol, "real_case_reviewer_handoff_bootstrap_v1");
assert.deepEqual(parsed.handoff.openTaskIds, ["employment-market"]);
assert.equal(parsed.handoff.familyFacingAllowed, false);
assert.equal(parsed.brief.familyFacingAllowed, false);
assert.doesNotMatch(jsonArtifact.content, /recommend applying|guaranteed admission|guaranteed employment/i);

assert.equal(markdownArtifact.byteLength > markdownArtifact.content.length, false);
assert.equal(jsonArtifact.byteLength > jsonArtifact.content.length, false);

assert.throws(
  () => artifact.buildRealCaseReviewerHandoffArtifactManifest({
    ...bootstrapResult,
    protocol: "wrong_protocol",
  }),
  /handoff bootstrap/i,
);

console.log("Evidence Autopilot real case reviewer handoff artifact manifest test passed");

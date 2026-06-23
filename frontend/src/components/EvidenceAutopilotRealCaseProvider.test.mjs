import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..", "..", "..");
const fixturePath = path.join(root, "data", "evidence_autopilot", "real_case_v0.json");
const providerPath = path.join(here, "..", "lib", "evidenceAutopilotRealCaseProvider.ts");

assert.equal(fs.existsSync(fixturePath), true, "Real Case v0 fixture should exist");
assert.equal(fs.existsSync(providerPath), true, "Real Case provider should exist");

function loadTsModule(source, requireMap = {}) {
  const output = ts.transpileModule(source, {
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

const providerModule = loadTsModule(fs.readFileSync(providerPath, "utf8"), {
  "../../../data/evidence_autopilot/real_case_v0.json": JSON.parse(fs.readFileSync(fixturePath, "utf8")),
});

assert.equal(typeof providerModule.loadEvidenceAutopilotRealCaseFixture, "function");
assert.equal(typeof providerModule.buildEvidenceAutopilotRealCaseProviderResults, "function");

const fixture = providerModule.loadEvidenceAutopilotRealCaseFixture();
assert.equal(fixture.caseId, "scut-intelligent-manufacturing-real-case-v0");
assert.match(fixture.claimBoundary, /auditable opportunity hypothesis/i);
assert.match(fixture.claimBoundary, /does not prove admission probability/i);
assert(fixture.evidenceCards.length >= 5);

const captured = fixture.evidenceCards.filter((card) => card.status === "captured_candidate");
assert(captured.length >= 5);
assert(captured.some((card) => card.taskId === "counter-evidence"));

for (const card of captured) {
  assert(card.sourceTitle.trim().length > 0, `${card.taskId} has source title`);
  assert.match(card.sourceUrl, /^https?:\/\//, `${card.taskId} has public URL`);
  assert(card.excerpt.trim().length >= 20, `${card.taskId} has useful excerpt`);
  assert.match(card.capturedAt, /^\d{4}-\d{2}-\d{2}/, `${card.taskId} has capture date`);
  assert(["official", "school", "paper", "job", "wechat", "discussion", "other"].includes(card.sourceType));
  assert(["high", "medium", "low"].includes(card.confidence));
  assert(card.reviewAction.trim().length > 0, `${card.taskId} has review action`);
}

const providerResults = providerModule.buildEvidenceAutopilotRealCaseProviderResults();
assert(providerResults.length >= 5);
assert.equal(providerResults.every((result) => result.requestId.startsWith("real-case-v0-")), true);
assert.equal(providerResults.some((result) => result.taskId === "counter-evidence"), true);

console.log("Evidence Autopilot real case provider test passed");

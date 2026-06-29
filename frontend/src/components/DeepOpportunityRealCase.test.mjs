import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const lib = path.join(here, "..", "lib");
const root = path.join(here, "..", "..", "..");

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

const fixture = JSON.parse(fs.readFileSync(path.join(root, "data", "evidence_autopilot", "real_case_v0.json"), "utf8"));
const realCase = loadTsModule(fs.readFileSync(path.join(lib, "evidenceAutopilotRealCaseProvider.ts"), "utf8"), {
  "../../../data/evidence_autopilot/real_case_v0.json": fixture,
});
const planModule = loadTsModule(fs.readFileSync(path.join(lib, "deepEvidenceCollectionPlan.ts"), "utf8"));
const evaluator = loadTsModule(fs.readFileSync(path.join(lib, "deepOpportunityEvaluator.ts"), "utf8"), {
  "./deepEvidenceCollectionPlan": planModule,
});
const normalizer = loadTsModule(fs.readFileSync(path.join(lib, "evidenceAutopilotResultNormalizer.ts"), "utf8"), {
  "./deepEvidenceCollectionPlan": planModule,
  "./deepOpportunityEvaluator": evaluator,
});
const autopilot = loadTsModule(fs.readFileSync(path.join(lib, "evidenceAutopilot.ts"), "utf8"), {
  "./deepEvidenceCollectionPlan": planModule,
  "./deepOpportunityEvaluator": evaluator,
  "./evidenceAutopilotResultNormalizer": normalizer,
});

const plan = planModule.buildDeepEvidenceCollectionPlan({
  province: fixture.candidate.province,
  targetYear: fixture.candidate.targetYear,
  schoolName: fixture.target.schoolName,
  majorName: fixture.target.majorName,
});
const providerResults = realCase.buildEvidenceAutopilotRealCaseProviderResults(fixture);
const run = autopilot.buildEvidenceAutopilotRun({ plan, providerResults });

assert(providerResults.length >= 5);
assert.equal(providerResults.some((result) => result.taskId === "counter-evidence"), true);
assert.match(fixture.claimBoundary, /auditable opportunity hypothesis/i);
assert.match(fixture.claimBoundary, /does not prove admission probability/i);

const verifiedResults = run.evidenceResults.filter((result) => result.status === "verified");
assert(verifiedResults.length >= 2);
assert.equal(run.evidenceResults.find((result) => result.taskId === "official-plan-charter").status, "verified");
assert.equal(run.evidenceResults.find((result) => result.taskId === "graduate-progression").status, "verified");
assert.equal(run.evidenceResults.some((result) => result.taskId === "counter-evidence"), true);

assert.equal(run.evaluation.horizonSignals.length, 3);
for (const signal of run.evaluation.horizonSignals) {
  assert(String(signal.horizon).length > 0);
  assert(["supported", "weak", "blocked"].includes(signal.status));
  assert(String(signal.summary).length > 0);
}
assert.notEqual(run.evaluation.status, "blocked");

console.log("Deep opportunity real case test passed");

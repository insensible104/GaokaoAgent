import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const snapshotPath = path.join(here, "..", "lib", "evidenceAutopilotSnapshotProvider.ts");
const providerPath = path.join(here, "..", "lib", "evidenceAutopilotProvider.ts");
const planPath = path.join(here, "..", "lib", "deepEvidenceCollectionPlan.ts");
const evaluatorPath = path.join(here, "..", "lib", "deepOpportunityEvaluator.ts");
const normalizerPath = path.join(here, "..", "lib", "evidenceAutopilotResultNormalizer.ts");
const autopilotPath = path.join(here, "..", "lib", "evidenceAutopilot.ts");
const panelPath = path.join(here, "DeepOpportunityEvaluationPanel.tsx");

assert.equal(fs.existsSync(snapshotPath), true, "snapshot provider module should exist");

function loadTsModule(source, requireMap = {}) {
  const output = ts.transpileModule(source, {
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

const provider = loadTsModule(fs.readFileSync(providerPath, "utf8"));
const planModule = loadTsModule(fs.readFileSync(planPath, "utf8"));
const evaluator = loadTsModule(fs.readFileSync(evaluatorPath, "utf8"), {
  "./deepEvidenceCollectionPlan": planModule,
});
const normalizer = loadTsModule(fs.readFileSync(normalizerPath, "utf8"), {
  "./deepEvidenceCollectionPlan": planModule,
  "./deepOpportunityEvaluator": evaluator,
});
const autopilot = loadTsModule(fs.readFileSync(autopilotPath, "utf8"), {
  "./deepEvidenceCollectionPlan": planModule,
  "./deepOpportunityEvaluator": evaluator,
  "./evidenceAutopilotResultNormalizer": normalizer,
});
const snapshot = loadTsModule(fs.readFileSync(snapshotPath, "utf8"), {
  "./evidenceAutopilotProvider": provider,
});

assert.equal(typeof snapshot.createEvidenceAutopilotSnapshotProvider, "function");
assert.equal(typeof snapshot.buildEvidenceAutopilotSnapshotProviderResults, "function");

const plan = planModule.buildDeepEvidenceCollectionPlan(planModule.exampleCollectionContext);
const searchTasks = autopilot.buildEvidenceAutopilotRun({ plan }).searchTasks;
const snapshotProvider = snapshot.createEvidenceAutopilotSnapshotProvider();

function requestFor(claim, requestId) {
  const task = searchTasks.find((item) => plan.tasks.find((planTask) => planTask.id === item.taskId)?.claim === claim);
  assert(task, `missing task for claim: ${claim}`);
  return provider.buildEvidenceAutopilotProviderRequest({
    requestId,
    targetLabel: plan.targetLabel,
    task,
    maxResults: 3,
  });
}

const officialResults = await snapshotProvider.search(requestFor("official_admission", "req-official"));
assert(officialResults.some((result) => result.sourceType === "official"));
assert(officialResults.some((result) => result.excerpt.includes("招生") || result.excerpt.includes("计划")));

const facultyResults = await snapshotProvider.search(requestFor("faculty_research", "req-faculty"));
assert(facultyResults.some((result) => result.sourceType === "school"));
assert(facultyResults.some((result) => result.excerpt.includes("课题组") || result.excerpt.includes("科研")));

const jobResults = await snapshotProvider.search(requestFor("employment_market", "req-job"));
assert(jobResults.some((result) => result.sourceType === "job"));
assert(jobResults.some((result) => result.excerpt.includes("岗位") || result.excerpt.includes("技能")));

const wechatResults = await snapshotProvider.search(requestFor("wechat_public_account", "req-wechat"));
assert.deepEqual(wechatResults, [], "wechat operator channel must not get fake full evidence by default");

const providerResults = snapshot.buildEvidenceAutopilotSnapshotProviderResults({
  plan,
  searchTasks,
  targetLabel: plan.targetLabel,
});
const snapshotRun = autopilot.buildEvidenceAutopilotRun({ plan, providerResults });
assert.equal(snapshotRun.evidenceResults.find((result) => result.claim === "official_admission").status, "verified");
assert.equal(snapshotRun.evidenceResults.find((result) => result.claim === "faculty_research").status, "verified");
assert.equal(snapshotRun.evidenceResults.find((result) => result.claim === "wechat_public_account").status, "missing");
assert.equal(snapshotRun.evaluation.status, "counselor_review_ready");

const panelSource = fs.readFileSync(panelPath, "utf8");
assert(panelSource.includes("buildEvidenceAutopilotSnapshotProviderResults"));
assert(panelSource.includes("providerResults"));

console.log("Evidence Autopilot snapshot provider test passed");

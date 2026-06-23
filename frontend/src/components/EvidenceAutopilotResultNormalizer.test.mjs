import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const normalizerPath = path.join(here, "..", "lib", "evidenceAutopilotResultNormalizer.ts");
const planPath = path.join(here, "..", "lib", "deepEvidenceCollectionPlan.ts");
const autopilotPath = path.join(here, "..", "lib", "evidenceAutopilot.ts");
const evaluatorPath = path.join(here, "..", "lib", "deepOpportunityEvaluator.ts");

assert.equal(fs.existsSync(normalizerPath), true, "result normalizer module should exist");

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

assert.equal(typeof normalizer.normalizeEvidenceAutopilotResults, "function");

const plan = planModule.buildDeepEvidenceCollectionPlan(planModule.exampleCollectionContext);
const official = plan.tasks.find((task) => task.claim === "official_admission");
const faculty = plan.tasks.find((task) => task.claim === "faculty_research");
const counter = plan.tasks.find((task) => task.claim === "counter_evidence");
const wechat = plan.tasks.find((task) => task.claim === "wechat_public_account");
assert(official);
assert(faculty);
assert(counter);
assert(wechat);

function providerResult(task, index, overrides = {}) {
  return {
    requestId: `req-${task.id}-${index}`,
    taskId: task.id,
    sourceTitle: `${task.title} 来源 ${index}`,
    sourceUrl: `https://example.edu/${task.id}/${index}`,
    sourceType: index === 1 ? "official" : "school",
    excerpt: `${task.title} 原文摘录 ${index}`,
    capturedAt: "2026-06-23T00:00:00.000Z",
    confidence: index === 1 ? "high" : "medium",
    ...overrides,
  };
}

const fullResults = normalizer.normalizeEvidenceAutopilotResults({
  plan,
  providerResults: [
    providerResult(official, 1),
    providerResult(official, 2),
    providerResult(faculty, 1),
  ],
});

const officialEvidence = fullResults.find((result) => result.taskId === official.id);
assert.equal(officialEvidence.status, "verified", "P0 task with two sources should be verified");
assert.equal(officialEvidence.sourceCount, 2);
assert.equal(officialEvidence.note.includes("来源 1"), true);
assert.equal(officialEvidence.note.includes("原文摘录 2"), true);

const facultyEvidence = fullResults.find((result) => result.taskId === faculty.id);
assert.equal(facultyEvidence.status, "weak", "P0 task with one source should be weak");
assert.equal(facultyEvidence.sourceCount, 1);

const missingWechat = fullResults.find((result) => result.taskId === wechat.id);
assert.equal(missingWechat.status, "missing", "operator-only task with no capture should stay missing");
assert.equal(missingWechat.sourceCount, 0);

const missingOnly = normalizer.normalizeEvidenceAutopilotResults({
  plan,
  providerResults: [],
});
assert.equal(missingOnly.find((result) => result.taskId === official.id).status, "missing");

const counterHit = normalizer.normalizeEvidenceAutopilotResults({
  plan,
  providerResults: [
    providerResult(counter, 1, {
      sourceTitle: "学生投诉与专业组调剂风险记录",
      sourceType: "discussion",
      excerpt: "该专业组存在黑名单专业与校区冲突，调剂风险需要阻断推荐。",
    }),
  ],
});
const counterEvidence = counterHit.find((result) => result.taskId === counter.id);
assert.equal(counterEvidence.status, "counter_hit");
assert.equal(counterEvidence.note.includes("黑名单"), true);
assert.equal(counterEvidence.note.includes("调剂风险"), true);

const run = autopilot.buildEvidenceAutopilotRun({
  plan,
  providerResults: [providerResult(official, 1), providerResult(official, 2)],
});
assert.equal(run.evidenceResults.find((result) => result.taskId === official.id).status, "verified");
assert.equal(run.evidenceResults.find((result) => result.taskId === faculty.id).status, "missing");
assert.equal(run.evaluation.status, "evidence_gap");

console.log("Evidence Autopilot result normalizer test passed");

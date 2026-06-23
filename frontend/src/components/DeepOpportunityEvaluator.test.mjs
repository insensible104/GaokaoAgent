import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const libPath = path.join(here, "..", "lib", "deepOpportunityEvaluator.ts");
const planPath = path.join(here, "..", "lib", "deepEvidenceCollectionPlan.ts");
const cardModelPath = path.join(here, "..", "lib", "deepOpportunityCard.ts");
const autopilotPath = path.join(here, "..", "lib", "evidenceAutopilot.ts");
const componentPath = path.join(here, "DeepOpportunityEvaluationPanel.tsx");
const cardPath = path.join(here, "DeepOpportunityCard.tsx");

const libSource = fs.readFileSync(libPath, "utf8");
const planSource = fs.readFileSync(planPath, "utf8");
const cardModelSource = fs.readFileSync(cardModelPath, "utf8");
const componentSource = fs.readFileSync(componentPath, "utf8");
const cardSource = fs.readFileSync(cardPath, "utf8");
const autopilotSource = fs.existsSync(autopilotPath) ? fs.readFileSync(autopilotPath, "utf8") : "";

for (const source of [libSource, planSource, cardModelSource, componentSource, cardSource, autopilotSource]) {
  assert.equal(source.includes("�"), false, "public demo source must not contain replacement characters");
  assert.equal(
    /(閺|锟|鎷|鏈|鐭|鍙嶈|涓|鏅鸿|骞夸|鍗庡)/.test(source),
    false,
    "public demo source must not contain mojibake-looking CJK runs",
  );
}

for (const token of [
  "机会雷达",
  "综合机会分",
  "P0 门槛",
  "反证命中",
  "证据缺口",
  "顾问复核就绪",
  "阻断推荐",
  "短期录取",
  "中期升学",
  "长期职业",
]) {
  assert(componentSource.includes(token), `evaluation panel should include token: ${token}`);
}

assert.match(cardSource, /DeepOpportunityEvaluationPanel/);

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

const planModule = loadTsModule(planSource);
const evaluator = loadTsModule(libSource, {
  "./deepEvidenceCollectionPlan": planModule,
});
const cardModel = loadTsModule(cardModelSource);
const autopilot = loadTsModule(autopilotSource, {
  "./deepEvidenceCollectionPlan": planModule,
  "./deepOpportunityEvaluator": evaluator,
});

const {
  buildDeepOpportunityEvaluation,
  exampleReadyEvidenceResults,
  exampleCounterEvidenceResults,
} = evaluator;

assert.equal(typeof buildDeepOpportunityEvaluation, "function");
assert(Array.isArray(exampleReadyEvidenceResults));
assert(Array.isArray(exampleCounterEvidenceResults));

const plan = planModule.buildDeepEvidenceCollectionPlan(planModule.exampleCollectionContext);
const ready = buildDeepOpportunityEvaluation({ plan, evidenceResults: exampleReadyEvidenceResults });

assert.equal(plan.targetLabel, "广东 2026 · 华南理工示例校 · 智能制造与数据工程");
assert.equal(ready.protocol, "deep_opportunity_evaluation_v1");
assert.equal(ready.status, "counselor_review_ready");
assert(ready.opportunityScore >= 82);
assert.equal(ready.p0Gate.passed, true);
assert.equal(ready.counterEvidence.hit, false);
assert.equal(ready.claimBoundary.includes("不是最终志愿推荐"), true);
assert(ready.positiveSignals.some((signal) => signal.includes("科研")));
assert(ready.positiveSignals.some((signal) => signal.includes("真实就业")));
assert(ready.reviewChecklist.some((item) => item.includes("顾问复核")));
assert(ready.horizonSignals.some((item) => item.horizon === "短期录取" && item.status === "supported"));
assert(ready.horizonSignals.some((item) => item.horizon === "中期升学" && item.status === "supported"));
assert(ready.horizonSignals.some((item) => item.horizon === "长期职业" && item.status === "supported"));

const blocked = buildDeepOpportunityEvaluation({ plan, evidenceResults: exampleCounterEvidenceResults });
assert.equal(blocked.status, "blocked");
assert(blocked.opportunityScore < ready.opportunityScore);
assert.equal(blocked.counterEvidence.hit, true);
assert(blocked.blockedReasons.some((reason) => reason.includes("反证命中") || reason.includes("阻断推荐")));
assert(blocked.missingEvidence.some((gap) => gap.includes("P0")));
assert(blocked.horizonSignals.some((item) => item.status === "blocked" || item.status === "weak"));

const card = cardModel.buildDeepOpportunityCard(cardModel.exampleDeepOpportunityInput);
assert.equal(card.protocol, "deep_opportunity_card_v1");
assert.equal(card.confidence, "高");
assert(card.alphaBoard.length >= 5);
assert(card.alphaBoard.some((row) => row.factor === "同分段相对提升"));
assert(card.alphaBoard.some((row) => row.factor === "职业路径兑现度"));
assert(card.fitFor.some((item) => item.includes("考研") || item.includes("保研")));
assert(card.notFitFor.some((item) => item.includes("调剂")));

assert.equal(typeof autopilot.buildEvidenceAutopilotRun, "function");
const autopilotRun = autopilot.buildEvidenceAutopilotRun({ plan });
assert.equal(autopilotRun.protocol, "evidence_autopilot_run_v1");
assert(autopilotRun.searchTasks.some((task) => task.channel === "public_web" && task.query.includes("华南理工示例校")));
assert(autopilotRun.searchTasks.some((task) => task.channel === "wechat_operator" && task.query.includes("公众号")));
assert(autopilotRun.searchTasks.some((task) => task.channel === "job_market_operator" && task.query.includes("Boss直聘")));
assert(autopilotRun.operatorTasks.every((task) => task.complianceBoundary.includes("不绕过登录")));
assert(autopilotRun.evidenceResults.some((result) => result.claim === "employment_market" && result.status === "verified"));
assert.equal(autopilotRun.evaluation.status, "counselor_review_ready");
assert(autopilotRun.claimBoundary.includes("自动生成证据任务"));

console.log("Deep opportunity evaluator test passed");

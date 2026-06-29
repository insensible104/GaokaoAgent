import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const libPath = path.join(here, "..", "lib", "deepEvidenceCollectionPlan.ts");
const componentPath = path.join(here, "DeepEvidenceCollectionPlan.tsx");
const cardPath = path.join(here, "DeepOpportunityCard.tsx");

const libSource = fs.readFileSync(libPath, "utf8");
const componentSource = fs.readFileSync(componentPath, "utf8");
const cardSource = fs.readFileSync(cardPath, "utf8");

for (const token of [
  "高维证据采集台账",
  "官方招生",
  "科研方向",
  "师资与论文",
  "本科生可获得性",
  "真实就业",
  "考研/保研",
  "考公",
  "微信公众号",
  "Boss直聘",
  "反证降权",
]) {
  assert(componentSource.includes(token), `collection component should include token: ${token}`);
}

for (const source of [libSource, componentSource]) {
  assert.equal(/(閺|锟|鎷|鏈|鐭|鍙嶈|涓|鏅鸿|骞夸|鍗庡)/.test(source), false);
}

assert.match(cardSource, /DeepEvidenceCollectionPlan/);

const output = ts.transpileModule(libSource, {
  compilerOptions: {
    esModuleInterop: true,
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
  },
}).outputText;

const module = { exports: {} };
new Function("module", "exports", output)(module, module.exports);

const { buildDeepEvidenceCollectionPlan, exampleCollectionContext } = module.exports;
assert.equal(typeof buildDeepEvidenceCollectionPlan, "function");

const plan = buildDeepEvidenceCollectionPlan(exampleCollectionContext);
assert.equal(plan.protocol, "deep_evidence_collection_plan_v1");
assert(plan.tasks.length >= 9, "plan should cover enough high-dimensional evidence tasks");
assert.equal(plan.claimBoundary.includes("不是自动抓取承诺"), true);

for (const claim of [
  "official_admission",
  "faculty_research",
  "publication_trace",
  "undergrad_access",
  "employment_market",
  "graduate_progression",
  "civil_service_path",
  "wechat_public_account",
  "counter_evidence",
]) {
  assert(plan.tasks.some((task) => task.claim === claim), `missing evidence claim: ${claim}`);
}

assert(
  plan.tasks.some((task) => task.accessMethod.includes("不绕过登录") && task.outputFields.includes("原文摘录")),
  "WeChat and semi-closed sources should require compliant excerpts",
);
assert(
  plan.tasks.some((task) => task.passRule.includes("降权") || task.failRule.includes("降权")),
  "plan should include downgrade rules",
);
assert(
  plan.reviewGates.some((gate) => gate.includes("双来源") || gate.includes("第二来源")),
  "plan should require source triangulation",
);

console.log("Deep evidence collection plan test passed");

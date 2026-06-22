import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const libPath = path.join(here, "..", "lib", "deepOpportunityCard.ts");
const componentPath = path.join(here, "DeepOpportunityCard.tsx");
const appPath = path.join(here, "..", "App.tsx");

const libSource = fs.readFileSync(libPath, "utf8");
const componentSource = fs.readFileSync(componentPath, "utf8");
const appSource = fs.readFileSync(appPath, "utf8");

for (const token of [
  "深度机会卡",
  "量化定位",
  "研究方向",
  "师资与论文",
  "本科生可获得性",
  "真实就业",
  "升学路径",
  "反证与降权",
  "证据缺口",
]) {
  assert(componentSource.includes(token), `DeepOpportunityCard should render section token: ${token}`);
}

assert.match(appSource, /DeepOpportunityCard/);
assert.match(appSource, /deep-opportunity-card/);

const output = ts.transpileModule(libSource, {
  compilerOptions: {
    esModuleInterop: true,
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
  },
}).outputText;

const module = { exports: {} };
new Function("module", "exports", output)(module, module.exports);

const { buildDeepOpportunityCard, exampleDeepOpportunityInput } = module.exports;

assert.equal(typeof buildDeepOpportunityCard, "function");
assert.equal(typeof exampleDeepOpportunityInput, "object");

const card = buildDeepOpportunityCard(exampleDeepOpportunityInput);

assert.equal(card.protocol, "deep_opportunity_card_v1");
assert.equal(card.opportunityType, "科研资源被低估型机会");
assert(card.totalScore >= 80, "sample opportunity should be strong enough for a public MVP card");
assert(card.fitFor.some((item) => item.includes("读研")));
assert(card.notFitFor.some((item) => item.includes("只想本科稳定就业")));
assert(card.claimBoundary.includes("不是最终志愿推荐"));

for (const pillar of [
  "量化定位",
  "科研资源",
  "本科生可获得性",
  "真实就业",
  "升学路径",
  "低估可能",
  "反证边界",
]) {
  assert(
    card.evidencePillars.some((item) => item.label === pillar && item.score > 0),
    `card should include scored evidence pillar: ${pillar}`,
  );
}

assert(card.evidenceGaps.some((gap) => gap.includes("2026")));
assert(card.researchSignals.some((signal) => signal.includes("实验室") || signal.includes("课题组")));
assert(card.employmentSignals.some((signal) => signal.includes("岗位")));

console.log("DeepOpportunityCard behavior test passed");

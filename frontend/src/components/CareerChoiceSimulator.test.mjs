import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const componentPath = path.join(here, "CareerChoiceSimulator.tsx");
const libPath = path.join(here, "..", "lib", "careerSimulation.ts");
const componentSource = fs.readFileSync(componentPath, "utf8");
const libSource = fs.readFileSync(libPath, "utf8");

for (const token of [
  "CareerChoiceSimulator",
  "生涯选择模拟",
  "先看这个职业每天到底在做什么",
  "一天工作切片",
  "升学、就业、考公的真实路径",
  "O*NET",
  "Lightcast Open Skills",
  "职业模拟，不替代访谈",
  "国内真实岗位锚点",
  "JD 关键词",
  "岗位证据",
]) {
  assert(componentSource.includes(token), `CareerChoiceSimulator should include token: ${token}`);
}

for (const token of [
  "buildCareerSimulations",
  "AI 产品 / 算法工程师",
  "公务员 / 选调 / 公共政策",
  "clinical_medicine",
  "routesDetail",
  "sourceRefs",
  "domesticJobAnchorMap",
  "大模型应用工程师 / AI 应用开发",
  "基层公务员 / 选调生",
]) {
  assert(libSource.includes(token), `careerSimulation should include token: ${token}`);
}

const output = ts.transpileModule(libSource, {
  compilerOptions: {
    esModuleInterop: true,
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
  },
}).outputText;

const module = { exports: {} };
new Function("module", "exports", output)(module, module.exports);

const simulations = module.exports.buildCareerSimulations({
  profile: {
    preferred_majors: ["计算机科学", "软件工程"],
    blacklist_majors: ["土木工程"],
    riasec_top_codes: ["I", "R"],
    career_values: ["growth"],
    risk_tolerance: "balanced",
  },
  rows: [
    {
      major_list: ["人工智能", "数据科学"],
      suggested_major_choices: [{ major_name: "计算机科学" }],
    },
  ],
  limit: 3,
});

assert.equal(simulations[0].id, "ai_product_engineer");
assert(simulations[0].fitScore > simulations[1].fitScore);
assert(simulations[0].routesDetail.some((route) => route.label.includes("考研")));
assert(simulations[0].dayParts.length >= 4);
assert(simulations[0].sourceRefs.some((source) => source.includes("O*NET")));
assert(simulations[0].domesticJobAnchors.some((anchor) => anchor.title.includes("大模型应用工程师")));
assert(simulations[0].domesticJobAnchors.some((anchor) => anchor.jdKeywords.includes("RAG")));
assert(simulations[0].domesticJobAnchors.every((anchor) => anchor.evidenceToCollect.length > 0));

console.log("CareerChoiceSimulator smoke and ranking test passed");

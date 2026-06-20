import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const componentPath = path.join(here, "JobEvidenceWorkbench.tsx");
const libPath = path.join(here, "..", "lib", "jobEvidence.ts");
const demoPath = path.join(here, "AdmissionsOpportunityDemoCasePanel.tsx");

const componentSource = fs.readFileSync(componentPath, "utf8");
const libSource = fs.readFileSync(libPath, "utf8");
const demoSource = fs.readFileSync(demoPath, "utf8");

for (const token of [
  "JobEvidenceWorkbench",
  "岗位证据工作台",
  "请粘贴你有权查看或保存的 JD",
  "不支持绕过平台反爬抓取",
  "岗位路径判断",
  "本科就业",
  "读研/保研",
  "考公/事业单位",
]) {
  assert(componentSource.includes(token), `JobEvidenceWorkbench should include token: ${token}`);
}

for (const token of [
  "parseManualJobDescription",
  "buildJobEvidenceBrief",
  "manual_jd",
  "public_report",
  "campus_recruitment",
  "civil_service_table",
  "platformPolicyNote",
]) {
  assert(libSource.includes(token), `jobEvidence should include token: ${token}`);
}

assert(demoSource.includes("JobEvidenceWorkbench"), "public demo should mount JobEvidenceWorkbench");

const output = ts.transpileModule(libSource, {
  compilerOptions: {
    esModuleInterop: true,
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
  },
}).outputText;

const module = { exports: {} };
new Function("module", "exports", output)(module, module.exports);

const sampleJd = [
  "岗位：大模型应用工程师",
  "地点：广州/深圳",
  "学历要求：本科及以上，计算机、软件工程、人工智能相关专业优先",
  "经验：应届生可投，有 AI 项目或实习经历优先",
  "职责：负责 RAG 应用、Agent 工作流、模型评测、向量数据库接入和业务指标复盘",
  "技能：Python、SQL、LangChain、Prompt Engineering、A/B 实验",
].join("\n");

const parsed = module.exports.parseManualJobDescription(sampleJd);
assert.equal(parsed.jobTitle, "大模型应用工程师");
assert.deepEqual(parsed.cities, ["广州", "深圳"]);
assert.equal(parsed.educationRequirement, "本科及以上");
assert.equal(parsed.experienceRequirement, "应届可投");
assert(parsed.skillKeywords.includes("RAG"));
assert(parsed.skillKeywords.includes("Python"));
assert(parsed.skillKeywords.includes("向量数据库"));
assert(parsed.routeSignals.employment.some((item) => item.includes("项目")));
assert(parsed.routeSignals.graduate.some((item) => item.includes("算法")));
assert(parsed.boundaryWarnings.some((item) => item.includes("粘贴")));

const brief = module.exports.buildJobEvidenceBrief({
  sourceType: "manual_jd",
  text: sampleJd,
  capturedAt: "2026-06-20",
});

assert.equal(brief.sourceType, "manual_jd");
assert.equal(brief.normalizedRoleFamily, "AI 应用开发");
assert(brief.evidenceQuestions.some((item) => item.includes("学历")));
assert(brief.platformPolicyNote.includes("不支持绕过平台反爬抓取"));
assert(brief.summary.includes("大模型应用工程师"));

console.log("JobEvidenceWorkbench parser and public demo test passed");

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(path.join(here, "AdmissionsOpportunityDemoCasePanel.tsx"), "utf8");
const output = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
    jsx: ts.JsxEmit.React,
    esModuleInterop: true,
  },
}).outputText;

const module = { exports: {} };
const localRequire = (specifier) => {
  if (specifier === "react") return {};
  if (specifier === "../lib/admissionsOpportunityDemoCase") return { buildAdmissionsOpportunityDemoCase: () => ({}) };
  if (specifier === "./CareerChoiceSimulator") return { CareerChoiceSimulator: () => null };
  if (specifier === "./EvidenceCollectionWorkspacePanel") return { EvidenceCollectionWorkspacePanel: () => null };
  if (specifier === "./JobEvidenceWorkbench") return { JobEvidenceWorkbench: () => null };
  throw new Error(`Unexpected require: ${specifier}`);
};

new Function("require", "module", "exports", output)(localRequire, module, module.exports);

const { formatAdmissionsDemoText } = module.exports;

assert.equal(typeof formatAdmissionsDemoText, "function");
assert.equal(formatAdmissionsDemoText("Student A"), "学生 A");
assert.equal(formatAdmissionsDemoText("hypothesis_only"), "仅作假设");
assert.equal(formatAdmissionsDemoText("ready_for_counselor_review"), "可进入顾问复核");
assert.equal(formatAdmissionsDemoText("Hidden opportunity audit"), "隐性机会复核");
assert.equal(formatAdmissionsDemoText("can enter ledger: yes"), "可进入机会台账：是");
assert.equal(formatAdmissionsDemoText("specialized"), "专业来源");
assert.equal(formatAdmissionsDemoText("current_cycle"), "当前招生周期");
assert.equal(formatAdmissionsDemoText("official_change"), "官方计划变化");
assert.equal(formatAdmissionsDemoText("Attach official plan diff before using trend language."), "使用趋势话术前，必须先补充官方招生计划变化证据。");
assert.equal(formatAdmissionsDemoText("This dossier can be shown as a counselor-review explanation, with final filing still gated by counselor signoff."), "这份材料可以作为顾问复核说明展示，但最终填报仍需顾问签字。");
assert.equal(
  formatAdmissionsDemoText(
    "This demo case is not a final recommendation. It demonstrates the auditable workflow from official diff, public-opinion hypothesis, capture worksheet, evidence intake, and counselor-review package.",
  ),
  "这个演示案例不是最终志愿推荐。它展示的是从官方计划变化、公开讨论假设、采集任务表、证据入库到顾问复核材料包的可审计流程。",
);
assert.equal(
  formatAdmissionsDemoText("South China Tech Computer Science can be described only as an under-attention candidate."),
  "华南理工示例校计算机科学只能表述为关注度不足的候选机会。",
);

console.log("Admissions opportunity Chinese surface formatter test passed");

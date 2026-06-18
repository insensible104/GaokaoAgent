import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = fs.readFileSync(path.join(here, "..", "App.tsx"), "utf8");
const externalDemoSource = fs.readFileSync(path.join(here, "ExternalPlanAuditDemoPanel.tsx"), "utf8");
const admissionsDemoSource = fs.readFileSync(path.join(here, "AdmissionsOpportunityDemoCasePanel.tsx"), "utf8");
const reportSource = fs.readFileSync(path.join(here, "PathFinderReportTemplate.tsx"), "utf8");
const formSource = fs.readFileSync(path.join(here, "GaokaoAgentForm.tsx"), "utf8");

const combinedPublicSource = [
  appSource,
  externalDemoSource,
  admissionsDemoSource,
  reportSource,
  formSource,
].join("\n");

for (const token of [
  "#F8FBFF",
  "#EAF3FF",
  "#C8D8EA",
  "#1F5E99",
  "#0F766E",
  "#B7791F",
  "#C14E2A",
  "志愿表体检",
  "趋势机会",
  "证据账本",
  "交付边界",
  "flagship-hero",
  "志愿体检结果预览",
  "报告成品预览",
  "趋势机会雷达",
  "证据工作台",
  "顾问复核签字",
  "case-artifact",
  "public-shell",
  "workbench-grid",
  "workbench-rail",
  "workbench-main",
  "workbench-decision",
  "research-report",
]) {
  assert(
    combinedPublicSource.includes(token),
    `public redesign should include token: ${token}`,
  );
}

for (const badToken of [
  "#FBFAF6",
  "#F1ECDE",
  "#D8D2C2",
  "bg-gradient-to-br from-sky-50 via-blue-50 to-cyan-50",
  "bg-gradient-to-br from-white to-sky-50",
  "bg-gradient-to-r from-sky-500",
  "现代中文升学画册试样",
  "鍐",
  "涓",
  "绠",
  "浼",
]) {
  assert(
    !combinedPublicSource.includes(badToken),
    `public redesign should not include stale or mojibake token: ${badToken}`,
  );
}

console.log("Public demo and report redesign smoke test passed");

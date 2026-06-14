import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const componentPath = path.join(here, "DeliveryReadinessConsole.tsx");
const helperPath = path.join(here, "..", "lib", "deliveryReadiness.ts");
const appPath = path.join(here, "..", "App.tsx");
const reportTemplatePath = path.join(here, "PathFinderReportTemplate.tsx");

assert.ok(fs.existsSync(componentPath), "DeliveryReadinessConsole.tsx should render the readiness gates");
assert.ok(fs.existsSync(helperPath), "deliveryReadiness.ts should centralize readiness gate logic");

const componentSource = fs.readFileSync(componentPath, "utf8");
const helperSource = fs.readFileSync(helperPath, "utf8");
const appSource = fs.readFileSync(appPath, "utf8");
const reportTemplateSource = fs.readFileSync(reportTemplatePath, "utf8");

for (const token of [
  "buildDeliveryReadinessSummary",
  "DeliveryReadinessSummary",
  "data_boundary",
  "plan_structure",
  "evidence_pack",
  "report_package",
  "human_review",
  "ready",
  "needs_review",
  "blocked",
  "不是录取承诺",
  "正式交付前必须复核",
]) {
  assert(
    helperSource.includes(token),
    `deliveryReadiness helper should include token: ${token}`,
  );
}

for (const token of [
  "DeliveryReadinessConsole",
  "交付准备度",
  "交付 gate",
  "正式交付前必须复核",
  "不是录取承诺",
  "打开 A4 报告预览",
  "ShieldCheck",
  "AlertTriangle",
]) {
  assert(
    componentSource.includes(token),
    `DeliveryReadinessConsole should include token: ${token}`,
  );
}

for (const token of [
  "DeliveryReadinessConsole",
  "buildDeliveryReadinessSummary",
  "deliveryReadiness",
  "pathfinder-report-preview",
]) {
  assert(
    appSource.includes(token),
    `App should wire readiness console and report payload token: ${token}`,
  );
}

for (const token of [
  "DeliveryReadiness",
  "deliveryReadiness",
  "交付准备度",
  "正式交付前必须复核",
]) {
  assert(
    reportTemplateSource.includes(token),
    `PathFinder report template should include readiness token: ${token}`,
  );
}

for (const source of [componentSource, helperSource, reportTemplateSource]) {
  for (const garbledToken of ["鍗", "璁", "绋", "鐗", "骞", "鎷", "€?"]) {
    assert(
      !source.includes(garbledToken),
      `delivery readiness files should not contain mojibake token: ${garbledToken}`,
    );
  }
}

console.log("DeliveryReadinessConsole smoke test passed");

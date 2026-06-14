import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const templatePath = path.join(here, "PathFinderReportTemplate.tsx");
const appPath = path.join(here, "..", "App.tsx");

assert.ok(
  fs.existsSync(templatePath),
  "PathFinderReportTemplate.tsx should provide the A4 HTML report template",
);

const source = fs.readFileSync(templatePath, "utf8");
const appSource = fs.readFileSync(appPath, "utf8");

for (const token of [
  "PathFinderReportTemplate",
  "InvestmentResearchReportPreview",
  "report-page",
  "@page",
  "size: A4",
  "page-break-after",
  "VolunteerMatrix",
  "EvidenceLedger",
  "RiskLedger",
  "DecisionEvidenceCard",
  "DataBoundary",
  "RIASEC",
  "MBTI",
  "first_hit_prob",
  "tail_assignment_risk",
  "probability_range",
  "print",
  "window.print",
  "PathFinderReportPayload",
  "buildReportPayload",
  "pathfinder-report-preview",
  "sessionStorage",
  "gameMatrix",
  "deliveryProfile",
  "升学规划定制报告",
  "志愿矩阵",
  "关键前缀志愿解释",
  "证据账本",
  "风险账本",
  "正式填报前必须复核",
]) {
  assert(
    source.includes(token),
    `PathFinder report template should include token: ${token}`,
  );
}

for (const garbledToken of ["鍗", "璁", "绋", "鐗", "骞", "鎷", "€?"]) {
  assert(
    !source.includes(garbledToken),
    `PathFinder report template should not contain mojibake token: ${garbledToken}`,
  );
}

assert(
  appSource.includes("report-template-preview"),
  "App should expose a preview path for the report template",
);

assert(
  appSource.includes("/app/report-template-preview"),
  "App should open the report preview under the Vite /app base path",
);

assert(
  appSource.includes("pathfinder-report-preview"),
  "App should persist the latest analyzed report payload for the report preview",
);

console.log("PathFinder report template smoke test passed");

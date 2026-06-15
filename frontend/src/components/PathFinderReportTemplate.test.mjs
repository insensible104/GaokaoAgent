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
  "霍兰德兴趣",
  "MBTI",
  "first_hit_prob",
  "tail_assignment_risk",
  "probability_range",
  "print",
  "window.print",
  "PathFinderReportPayload",
  "buildReportPayload",
  "export function buildReportPayload",
  "isSampleMode",
  "pathfinder-report-preview",
  "sessionStorage",
  "gameMatrix",
  "deliveryProfile",
  "report-title-cn",
  "report-kicker-en",
  "section-heading__cn",
  "section-heading__en",
  "report-page--dense",
  "compact-evidence-panel",
  "ChineseFirstReport",
  "DeliveryReadiness",
  "sample-student-29",
  "subject-combo-wuhuasheng",
  "mbti-intj",
  "canva-editorial-cover",
  "reference-summary-strip",
  "半导体方向",
  "仪器类",
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

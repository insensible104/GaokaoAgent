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
  "PathFinderReportPayload",
  "export function buildReportPayload",
  "report-page",
  "@page",
  "size: A4",
  "page-break-after",
  "window.print",
  "pathfinder-report-preview",
  "sessionStorage",
  "gameMatrix",
  "deliveryProfile",
  "research-report",
  "cover-modern",
  "VolunteerCardDeck",
  "VolunteerMatrix",
  "EvidenceLedger",
  "RiskLedger",
  "DecisionEvidenceCard",
  "DataBoundary",
  "emotion-value-strip",
  "advisor-note",
  "report-title-cn",
  "sample-student-29",
  "subject-combo-wuhuasheng",
  "mbti-intj",
  "11845",
  "广东工业大学",
  "206 专业组",
  "研究报告",
  "趋势机会雷达",
  "趋势分析",
  "顾问复核签字",
  "志愿表体检",
  "趋势机会",
  "证据账本",
  "交付边界",
]) {
  assert(
    source.includes(token),
    `PathFinder report template should include token: ${token}`,
  );
}

for (const badToken of [
  "DataBoundary</p>",
  "VolunteerMatrix</span>",
  "现代中文升学画册试样",
  "bg-gradient-to-br from-sky-50 via-blue-50 to-cyan-50",
]) {
  assert(
    !source.includes(badToken),
    `PathFinder report template should not expose internal token: ${badToken}`,
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

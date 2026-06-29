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
  "cover-media",
  "report-cover-campus.svg",
  "cover-title-card",
  "cover-focus-summary",
  "cover-meta-line",
  "ReportContentsPage",
  "contents-layout",
  "contents-rail",
  "contents-list",
  "report-boundary-panel",
  "VolunteerCardDeck",
  "VolunteerMatrix",
  "EvidenceLedger",
  "RiskLedger",
  "DecisionEvidenceCard",
  "PortfolioDiagnosis",
  "EvaluationMatrix",
  "CounterEvidenceChecklist",
  "DataBoundary",
  "emotion-value-strip",
  "advisor-note",
  "report-title-cn",
  "升学质量报告",
  "寻径升学",
  "sample-student-29",
  "subject-combo-wuhuasheng",
  "mbti-intj",
  "11845",
  "广东工业大学",
  "206 专业组",
  "研究报告",
  "趋势机会雷达",
  "趋势分析",
  "顾问判断",
  "组合诊断",
  "行级评估矩阵",
  "反证清单",
  "证据强度",
  "下一步复核",
  "志愿表体检",
  "趋势机会",
  "证据账本",
  "交付边界",
  "报告阅读顺序",
  "选择之书",
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
  "campus-window",
  "cover-decision-metrics",
  "cover-roadmap",
  "cover-volunteer-sample",
  "cover-hero-plate",
  "cover-system-tags",
  "cover-detail-route",
  "identity-strip",
  "Quantitative",
  "Research<br />Report",
  "稳住",
  "这一版方案",
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
  appSource.includes("buildAppPath(\"/report-template-preview\")"),
  "App should open the report preview under the active Vite base path",
);

assert(
  appSource.includes("import.meta.env.BASE_URL"),
  "App should derive public demo links from the active Vite base path",
);

assert(
  appSource.includes("pathfinder-report-preview"),
  "App should persist the latest analyzed report payload for the report preview",
);

for (const token of [
  "fetchReviewedEvidenceRecords",
  "resolveReviewedEvidenceCaseId",
  "buildReportEvidenceAutopilotPayload",
  "reviewedEvidenceRecords",
  "evidenceAutopilot",
]) {
  assert(
    appSource.includes(token),
    `App report preview should wire reviewed evidence token: ${token}`,
  );
}

console.log("PathFinder report template smoke test passed");

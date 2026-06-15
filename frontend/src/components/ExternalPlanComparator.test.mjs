import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const componentPath = path.join(__dirname, "ExternalPlanComparator.tsx");
const helperPath = path.join(__dirname, "..", "lib", "externalPlanAudit.ts");
const gameMatrixPath = path.join(__dirname, "GameMatrixView.tsx");

function assert(condition, message) {
  if (!condition) {
    console.error(message);
    process.exit(1);
  }
}

function read(filePath) {
  assert(fs.existsSync(filePath), `${path.basename(filePath)} should exist`);
  return fs.readFileSync(filePath, "utf8");
}

const component = read(componentPath);
const helper = read(helperPath);
const gameMatrix = read(gameMatrixPath);
const newSourceText = [component, helper].join("\n");

[
  "ExternalPlanComparator",
  "外部方案审计",
  "粘贴千问/家长/人工方案",
  "PathFinder 审计口径",
  "解析行数",
  "重合院校专业组",
  "未匹配条目",
  "复核动作",
].forEach((token) => {
  assert(component.includes(token), `component should include ${token}`);
});

[
  "parseExternalPlanText",
  "auditExternalPlan",
  "ExternalPlanAuditSummary",
  "external_plan_audit",
  "overlap_rate",
  "unmatched_entries",
  "strategy_mix",
  "claimBoundary",
  "不判断外部方案对错",
  "不使用2026官方数据生成新结论",
].forEach((token) => {
  assert(helper.includes(token), `helper should include ${token}`);
});

assert(
  gameMatrix.includes("ExternalPlanComparator") &&
    gameMatrix.includes("<ExternalPlanComparator"),
  "GameMatrixView should render ExternalPlanComparator"
);

["鍗", "璁", "鏉", "瀛"].forEach((token) => {
  assert(!newSourceText.includes(token), `new source should not include mojibake/token ${token}`);
});

console.log("ExternalPlanComparator smoke assertions passed");

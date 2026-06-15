import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const componentPath = path.join(__dirname, "CounselorDeliveryChecklist.tsx");
const helperPath = path.join(__dirname, "..", "lib", "counselorDeliveryChecklist.ts");
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

[
  "buildCounselorDeliveryChecklist",
  "CounselorDeliveryChecklistSummary",
  "counselor_delivery_checklist",
  "profile_completeness",
  "plan_structure",
  "evidence_integrity",
  "external_comparison",
  "leadAction",
  "claimBoundary",
  "不生成新的录取结论",
  "不替代人工复核",
].forEach((token) => {
  assert(helper.includes(token), `helper should include ${token}`);
});

[
  "CounselorDeliveryChecklist",
  "顾问交付清单",
  "1 分钟交付判断",
  "阻断项",
  "复核项",
  "下一步动作",
  "交付口径",
  "千问/老师方案",
].forEach((token) => {
  assert(component.includes(token), `component should include ${token}`);
});

assert(
  gameMatrix.includes("CounselorDeliveryChecklist") &&
    gameMatrix.includes("<CounselorDeliveryChecklist"),
  "GameMatrixView should render CounselorDeliveryChecklist"
);

console.log("CounselorDeliveryChecklist smoke assertions passed");

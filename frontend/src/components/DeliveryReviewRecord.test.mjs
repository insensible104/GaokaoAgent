import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const componentPath = path.join(__dirname, "DeliveryReviewRecord.tsx");
const helperPath = path.join(__dirname, "..", "lib", "deliveryReviewRecord.ts");
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
  "buildDeliveryReviewRecord",
  "DeliveryReviewRecordSnapshot",
  "delivery_review_record_v1",
  "review_record",
  "versionStamp",
  "copyText",
  "blocked_items",
  "review_items",
  "不生成新的录取结论",
  "不替代签字确认",
].forEach((token) => {
  assert(helper.includes(token), `helper should include ${token}`);
});

[
  "DeliveryReviewRecord",
  "交付复核记录",
  "版本快照",
  "复制记录",
  "复核记录",
  "阻断项",
  "待复核项",
  "证据边界",
].forEach((token) => {
  assert(component.includes(token), `component should include ${token}`);
});

assert(
  gameMatrix.includes("DeliveryReviewRecord") &&
    gameMatrix.includes("<DeliveryReviewRecord"),
  "GameMatrixView should render DeliveryReviewRecord"
);

console.log("DeliveryReviewRecord smoke assertions passed");

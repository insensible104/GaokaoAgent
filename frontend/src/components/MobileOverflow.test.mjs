import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const reportSource = fs.readFileSync(path.join(here, "ReportView.tsx"), "utf8");
const matrixSource = fs.readFileSync(path.join(here, "GameMatrixView.tsx"), "utf8");

assert.match(
  reportSource,
  /\[overflow-wrap:anywhere\]/,
  "generated report and debug text must wrap unbroken machine tokens on mobile"
);
assert.match(
  matrixSource,
  /break-all/,
  "runtime policy identifiers must wrap instead of widening the mobile page"
);

console.log("mobile overflow smoke test passed");

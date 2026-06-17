import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(path.join(here, "ProgressTracker.tsx"), "utf8");

assert(source.includes("智能分析服务暂不可用，已切换到稳定量化方案"));
assert(source.includes("formatProgressMessage(step)"));
assert(!source.includes(">{step.message}</p>"));

console.log("ProgressTracker trust copy smoke test passed");

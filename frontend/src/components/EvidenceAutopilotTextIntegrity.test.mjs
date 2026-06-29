import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();

const scopedFiles = [
  "frontend/src/lib/evidenceAutopilotProvider.ts",
  "frontend/src/lib/evidenceAutopilotResultNormalizer.ts",
  "frontend/src/lib/evidenceAutopilotApi.ts",
  "backend/src/evidence_autopilot_api.py",
];

const mojibakeMarkers = [
  "锛",
  "榛",
  "鍚",
  "灏",
  "瀹",
  "寰",
  "鎶",
  "娌",
  "绛",
  "鏍",
  "璋",
  "鏂",
];

for (const file of scopedFiles) {
  const source = readFileSync(join(root, file), "utf8");
  for (const marker of mojibakeMarkers) {
    assert.equal(source.includes(marker), false, `${file} contains mojibake marker ${marker}`);
  }
}

const normalizer = readFileSync(join(root, "frontend/src/lib/evidenceAutopilotResultNormalizer.ts"), "utf8");
assert.match(normalizer, /黑名单/);
assert.match(normalizer, /校区冲突/);
assert.match(normalizer, /调剂风险/);
assert.match(normalizer, /投诉/);

const provider = readFileSync(join(root, "frontend/src/lib/evidenceAutopilotProvider.ts"), "utf8");
assert.match(provider, /半封闭/);
assert.match(provider, /人工采集原文/);

const backend = readFileSync(join(root, "backend/src/evidence_autopilot_api.py"), "utf8");
assert.match(backend, /后端只生成可审计研究任务/);
assert.match(backend, /不会承诺录取、升学或就业结果/);
assert.match(backend, /微信、Boss 等半封闭渠道/);

console.log("Evidence Autopilot text integrity test passed");

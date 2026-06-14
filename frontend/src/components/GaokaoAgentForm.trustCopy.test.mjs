import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("./GaokaoAgentForm.tsx", import.meta.url), "utf8");

assert.doesNotMatch(source, /正态分布概率计算/);
assert.match(source, /历史位次区间/);
assert.match(source, /数据年份透明/);

console.log("GaokaoAgentForm trust copy smoke test passed");

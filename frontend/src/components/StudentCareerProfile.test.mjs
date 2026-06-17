import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const component = await readFile(new URL("./StudentCareerProfile.tsx", import.meta.url), "utf8");
const form = await readFile(new URL("./GaokaoAgentForm.tsx", import.meta.url), "utf8");

for (const token of [
  "跳过测评",
  "12题快速版",
  "30题完整版",
  "职业兴趣探索",
  "RIASEC",
  "仅用于沟通和自我描述，不决定专业",
  "最多选择 3 项",
  "career_values",
  "mbti_type",
  "R1",
  "I1",
  "A1",
  "S1",
  "E1",
  "C1",
]) {
  assert(component.includes(token), `StudentCareerProfile should contain ${token}`);
}

assert.match(form, /StudentCareerProfile/);
assert.match(form, /career_assessment/);
assert.match(form, /isCareerAssessmentComplete/);

console.log("StudentCareerProfile smoke test passed");

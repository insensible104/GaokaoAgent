import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import assert from "node:assert/strict";

const __dirname = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(__dirname, "GameMatrixView.tsx"), "utf8");

for (const token of [
  "volunteer_plan",
  "expected_admission_prob",
  "first_hit_prob",
  "quant_score",
  "quant_evidence",
  "核心推荐证据链",
  "data_vintage",
  "formal_recommendation_ready",
  "admission_probability_lower_bound",
  "admission_probability_upper_bound",
  "probability_warning",
  "数据适用边界",
  "启发式命中区间",
  "decision_trace",
  "推荐依据",
  "主要风险",
  "coverage_report",
  "capacity_fill",
  "原冲稳保标签未改",
  "目标配比",
  "实际入选",
  "候选缺口",
  "plan_change_explanation",
  'planChange.status !== "none"',
  'sortBy === "choice"',
  '<option value="choice">志愿顺序</option>',
  "方案变化",
  "方案变化证据",
  "历史校准单组命中率",
  "历史校准命中区间",
  "原始历史模拟",
  "最高单组历史校准命中率",
  "probability_calibration_year",
  "影响排序",
  "本次方案已锁定的显式偏好",
  "优先级高于系统从对话中的推断",
  "field_provenance",
  "不接受专业",
  "职业兴趣与价值观档案",
  "RIASEC 仅参与专业方向的辅助排序",
  "MBTI 仅用于沟通和自我描述",
  "career_values",
  "riasec_top_codes",
  "志愿表审计工作台",
  "方案对比",
  "auditItems",
  "plan_audit_summary",
  "comparisonSignals",
  "keyPrefixAudit",
  "shadowedAudit",
  "CounselorDeliveryChecklist",
  "ExternalPlanComparator",
]) {
  assert(
    source.includes(token),
    `GameMatrixView should expose recommendation quant evidence token: ${token}`,
  );
}

console.log("GameMatrixView quant evidence smoke test passed");

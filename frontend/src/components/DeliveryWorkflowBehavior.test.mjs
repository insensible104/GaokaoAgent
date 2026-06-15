import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const libDir = path.join(here, "..", "lib");

function loadTsModule(filePath, mocks = {}) {
  const source = fs.readFileSync(filePath, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      esModuleInterop: true,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (mocks[specifier]) return mocks[specifier];
    throw new Error(`Unexpected require: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const externalAudit = loadTsModule(path.join(libDir, "externalPlanAudit.ts"));
const checklist = loadTsModule(path.join(libDir, "counselorDeliveryChecklist.ts"));
const reviewRecord = loadTsModule(path.join(libDir, "deliveryReviewRecord.ts"), {
  "./counselorDeliveryChecklist": checklist,
});

const gameMatrix = {
  major_group_rows: [
    {
      school_name: "华南理工大学",
      major_group_code: "202",
      strategy_tag: "rush",
      is_key_prefix: true,
      quant_evidence: ["historical rank evidence"],
    },
    {
      school_name: "广东工业大学",
      major_group_code: "205",
      strategy_tag: "target",
      quant_evidence: ["fit evidence"],
    },
    {
      school_name: "佛山科学技术学院",
      major_group_code: "204",
      strategy_tag: "safe",
      prefix_role: "safety_anchor",
      quant_evidence: ["safety evidence"],
    },
  ],
  data_vintage: {
    formal_recommendation_ready: false,
    limitations: ["2026 当前年招生/录取数据仍不完整"],
  },
  volunteer_plan: {
    key_prefix_count: 1,
    shadowed_choice_count: 1,
    blacklist_violation_count: 0,
  },
  plan_audit_summary: {
    key_prefix: { count: 1 },
    coverage: { coverage_sufficient: true, deficits: {} },
    data_boundary: {
      formal_recommendation_ready: false,
      limitations: ["2026 当前年招生/录取数据仍不完整"],
    },
    student_facing_items: [{ title: "data boundary", severity: "review" }],
  },
};

const userProfile = {
  score: 610,
  rank: 52000,
  subject_group: "物化生",
  field_provenance: {
    preferred_cities: "user_explicit",
    blacklist_majors: "user_explicit",
  },
};

const externalPlanAuditSummary = externalAudit.auditExternalPlan({
  gameMatrix,
  text: [
    "冲 华南理工大学 专业组 202",
    "稳 广东工业大学 专业组 205",
    "保 假设大学 专业组 999",
  ].join("\n"),
});

assert.equal(externalPlanAuditSummary.parsedCount, 3);
assert.equal(externalPlanAuditSummary.unmatchedEntries.length, 1);

const checklistSummary = checklist.buildCounselorDeliveryChecklist({
  gameMatrix,
  userProfile,
  externalPlanAuditSummary,
});

const externalItem = checklistSummary.items.find((item) => item.id === "external_comparison");
assert.equal(externalItem?.status, "needs_review");
assert.match(externalItem?.evidence ?? "", /未匹配 1 行/);
assert.match(externalItem?.action ?? "", /外部方案未匹配条目/);

const record = reviewRecord.buildDeliveryReviewRecord({
  gameMatrix,
  userProfile,
  externalPlanAuditSummary,
  generatedAt: "2026-06-15T10:30:00+08:00",
  operatorName: "顾问A",
});

assert.equal(record.metrics.review_items > 0, true);
assert.match(record.copyText, /外部方案对照/);
assert.match(record.copyText, /未匹配 1 行/);
assert.match(record.copyText, /不生成新的录取结论/);

console.log("Delivery workflow behavior test passed");

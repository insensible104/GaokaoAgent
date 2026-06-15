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

const checklist = loadTsModule(path.join(libDir, "counselorDeliveryChecklist.ts"));
const reviewRecord = loadTsModule(path.join(libDir, "deliveryReviewRecord.ts"), {
  "./counselorDeliveryChecklist": checklist,
});
const caseStatus = loadTsModule(path.join(libDir, "deliveryCaseStatus.ts"), {
  "./counselorDeliveryChecklist": checklist,
  "./deliveryReviewRecord": reviewRecord,
});

const externalPlanAuditSummary = {
  protocol: "external_plan_audit_v1",
  metricKeys: {
    overlapRate: "overlap_rate",
    unmatchedEntries: "unmatched_entries",
    strategyMix: "strategy_mix",
  },
  parsedCount: 4,
  matchedCount: 2,
  overlapRate: 0.5,
  unmatchedEntries: [{ schoolName: "External U", normalizedKey: "externalu#999" }],
  duplicateEntries: [{ schoolName: "Duplicate U", normalizedKey: "duplicateu#111" }],
  strategyMix: { rush: 1, target: 1, safe: 0, unknown: 2 },
  findings: [{ severity: "review", type: "unmatched_entries", title: "unmatched", detail: "", action: "" }],
  claimBoundary: "External comparison is a review input only.",
};

const gameMatrix = {
  major_group_rows: [
    {
      school_name: "South China Tech",
      major_group_code: "202",
      strategy_tag: "rush",
      is_key_prefix: true,
      quant_evidence: ["rank evidence"],
    },
    {
      school_name: "Guangdong Industry",
      major_group_code: "205",
      strategy_tag: "target",
      quant_evidence: ["fit evidence"],
    },
  ],
  data_vintage: {
    formal_recommendation_ready: false,
    limitations: ["2026 official admission data is incomplete"],
  },
  volunteer_plan: {
    key_prefix_count: 1,
    shadowed_choice_count: 0,
    blacklist_violation_count: 0,
  },
  plan_audit_summary: {
    key_prefix: { count: 1 },
    coverage: { coverage_sufficient: true, deficits: {} },
    data_boundary: {
      formal_recommendation_ready: false,
      limitations: ["2026 official admission data is incomplete"],
    },
    student_facing_items: [{ title: "data boundary", severity: "review" }],
  },
};

const userProfile = {
  score: 610,
  rank: 52000,
  subject_group: "physics",
  field_provenance: {
    preferred_cities: "user_explicit",
    blacklist_majors: "user_explicit",
  },
};

const status = caseStatus.buildDeliveryCaseStatus({
  caseId: "pf-2026-gd-0007",
  gameMatrix,
  userProfile,
  externalPlanCompared: true,
  externalPlanAuditSummary,
  reportReady: true,
  generatedAt: "2026-06-15T10:30:00+08:00",
  updatedAt: "2026-06-15T10:45:00+08:00",
  operatorName: "Counselor A",
  reviewer: "Lead Counselor",
  signoffState: "locked",
  parentConfirmationState: "confirmed",
});

assert.equal(status.protocol, "delivery_case_status_v1");
assert.equal(status.caseId, "pf-2026-gd-0007");
assert.equal(status.reviewer, "Lead Counselor");
assert.equal(status.status, "blocked");
assert.equal(status.workflowStage, "intake");
assert.equal(status.signoffState, "not_started");
assert.equal(status.parentConfirmationState, "requested");
assert.equal(status.externalAuditSummary?.parsedCount, 4);
assert.equal(status.externalAuditSummary?.unmatchedCount, 1);
assert.equal(status.externalAuditSummary?.duplicateCount, 1);
assert.equal(status.externalAuditSummary?.needsReview, true);
assert.equal(status.blockedItems.some((item) => item.id === "data_boundary"), true);
assert.equal(status.reviewItems.some((item) => item.id === "external_comparison"), true);
assert.equal(status.reviewRecord.protocol, "delivery_review_record_v1");
assert.equal(status.reviewRecord.metrics.blocked_items, status.blockedItems.length);
assert.match(status.claimBoundary, /operational workflow snapshot/);
assert.match(status.nextAction, /review|data|official|2026|formal/i);

console.log("Delivery case status behavior test passed");

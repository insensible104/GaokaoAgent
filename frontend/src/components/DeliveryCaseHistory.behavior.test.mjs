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
const caseHistory = loadTsModule(path.join(libDir, "deliveryCaseHistory.ts"), {
  "./deliveryCaseStatus": caseStatus,
});

const readyMatrix = {
  major_group_rows: [
    {
      school_name: "South China Tech",
      major_group_code: "202",
      strategy_tag: "target",
      is_key_prefix: true,
      quant_evidence: ["rank evidence", "fit evidence"],
    },
  ],
  data_vintage: {
    formal_recommendation_ready: true,
    limitations: [],
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
      formal_recommendation_ready: true,
      limitations: [],
    },
    student_facing_items: [{ title: "evidence", severity: "info" }],
  },
};

const profile = {
  score: 610,
  rank: 52000,
  subject_group: "physics",
  field_provenance: {
    preferred_cities: "user_explicit",
    blacklist_majors: "user_explicit",
  },
};

const previous = caseStatus.buildDeliveryCaseStatus({
  caseId: "pf-history-001",
  gameMatrix: readyMatrix,
  userProfile: profile,
  reportReady: false,
  generatedAt: "2026-06-15T09:00:00+08:00",
  updatedAt: "2026-06-15T09:15:00+08:00",
  signoffState: "counselor_reviewed",
});

const current = caseStatus.buildDeliveryCaseStatus({
  caseId: "pf-history-001",
  gameMatrix: readyMatrix,
  userProfile: profile,
  reportReady: true,
  externalPlanCompared: true,
  externalPlanAuditSummary: {
    parsedCount: 2,
    matchedCount: 2,
    overlapRate: 1,
    unmatchedEntries: [],
    duplicateEntries: [],
    findings: [],
  },
  generatedAt: "2026-06-15T10:00:00+08:00",
  updatedAt: "2026-06-15T10:20:00+08:00",
  signoffState: "locked",
  parentConfirmationState: "confirmed",
});

const history = caseHistory.buildDeliveryCaseHistory({
  current,
  previous: [previous],
  actor: "Lead Counselor",
});

assert.equal(history.protocol, "delivery_case_history_v1");
assert.equal(history.caseId, "pf-history-001");
assert.equal(history.eventCount, 2);
assert.equal(history.currentStage, "locked");
assert.equal(history.lockReady, true);
assert.deepEqual(history.missingBeforeLock, []);
assert.equal(history.events[0].type, "counselor_review");
assert.equal(history.events[1].type, "case_locked");
assert.equal(history.events[1].actor, "Lead Counselor");
assert.match(history.claimBoundary, /audit trail contract/);

console.log("Delivery case history behavior test passed");

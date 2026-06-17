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
const caseEventStore = loadTsModule(path.join(libDir, "deliveryCaseEventStore.ts"), {
  "./deliveryCaseStatus": caseStatus,
});

const baseMatrix = {
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

const readyMatrix = {
  ...baseMatrix,
  data_vintage: {
    formal_recommendation_ready: true,
    limitations: [],
  },
  plan_audit_summary: {
    ...baseMatrix.plan_audit_summary,
    data_boundary: {
      formal_recommendation_ready: true,
      limitations: [],
    },
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

const blocked = caseStatus.buildDeliveryCaseStatus({
  caseId: "pf-store-001",
  gameMatrix: baseMatrix,
  userProfile: profile,
  reportReady: false,
  generatedAt: "2026-06-15T09:00:00+08:00",
  updatedAt: "2026-06-15T09:15:00+08:00",
  reviewer: "Lead Counselor",
});

const ready = caseStatus.buildDeliveryCaseStatus({
  caseId: "pf-store-001",
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
  reviewer: "Lead Counselor",
  signoffState: "locked",
  parentConfirmationState: "confirmed",
});

let store = caseEventStore.createDeliveryCaseEventStore("pf-store-001");
store = caseEventStore.recordDeliveryCaseStatusEvent({
  store,
  status: blocked,
  actor: "Lead Counselor",
  createdAt: "2026-06-15T09:15:00+08:00",
});
store = caseEventStore.recordDeliveryCaseStatusEvent({
  store,
  status: ready,
  actor: "Lead Counselor",
  createdAt: "2026-06-15T10:20:00+08:00",
});

assert.equal(store.protocol, "delivery_case_event_store_v1");
assert.equal(store.caseId, "pf-store-001");
assert.equal(store.eventCount, 2);
assert.equal(store.events[0].sequence, 1);
assert.equal(store.events[1].sequence, 2);
assert.equal(store.events[0].eventType, "status_snapshot");
assert.equal(store.events[1].eventType, "case_locked");
assert.equal(store.events[1].payload.signoffState, "locked");
assert.equal(store.events[1].payload.parentConfirmationState, "confirmed");
assert.match(store.events[1].checksum, /^pf-store-001:/);
assert.equal(store.lockReady, true);
assert.deepEqual(store.missingBeforeLock, []);

const serialized = caseEventStore.serializeDeliveryCaseEventStore(store);
const parsed = caseEventStore.parseDeliveryCaseEventStore(serialized);
assert.deepEqual(parsed, store);

const replay = caseEventStore.replayDeliveryCaseEventStore(parsed);
assert.equal(replay.caseId, "pf-store-001");
assert.equal(replay.currentStage, "locked");
assert.equal(replay.eventCount, 2);
assert.equal(replay.lockReady, true);
assert.equal(replay.events[1].type, "case_locked");

assert.throws(
  () =>
    caseEventStore.recordDeliveryCaseStatusEvent({
      store,
      status: { ...ready, caseId: "pf-store-002" },
      actor: "Lead Counselor",
    }),
  /caseId mismatch/,
);

console.log("Delivery case event store behavior test passed");

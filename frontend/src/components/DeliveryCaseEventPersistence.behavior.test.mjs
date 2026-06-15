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
const eventStore = loadTsModule(path.join(libDir, "deliveryCaseEventStore.ts"), {
  "./deliveryCaseStatus": caseStatus,
});
const persistence = loadTsModule(path.join(libDir, "deliveryCaseEventPersistence.ts"), {
  "./deliveryCaseEventStore": eventStore,
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

const lockedStatus = caseStatus.buildDeliveryCaseStatus({
  caseId: "pf-persist-001",
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

const memory = persistence.createMemoryDeliveryCaseEventPersistence();
assert.equal(await memory.load("pf-persist-001"), null);

const saved = await memory.appendStatusEvent({
  caseId: "pf-persist-001",
  status: lockedStatus,
  actor: "Lead Counselor",
  createdAt: "2026-06-15T10:20:00+08:00",
});
assert.equal(saved.eventCount, 1);
assert.equal(saved.lockReady, true);
assert.deepEqual(await memory.listCaseIds(), ["pf-persist-001"]);
assert.deepEqual(await memory.load("pf-persist-001"), saved);

await memory.clear("pf-persist-001");
assert.equal(await memory.load("pf-persist-001"), null);
assert.deepEqual(await memory.listCaseIds(), []);

const backing = new Map();
const fakeStorage = {
  getItem: (key) => backing.get(key) ?? null,
  setItem: (key, value) => backing.set(key, value),
  removeItem: (key) => backing.delete(key),
  key: (index) => Array.from(backing.keys())[index] ?? null,
  get length() {
    return backing.size;
  },
};

const browserAdapter = persistence.createBrowserStorageDeliveryCaseEventPersistence({
  storage: fakeStorage,
  namespace: "pf-test",
});
const browserSaved = await browserAdapter.appendStatusEvent({
  caseId: "pf-persist-001",
  status: lockedStatus,
  actor: "Lead Counselor",
});

assert.equal(backing.has("pf-test:pf-persist-001"), true);
assert.deepEqual(await browserAdapter.load("pf-persist-001"), browserSaved);
assert.deepEqual(await browserAdapter.listCaseIds(), ["pf-persist-001"]);

backing.set("pf-test:broken", JSON.stringify({ protocol: "wrong" }));
await assert.rejects(() => browserAdapter.load("broken"), /invalid delivery case event store protocol/);

await assert.rejects(
  () =>
    browserAdapter.appendStatusEvent({
      caseId: "pf-persist-002",
      status: lockedStatus,
      actor: "Lead Counselor",
    }),
  /caseId mismatch/,
);

console.log("Delivery case event persistence behavior test passed");

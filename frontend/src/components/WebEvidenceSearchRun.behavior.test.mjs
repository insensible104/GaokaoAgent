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

const worksheet = loadTsModule(path.join(libDir, "webEvidenceCaptureWorksheet.ts"), {
  "./evidenceCollectionWorkspace": {},
  "./webEvidenceIntake": {},
});
const adapter = loadTsModule(path.join(libDir, "webEvidenceSearchAdapter.ts"), {
  "./evidenceCollectionWorkspace": {},
  "./webEvidenceCaptureWorksheet": worksheet,
});
const searchRun = loadTsModule(path.join(libDir, "webEvidenceSearchRun.ts"), {
  "./webEvidenceSearchAdapter": adapter,
  "./webEvidenceIntake": {},
});

const workspace = {
  taskRows: [
    taskRow({
      taskId: "official-plan",
      taskType: "official_plan_verification",
      status: "accepted",
      sourceTier: "official",
      claims: ["official_diff"],
    }),
    taskRow({
      taskId: "rank-history",
      taskType: "rank_history_calibration",
      status: "needs_capture",
      sourceTier: "historical_data",
      claims: ["rank_delta"],
      domains: ["eea.gd.gov.cn", "gaokao.chsi.com.cn"],
    }),
    taskRow({
      taskId: "school-rule",
      taskType: "school_rule_verification",
      status: "needs_capture",
      sourceTier: "official",
      claims: ["risk_guard"],
      domains: ["admission.example.edu.cn"],
    }),
    taskRow({
      taskId: "external-plan",
      taskType: "external_plan_comparison",
      status: "needs_capture",
      sourceTier: "competitor_plan",
      claims: ["competitor_missed"],
      domains: ["example.com"],
    }),
    taskRow({
      taskId: "public-opinion",
      taskType: "public_opinion_scan",
      status: "needs_capture",
      sourceTier: "public_opinion",
      claims: ["hypothesis_only"],
      domains: ["zhihu.com", "xiaohongshu.com"],
    }),
  ],
};

const run = searchRun.buildWebEvidenceSearchRun({
  workspace,
  capturedAt: "2026-06-16",
  responses: [
    {
      taskId: "rank-history",
      provider: "browser-search",
      results: [
        {
          title: "Guangdong rank history table",
          url: "https://eea.gd.gov.cn/rank-history",
          snippet: "2025 rank 42000; 2024 rank 43800 for the same school group.",
          sourceTier: "historical_data",
          claimedSupports: ["rank_delta"],
        },
      ],
    },
    {
      taskId: "external-plan",
      provider: "browser-search",
      results: [
        {
          title: "Forum discussion",
          url: "https://example.com/forum",
          snippet: "A parent says the row is guaranteed.",
          sourceTier: "public_opinion",
          claimedSupports: ["competitor_missed"],
        },
      ],
    },
    {
      taskId: "public-opinion",
      requestId: "public-opinion-counter_evidence",
      provider: "browser-search",
      results: [
        {
          title: "Counter evidence discussion",
          url: "https://zhihu.com/question/counter",
          snippet: "Many families already discuss the quota expansion and recognize this school group.",
          sourceTier: "public_opinion",
          claimedSupports: ["hypothesis_only"],
        },
      ],
    },
  ],
});

assert.equal(run.protocol, "web_evidence_search_run_v1");
assert.equal(run.status, "partial_success");
assert.equal(run.requestBatch.protocol, "web_evidence_search_requests_v1");
assert.deepEqual(
  run.requestBatch.requests.map((request) => request.taskId),
  [
    "rank-history",
    "school-rule",
    "external-plan",
    "public-opinion",
    "public-opinion",
    "public-opinion",
    "public-opinion",
    "public-opinion",
  ],
);
assert.equal(run.requestBatch.requests.some((request) => request.requestId === "public-opinion-counter_evidence"), true);
assert.equal(run.requestBatch.requests.some((request) => request.searchIntent === "counter_evidence"), true);
assert.equal(run.providerResponseCount, 3);
assert.equal(run.acceptedEvidenceResults.length, 2);
assert.equal(run.acceptedEvidenceResults[0].taskId, "rank-history");
assert.equal(run.acceptedEvidenceResults[0].sourceTier, "historical_data");
assert.equal(run.rejectedAdapterResults.length, 1);
assert.match(run.rejectedAdapterResults[0].reason, /source tier public_opinion does not match required competitor_plan/);
assert.deepEqual(run.unreturnedTaskIds, ["school-rule", "public-opinion"]);
assert.equal(run.searchTrace.protocol, "web_evidence_search_trace_v1");
assert.equal(run.searchTrace.rows.length >= 8, true);
assert.equal(run.searchTrace.rows[0].taskId, "rank-history");
assert.equal(run.searchTrace.rows[0].provider, "browser-search");
assert.match(run.searchTrace.rows[0].query, /rank_history_calibration rank-history query/);
assert.equal(run.searchTrace.rows[0].sourceUrl, "https://eea.gd.gov.cn/rank-history");
assert.deepEqual(run.searchTrace.rows[0].claimedSupports, ["rank_delta"]);
assert.equal(run.searchTrace.rows[1].taskId, "external-plan");
assert.match(run.searchTrace.rows[1].rejectionReason, /source tier public_opinion/);
const publicOpinionTrace = run.searchTrace.rows.find((row) => row.requestId === "public-opinion-counter_evidence");
assert.ok(publicOpinionTrace);
assert.equal(publicOpinionTrace.searchIntent, "counter_evidence");
assert.match(publicOpinionTrace.evidenceQuestion, /disprove/i);
assert.match(publicOpinionTrace.rejectsAsProof.join("\n"), /official plan/i);
assert.equal(publicOpinionTrace.outcome, "accepted");
assert.equal(run.searchTrace.rows.some((row) => row.taskId === "school-rule" && row.outcome === "unreturned"), true);
assert.equal(run.searchTrace.rows.some((row) => row.taskId === "public-opinion" && row.searchIntent === "hype_pressure" && row.outcome === "unreturned"), true);
assert.match(run.nextActions.join("\n"), /Attach 2 normalized evidence results/);
assert.match(run.nextActions.join("\n"), /Manually capture or rerun search for school-rule/);
assert.match(run.nextActions.join("\n"), /Review rejected provider results/);
assert.match(run.claimBoundary, /Search runs collect candidate evidence/);

const emptyRun = searchRun.buildWebEvidenceSearchRun({
  workspace,
  capturedAt: "2026-06-16",
  responses: [],
});

assert.equal(emptyRun.status, "no_results");
assert.equal(emptyRun.acceptedEvidenceResults.length, 0);
assert.deepEqual(emptyRun.unreturnedTaskIds, ["rank-history", "school-rule", "external-plan", "public-opinion"]);
assert.equal(emptyRun.searchTrace.rows.filter((row) => row.outcome === "unreturned").length, 8);

function taskRow({ taskId, taskType, status, sourceTier, claims, domains = ["example.com"] }) {
  return {
    taskId,
    taskType,
    priority: "blocking",
    status,
    acceptedEvidenceCount: status === "accepted" ? 1 : 0,
    rejectedEvidenceCount: 0,
    primaryQuery: `${taskType} ${taskId} query`,
    preferredDomains: domains,
    operatorChecklist: ["capture row-level evidence"],
    mustReject: ["reject unsupported claims"],
    resultTemplate: {
      taskId,
      sourceTier,
      claimedSupports: claims,
      excerptsRequired: true,
    },
  };
}

console.log("Web evidence search run behavior test passed");

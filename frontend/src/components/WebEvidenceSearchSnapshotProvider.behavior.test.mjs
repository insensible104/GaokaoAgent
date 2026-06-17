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
const runModule = loadTsModule(path.join(libDir, "webEvidenceSearchRun.ts"), {
  "./webEvidenceSearchAdapter": adapter,
  "./webEvidenceIntake": {},
});
const providerExecution = loadTsModule(path.join(libDir, "webEvidenceSearchProvider.ts"), {
  "./webEvidenceSearchAdapter": adapter,
  "./webEvidenceSearchRun": runModule,
});
const snapshotProviderModule = loadTsModule(path.join(libDir, "webEvidenceSearchSnapshotProvider.ts"), {
  "./webEvidenceSearchAdapter": adapter,
  "./webEvidenceSearchProvider": providerExecution,
});

const documents = [
  {
    title: "Guangdong 2026 official enrollment plan",
    url: "https://eea.gd.gov.cn/plan/2026",
    snippet: "10561 major group 201 Computer Science quota 36 subject physics chemistry.",
  },
  {
    title: "Blog repost of Guangdong enrollment plan",
    url: "https://blog.example.com/plan-copy",
    snippet: "A copied table says Computer Science quota 36.",
  },
  {
    title: "Parent discussion about non-local engineering",
    url: "https://www.zhihu.com/question/example",
    snippet: "Parents mostly discuss local brands and avoid non-local engineering groups.",
  },
  {
    title: "Unrelated campus food post",
    url: "https://forum.example.com/food",
    snippet: "Campus dining and dormitory discussion.",
  },
];

const provider = snapshotProviderModule.createWebEvidenceSearchSnapshotProvider({
  id: "browser-snapshot",
  documents,
});

const officialResults = await provider.search({
  taskId: "official-plan",
  taskType: "official_plan_verification",
  query: "Guangdong 2026 official enrollment plan 10561 Computer Science quota",
  domains: ["eea.gd.gov.cn"],
  sourceTier: "official",
  allowedClaims: ["official_diff"],
  maxResults: 3,
});

assert.equal(provider.id, "browser-snapshot");
assert.equal(officialResults.length, 2);
assert.equal(officialResults[0].title, "Guangdong 2026 official enrollment plan");
assert.equal(officialResults[0].sourceTier, "official");
assert.deepEqual(officialResults[0].claimedSupports, ["official_diff"]);
assert.match(officialResults[0].excerpts[0], /quota 36/);
assert.equal(officialResults[1].sourceTier, "public_opinion");

const publicOpinionResults = await provider.search({
  taskId: "public-opinion",
  taskType: "public_opinion_scan",
  query: "non-local engineering parents avoid local brands",
  domains: ["zhihu.com", "xiaohongshu.com"],
  sourceTier: "public_opinion",
  allowedClaims: ["hypothesis_only"],
  maxResults: 2,
});

assert.equal(publicOpinionResults.length, 1);
assert.equal(publicOpinionResults[0].sourceTier, "public_opinion");
assert.deepEqual(publicOpinionResults[0].claimedSupports, ["hypothesis_only"]);
assert.match(publicOpinionResults[0].snippet, /local brands/);

const execution = await providerExecution.executeWebEvidenceSearchProvider({
  workspace: {
    taskRows: [
      taskRow({
        taskId: "official-plan",
        taskType: "official_plan_verification",
        sourceTier: "official",
        claims: ["official_diff"],
        query: "Guangdong 2026 official enrollment plan 10561 Computer Science quota",
        domains: ["eea.gd.gov.cn"],
      }),
      taskRow({
        taskId: "public-opinion",
        taskType: "public_opinion_scan",
        sourceTier: "public_opinion",
        claims: ["hypothesis_only"],
        query: "non-local engineering parents avoid local brands",
        domains: ["zhihu.com", "xiaohongshu.com"],
      }),
    ],
  },
  provider,
  capturedAt: "2026-06-16",
});

assert.equal(execution.status, "partial_success");
assert.equal(execution.requestBatch.requests.filter((request) => request.taskId === "public-opinion").length, 5);
assert.equal(execution.providerResponses.some((response) => response.requestId === "public-opinion-counter_evidence"), true);
assert.equal(execution.searchRun.searchTrace.rows.some((row) => row.searchIntent === "counter_evidence"), true);
assert.equal(execution.searchRun.searchTrace.rows.some((row) => /disprove/i.test(row.evidenceQuestion ?? "")), true);
assert.equal(execution.searchRun.acceptedEvidenceResults.length >= 5, true);
assert.equal(execution.searchRun.rejectedAdapterResults.length, 1);
assert.match(execution.searchRun.rejectedAdapterResults[0].reason, /source tier public_opinion does not match required official/);
assert.match(execution.claimBoundary, /candidate evidence/);

function taskRow({ taskId, taskType, sourceTier, claims, query, domains }) {
  return {
    taskId,
    taskType,
    priority: taskType === "public_opinion_scan" ? "context" : "blocking",
    status: "needs_capture",
    acceptedEvidenceCount: 0,
    rejectedEvidenceCount: 0,
    primaryQuery: query,
    preferredDomains: domains,
    operatorChecklist: ["capture evidence"],
    mustReject: ["reject unsupported claims"],
    resultTemplate: {
      taskId,
      sourceTier,
      claimedSupports: claims,
      excerptsRequired: true,
    },
  };
}

console.log("Web evidence search snapshot provider behavior test passed");

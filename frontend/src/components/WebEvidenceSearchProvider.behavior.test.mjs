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
const providerModule = loadTsModule(path.join(libDir, "webEvidenceSearchProvider.ts"), {
  "./webEvidenceSearchAdapter": adapter,
  "./webEvidenceSearchRun": runModule,
});

const calls = [];
const execution = await providerModule.executeWebEvidenceSearchProvider({
  workspace: {
    taskRows: [
      taskRow({ taskId: "official-plan", status: "accepted", sourceTier: "official", claims: ["official_diff"] }),
      taskRow({ taskId: "rank-history", status: "needs_capture", sourceTier: "historical_data", claims: ["rank_delta"] }),
      taskRow({ taskId: "school-rule", status: "needs_capture", sourceTier: "official", claims: ["risk_guard"] }),
      taskRow({ taskId: "external-plan", status: "needs_capture", sourceTier: "competitor_plan", claims: ["competitor_missed"] }),
    ],
  },
  capturedAt: "2026-06-16",
  provider: {
    id: "fake-live-search",
    search: async (request) => {
      calls.push(request.taskId);
      if (request.taskId === "school-rule") {
        throw new Error("provider timeout");
      }
      if (request.taskId === "external-plan") {
        return [];
      }
      return [
        {
          title: "Rank history result",
          url: "https://eea.gd.gov.cn/rank-history",
          snippet: "2025 rank 42000; 2024 rank 43800.",
          sourceTier: request.sourceTier,
          claimedSupports: request.allowedClaims,
        },
      ];
    },
  },
});

assert.equal(execution.protocol, "web_evidence_search_provider_execution_v1");
assert.equal(execution.providerId, "fake-live-search");
assert.equal(execution.status, "partial_success");
assert.deepEqual(calls, ["rank-history", "school-rule", "external-plan"]);
assert.deepEqual(
  execution.requestBatch.requests.map((request) => request.taskId),
  ["rank-history", "school-rule", "external-plan"],
);
assert.equal(execution.providerResponses.length, 2);
assert.equal(execution.failedRequests.length, 1);
assert.equal(execution.failedRequests[0].taskId, "school-rule");
assert.match(execution.failedRequests[0].reason, /provider timeout/);
assert.equal(execution.searchRun.protocol, "web_evidence_search_run_v1");
assert.equal(execution.searchRun.status, "partial_success");
assert.equal(execution.searchRun.acceptedEvidenceResults.length, 1);
assert.equal(execution.searchRun.unreturnedTaskIds.includes("school-rule"), true);
assert.match(execution.nextActions.join("\n"), /Retry failed provider requests for school-rule/);
assert.match(execution.nextActions.join("\n"), /Manually capture or rerun search/);
assert.match(execution.claimBoundary, /Provider execution retrieves candidate evidence/);

function taskRow({ taskId, status, sourceTier, claims }) {
  return {
    taskId,
    taskType: taskId === "rank-history"
      ? "rank_history_calibration"
      : taskId === "school-rule"
        ? "school_rule_verification"
        : taskId === "external-plan"
          ? "external_plan_comparison"
          : "official_plan_verification",
    priority: "blocking",
    status,
    acceptedEvidenceCount: status === "accepted" ? 1 : 0,
    rejectedEvidenceCount: 0,
    primaryQuery: `${taskId} query`,
    preferredDomains: ["example.com"],
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

console.log("Web evidence search provider behavior test passed");

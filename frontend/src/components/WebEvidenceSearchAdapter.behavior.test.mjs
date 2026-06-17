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
  "./webEvidenceCaptureWorksheet": {},
  "./webEvidenceIntake": {},
  "./webEvidencePlanner": {},
});
const adapter = loadTsModule(path.join(libDir, "webEvidenceSearchAdapter.ts"), {
  "./evidenceCollectionWorkspace": {},
  "./webEvidenceCaptureWorksheet": worksheet,
});

const workspace = {
  taskRows: [
    {
      taskId: "official-plan",
      taskType: "official_plan_verification",
      priority: "blocking",
      status: "needs_capture",
      acceptedEvidenceCount: 0,
      rejectedEvidenceCount: 0,
      primaryQuery: "site:eea.gd.gov.cn Guangdong 2026 official enrollment catalog quota major group",
      preferredDomains: ["eea.gd.gov.cn", "gd.gov.cn"],
      operatorChecklist: ["row-level school code and quota"],
      mustReject: ["Reject public-opinion or reposted plan tables as support for official_diff."],
      resultTemplate: {
        taskId: "official-plan",
        sourceTier: "official",
        claimedSupports: ["official_diff"],
        excerptsRequired: true,
      },
    },
    {
      taskId: "public-opinion",
      taskType: "public_opinion_scan",
      priority: "context",
      status: "needs_capture",
      acceptedEvidenceCount: 0,
      rejectedEvidenceCount: 0,
      primaryQuery: "South China Tech Computer Science low attention avoidance parent discussion",
      preferredDomains: ["zhihu.com", "xiaohongshu.com"],
      operatorChecklist: ["attention level and counter-evidence"],
      mustReject: ["Reject public-opinion evidence as proof of official plan changes."],
      resultTemplate: {
        taskId: "public-opinion",
        sourceTier: "public_opinion",
        claimedSupports: ["hypothesis_only"],
        excerptsRequired: true,
      },
    },
    {
      taskId: "rank-history",
      taskType: "rank_history_calibration",
      priority: "blocking",
      status: "accepted",
      acceptedEvidenceCount: 1,
      rejectedEvidenceCount: 0,
      primaryQuery: "South China Tech Computer Science Guangdong 2025 2024 admission rank",
      preferredDomains: ["eea.gd.gov.cn", "gaokao.chsi.com.cn"],
      operatorChecklist: ["2024 and 2025 admission rank or score lines for the same school and group"],
      mustReject: ["Reject sources that are not historical_data tier for this task."],
      resultTemplate: {
        taskId: "rank-history",
        sourceTier: "historical_data",
        claimedSupports: ["rank_delta"],
        excerptsRequired: true,
      },
    },
  ],
  evidenceGapSearchPlan: {
    protocol: "evidence_gap_search_plan_v1",
    status: "ready_to_search",
    followUps: [
      {
        id: "rank-history-needs_second_source-follow-up",
        claim: "rank_delta",
        taskId: "rank-history",
        taskType: "rank_history_calibration",
        gapStatus: "needs_second_source",
        priority: "blocking",
        sourceTier: "historical_data",
        query: "South China Tech Computer Science Guangdong 2025 2024 admission rank second independent source -site:data.example",
        domains: ["eea.gd.gov.cn", "gaokao.chsi.com.cn"],
        existingSourceHosts: ["data.example"],
        reason: "rank_delta has only one independent source host.",
        nextActions: ["Attach a second independent source for rank_delta."],
        blocksCounselorReview: true,
      },
    ],
    claimBoundary: "Evidence gap search plans turn triangulation gaps into follow-up searches.",
  },
};

const requests = adapter.buildWebEvidenceSearchRequests({ workspace, maxResultsPerTask: 5 });

assert.equal(requests.protocol, "web_evidence_search_requests_v1");
assert.equal(requests.requests.length >= 7, true);
assert.equal(requests.requests[0].taskId, "official-plan");
assert.equal(requests.requests[0].query.includes("site:eea.gd.gov.cn"), true);
assert.deepEqual(requests.requests[0].domains, ["eea.gd.gov.cn", "gd.gov.cn"]);
assert.equal(requests.requests[0].sourceTier, "official");
assert.deepEqual(requests.requests[0].allowedClaims, ["official_diff"]);
assert.equal(requests.requests[0].maxResults, 5);
const publicOpinionRequests = requests.requests.filter((request) => request.taskId === "public-opinion");
assert.equal(publicOpinionRequests.length >= 5, true);
assert.equal(publicOpinionRequests.some((request) => request.searchIntent === "low_attention_signal"), true);
assert.equal(publicOpinionRequests.some((request) => request.searchIntent === "counter_evidence"), true);
assert.equal(publicOpinionRequests.some((request) => request.searchIntent === "hype_pressure"), true);
assert.equal(publicOpinionRequests.some((request) => request.searchIntent === "regional_preference"), true);
assert.equal(publicOpinionRequests.every((request) => request.sourceTier === "public_opinion"), true);
assert.equal(publicOpinionRequests.every((request) => request.allowedClaims.length === 1 && request.allowedClaims[0] === "hypothesis_only"), true);
assert.match(publicOpinionRequests.map((request) => request.query).join("\n"), /counter-evidence|widely discussed|热度|冷门/i);
assert.match(publicOpinionRequests.map((request) => request.evidenceQuestion).join("\n"), /disprove|counter/i);
assert.match(publicOpinionRequests.map((request) => request.rejectsAsProof).join("\n"), /official plan|admission probability/i);
const gapRequest = requests.requests.find((request) => request.query.includes("second independent source"));
assert.ok(gapRequest);
assert.equal(gapRequest.taskId, "rank-history");
assert.equal(gapRequest.sourceTier, "historical_data");
assert.deepEqual(gapRequest.allowedClaims, ["rank_delta"]);
assert.deepEqual(gapRequest.domains, ["eea.gd.gov.cn", "gaokao.chsi.com.cn"]);
assert.match(requests.claimBoundary, /Search requests do not support claims/);

const normalized = adapter.normalizeWebEvidenceSearchAdapterResults({
  workspace,
  capturedAt: "2026-06-16",
  responses: [
    {
      taskId: "official-plan",
      provider: "manual-browser",
      results: [
        {
          title: "Guangdong official 2026 enrollment plan",
          url: "https://eea.gd.gov.cn/2026-plan",
          snippet: "10561 major group 201 Computer Science quota 36",
          sourceTier: "official",
          excerpts: ["10561 major group 201 Computer Science quota 36"],
          claimedSupports: ["official_diff"],
        },
        {
          title: "Blog repost of plan",
          url: "https://example.com/blog-plan",
          snippet: "reposted quota table",
          sourceTier: "public_opinion",
          excerpts: ["quota 36"],
          claimedSupports: ["official_diff"],
        },
      ],
    },
    {
      taskId: "public-opinion",
      provider: "manual-browser",
      results: [
        {
          title: "Parent discussion summary",
          url: "https://zhihu.com/question/example",
          snippet: "Families mostly discuss local brands and avoid non-local engineering groups.",
          sourceTier: "public_opinion",
          excerpts: ["Families mostly discuss local brands and avoid non-local engineering groups."],
        },
        {
          title: "Forum overclaim",
          url: "https://example.com/overclaim",
          snippet: "Guaranteed admission",
          sourceTier: "public_opinion",
          excerpts: ["Guaranteed admission"],
          claimedSupports: ["final_recommendation"],
        },
      ],
    },
  ],
});

assert.equal(normalized.protocol, "web_evidence_search_adapter_normalization_v1");
assert.equal(normalized.captureNormalization.evidenceResults.length, 2);
assert.deepEqual(
  normalized.captureNormalization.evidenceResults.map((item) => item.taskId),
  ["official-plan", "public-opinion"],
);
assert.equal(normalized.captureNormalization.evidenceResults[1].claimedSupports[0], "hypothesis_only");
assert.equal(normalized.rejectedAdapterResults.length, 2);
assert.match(normalized.rejectedAdapterResults.map((item) => item.reason).join("\n"), /source tier public_opinion does not match required official/);
assert.match(normalized.rejectedAdapterResults.map((item) => item.reason).join("\n"), /not allowed/);
assert.match(normalized.claimBoundary, /adapter normalization/i);

console.log("Web evidence search adapter behavior test passed");

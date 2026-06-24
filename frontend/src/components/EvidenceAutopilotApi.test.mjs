import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const apiPath = path.join(here, "..", "lib", "evidenceAutopilotApi.ts");
const planPath = path.join(here, "..", "lib", "deepEvidenceCollectionPlan.ts");
const providerPath = path.join(here, "..", "lib", "evidenceAutopilotProvider.ts");
const snapshotPath = path.join(here, "..", "lib", "evidenceAutopilotSnapshotProvider.ts");
const autopilotPath = path.join(here, "..", "lib", "evidenceAutopilot.ts");
const panelPath = path.join(here, "DeepOpportunityEvaluationPanel.tsx");

assert.equal(fs.existsSync(apiPath), true, "Evidence Autopilot API adapter should exist");
const apiSource = fs.readFileSync(apiPath, "utf8");
for (const token of ["attachments", "redactionStatus", "reviewerIdentity"]) {
  assert.match(apiSource, new RegExp(token), `API adapter should preserve reviewed evidence ${token}`);
}

function loadTsModule(source, requireMap = {}) {
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (requireMap[specifier]) return requireMap[specifier];
    throw new Error(`Unexpected require: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const provider = loadTsModule(fs.readFileSync(providerPath, "utf8"));
const snapshot = loadTsModule(fs.readFileSync(snapshotPath, "utf8"), {
  "./evidenceAutopilotProvider": provider,
});
const api = loadTsModule(fs.readFileSync(apiPath, "utf8"), {
  "./api": { buildApiUrl: (route) => `https://api.test${route}` },
  "./evidenceAutopilotSnapshotProvider": snapshot,
});
const planModule = loadTsModule(fs.readFileSync(planPath, "utf8"));
const autopilot = loadTsModule(fs.readFileSync(autopilotPath, "utf8"), {
  "./deepEvidenceCollectionPlan": planModule,
  "./deepOpportunityEvaluator": { buildDeepOpportunityEvaluation: () => ({}) },
  "./evidenceAutopilotResultNormalizer": { normalizeEvidenceAutopilotResults: () => [] },
});

assert.equal(typeof api.buildEvidenceAutopilotResearchPayload, "function");
assert.equal(typeof api.mapBackendEvidenceCardsToProviderResults, "function");
assert.equal(typeof api.fetchEvidenceAutopilotResearch, "function");
assert.equal(typeof api.buildEvidenceAutopilotSnapshotFallback, "function");
assert.equal(typeof api.fetchReviewedEvidenceRecords, "function");
assert.equal(typeof api.uploadReviewedEvidenceAttachment, "function");
assert.equal(typeof api.buildOperatorReviewedEvidenceCard, "function");
assert.equal(typeof api.submitReviewedEvidenceCard, "function");

const context = {
  province: "广东",
  schoolName: "华南理工示例校",
  majorName: "智能制造与数据工程",
  targetYear: 2026,
};
assert.deepEqual(api.buildEvidenceAutopilotResearchPayload(context), context);
assert.deepEqual(
  api.buildEvidenceAutopilotResearchPayload(context, {
    caseId: "scut-im-v0",
    enableReviewedEvidenceLedger: true,
  }),
  {
    ...context,
    caseId: "scut-im-v0",
    enableReviewedEvidenceLedger: true,
  },
);

const backendResponse = {
  success: true,
  targetLabel: "广东 2026 华南理工示例校 智能制造与数据工程",
  tasks: [],
  searchQueries: [],
  evidenceCoverage: {
    totalTasks: 8,
    capturedTaskIds: ["official-plan-charter"],
    missingP0TaskIds: ["employment-market", "counter-evidence"],
    operatorTaskIds: ["employment-market", "counter-evidence"],
    readyForCounselorReview: false,
    reviewBlockers: ["Missing captured P0 evidence: employment-market, counter-evidence"],
  },
  claimBoundary: "后端只返回可审计证据。",
  evidenceCards: [
    {
      taskId: "official-plan-charter",
      claim: "official_admission",
      status: "captured_candidate",
      sourceTitle: "华南理工大学本科招生章程",
      sourceUrl: "https://example.edu/charter.pdf",
      sourceType: "official",
      excerpt: "招生章程列明专业组计划数、选科要求与校区。",
      capturedAt: "2026-06-23T00:00:00.000Z",
      confidence: "high",
      reviewAction: "复核官方 PDF。",
    },
    {
      taskId: "wechat-public-account",
      claim: "wechat_public_account",
      status: "operator_review",
      sourceTitle: "微信公众号材料：待采集",
      sourceUrl: "",
      sourceType: "wechat",
      excerpt: "",
      capturedAt: "",
      confidence: "low",
      reviewAction: "人工采集。",
    },
  ],
};

const providerResults = api.mapBackendEvidenceCardsToProviderResults(backendResponse);
assert.equal(providerResults.length, 1);
assert.deepEqual(providerResults[0], {
  requestId: "backend-official-plan-charter-1",
  taskId: "official-plan-charter",
  sourceTitle: "华南理工大学本科招生章程",
  sourceUrl: "https://example.edu/charter.pdf",
  sourceType: "official",
  excerpt: "招生章程列明专业组计划数、选科要求与校区。",
  capturedAt: "2026-06-23T00:00:00.000Z",
  confidence: "high",
});

const connected = await api.fetchEvidenceAutopilotResearch({
  context,
  caseId: "scut-im-v0",
  enableReviewedEvidenceLedger: true,
  fetchImpl: async (url, init) => {
    assert.equal(url, "https://api.test/api/evidence-autopilot/research");
    assert.equal(init.method, "POST");
    assert.deepEqual(JSON.parse(init.body), {
      ...context,
      caseId: "scut-im-v0",
      enableReviewedEvidenceLedger: true,
    });
    return {
      ok: true,
      async json() {
        return backendResponse;
      },
    };
  },
});
assert.equal(connected.status, "backend_connected");
assert.equal(connected.providerResults.length, 1);
assert.equal(connected.claimBoundary, backendResponse.claimBoundary);
assert.deepEqual(connected.evidenceCoverage, backendResponse.evidenceCoverage);
assert.equal(connected.backendResponse.evidenceCoverage.readyForCounselorReview, false);

const reviewedRecordsResponse = {
  success: true,
  caseId: "scut-im-v0",
  recordCount: 1,
  records: [
    {
      reviewId: "review-20260624T000000Z-abc12345",
      targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
      reviewedEvidenceCard: {
        taskId: "employment-market",
        claim: "employment_market",
        status: "captured_candidate",
        sourceTitle: "Reviewed job-market sample",
        sourceUrl: "operator-review://review-20260624T000000Z-abc12345",
        sourceType: "job",
        excerpt: "Visible job sample describes robotics integration responsibilities.",
        capturedAt: "2026-06-24",
        confidence: "medium",
        reviewAction: "Use as operator-captured job sample only.",
      },
      reviewer: "operator-a",
      caseId: "scut-im-v0",
      recordedAt: "2026-06-24T00:00:00Z",
      ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
    },
  ],
};

const reviewedListing = await api.fetchReviewedEvidenceRecords({
  caseId: "scut-im-v0",
  fetchImpl: async (url, init) => {
    assert.equal(url, "https://api.test/api/evidence-autopilot/reviewed-evidence/scut-im-v0");
    assert.equal(init.method, "GET");
    return {
      ok: true,
      async json() {
        return reviewedRecordsResponse;
      },
    };
  },
});
assert.equal(reviewedListing.success, true);
assert.equal(reviewedListing.recordCount, 1);
assert.equal(reviewedListing.records[0].reviewedEvidenceCard.taskId, "employment-market");

const uploadedAttachment = await api.uploadReviewedEvidenceAttachment({
  payload: {
    caseId: "scut-im-v0",
    taskId: "employment-market",
    reviewerId: "operator-a",
    kind: "screenshot",
    contentType: "image/png",
    contentBase64: "ZmFrZS1zY3JlZW5zaG90",
    capturedAt: "2026-06-24T00:00:00Z",
    redactionStatus: "redacted",
    originalFileName: "job-sample.png",
  },
  fetchImpl: async (url, init) => {
    assert.equal(
      url,
      "https://api.test/api/evidence-autopilot/reviewed-evidence/attachments",
    );
    assert.equal(init.method, "POST");
    assert.deepEqual(JSON.parse(init.body), {
      caseId: "scut-im-v0",
      taskId: "employment-market",
      reviewerId: "operator-a",
      kind: "screenshot",
      contentType: "image/png",
      contentBase64: "ZmFrZS1zY3JlZW5zaG90",
      capturedAt: "2026-06-24T00:00:00Z",
      redactionStatus: "redacted",
      originalFileName: "job-sample.png",
    });
    return {
      ok: true,
      async json() {
        return {
          success: true,
          attachment: {
            attachmentId: "att-20260624T000000Z-abc12345",
            kind: "screenshot",
            storageRef: "reviewed-evidence/scut-im-v0/att-20260624T000000Z-abc12345.png",
            capturedAt: "2026-06-24T00:00:00Z",
            redactionStatus: "redacted",
          },
          byteSize: 15,
          sha256: "a".repeat(64),
          metadataPath: [
            "C:/PathFinder/backend/logs/evidence_autopilot/attachments",
            "reviewed-evidence/scut-im-v0/att-20260624T000000Z-abc12345.png.json",
          ].join("/"),
        };
      },
    };
  },
});
assert.equal(uploadedAttachment.success, true);
assert.equal(uploadedAttachment.attachment.storageRef.includes("reviewed-evidence/scut-im-v0/"), true);
assert.equal(uploadedAttachment.sha256.length, 64);

const operatorReviewedCard = api.buildOperatorReviewedEvidenceCard({
  taskId: "employment-market",
  claim: "employment_market",
  sourceTitle: "Reviewed job-market sample",
  sourceType: "job",
  excerpt: "Visible job sample describes robotics integration responsibilities.",
  capturedAt: "2026-06-24T00:00:00Z",
  confidence: "medium",
  reviewAction: "Use as operator-captured job sample only; do not infer employment certainty.",
  attachments: [uploadedAttachment.attachment],
  redactionStatus: "redacted",
  reviewerIdentity: {
    reviewerId: "operator-a",
    displayName: "Operator A",
    role: "operator",
  },
});
assert.equal(operatorReviewedCard.status, "captured_candidate");
assert.equal(operatorReviewedCard.sourceUrl, "");
assert.equal(operatorReviewedCard.attachments.length, 1);
assert.equal(operatorReviewedCard.reviewerIdentity.reviewerId, "operator-a");

const submittedReviewedCard = await api.submitReviewedEvidenceCard({
  payload: {
    targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
    caseId: "scut-im-v0",
    reviewer: "operator-a",
    card: operatorReviewedCard,
  },
  fetchImpl: async (url, init) => {
    assert.equal(url, "https://api.test/api/evidence-autopilot/reviewed-evidence");
    assert.equal(init.method, "POST");
    assert.deepEqual(JSON.parse(init.body), {
      targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
      caseId: "scut-im-v0",
      reviewer: "operator-a",
      card: operatorReviewedCard,
    });
    return {
      ok: true,
      async json() {
        return {
          success: true,
          reviewId: "review-20260624T010000Z-def67890",
          reviewedEvidenceCard: {
            ...operatorReviewedCard,
            sourceUrl: "operator-review://review-20260624T010000Z-def67890",
          },
          ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
          recordedAt: "2026-06-24T01:00:00Z",
        };
      },
    };
  },
});
assert.equal(submittedReviewedCard.success, true);
assert.equal(
  submittedReviewedCard.reviewedEvidenceCard.sourceUrl,
  "operator-review://review-20260624T010000Z-def67890",
);
assert.equal(submittedReviewedCard.reviewedEvidenceCard.attachments[0].attachmentId, uploadedAttachment.attachment.attachmentId);

assert.throws(
  () => api.buildOperatorReviewedEvidenceCard({
    taskId: "employment-market",
    claim: "employment_market",
    sourceTitle: "Reviewed job-market sample",
    sourceType: "job",
    excerpt: "Visible job sample describes robotics integration responsibilities.",
    capturedAt: "2026-06-24T00:00:00Z",
    confidence: "medium",
    reviewAction: "Use as operator-captured job sample only.",
    attachments: [uploadedAttachment.attachment],
    redactionStatus: "redacted",
  }),
  /reviewer identity/i,
);

await assert.rejects(
  () => api.uploadReviewedEvidenceAttachment({
    payload: {
      caseId: "scut-im-v0",
      taskId: "employment-market",
      reviewerId: "operator-a",
      kind: "screenshot",
      contentType: "image/png",
      contentBase64: "ZmFrZS1zY3JlZW5zaG90",
      capturedAt: "2026-06-24T00:00:00Z",
      redactionStatus: "redacted",
    },
    fetchImpl: async () => ({
      ok: true,
      async json() {
        return {
          success: true,
          attachment: { storageRef: "" },
          byteSize: "15",
          sha256: "short",
        };
      },
    }),
  }),
  /invalid reviewed evidence attachment upload response/i,
);

await assert.rejects(
  () => api.fetchReviewedEvidenceRecords({
    caseId: "scut-im-v0",
    fetchImpl: async () => ({
      ok: true,
      async json() {
        return { ...reviewedRecordsResponse, records: "not-an-array" };
      },
    }),
  }),
  /records was not an array/i,
);

const plan = planModule.buildDeepEvidenceCollectionPlan(planModule.exampleCollectionContext);
const draftRun = autopilot.buildEvidenceAutopilotRun({ plan });

const malformedBackendFallback = await api.fetchEvidenceAutopilotResearch({
  context,
  fallback: {
    plan,
    searchTasks: draftRun.searchTasks,
    targetLabel: plan.targetLabel,
  },
  fetchImpl: async () => ({
    ok: true,
    async json() {
      return {
        ...backendResponse,
        evidenceCards: [
          {
            ...backendResponse.evidenceCards[0],
            sourceType: "unsupported-blog-source",
            confidence: "certain",
          },
        ],
      };
    },
  }),
});
assert.equal(malformedBackendFallback.status, "backend_failed_snapshot_fallback");
assert.match(malformedBackendFallback.error, /invalid backend evidence card/i);
assert(malformedBackendFallback.providerResults.length > 0);

const missingCoverageFallback = await api.fetchEvidenceAutopilotResearch({
  context,
  fallback: {
    plan,
    searchTasks: draftRun.searchTasks,
    targetLabel: plan.targetLabel,
  },
  fetchImpl: async () => ({
    ok: true,
    async json() {
      const { evidenceCoverage, ...withoutCoverage } = backendResponse;
      return withoutCoverage;
    },
  }),
});
assert.equal(missingCoverageFallback.status, "backend_failed_snapshot_fallback");
assert.match(missingCoverageFallback.error, /evidenceCoverage/i);
assert(missingCoverageFallback.providerResults.length > 0);

const placeholderWithExcerptFallback = await api.fetchEvidenceAutopilotResearch({
  context,
  fallback: {
    plan,
    searchTasks: draftRun.searchTasks,
    targetLabel: plan.targetLabel,
  },
  fetchImpl: async () => ({
    ok: true,
    async json() {
      return {
        ...backendResponse,
        evidenceCards: [
          {
            ...backendResponse.evidenceCards[0],
            status: "requires_capture",
          },
        ],
      };
    },
  }),
});
assert.equal(placeholderWithExcerptFallback.status, "backend_failed_snapshot_fallback");
assert.match(placeholderWithExcerptFallback.error, /task placeholders without captured evidence/i);
assert(placeholderWithExcerptFallback.providerResults.length > 0);

const fallback = await api.fetchEvidenceAutopilotResearch({
  context,
  fallback: {
    plan,
    searchTasks: draftRun.searchTasks,
    targetLabel: plan.targetLabel,
  },
  fetchImpl: async () => {
    throw new Error("network down");
  },
});
assert.equal(fallback.status, "backend_failed_snapshot_fallback");
assert(fallback.providerResults.length > 0);
assert(fallback.claimBoundary.includes("demo snapshot"));
assert(fallback.error.includes("network down"));

const realCaseState = api.buildEvidenceAutopilotRealCaseState({
  providerResults: [
    {
      requestId: "real-case-v0-1",
      taskId: "official-plan-charter",
      sourceTitle: "Official source",
      sourceUrl: "https://example.edu/official",
      sourceType: "official",
      excerpt: "Official public source excerpt for audited real case.",
      capturedAt: "2026-06-24",
      confidence: "high",
    },
  ],
  claimBoundary: "Real Case v0 fixture supports an auditable opportunity hypothesis only.",
});
assert.equal(realCaseState.status, "real_case_fixture");
assert.equal(realCaseState.providerResults.length, 1);
assert.match(realCaseState.claimBoundary, /auditable opportunity hypothesis/i);

const panelSource = fs.readFileSync(panelPath, "utf8");
assert(panelSource.includes("fetchEvidenceAutopilotResearch"));
assert(panelSource.includes("demo_snapshot"));
assert(panelSource.includes("backend_connected"));
assert(panelSource.includes("backend_failed_snapshot_fallback"));

console.log("Evidence Autopilot API adapter test passed");

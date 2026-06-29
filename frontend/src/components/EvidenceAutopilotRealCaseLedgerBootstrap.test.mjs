import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..", "..", "..");
const lib = path.join(here, "..", "lib");
const fixturePath = path.join(root, "data", "evidence_autopilot", "real_case_v0.json");
const providerPath = path.join(lib, "evidenceAutopilotRealCaseProvider.ts");
const reviewedPath = path.join(lib, "evidenceAutopilotRealCaseReviewedEvidence.ts");
const apiPath = path.join(lib, "evidenceAutopilotApi.ts");
const browserPath = path.join(lib, "reviewedEvidenceCaseBrowser.ts");
const bootstrapPath = path.join(lib, "evidenceAutopilotRealCaseLedgerBootstrap.ts");

assert.equal(fs.existsSync(bootstrapPath), true, "real case ledger bootstrap helper should exist");

function loadTsModule(filePath, requireMap = {}) {
  const output = ts.transpileModule(fs.readFileSync(filePath, "utf8"), {
    compilerOptions: {
      esModuleInterop: true,
      module: ts.ModuleKind.CommonJS,
      resolveJsonModule: true,
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

const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
const provider = loadTsModule(providerPath, {
  "../../../data/evidence_autopilot/real_case_v0.json": fixture,
});
const reviewed = loadTsModule(reviewedPath, {
  "./evidenceAutopilotRealCaseProvider": provider,
  "./evidenceAutopilotApi": {},
});
const browser = loadTsModule(browserPath);
const api = loadTsModule(apiPath, {
  "./api": { buildApiUrl: (route) => `https://api.test${route}` },
  "./evidenceAutopilotSnapshotProvider": { buildEvidenceAutopilotSnapshotProviderResults: () => [] },
});
const bootstrap = loadTsModule(bootstrapPath, {
  "./evidenceAutopilotRealCaseReviewedEvidence": reviewed,
  "./evidenceAutopilotApi": api,
  "./reviewedEvidenceCaseBrowser": browser,
});

assert.equal(typeof bootstrap.bootstrapRealCaseReviewedEvidenceLedger, "function");

const plan = {
  tasks: [
    { id: "official-plan-charter", priority: "P0", claim: "official_admission", title: "Official admission" },
    { id: "rank-history-band", priority: "P0", claim: "rank_history", title: "Rank history" },
    { id: "faculty-research-direction", priority: "P0", claim: "faculty_research", title: "Faculty research" },
    { id: "undergrad-access", priority: "P0", claim: "undergrad_access", title: "Undergraduate access" },
    { id: "graduate-progression", priority: "P1", claim: "graduate_progression", title: "Graduate progression" },
    { id: "employment-market", priority: "P0", claim: "employment_market", title: "Employment market" },
    { id: "counter-evidence", priority: "P0", claim: "counter_evidence", title: "Counter evidence" },
  ],
};

const submissions = reviewed.buildRealCaseReviewedEvidenceSubmissions({
  fixture: provider.loadEvidenceAutopilotRealCaseFixture(),
  caseId: fixture.caseId,
});
const calls = [];
const records = [];

const result = await bootstrap.bootstrapRealCaseReviewedEvidenceLedger({
  fixture: provider.loadEvidenceAutopilotRealCaseFixture(),
  caseId: fixture.caseId,
  plan,
  fetchImpl: async (url, init) => {
    calls.push({ url, method: init.method, body: init.body ? JSON.parse(init.body) : null });
    if (url.endsWith("/reviewed-evidence") && init.method === "POST") {
      const body = JSON.parse(init.body);
      const reviewId = `review-real-case-${records.length + 1}`;
      const record = {
        reviewId,
        targetLabel: body.targetLabel,
        reviewedEvidenceCard: body.card,
        reviewer: body.reviewer,
        caseId: body.caseId,
        recordedAt: `2026-06-24T00:00:0${records.length}Z`,
        ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
        attachmentAudit: {
          status: "not_applicable",
          validAttachmentCount: 0,
          invalidAttachmentCount: 0,
          findings: [],
        },
      };
      records.push(record);
      return {
        ok: true,
        async json() {
          return {
            success: true,
            reviewId,
            reviewedEvidenceCard: body.card,
            ledgerPath: record.ledgerPath,
            recordedAt: record.recordedAt,
          };
        },
      };
    }
    if (url.endsWith(`/reviewed-evidence/${encodeURIComponent(fixture.caseId)}`) && init.method === "GET") {
      return {
        ok: true,
        async json() {
          return {
            success: true,
            caseId: fixture.caseId,
            recordCount: records.length,
            records,
          };
        },
      };
    }
    throw new Error(`Unexpected URL ${url}`);
  },
});

assert.equal(result.protocol, "real_case_reviewed_evidence_bootstrap_v1");
assert.equal(result.caseId, fixture.caseId);
assert.equal(result.submittedCount, submissions.length);
assert.equal(result.recordCount, submissions.length);
assert.equal(result.submissions.length, submissions.length);
assert.equal(result.listing.records.length, submissions.length);
assert.equal(result.browser.caseId, fixture.caseId);
assert.equal(result.browser.readyForReportCount, submissions.length);
assert.deepEqual(result.browser.missingP0TaskIds, ["employment-market"]);
assert.equal(result.browser.counterEvidenceHit, true);
assert.equal(result.browser.reviewRequired, true);
assert.match(result.claimBoundary, /does not prove admission probability/i);
assert.match(result.claimBoundary, /case-scoped reviewed evidence/i);

assert.equal(calls.filter((call) => call.method === "POST").length, submissions.length);
assert.equal(calls.at(-1).method, "GET");
assert.equal(calls.at(-1).url, `https://api.test/api/evidence-autopilot/reviewed-evidence/${fixture.caseId}`);
assert.equal(
  calls
    .filter((call) => call.method === "POST")
    .every((call) => call.body.caseId === fixture.caseId && call.body.reviewer === "real-case-v0-source-log"),
  true,
);
assert.equal(
  calls
    .filter((call) => call.method === "POST")
    .every((call) => /^https?:\/\//.test(call.body.card.sourceUrl)),
  true,
  "bootstrap should only submit public source fixture evidence",
);

await assert.rejects(
  () => bootstrap.bootstrapRealCaseReviewedEvidenceLedger({
    fixture,
    caseId: "",
    plan,
    fetchImpl: async () => {
      throw new Error("should not fetch without case id");
    },
  }),
  /caseId/i,
);

console.log("Evidence Autopilot real case ledger bootstrap test passed");

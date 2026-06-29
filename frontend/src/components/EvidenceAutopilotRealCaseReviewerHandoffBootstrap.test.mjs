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
const ledgerBootstrapPath = path.join(lib, "evidenceAutopilotRealCaseLedgerBootstrap.ts");
const worklistPath = path.join(lib, "operatorEvidenceCaptureWorklist.ts");
const packetPath = path.join(lib, "operatorEvidenceCapturePacket.ts");
const handoffPath = path.join(lib, "evidenceAutopilotRealCaseReviewerHandoff.ts");

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
const api = loadTsModule(apiPath, {
  "./api": { buildApiUrl: (route) => `https://api.test${route}` },
  "./evidenceAutopilotSnapshotProvider": { buildEvidenceAutopilotSnapshotProviderResults: () => [] },
});
const browser = loadTsModule(browserPath);
const ledgerBootstrap = loadTsModule(ledgerBootstrapPath, {
  "./evidenceAutopilotApi": api,
  "./evidenceAutopilotRealCaseReviewedEvidence": reviewed,
  "./reviewedEvidenceCaseBrowser": browser,
});
const worklist = loadTsModule(worklistPath, {
  "./reviewedEvidenceCaseBrowser": browser,
});
const packet = loadTsModule(packetPath, {
  "./operatorEvidenceCaptureWorklist": worklist,
});
const handoff = loadTsModule(handoffPath, {
  "./evidenceAutopilotRealCaseLedgerBootstrap": ledgerBootstrap,
  "./operatorEvidenceCaptureWorklist": worklist,
  "./operatorEvidenceCapturePacket": packet,
});

assert.equal(typeof handoff.bootstrapRealCaseReviewerHandoff, "function");

const plan = {
  protocol: "deep_evidence_collection_plan_v1",
  targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
  tasks: [
    { id: "official-plan-charter", priority: "P0", claim: "official_admission", title: "Official admission", outputFields: ["sourceTitle", "excerpt"] },
    { id: "rank-history-band", priority: "P0", claim: "rank_history", title: "Rank history", outputFields: ["scoreRange", "rankBand", "excerpt"] },
    { id: "faculty-research-direction", priority: "P0", claim: "faculty_research", title: "Faculty research", outputFields: ["sourceTitle", "excerpt"] },
    { id: "undergrad-access", priority: "P0", claim: "undergrad_access", title: "Undergraduate access", outputFields: ["sourceTitle", "excerpt"] },
    { id: "graduate-progression", priority: "P1", claim: "graduate_progression", title: "Graduate progression", outputFields: ["sourceTitle", "excerpt"] },
    { id: "employment-market", priority: "P0", claim: "employment_market", title: "Employment market", outputFields: ["jobTitle", "city", "educationRequirement", "skills", "excerpt"] },
    { id: "counter-evidence", priority: "P0", claim: "counter_evidence", title: "Counter evidence", outputFields: ["sourceTitle", "risk", "excerpt"] },
  ],
  reviewGates: [],
  claimBoundary: "test boundary",
};

const records = [];
const calls = [];
const result = await handoff.bootstrapRealCaseReviewerHandoff({
  fixture: provider.loadEvidenceAutopilotRealCaseFixture(),
  caseId: fixture.caseId,
  plan,
  fetchImpl: async (url, init) => {
    calls.push({ url, method: init.method, body: init.body ? JSON.parse(init.body) : null });
    if (url.endsWith("/reviewed-evidence") && init.method === "POST") {
      const body = JSON.parse(init.body);
      const reviewId = `review-public-${records.length + 1}`;
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
      return jsonResponse({
        success: true,
        reviewId,
        reviewedEvidenceCard: body.card,
        ledgerPath: record.ledgerPath,
        recordedAt: record.recordedAt,
      });
    }
    if (url.endsWith(`/reviewed-evidence/${encodeURIComponent(fixture.caseId)}`) && init.method === "GET") {
      return jsonResponse({
        success: true,
        caseId: fixture.caseId,
        recordCount: records.length,
        records,
      });
    }
    throw new Error(`Unexpected fetch ${init.method} ${url}`);
  },
});

assert.equal(result.protocol, "real_case_reviewer_handoff_bootstrap_v1");
assert.equal(result.caseId, fixture.caseId);
assert.equal(result.publicBootstrap.protocol, "real_case_reviewed_evidence_bootstrap_v1");
assert.equal(result.handoff.protocol, "real_case_reviewer_handoff_v1");
assert.equal(result.brief.protocol, "real_case_reviewer_handoff_brief_v1");
assert.deepEqual(result.handoff.openTaskIds, ["employment-market"]);
assert.equal(result.handoff.familyFacingAllowed, false);
assert.equal(result.brief.familyFacingAllowed, false);
assert.match(result.brief.markdown, /employment-market/);
assert.match(result.brief.markdown, /executeRealCaseOperatorClosureWorkflow/);
assert.match(result.brief.markdown, /OperatorReviewedEvidenceCaptureInput/);
assert.match(result.claimBoundary, /does not prove admission probability/i);
assert.match(result.claimBoundary, /does not prove employment outcomes/i);
assert.doesNotMatch(result.brief.markdown, /推荐报考|保证录取|保证就业/);

assert.equal(calls.filter((call) => call.method === "POST").length, records.length);
assert.equal(calls.filter((call) => call.method === "GET").length, 1);
assert.equal(calls.every((call) => call.method !== "POST" || /^https?:\/\//.test(call.body.card.sourceUrl)), true);

await assert.rejects(
  () => handoff.bootstrapRealCaseReviewerHandoff({
    fixture: provider.loadEvidenceAutopilotRealCaseFixture(),
    caseId: "other-case",
    plan,
    fetchImpl: async () => {
      throw new Error("should not fetch with mismatched case id");
    },
  }),
  /caseId/i,
);

console.log("Evidence Autopilot real case reviewer handoff bootstrap test passed");

function jsonResponse(payload) {
  return {
    ok: true,
    status: 200,
    async json() {
      return payload;
    },
  };
}

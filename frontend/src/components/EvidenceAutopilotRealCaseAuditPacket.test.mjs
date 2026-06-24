import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..", "..", "..");
const lib = path.join(here, "..", "lib");
const fixturePath = path.join(root, "data", "evidence_autopilot", "real_case_v0.json");
const auditPacketPath = path.join(lib, "evidenceAutopilotRealCaseAuditPacket.ts");

assert.equal(fs.existsSync(auditPacketPath), true, "real case audit packet helper should exist");

function loadTsModule(filePath) {
  const output = ts.transpileModule(fs.readFileSync(filePath, "utf8"), {
    compilerOptions: {
      esModuleInterop: true,
      module: ts.ModuleKind.CommonJS,
      resolveJsonModule: true,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
  const module = { exports: {} };
  new Function("require", "module", "exports", output)(() => {
    throw new Error("No runtime imports expected");
  }, module, module.exports);
  return module.exports;
}

const auditPacket = loadTsModule(auditPacketPath);
assert.equal(typeof auditPacket.buildRealCaseOpportunityAuditPacket, "function");

const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
const bootstrapResult = {
  protocol: "real_case_reviewed_evidence_bootstrap_v1",
  caseId: fixture.caseId,
  submittedCount: 6,
  recordCount: 6,
  submissions: [],
  listing: { success: true, caseId: fixture.caseId, recordCount: 6, records: [] },
  browser: {
    protocol: "reviewed_evidence_case_browser_v1",
    caseId: fixture.caseId,
    totalRecords: 6,
    capturedCount: 6,
    pendingCount: 0,
    readyForReportCount: 6,
    missingP0TaskIds: ["employment-market"],
    counterEvidenceHit: true,
    reviewRequired: true,
    claimBoundary: "Case-scoped reviewed evidence browser only organizes captured ledger records.",
    taskGroups: [
      readyGroup({
        taskId: "official-plan-charter",
        claim: "official_admission",
        title: "Official admission",
        priority: "P0",
        sourceTitle: "华南理工大学本科招生网 - 招生计划",
        sourceId: "https://admission.scut.edu.cn/30820/list.htm",
        excerpt: "2026 年招生专业和分组进一步优化，2025 年录取分数仅供参考。",
      }),
      readyGroup({
        taskId: "undergrad-access",
        claim: "undergrad_access",
        title: "Undergraduate access",
        priority: "P0",
        sourceTitle: "华南理工大学吴贤铭智能工程学院 - 智能制造工程专业介绍",
        sourceId: "https://www2.scut.edu.cn/wusie/2022/0907/c34046a488201/page.htm",
        excerpt: "Research platforms are open to undergraduates.",
      }),
      {
        taskId: "employment-market",
        claim: "employment_market",
        title: "Employment market",
        priority: "P0",
        status: "missing",
        records: [],
      },
      readyGroup({
        taskId: "counter-evidence",
        claim: "counter_evidence",
        title: "Counter evidence",
        priority: "P0",
        sourceTitle: "华南理工大学 2025 年广东省综合评价招生简章",
        sourceId: "https://xxgk.scut.edu.cn/2025/0402/c108a48077/page.htm",
        excerpt: "学费：9.5 万元/生·学年；不可转入其它校区的专业。",
      }),
    ],
  },
  claimBoundary:
    "Real Case reviewed-evidence bootstrap only submits completed public fixture evidence into the case-scoped reviewed evidence ledger.",
};

const packet = auditPacket.buildRealCaseOpportunityAuditPacket({
  fixture,
  bootstrap: bootstrapResult,
});

assert.equal(packet.protocol, "real_case_opportunity_audit_packet_v1");
assert.equal(packet.caseId, fixture.caseId);
assert.equal(packet.targetLabel.includes("South China University of Technology"), true);
assert.equal(packet.status, "blocked_by_p0_gaps");
assert.equal(packet.metrics.readyForReport, 6);
assert.equal(packet.metrics.missingP0, 1);
assert.deepEqual(packet.missingP0TaskIds, ["employment-market"]);
assert.equal(packet.counterEvidence.requiresCounselorReview, true);
assert.equal(packet.counterEvidence.records.length, 1);
assert.match(packet.counterEvidence.records[0].excerpt, /9\.5/);
assert.equal(packet.supportedClaims.some((claim) => claim.taskId === "undergrad-access"), true);
assert.equal(packet.supportedClaims.some((claim) => claim.taskId === "employment-market"), false);
assert.match(packet.blockingGaps[0].reason, /operator-captured job-market/i);
assert(packet.nextActions.some((action) => /employment-market/.test(action)));
assert(packet.nextActions.some((action) => /counter-evidence/i));
assert.match(packet.claimBoundary, /does not prove admission probability/i);
assert.match(packet.claimBoundary, /does not prove employment outcomes/i);

assert.throws(
  () => auditPacket.buildRealCaseOpportunityAuditPacket({
    fixture,
    bootstrap: { ...bootstrapResult, caseId: "other-case" },
  }),
  /caseId/i,
);

console.log("Evidence Autopilot real case audit packet test passed");

function readyGroup({
  taskId,
  claim,
  title,
  priority,
  sourceTitle,
  sourceId,
  excerpt,
}) {
  return {
    taskId,
    claim,
    title,
    priority,
    status: "ready_for_report",
    records: [
      {
        reviewId: `review-${taskId}`,
        taskId,
        claim,
        sourceTitle,
        sourceId,
        excerpt,
        reviewer: "real-case-v0-source-log",
        recordedAt: "2026-06-24T00:00:00Z",
        capturedAt: "2026-06-24",
        confidence: "high",
        reviewAction: "Use as audited public fixture evidence only.",
        attachmentCount: 0,
        redactionStatus: "not_required",
        reviewerIdentity: "unverified reviewer",
        attachmentAuditStatus: "not_applicable",
        attachmentAuditDetail: "public source URL does not require attachment audit",
        readyForReport: true,
      },
    ],
  };
}

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const lib = path.join(here, "..", "lib");
const reportBriefPath = path.join(lib, "evidenceAutopilotRealCaseReportBrief.ts");

assert.equal(fs.existsSync(reportBriefPath), true, "real case report brief helper should exist");

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

const reportBrief = loadTsModule(reportBriefPath);
assert.equal(typeof reportBrief.buildRealCaseOpportunityReportBrief, "function");

const packet = {
  protocol: "real_case_opportunity_audit_packet_v1",
  caseId: "scut-wusie-2026-gd-001",
  targetLabel: "Guangdong 2026 South China University of Technology Intelligent Manufacturing",
  opportunityHypothesis: "SCUT intelligent manufacturing may be a deep opportunity if evidence gates close.",
  status: "blocked_by_p0_gaps",
  metrics: {
    submitted: 6,
    ledgerRecords: 6,
    readyForReport: 6,
    missingP0: 1,
  },
  missingP0TaskIds: ["employment-market"],
  supportedClaims: [
    {
      taskId: "official-plan-charter",
      claim: "official_admission",
      title: "Official admission",
      priority: "P0",
      sourceCount: 1,
      sourceTitles: ["SCUT undergraduate admissions plan"],
      excerpts: ["2026 admission-major grouping is still changing; 2025 scores are for reference."],
      reviewActions: ["Use as audited public fixture evidence only."],
    },
    {
      taskId: "undergrad-access",
      claim: "undergrad_access",
      title: "Undergraduate access",
      priority: "P0",
      sourceCount: 1,
      sourceTitles: ["SCUT WUSIE major profile"],
      excerpts: ["Research platforms are open to undergraduates."],
      reviewActions: ["Use as audited public fixture evidence only."],
    },
  ],
  blockingGaps: [
    {
      taskId: "employment-market",
      claim: "employment_market",
      title: "Employment market",
      priority: "P0",
      reason: "Missing compliant operator-captured job-market evidence with source proof.",
    },
  ],
  counterEvidence: {
    requiresCounselorReview: true,
    records: [
      {
        taskId: "counter-evidence",
        sourceTitle: "SCUT 2025 comprehensive evaluation policy",
        sourceId: "https://example.edu/counter",
        excerpt: "High tuition and transfer limits require counselor review.",
        reviewAction: "Review before any family-facing opportunity wording.",
      },
    ],
  },
  nextActions: [
    "Capture employment-market operator evidence with screenshot/PDF/page proof before report use.",
    "Review counter-evidence with a counselor before any family-facing opportunity wording.",
  ],
  claimBoundary:
    "Real Case opportunity audit packet summarizes case-scoped reviewed evidence readiness only; it does not prove admission probability, does not prove employment outcomes, and does not replace counselor review or source freshness checks.",
};

const brief = reportBrief.buildRealCaseOpportunityReportBrief(packet);

assert.equal(brief.protocol, "real_case_opportunity_report_brief_v1");
assert.equal(brief.caseId, packet.caseId);
assert.equal(brief.familyFacingAllowed, false);
assert.equal(brief.status, "blocked_by_p0_gaps");
assert.match(brief.statusLabel, /暂不进入家庭版报告/);
assert.match(brief.briefTitle, /内部审计/);
assert.equal(brief.sections.some((section) => section.title === "已审证据"), true);
assert.equal(brief.sections.some((section) => section.title === "阻塞缺口"), true);
assert.equal(brief.sections.some((section) => section.title === "反证复核"), true);
assert.equal(brief.sections.some((section) => section.title === "下一步"), true);
assert.match(JSON.stringify(brief.sections), /employment-market/);
assert.match(JSON.stringify(brief.sections), /SCUT undergraduate admissions plan/);
assert.match(brief.claimBoundary, /不证明录取概率/);
assert.match(brief.claimBoundary, /不证明就业结果/);
assert.doesNotMatch(JSON.stringify(brief), /已证明录取|保证录取/);
assert.doesNotMatch(JSON.stringify(brief), /已证明就业|保证就业/);
assert.doesNotMatch(JSON.stringify(brief), /推荐报考/);

assert.throws(
  () => reportBrief.buildRealCaseOpportunityReportBrief({ ...packet, protocol: "other" }),
  /audit packet/i,
);

console.log("Evidence Autopilot real case report brief test passed");

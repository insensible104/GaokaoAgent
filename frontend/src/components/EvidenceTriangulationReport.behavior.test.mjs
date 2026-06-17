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

const triangulation = loadTsModule(path.join(libDir, "evidenceTriangulationReport.ts"), {
  "./webEvidenceIntake": {},
  "./webEvidencePlanner": {},
});

const intakeResult = {
  protocol: "web_evidence_intake_v1",
  status: "review_ready",
  acceptedEvidence: [
    evidence("official_diff", "Official exam authority plan", "https://eea.gd.gov.cn/plan-2026", "quota increases from 20 to 36"),
    evidence("risk_guard", "School admission charter", "https://admission.school.edu.cn/charter", "adjustment remains inside the same eligible major group"),
    evidence("rank_delta", "Exam authority rank history", "https://eea.gd.gov.cn/rank-2025", "2025 minimum rank 42000"),
    evidence("competitor_missed", "Teacher plan comparison", "https://teacher.example/plan", "teacher plan keeps the old 20-seat assumption"),
    evidence("competitor_missed", "Family spreadsheet comparison", "https://docs.example/family-plan", "family plan omits the 2026 quota expansion"),
    evidence("hypothesis_only", "Parent discussion scan", "https://zhihu.com/question/example", "families focus on local brands and rarely mention this group"),
    evidence("parent_understanding", "Concept checklist", "internal://concept-brief", "professional group and adjustment tradeoffs explained"),
  ],
  rejectedEvidence: [
    {
      taskId: "rank-counter",
      claim: "rank_delta",
      sourceTitle: "Counter rank table",
      reason: "Counter-evidence contradicts the easier-rank direction and needs counselor review.",
    },
    {
      taskId: "public-overclaim",
      claim: "final_recommendation",
      sourceTitle: "Forum answer",
      reason: "Search evidence cannot support final_recommendation directly.",
    },
  ],
  blockedTasks: [],
  claimSupport: {},
  claimBoundary: "Evidence intake can make a case review-ready, not final.",
};

const report = triangulation.buildEvidenceTriangulationReport({ intakeResult });

assert.equal(report.protocol, "evidence_triangulation_report_v1");
assert.equal(report.status, "conflict_review");
assert.match(report.claimBoundary, /does not make final recommendations/i);
assert.equal(report.summary.totalAcceptedEvidence, 7);
assert.equal(report.summary.conflictedClaims, 1);
assert.equal(report.summary.claimsNeedingMoreEvidence >= 1, true);

const officialDiff = report.claims.find((claim) => claim.claim === "official_diff");
assert.equal(officialDiff.status, "authoritative");
assert.equal(officialDiff.distinctSourceHosts, 1);
assert.deepEqual(officialDiff.sourceHosts, ["eea.gd.gov.cn"]);

const rankDelta = report.claims.find((claim) => claim.claim === "rank_delta");
assert.equal(rankDelta.status, "conflicted");
assert.match(rankDelta.issues.join("\n"), /Counter-evidence contradicts/);
assert.match(rankDelta.nextActions.join("\n"), /Resolve conflicting evidence/);

const competitorMissed = report.claims.find((claim) => claim.claim === "competitor_missed");
assert.equal(competitorMissed.status, "triangulated");
assert.equal(competitorMissed.distinctSourceHosts, 2);

const hypothesis = report.claims.find((claim) => claim.claim === "hypothesis_only");
assert.equal(hypothesis.status, "hypothesis_only");
assert.match(hypothesis.nextActions.join("\n"), /Keep public-opinion evidence as hypothesis-only/);

const finalRecommendation = report.claims.find((claim) => claim.claim === "final_recommendation");
assert.equal(finalRecommendation.status, "forbidden");
assert.match(finalRecommendation.issues.join("\n"), /cannot be supported by search evidence/i);

const singleSourceIntake = {
  ...intakeResult,
  rejectedEvidence: [],
  acceptedEvidence: intakeResult.acceptedEvidence.filter((item) => item.claim !== "competitor_missed").concat([
    evidence("competitor_missed", "Teacher plan comparison", "https://teacher.example/plan", "teacher plan keeps the old 20-seat assumption"),
  ]),
};
const singleSourceReport = triangulation.buildEvidenceTriangulationReport({ intakeResult: singleSourceIntake });
assert.equal(singleSourceReport.status, "needs_more_evidence");
assert.equal(singleSourceReport.claims.find((claim) => claim.claim === "competitor_missed").status, "needs_second_source");

function evidence(claim, sourceTitle, sourceUrl, excerpt) {
  return {
    taskId: `${claim}-task`,
    claim,
    sourceTitle,
    sourceUrl,
    capturedAt: "2026-06-16",
    excerpts: [excerpt],
  };
}

console.log("Evidence triangulation report behavior test passed");

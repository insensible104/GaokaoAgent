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

const gapPlanner = loadTsModule(path.join(libDir, "evidenceGapSearchPlan.ts"), {
  "./evidenceCollectionWorkspace": {},
  "./evidenceTriangulationReport": {},
  "./webEvidencePlanner": {},
});

const plan = gapPlanner.buildEvidenceGapSearchPlan({
  triangulationReport: {
    protocol: "evidence_triangulation_report_v1",
    status: "needs_more_evidence",
    summary: {
      totalAcceptedEvidence: 4,
      conflictedClaims: 0,
      claimsNeedingMoreEvidence: 2,
      authoritativeClaims: 2,
      triangulatedClaims: 0,
    },
    claims: [
      claim({
        claim: "official_diff",
        status: "authoritative",
        acceptedEvidenceCount: 1,
        sourceHosts: ["eea.gd.gov.cn"],
      }),
      claim({
        claim: "rank_delta",
        status: "needs_second_source",
        acceptedEvidenceCount: 1,
        sourceHosts: ["data.example"],
        issues: ["rank_delta has only one independent source host."],
        nextActions: ["Attach a second independent source for rank_delta."],
      }),
      claim({
        claim: "competitor_missed",
        status: "unsupported",
        acceptedEvidenceCount: 0,
        sourceHosts: [],
        issues: ["No accepted evidence supports competitor_missed."],
        nextActions: ["Capture accepted evidence for competitor_missed before using it in an interpretation package."],
      }),
    ],
    claimBoundary: "Evidence triangulation audits source diversity, conflicts, and claim boundaries.",
  },
  taskRows: [
    taskRow({
      taskId: "rank-history",
      taskType: "rank_history_calibration",
      sourceTier: "historical_data",
      claimedSupports: ["rank_delta"],
      primaryQuery: "South China Tech Computer Science Guangdong 2025 2024 admission rank",
      preferredDomains: ["eea.gd.gov.cn", "gaokao.chsi.com.cn"],
    }),
    taskRow({
      taskId: "external-plan",
      taskType: "external_plan_comparison",
      sourceTier: "competitor_plan",
      claimedSupports: ["competitor_missed"],
      primaryQuery: "South China Tech Computer Science volunteer plan omitted quota expansion",
      preferredDomains: ["qianwen", "tencent", "teacher-plan"],
    }),
  ],
});

assert.equal(plan.protocol, "evidence_gap_search_plan_v1");
assert.equal(plan.status, "ready_to_search");
assert.equal(plan.followUps.length, 2);
assert.match(plan.claimBoundary, /do not prove claims/i);

const rankFollowUp = plan.followUps.find((item) => item.claim === "rank_delta");
assert.ok(rankFollowUp);
assert.equal(rankFollowUp.gapStatus, "needs_second_source");
assert.equal(rankFollowUp.priority, "blocking");
assert.equal(rankFollowUp.sourceTier, "historical_data");
assert.match(rankFollowUp.query, /second independent source/i);
assert.match(rankFollowUp.query, /-site:data\.example/);
assert.deepEqual(rankFollowUp.existingSourceHosts, ["data.example"]);
assert.equal(rankFollowUp.blocksCounselorReview, true);

const competitorFollowUp = plan.followUps.find((item) => item.claim === "competitor_missed");
assert.ok(competitorFollowUp);
assert.equal(competitorFollowUp.gapStatus, "unsupported");
assert.equal(competitorFollowUp.sourceTier, "competitor_plan");
assert.match(competitorFollowUp.reason, /No accepted evidence supports competitor_missed/);
assert.match(competitorFollowUp.query, /volunteer plan omitted quota expansion/);
assert.equal(competitorFollowUp.blocksCounselorReview, true);

const noGapPlan = gapPlanner.buildEvidenceGapSearchPlan({
  triangulationReport: {
    protocol: "evidence_triangulation_report_v1",
    status: "triangulated",
    summary: {
      totalAcceptedEvidence: 5,
      conflictedClaims: 0,
      claimsNeedingMoreEvidence: 0,
      authoritativeClaims: 2,
      triangulatedClaims: 2,
    },
    claims: [claim({ claim: "rank_delta", status: "triangulated", acceptedEvidenceCount: 2, sourceHosts: ["a.example", "b.example"] })],
    claimBoundary: "Evidence triangulation audits source diversity, conflicts, and claim boundaries.",
  },
  taskRows: [],
});

assert.equal(noGapPlan.status, "no_gaps");
assert.deepEqual(noGapPlan.followUps, []);

function claim({ claim, status, acceptedEvidenceCount, sourceHosts, issues = [], nextActions = [] }) {
  return {
    claim,
    status,
    acceptedEvidenceCount,
    distinctSourceHosts: sourceHosts.length,
    sourceHosts,
    sourceTitles: [],
    issues,
    nextActions,
  };
}

function taskRow({ taskId, taskType, sourceTier, claimedSupports, primaryQuery, preferredDomains }) {
  return {
    taskId,
    taskType,
    priority: "blocking",
    status: "accepted",
    acceptedEvidenceCount: 1,
    rejectedEvidenceCount: 0,
    primaryQuery,
    preferredDomains,
    operatorChecklist: [],
    mustReject: [],
    resultTemplate: {
      taskId,
      sourceTier,
      claimedSupports,
      excerptsRequired: true,
    },
  };
}

console.log("Evidence gap search plan behavior test passed");

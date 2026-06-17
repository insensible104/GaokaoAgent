import assert from "node:assert/strict";
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const require = createRequire(import.meta.url);
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const here = path.dirname(fileURLToPath(import.meta.url));
const libDir = path.join(here, "..", "lib");

function loadTsModule(filePath, mocks = {}, jsx = ts.JsxEmit.React) {
  const source = fs.readFileSync(filePath, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      jsx,
      esModuleInterop: true,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (mocks[specifier]) return mocks[specifier];
    if (specifier === "react") return React;
    throw new Error(`Unexpected require: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const captureWorksheet = loadTsModule(path.join(libDir, "webEvidenceCaptureWorksheet.ts"), {
  "./evidenceCollectionWorkspace": {},
  "./webEvidenceIntake": {},
  "./webEvidencePlanner": {},
});
const searchAdapter = loadTsModule(path.join(libDir, "webEvidenceSearchAdapter.ts"), {
  "./evidenceCollectionWorkspace": {},
  "./webEvidenceCaptureWorksheet": captureWorksheet,
  "./webEvidencePlanner": {},
});
const panel = loadTsModule(path.join(here, "EvidenceCollectionWorkspacePanel.tsx"), {
  "../lib/evidenceCollectionWorkspace": {},
  "../lib/webEvidenceCaptureWorksheet": captureWorksheet,
  "../lib/webEvidenceSearchAdapter": searchAdapter,
  "../lib/evidenceTriangulationReport": {},
});

const workspace = {
  protocol: "evidence_collection_workspace_v1",
  status: "collecting_evidence",
  searchBrief: {
    protocol: "web_evidence_search_brief_v1",
    status: "ready_to_search",
    taskBriefs: [],
    claimBoundary: "Search briefs prepare evidence collection.",
  },
  completion: {
    protocol: "admissions_opportunity_workflow_completion_v1",
    status: "blocked",
    blockedReasons: [
      "rank_history_calibration:10561-201-080901-quota_expansion-rank-history",
      "external_plan_comparison:10561-201-080901-quota_expansion-external-plan",
    ],
    nextAction: "Attach blocking evidence before counselor review.",
    claimBoundary: "Workflow completion can produce a counselor-review package, not a final recommendation.",
    interpretationPackage: null,
    intakeResult: {
      protocol: "web_evidence_intake_v1",
      status: "blocked",
      acceptedEvidence: [],
      rejectedEvidence: [],
      blockedTasks: [],
      claimSupport: {},
      claimBoundary: "Evidence intake can make a case review-ready, not final.",
    },
  },
  triangulationReport: {
    protocol: "evidence_triangulation_report_v1",
    status: "needs_more_evidence",
    summary: {
      totalAcceptedEvidence: 2,
      conflictedClaims: 0,
      claimsNeedingMoreEvidence: 4,
      authoritativeClaims: 1,
      triangulatedClaims: 0,
    },
    claims: [
      {
        claim: "official_diff",
        status: "authoritative",
        acceptedEvidenceCount: 1,
        distinctSourceHosts: 1,
        sourceHosts: ["eea.gd.gov.cn"],
        sourceTitles: ["Guangdong official 2026 enrollment plan"],
        issues: [],
        nextActions: [],
      },
      {
        claim: "rank_delta",
        status: "unsupported",
        acceptedEvidenceCount: 0,
        distinctSourceHosts: 0,
        sourceHosts: [],
        sourceTitles: [],
        issues: ["No accepted evidence supports rank_delta."],
        nextActions: ["Capture accepted evidence for rank_delta before using it in an interpretation package."],
      },
      {
        claim: "hypothesis_only",
        status: "hypothesis_only",
        acceptedEvidenceCount: 1,
        distinctSourceHosts: 1,
        sourceHosts: ["search.example"],
        sourceTitles: ["Search summary for non-local engineering attention"],
        issues: [],
        nextActions: ["Keep public-opinion evidence as hypothesis-only and look for counter-evidence."],
      },
    ],
    claimBoundary:
      "Evidence triangulation audits source diversity, conflicts, and claim boundaries. It does not make final recommendations.",
  },
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
        query: "Guangdong 2025 2024 admission line minimum rank history second independent source -site:data.example",
        domains: ["eea.gd.gov.cn", "gaokao.chsi.com.cn"],
        existingSourceHosts: ["data.example"],
        reason: "rank_delta has only one independent source host.",
        nextActions: ["Attach a second independent source for rank_delta."],
        blocksCounselorReview: true,
      },
    ],
    claimBoundary: "Evidence gap search plans turn triangulation gaps into follow-up searches. Search plans do not prove claims.",
  },
  coverageSummary: {
    totalTasks: 6,
    blockingTasks: 4,
    completedBlockingTasks: 1,
    acceptedEvidenceCount: 2,
    rejectedEvidenceCount: 0,
    missingClaims: ["rank_delta", "risk_guard", "competitor_missed", "final_recommendation"],
  },
  taskRows: [
    {
      taskId: "official-plan",
      taskType: "official_plan_verification",
      priority: "blocking",
      status: "accepted",
      acceptedEvidenceCount: 1,
      rejectedEvidenceCount: 0,
      primaryQuery: "site:eea.gd.gov.cn Guangdong 2026 official enrollment catalog quota major group",
      preferredDomains: ["eea.gd.gov.cn", "gd.gov.cn"],
      operatorChecklist: ["row-level school code, major group code, major code, major name, quota, and subject requirements"],
      mustReject: ["Reject public-opinion or reposted plan tables as support for official_diff."],
      resultTemplate: {
        taskId: "official-plan",
        sourceTier: "official",
        claimedSupports: ["official_diff"],
        excerptsRequired: true,
      },
    },
    {
      taskId: "rank-history",
      taskType: "rank_history_calibration",
      priority: "blocking",
      status: "needs_capture",
      acceptedEvidenceCount: 0,
      rejectedEvidenceCount: 0,
      primaryQuery: "Guangdong 2025 2024 admission line minimum rank history",
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
  ],
  nextSearchActions: [
    "Capture rank_history_calibration evidence using: Guangdong 2025 2024 admission line minimum rank history",
    "Capture external_plan_comparison evidence using: volunteer plan comparison omitted quota expansion major group",
  ],
  familyConceptReadiness: {
    status: "needs_explanation",
    nextAction: "Explain professional group, adjustment, safe anchor, interest boundaries, and tradeoffs before final row discussion.",
  },
  claimBoundary:
    "Evidence collection workspace coordinates collection and readiness. It does not make final recommendations or replace counselor review.",
};

const markup = renderToStaticMarkup(
  React.createElement(panel.EvidenceCollectionWorkspacePanel, {
    workspace,
  }),
);

assert.match(markup, /data-protocol="evidence_collection_workspace_v1"/);
assert.match(markup, /Evidence collection workspace/);
assert.match(markup, /collecting_evidence/);
assert.match(markup, /1 \/ 4/);
assert.match(markup, /Missing claims/);
assert.match(markup, /rank_delta/);
assert.match(markup, /competitor_missed/);
assert.match(markup, /official_plan_verification/);
assert.match(markup, /rank_history_calibration/);
assert.match(markup, /needs_capture/);
assert.match(markup, /site:eea.gd.gov.cn/);
assert.match(markup, /Next search actions/);
assert.match(markup, /Search request batch/);
assert.match(markup, /web_evidence_search_requests_v1/);
assert.match(markup, /rank-history/);
assert.match(markup, /gaokao\.chsi\.com\.cn/);
assert.match(markup, /historical_data/);
assert.match(markup, /rank_delta/);
assert.match(markup, /Search requests do not support claims/);
assert.match(markup, /low_attention_signal/);
assert.match(markup, /counter_evidence/);
assert.match(markup, /hype_pressure/);
assert.match(markup, /What evidence would disprove/);
assert.match(markup, /admission probability/);
assert.match(markup, /Evidence triangulation/);
assert.match(markup, /evidence_triangulation_report_v1/);
assert.match(markup, /needs_more_evidence/);
assert.match(markup, /authoritative/);
assert.match(markup, /unsupported/);
assert.match(markup, /Keep public-opinion evidence as hypothesis-only/);
assert.match(markup, /source diversity, conflicts, and claim boundaries/);
assert.match(markup, /Evidence gap follow-up/);
assert.match(markup, /evidence_gap_search_plan_v1/);
assert.match(markup, /needs_second_source/);
assert.match(markup, /second independent source/);
assert.match(markup, /data\.example/);
assert.match(markup, /Search plans do not prove claims/);
assert.match(markup, /Capture worksheet/);
assert.match(markup, /copyable submission/i);
assert.match(markup, /web_evidence_capture_worksheet_v1/);
assert.match(markup, /&quot;taskId&quot;: &quot;rank-history&quot;/);
assert.match(markup, /&quot;sourceTier&quot;: &quot;historical_data&quot;/);
assert.match(markup, /&quot;claimedSupports&quot;: \[/);
assert.match(markup, /professional group/);
assert.match(markup, /not make final recommendations/);

console.log("Evidence collection workspace panel behavior test passed");

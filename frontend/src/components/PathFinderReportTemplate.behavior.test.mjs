import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const templatePath = path.join(here, "PathFinderReportTemplate.tsx");
const source = fs
  .readFileSync(templatePath, "utf8")
  .replace(/import\.meta\.env\.BASE_URL/g, '"/app/"');
const output = ts.transpileModule(source, {
  compilerOptions: {
    esModuleInterop: true,
    jsx: ts.JsxEmit.ReactJSX,
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
  },
}).outputText;

const module = { exports: {} };
const localRequire = (specifier) => {
  if (specifier === "react/jsx-runtime") {
    return {
      Fragment: Symbol("Fragment"),
      jsx: () => null,
      jsxs: () => null,
    };
  }
  if (specifier === "@/lib/deliveryReadiness") {
    return {
      buildDeliveryReadinessSummary: () => ({
        status: "needs_review",
        score: 60,
        gates: [],
        claimBoundary: "readiness boundary",
        nextAction: "review official data",
      }),
    };
  }
  if (specifier === "@/lib/deepOpportunityCard") {
    return {
      buildDeepOpportunityCard: () => ({
        evidencePillars: [
          { label: "量化定位", score: 84, interpretation: "rank fit" },
          { label: "科研资源", score: 88, interpretation: "research fit" },
          { label: "本科生可获得性", score: 82, interpretation: "undergrad access" },
          { label: "真实就业", score: 81, interpretation: "job fit" },
        ],
        researchSignals: ["research signal", "lab signal", "paper signal"],
        graduateSignals: ["graduate signal"],
        counterEvidenceChecks: ["counter evidence"],
        evidenceGaps: ["gap"],
        nextActions: ["next action"],
      }),
      exampleDeepOpportunityInput: {},
    };
  }
  if (specifier === "@/lib/deepEvidenceCollectionPlan") {
    return {
      exampleCollectionContext: {
        province: "广东",
        schoolName: "华南理工示例校",
        majorName: "智能制造与数据工程",
        targetYear: 2026,
      },
      buildDeepEvidenceCollectionPlan: () => ({
        targetLabel: "广东 2026 华南理工示例校 智能制造与数据工程",
        tasks: [],
      }),
    };
  }
  if (specifier === "@/lib/evidenceAutopilot") {
    return {
      buildEvidenceAutopilotRun: () => ({
        searchTasks: [],
        evidenceResults: [
          { claim: "official_admission", excerpts: ["official excerpt"] },
        ],
        evaluation: {
          opportunityScore: 90,
          claimBoundary: "radar boundary",
          p0Gate: { passedCount: 6, totalCount: 6 },
          counterEvidence: { hit: false, reasons: [] },
          horizonSignals: [
            { horizon: "短期录取", status: "supported", summary: "short" },
            { horizon: "中期升学", status: "supported", summary: "mid" },
            { horizon: "长期职业", status: "supported", summary: "long" },
          ],
        },
      }),
    };
  }
  if (specifier === "@/lib/evidenceAutopilotSnapshotProvider") {
    return {
      buildEvidenceAutopilotSnapshotProviderResults: () => [],
    };
  }
  if (specifier === "@/lib/evidenceAutopilotRealCaseProvider") {
    return {
      loadEvidenceAutopilotRealCaseFixture: () => ({
        claimBoundary: "Real Case v0 fixture supports an auditable opportunity hypothesis only.",
      }),
      buildEvidenceAutopilotRealCaseProviderResults: () => [],
    };
  }
  throw new Error(`Unexpected require: ${specifier}`);
};

new Function("require", "module", "exports", output)(localRequire, module, module.exports);

assert.equal(
  typeof module.exports.buildReportPayload,
  "function",
  "buildReportPayload should be exported for evidence-binding tests",
);
assert.equal(
  typeof module.exports.buildDeepOpportunityEvidenceAuditTrailFromRecords,
  "function",
  "report should convert live reviewed-evidence records into an audit trail",
);

const liveReviewedTrail = module.exports.buildDeepOpportunityEvidenceAuditTrailFromRecords([
  {
    reviewId: "review-live-001",
    caseId: "scut-im-v0",
    reviewer: "operator-a",
    targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
    recordedAt: "2026-06-24T00:00:00Z",
    ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
    reviewedEvidenceCard: {
      taskId: "employment-market",
      status: "captured_candidate",
      sourceTitle: "Live reviewed job-market sample",
      sourceUrl: "operator-review://review-live-001",
      sourceType: "job",
      excerpt: "Visible job sample describes robotics integration responsibilities.",
      capturedAt: "2026-06-24",
      confidence: "medium",
      reviewAction: "Use as operator-captured job sample only.",
    },
  },
  {
    reviewId: "review-live-002",
    caseId: "scut-im-v0",
    reviewer: "operator-a",
    targetLabel: "Guangdong 2026 SCUT intelligent manufacturing",
    recordedAt: "2026-06-24T00:10:00Z",
    ledgerPath: "logs/evidence_autopilot/reviewed_evidence.jsonl",
    reviewedEvidenceCard: {
      taskId: "wechat-public-account",
      status: "operator_review",
      sourceTitle: "Incomplete WeChat note",
      sourceUrl: "",
      sourceType: "wechat",
      excerpt: "",
      capturedAt: "",
      confidence: "low",
      reviewAction: "Collect visible screenshot before use.",
    },
  },
]);
assert.equal(liveReviewedTrail.length, 1);
assert.equal(liveReviewedTrail[0].reviewId, "review-live-001");
assert.equal(liveReviewedTrail[0].caseId, "scut-im-v0");
assert.equal(liveReviewedTrail[0].sourceUrl, "operator-review://review-live-001");
assert.match(liveReviewedTrail[0].reviewAction, /operator-captured job sample/);

const reportData = module.exports.buildReportPayload({
  gameMatrix: {
    major_group_rows: [
      {
        school_name: "真实大学",
        major_group_code: "201",
        strategy_tag: "target",
        admission_prob: 0.62,
        first_hit_prob: 0.41,
        tail_assignment_risk: 0.12,
        quant_evidence: ["真实证据：2025 retrospective rank band"],
      },
    ],
    total_rush: 1,
    total_target: 1,
    total_safe: 1,
    volunteer_plan: {
      expected_admission_prob: 0.68,
      admission_probability_lower_bound: 0.61,
      admission_probability_upper_bound: 0.72,
      key_prefix_count: 1,
      shadowed_choice_count: 0,
      blacklist_violation_count: 0,
    },
    plan_audit_summary: {
      status: "needs_review",
      coverage: { coverage_sufficient: true, deficits: {} },
      data_boundary: {
        target_year: 2026,
        formal_recommendation_ready: false,
        limitations: ["2026 官方数据仍需复核"],
      },
      student_facing_items: [
        {
          title: "官方数据边界",
          detail: "正式填报前复核招生计划",
          severity: "P2",
          type: "data_boundary",
        },
      ],
    },
  },
  deliveryProfile: {
    score: 610,
    rank: 52000,
    subject_group: "physics",
    preferred_cities: ["广州"],
    preferred_majors: ["电子信息"],
    blacklist_majors: ["土木"],
    riasec_top_codes: ["I", "R"],
    mbti_type: "未填写",
  },
});

assert.equal(reportData.cards[0].school, "真实大学");
assert.match(reportData.evaluations[0].evidence, /真实证据/);
assert.match(reportData.profileLine, /广州/);
assert.match(reportData.profileLine, /电子信息/);
assert.equal(reportData.metrics[0].value, "1");
assert.equal(reportData.metrics[1].value, "1");
assert.equal(reportData.metrics[2].value, "1");
assert.equal(reportData.metrics[3].value, "1");
assert.doesNotMatch(reportData.profileLine, /示例29|北京|南京|成都|大连/);
assert.doesNotMatch(
  reportData.metrics.map((item) => `${item.label} ${item.value}`).join(" "),
  /985 院校 24|A\+ 学科 36/,
);
assert.doesNotMatch(reportData.studentLabel, /示例29/);

console.log("PathFinder report template behavior test passed");

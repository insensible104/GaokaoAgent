import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const templatePath = path.join(here, "PathFinderReportTemplate.tsx");
const source = fs.readFileSync(templatePath, "utf8");
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
  throw new Error(`Unexpected require: ${specifier}`);
};

new Function("require", "module", "exports", output)(localRequire, module, module.exports);

assert.equal(
  typeof module.exports.buildReportPayload,
  "function",
  "buildReportPayload should be exported for evidence-binding tests",
);

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

assert.equal(reportData.rows[0].school, "真实大学");
assert.match(reportData.rows[0].evidence, /真实证据/);
assert.match(reportData.profileLine, /广州/);
assert.match(reportData.profileLine, /电子信息/);
assert.match(reportData.strategyLine, /Rush 1 \/ Target 1 \/ Safe 1/);
assert.match(reportData.focusLine, /关键前缀 1/);
assert.doesNotMatch(reportData.profileLine, /示例29|北京|南京|成都|大连/);
assert.doesNotMatch(reportData.strategyLine, /985 院校 24|A\+ 学科 36/);
assert.doesNotMatch(reportData.studentLabel, /示例29/);

console.log("PathFinder report template behavior test passed");

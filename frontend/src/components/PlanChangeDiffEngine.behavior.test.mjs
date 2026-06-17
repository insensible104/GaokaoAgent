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

const diffEngine = loadTsModule(path.join(libDir, "planChangeDiffEngine.ts"));
const ledger = loadTsModule(path.join(libDir, "planChangeOpportunityLedger.ts"));

const officialSource = "Guangdong Education Exam Authority enrollment plan";

const priorRows = [
  row({ year: 2025, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080901", majorName: "Computer Science", quota: 20, subjects: ["physics", "chemistry"] }),
  row({ year: 2025, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080902", majorName: "Software Engineering", quota: 14, subjects: ["physics"] }),
  row({ year: 2025, schoolCode: "10561", schoolName: "South China Tech", groupCode: "202", majorCode: "080903", majorName: "Network Engineering", quota: 16, subjects: ["physics"] }),
  row({ year: 2025, schoolCode: "11845", schoolName: "Pearl River Normal", groupCode: "205", majorCode: "050201", majorName: "English", quota: 12, subjects: ["history"] }),
  row({ year: 2025, schoolCode: "11845", schoolName: "Pearl River Normal", groupCode: "206", majorCode: "050301", majorName: "Journalism", quota: 8, subjects: ["history"] }),
  row({ year: 2025, schoolCode: "11845", schoolName: "Pearl River Normal", groupCode: "207", majorCode: "050301", majorName: "Journalism", quota: 8, subjects: ["history"] }),
  row({ year: 2025, schoolCode: "10559", schoolName: "Lingnan Medical", groupCode: "211", majorCode: "100201", majorName: "Clinical Medicine", quota: 28, subjects: ["physics", "chemistry"] }),
];

const currentRows = [
  row({ year: 2026, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080901", majorName: "Computer Science", quota: 36, subjects: ["physics", "chemistry"] }),
  row({ year: 2026, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080902", majorName: "Software Engineering", quota: 10, subjects: ["physics"] }),
  row({ year: 2026, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080904", majorName: "Artificial Intelligence", quota: 18, subjects: ["physics", "chemistry"] }),
  row({ year: 2026, schoolCode: "11845", schoolName: "Pearl River Normal", groupCode: "205", majorCode: "050201", majorName: "English", quota: 12, subjects: ["history"] }),
  row({ year: 2026, schoolCode: "11845", schoolName: "Pearl River Normal", groupCode: "208", majorCode: "050201", majorName: "English", quota: 6, subjects: ["history"] }),
  row({ year: 2026, schoolCode: "11845", schoolName: "Pearl River Normal", groupCode: "209", majorCode: "050301", majorName: "Journalism", quota: 16, subjects: ["history"] }),
  row({ year: 2026, schoolCode: "10559", schoolName: "Lingnan Medical", groupCode: "211", majorCode: "100201", majorName: "Clinical Medicine", quota: 28, subjects: ["physics", "chemistry", "biology"] }),
];

function row({ year, schoolCode, schoolName, groupCode, majorCode, majorName, quota, subjects }) {
  return {
    officialSource,
    year,
    province: "Guangdong",
    batch: "本科批",
    schoolCode,
    schoolName,
    majorGroupCode: groupCode,
    majorCode,
    majorName,
    quota,
    subjectRequirements: subjects,
  };
}

const result = diffEngine.diffEnrollmentPlans({
  priorYear: 2025,
  currentYear: 2026,
  priorRows,
  currentRows,
  officialSource,
});

assert.equal(result.protocol, "plan_change_diff_engine_v1");
assert.equal(result.priorYear, 2025);
assert.equal(result.currentYear, 2026);
assert.equal(result.diffs.every((diff) => diff.sourceTier === "official"), true);

assertDiff("quota_expansion", "10561", "201", "080901", { before: 20, after: 36 });
assertDiff("quota_reduction", "10561", "201", "080902", { before: 14, after: 10 });
assertDiff("new_major", "10561", "201", "080904", { before: null, after: 18 });
assertDiff("discontinued_major", "10561", "202", "080903", { before: 16, after: null });
assertDiff("group_split", "11845", "208", "050201", { before: ["205"], after: ["205", "208"] });
assertDiff("group_merge", "11845", "209", "050301", { before: ["206", "207"], after: ["209"] });
assertDiff("subject_requirement_change", "10559", "211", "100201", {
  before: ["chemistry", "physics"],
  after: ["biology", "chemistry", "physics"],
});

const officialChanges = diffEngine.convertDiffsToOfficialChanges(result.diffs, {
  rankDeltaEstimates: {
    "10561-201-080901-quota_expansion": {
      direction: "easier",
      rank_delta: 1800,
      explanation: "Quota expands by 16 seats; use only as a calibrated directional placeholder.",
    },
  },
  externalPlanCoverage: {
    "10561-201-080901-quota_expansion": {
      competitor_missed: true,
      checked_sources: ["qianwen", "teacher"],
      evidence: "External plans kept the 2025 quota assumption.",
    },
  },
  recommendationActions: {
    "10561-201-080901-quota_expansion": "promote",
  },
  riskGuards: {
    "10561-201-080901-quota_expansion": {
      level: "medium",
      checks: ["verify group code before signoff", "do not use as sole safety anchor"],
    },
  },
});

const convertedExpansion = officialChanges.find((change) => change.change_type === "quota_expansion");
assert.equal(convertedExpansion.official_source, officialSource);
assert.equal(convertedExpansion.source_tier, "official");
assert.equal(convertedExpansion.before, 20);
assert.equal(convertedExpansion.after, 36);
assert.equal(convertedExpansion.rank_delta_estimate.rank_delta, 1800);

const ledgerResult = ledger.buildPlanChangeOpportunityLedger({
  gameMatrix: {
    major_group_rows: [
      {
        school_name: "South China Tech",
        school_code: "10561",
        major_group_code: "201",
        choice_index: 1,
        strategy_tag: "target",
        plan_change_explanation: {
          status: "official_diff",
          ranking_impact: "official_diff_applied",
          official_changes: [convertedExpansion],
        },
      },
    ],
    data_vintage: {
      target_year: 2026,
      formal_recommendation_ready: true,
      limitations: [],
    },
  },
  externalPlanAuditSummary: { parsedCount: 2 },
});

assert.equal(ledgerResult.status, "ready");
assert.equal(ledgerResult.opportunities[0].diffType, "quota_expansion");
assert.match(ledgerResult.opportunities[0].auditTrail.join("\n"), /official_source -> diff_type -> affected_rows/);

function assertDiff(diffType, schoolCode, groupCode, majorCode, values) {
  const diff = result.diffs.find(
    (candidate) =>
      candidate.diffType === diffType &&
      candidate.row.schoolCode === schoolCode &&
      candidate.row.majorGroupCode === groupCode &&
      candidate.row.majorCode === majorCode,
  );
  assert.ok(diff, `Expected ${diffType} for ${schoolCode}-${groupCode}-${majorCode}`);
  assert.deepEqual(diff.before, values.before);
  assert.deepEqual(diff.after, values.after);
  assert.match(diff.evidence, /Guangdong Education Exam Authority/);
  assert.equal(diff.auditKey, `${schoolCode}-${groupCode}-${majorCode}-${diffType}`);
}

console.log("Plan change diff engine behavior test passed");

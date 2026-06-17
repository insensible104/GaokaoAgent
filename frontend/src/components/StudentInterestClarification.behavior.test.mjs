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

const clarification = loadTsModule(path.join(libDir, "studentInterestClarification.ts"));

const explicitBrief = clarification.buildStudentInterestClarificationBrief({
  preferredMajors: ["Computer Science", "Software Engineering"],
  blacklistMajors: ["Civil Engineering", "Materials"],
  riskTolerance: "balanced",
  acceptableTradeoffs: ["can_accept_medium_adjustment_risk", "can_accept_outprovince"],
  conceptAnswers: {
    professionalGroup: "understands_group_unit",
    adjustment: "accepts_worst_case_major",
    safeAnchor: "checks_worst_case",
    interestTradeoff: "course_industry_city_workstyle",
  },
  careerAssessment: {
    mode: "quick",
    answers: {
      I1: 5,
      I2: 5,
      R1: 4,
      R2: 4,
      A1: 2,
      A2: 2,
      S1: 2,
      S2: 2,
      E1: 3,
      E2: 3,
      C1: 3,
      C2: 3,
    },
    mbti_type: "INTJ",
    career_values: ["growth", "stability"],
  },
});

assert.equal(explicitBrief.protocol, "student_interest_clarification_v1");
assert.equal(explicitBrief.status, "ready_for_plan_discussion");
assert.equal(explicitBrief.hardBoundaries.includes("Do not recommend majors matching blacklist: Civil Engineering, Materials."), true);
assert.equal(explicitBrief.softSignals.some((signal) => signal.source === "riasec" && signal.weight === "soft"), true);
assert.equal(explicitBrief.softSignals.some((signal) => signal.source === "mbti" && signal.allowedUse === "communication_only"), true);
assert.match(explicitBrief.interestAnchor, /Computer Science/);
assert.match(explicitBrief.tradeoffQuestions.join("\n"), /If this group protects admission chance but includes adjustment risk/);
assert.match(explicitBrief.tradeoffQuestions.join("\n"), /Would you still accept the group if the final major is not Computer Science/);
assert.match(explicitBrief.conceptExplanations.join("\n"), /Professional group/);
assert.match(explicitBrief.conceptExplanations.join("\n"), /Safe anchor/);
assert.equal(explicitBrief.conceptReadiness.protocol, "family_concept_readiness_v1");
assert.equal(explicitBrief.conceptReadiness.status, "ready");
assert.equal(explicitBrief.conceptReadiness.checkpoints.length, 4);
assert.equal(explicitBrief.conceptReadiness.checkpoints.every((checkpoint) => checkpoint.status === "understood"), true);
assert.match(explicitBrief.conceptReadiness.nextAction, /row-level discussion/i);
assert.match(explicitBrief.claimBoundary, /does not change admission probability/);
assert.equal(explicitBrief.blockedClaims.includes("Do not use MBTI or RIASEC to override explicit blacklist majors."), true);

const misconceptionBrief = clarification.buildStudentInterestClarificationBrief({
  preferredMajors: ["Computer Science"],
  blacklistMajors: ["Civil Engineering"],
  riskTolerance: "balanced",
  acceptableTradeoffs: ["can_accept_medium_adjustment_risk"],
  conceptAnswers: {
    professionalGroup: "single_major_only",
    adjustment: "only_accepts_first_major",
    safeAnchor: "score_only",
    interestTradeoff: "hot_major_label_only",
  },
});

assert.equal(misconceptionBrief.status, "ready_for_plan_discussion");
assert.equal(misconceptionBrief.conceptReadiness.status, "needs_concept_clarification");
assert.equal(
  misconceptionBrief.conceptReadiness.checkpoints.some(
    (checkpoint) => checkpoint.concept === "professional_group" && checkpoint.status === "misconception_risk",
  ),
  true,
);
assert.equal(
  misconceptionBrief.conceptReadiness.checkpoints.some(
    (checkpoint) => checkpoint.concept === "safe_anchor" && /score-only/.test(checkpoint.misconception ?? ""),
  ),
  true,
);
assert.match(misconceptionBrief.conceptReadiness.nextAction, /Do not show final row ranking/i);
assert.match(misconceptionBrief.tradeoffQuestions.join("\n"), /single major/i);
assert.match(misconceptionBrief.blockedClaims.join("\n"), /Do not present a safe anchor to a family that treats safe as score-only/);

const vagueBrief = clarification.buildStudentInterestClarificationBrief({
  preferredMajors: [],
  blacklistMajors: [],
  riskTolerance: "unknown",
  acceptableTradeoffs: [],
  careerAssessment: {
    mode: "skip",
    answers: {},
    career_values: [],
  },
});

assert.equal(vagueBrief.status, "needs_clarification");
assert.match(vagueBrief.interestAnchor, /not explicit enough/);
assert.equal(vagueBrief.missingInputs.includes("preferred major direction"), true);
assert.equal(vagueBrief.missingInputs.includes("blacklist majors"), true);
assert.equal(vagueBrief.missingInputs.includes("risk and adjustment tolerance"), true);
assert.equal(vagueBrief.conceptReadiness.status, "needs_concept_clarification");
assert.equal(vagueBrief.conceptReadiness.checkpoints.some((checkpoint) => checkpoint.status === "needs_answer"), true);
assert.equal(vagueBrief.tradeoffQuestions.length >= 4, true);
assert.equal(vagueBrief.hardBoundaries.length, 0);
assert.equal(vagueBrief.softSignals.length, 0);

console.log("Student interest clarification behavior test passed");

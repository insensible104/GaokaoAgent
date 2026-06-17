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
const discovery = loadTsModule(path.join(libDir, "opportunityDiscoveryEngine.ts"), {
  "./planChangeDiffEngine": diffEngine,
});
const planner = loadTsModule(path.join(libDir, "webEvidencePlanner.ts"), {
  "./opportunityDiscoveryEngine": discovery,
});
const intake = loadTsModule(path.join(libDir, "webEvidenceIntake.ts"), {
  "./webEvidencePlanner": planner,
});
const clarification = loadTsModule(path.join(libDir, "studentInterestClarification.ts"), {
  "./careerAssessment": {},
});
const interpretation = loadTsModule(path.join(libDir, "evidenceBackedInterpretationPackage.ts"), {
  "./opportunityDiscoveryEngine": discovery,
  "./webEvidencePlanner": planner,
  "./webEvidenceIntake": intake,
  "./studentInterestClarification": clarification,
});

const { discoveryLedger, evidencePlan } = buildDiscoveryAndPlan();
const reviewReadyIntake = intake.evaluateWebEvidenceResults({
  evidencePlan,
  results: evidencePlan.tasks.map((task) => resultForTask(task)),
});
const packageResult = interpretation.buildEvidenceBackedInterpretationPackage({
  discoveryLedger,
  evidencePlan,
  intakeResult: reviewReadyIntake,
  interestBrief: buildInterestBrief(),
  studentName: "Student A",
});

assert.equal(packageResult.protocol, "evidence_backed_interpretation_package_v1");
assert.equal(packageResult.status, "counselor_review_ready");
assert.match(packageResult.claimBoundary, /not a final filing recommendation/);
assert.match(packageResult.executiveSummary, /review-ready opportunity hypothesis/i);
assert.doesNotMatch(packageResult.executiveSummary, /final recommendation/i);
assert.equal(packageResult.opportunityCards.length, 1);

const [card] = packageResult.opportunityCards;
assert.equal(card.status, "counselor_review_ready");
assert.equal(card.officialEvidence.status, "supported");
assert.equal(card.rankEvidence.status, "supported");
assert.equal(card.publicOpinionEvidence.status, "hypothesis_only");
assert.equal(card.externalPlanEvidence.status, "supported");
assert.equal(card.familyConcepts.status, "explained");
assert.match(card.familyReadableExplanation, /Professional group/);
assert.match(card.familyReadableExplanation, /Adjustment/);
assert.match(card.familyReadableExplanation, /Safe anchor/);
assert.equal(card.familyDecisionBrief.protocol, "family_decision_brief_v1");
assert.equal(card.familyDecisionBrief.status, "ready_for_family_discussion");
assert.match(card.familyDecisionBrief.interestFitSummary, /Computer Science/);
assert.match(card.familyDecisionBrief.riskPosture, /balanced/);
assert.equal(card.familyDecisionBrief.conceptCheckpoints.length >= 4, true);
assert.equal(card.familyDecisionBrief.conceptReadiness.status, "ready");
assert.equal(card.familyDecisionBrief.conceptReadiness.checkpoints.every((checkpoint) => checkpoint.status === "understood"), true);
assert.equal(card.familyDecisionBrief.hardBoundaries.some((boundary) => /Civil Engineering/.test(boundary)), true);
assert.match(card.familyDecisionBrief.decisionQuestions.join("\n"), /Would you still accept/);
assert.match(card.familyDecisionBrief.cannotClaim.join("\n"), /final recommendation/i);
assert.equal(card.sourceLinks.length >= 5, true);
assert.equal(card.nextActions.includes("Counselor must review attached official source rows before signoff."), true);
assert.equal(card.nextActions.includes("Keep public-opinion trend as a hypothesis, not as proof of demand."), true);
assert.deepEqual(packageResult.unresolvedBlockers, []);

const blockedIntake = intake.evaluateWebEvidenceResults({
  evidencePlan,
  results: [
    resultForTask(evidencePlan.tasks.find((task) => task.taskType === "public_opinion_scan")),
    resultForTask(evidencePlan.tasks.find((task) => task.taskType === "family_concept_clarification")),
  ],
});
const blockedPackage = interpretation.buildEvidenceBackedInterpretationPackage({
  discoveryLedger,
  evidencePlan,
  intakeResult: blockedIntake,
  interestBrief: buildInterestBrief({ riskTolerance: "conservative" }),
  studentName: "Student A",
});

assert.equal(blockedPackage.status, "blocked");
assert.equal(blockedPackage.opportunityCards[0].status, "blocked");
assert.match(blockedPackage.executiveSummary, /not ready/i);
assert.match(blockedPackage.unresolvedBlockers.join("\n"), /official_plan_verification/);
assert.equal(blockedPackage.opportunityCards[0].officialEvidence.status, "missing");
assert.equal(blockedPackage.opportunityCards[0].publicOpinionEvidence.status, "hypothesis_only");
assert.equal(blockedPackage.opportunityCards[0].externalPlanEvidence.status, "missing");
assert.equal(blockedPackage.opportunityCards[0].familyDecisionBrief.status, "blocked_by_missing_evidence");
assert.match(blockedPackage.opportunityCards[0].familyDecisionBrief.riskPosture, /conservative/);
assert.equal(blockedPackage.opportunityCards[0].nextActions.includes("Attach official plan verification before claiming official change."), true);
assert.equal(blockedPackage.opportunityCards[0].nextActions.includes("Attach external-plan comparison before claiming competitors missed it."), true);

function resultForTask(taskItem) {
  assert.ok(taskItem, "Expected task item");
  const base = {
    taskId: taskItem.id,
    capturedAt: "2026-06-16",
  };
  if (taskItem.taskType === "official_plan_verification") {
    return {
      ...base,
      sourceTitle: "Guangdong official 2026 enrollment plan",
      sourceUrl: "https://eea.gd.gov.cn/2026-plan",
      sourceTier: "official",
      excerpts: ["10561 major group 201 Computer Science quota 36"],
      claimedSupports: ["official_diff"],
    };
  }
  if (taskItem.taskType === "school_rule_verification") {
    return {
      ...base,
      sourceTitle: "South China Tech 2026 admission charter",
      sourceUrl: "https://admission.example/charter-2026",
      sourceTier: "official",
      excerpts: ["Adjustment stays inside eligible majors in the same group."],
      claimedSupports: ["risk_guard"],
    };
  }
  if (taskItem.taskType === "rank_history_calibration") {
    return {
      ...base,
      sourceTitle: "Guangdong historical admission rank table",
      sourceUrl: "https://data.example/rank-history",
      sourceTier: "historical_data",
      excerpts: ["2025 rank 42000; 2024 rank 43800; quota context retained."],
      claimedSupports: ["rank_delta"],
    };
  }
  if (taskItem.taskType === "public_opinion_scan") {
    return {
      ...base,
      sourceTitle: "Search summary for non-local engineering attention",
      sourceUrl: "https://search.example/non-local-engineering",
      sourceTier: "public_opinion",
      excerpts: ["Search snippets emphasize local schools and rarely mention the quota expansion."],
      claimedSupports: ["hypothesis_only"],
    };
  }
  if (taskItem.taskType === "external_plan_comparison") {
    return {
      ...base,
      sourceTitle: "Qianwen and teacher plan comparison",
      sourceUrl: "https://example.com/external-plan-review",
      sourceTier: "competitor_plan",
      excerpts: ["External plans keep the 2025 quota assumption and omit the expansion."],
      claimedSupports: ["competitor_missed"],
    };
  }
  return {
    ...base,
    sourceTitle: "Family concept checklist",
    sourceUrl: "internal://concept-brief",
    sourceTier: "concept",
    excerpts: ["Professional group, adjustment, safe anchor, and interest tradeoff explained."],
    claimedSupports: ["parent_understanding"],
  };
}

function buildInterestBrief(overrides = {}) {
  return clarification.buildStudentInterestClarificationBrief({
    preferredMajors: ["Computer Science", "Software Engineering"],
    blacklistMajors: ["Civil Engineering", "Materials"],
    riskTolerance: overrides.riskTolerance ?? "balanced",
    acceptableTradeoffs: ["can_accept_medium_adjustment_risk", "can_accept_outprovince"],
    conceptAnswers: {
      professionalGroup: "understands_group_unit",
      adjustment: "accepts_worst_case_major",
      safeAnchor: "checks_worst_case",
      interestTradeoff: "course_industry_city_workstyle",
    },
    careerAssessment: {
      mode: "quick",
      answers: { I1: 5, I2: 5, R1: 4, R2: 4, A1: 2, A2: 2, S1: 2, S2: 2, E1: 3, E2: 3, C1: 3, C2: 3 },
      career_values: ["growth", "stability"],
    },
  });
}

function buildDiscoveryAndPlan() {
  const officialSource = "Guangdong Education Exam Authority 2026 enrollment plan";
  const diffResult = diffEngine.diffEnrollmentPlans({
    priorYear: 2025,
    currentYear: 2026,
    officialSource,
    priorRows: [
      row({ year: 2025, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080901", majorName: "Computer Science", quota: 20, subjects: ["physics", "chemistry"] }),
    ],
    currentRows: [
      row({ year: 2026, schoolCode: "10561", schoolName: "South China Tech", groupCode: "201", majorCode: "080901", majorName: "Computer Science", quota: 36, subjects: ["physics", "chemistry"] }),
    ],
  });
  const discoveryLedger = discovery.buildOpportunityDiscoveryLedger({
    trendSignals: [
      {
        id: "trend-low-attention-tech",
        topic: "low attention to non-local engineering groups",
        sourceKind: "social_summary",
        attention: "low",
        sentiment: "avoidance",
        schoolCode: "10561",
        majorKeywords: ["Computer"],
        evidence: "Search and discussion summaries focus on local brands, not the quota expansion.",
      },
    ],
    planDiffs: diffResult.diffs,
    rankDeltaEstimates: {
      "10561-201-080901-quota_expansion": {
        direction: "easier",
        rankDelta: 1800,
        confidence: "medium",
        explanation: "Quota expands from 20 to 36 seats; demand calibration is still required.",
      },
    },
    studentProfile: {
      preferredMajorKeywords: ["Computer", "Software"],
      blacklistMajorKeywords: ["Civil", "Materials"],
      riskTolerance: "balanced",
      acceptableTradeoffs: ["can_accept_medium_risk"],
    },
  });

  const evidencePlan = planner.buildWebEvidenceResearchPlan({
    discoveryLedger,
    targetYear: 2026,
    province: "Guangdong",
    externalPlanSources: ["qianwen", "tencent", "teacher", "family"],
  });

  return { discoveryLedger, evidencePlan };
}

function row({ year, schoolCode, schoolName, groupCode, majorCode, majorName, quota, subjects }) {
  return {
    year,
    officialSource: "Guangdong Education Exam Authority 2026 enrollment plan",
    province: "Guangdong",
    batch: "undergraduate",
    schoolCode,
    schoolName,
    majorGroupCode: groupCode,
    majorCode,
    majorName,
    quota,
    subjectRequirements: subjects,
  };
}

console.log("Evidence-backed interpretation package behavior test passed");

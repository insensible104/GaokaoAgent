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

const roadmapModule = loadTsModule(path.join(libDir, "familyDecisionClarityRoadmap.ts"), {
  "./evidenceBackedInterpretationPackage": {},
  "./detailedVolunteerPlanInterpretation": {},
  "./studentInterestClarification": {},
});

const readyDecisionBrief = {
  protocol: "family_decision_brief_v1",
  status: "ready_for_family_discussion",
  interestFitSummary: "Primary interest direction: Computer Science, Software Engineering. Student fit is fit.",
  riskPosture: "Interest brief is ready_for_plan_discussion; risk tolerance is balanced.",
  hardBoundaries: ["Do not recommend majors matching blacklist: Civil Engineering, Materials."],
  conceptCheckpoints: [
    "Professional group: the unit of filing is a school major group, not a single favorite major.",
    "Adjustment: accepting adjustment protects admission chance, but the final major may change.",
    "Safe anchor: a safe row is only safe if the worst acceptable outcome is still acceptable.",
    "Interest tradeoff: interest means course content, industry path, city, work style, and regret tolerance, not only a hot major label.",
  ],
  conceptReadiness: {
    protocol: "family_concept_readiness_v1",
    status: "ready",
    checkpoints: [
      {
        concept: "professional_group",
        status: "understood",
        familyQuestion: "Can the family explain that filing is by school major group, not by one favorite major?",
        evidenceNeeded: "Family accepts group-level uncertainty before row-level discussion.",
      },
      {
        concept: "adjustment",
        status: "understood",
        familyQuestion: "Can the family name the worst acceptable adjusted major?",
        evidenceNeeded: "Family accepts at least one worst-case adjusted major.",
      },
      {
        concept: "safe_anchor",
        status: "understood",
        familyQuestion: "Can the family define safety by the worst acceptable outcome, not only by entry probability?",
        evidenceNeeded: "Family checks worst-case major, campus, fee, and city.",
      },
      {
        concept: "interest_tradeoff",
        status: "understood",
        familyQuestion: "Can the student describe interest by courses, industry path, city, work style, and regret tolerance?",
        evidenceNeeded: "Student gives interest reasons beyond a hot major label.",
      },
    ],
    nextAction: "Concept readiness supports row-level discussion.",
    claimBoundary: "Concept readiness is a communication gate.",
  },
  decisionQuestions: [
    "Would you still accept the group if the final major is not Computer Science?",
    "Which matters more for this row: school platform, major certainty, city, tuition, or low regret risk?",
  ],
  cannotClaim: [
    "This is not a final recommendation.",
    "Public-opinion evidence cannot prove admission probability or demand.",
  ],
};

const readyInterpretation = {
  protocol: "detailed_volunteer_plan_interpretation_v1",
  status: "ready_for_family_review",
  headline: "Student A: evidence-backed plan interpretation ready for family review",
  summary: "Quota expansion candidate opportunity with hypothesis-only trend language.",
  claimRows: [
    {
      claim: "concept_readiness",
      stance: "can_explain",
      familyWording: "Concept readiness supports row-level discussion.",
      evidenceBasis: ["professional_group: understood; Family accepts group-level uncertainty."],
      sourceRefs: ["Family concept checklist (concept)"],
      counterChecks: [],
      claimBoundary: "Concept readiness is a communication gate.",
    },
  ],
  familyDecisionPath: {
    conceptReadinessProtocol: "family_concept_readiness_v1",
    conceptReadinessStatus: "ready",
    requiredQuestions: [
      "Would you still accept the group if the final major is not Computer Science?",
    ],
    hardStops: ["Do not recommend majors matching blacklist: Civil Engineering, Materials."],
  },
  planPosition: {
    rowUse: "candidate_for_counselor_review",
    notARecommendationReasons: [
      "This is not a final recommendation.",
      "This is not an admission guarantee.",
    ],
    counselorSignoffChecklist: ["Verify the official source row."],
  },
  nextActions: ["Keep public-opinion wording hypothesis-only and preserve counter-evidence checks."],
  claimBoundary: "This detailed interpretation is not a final filing recommendation.",
};

const readyRoadmap = roadmapModule.buildFamilyDecisionClarityRoadmap({
  decisionBrief: readyDecisionBrief,
  detailedInterpretation: readyInterpretation,
});

assert.equal(readyRoadmap.protocol, "family_decision_clarity_roadmap_v1");
assert.equal(readyRoadmap.status, "ready_for_row_discussion");
assert.equal(readyRoadmap.rowDiscussionGate.canDiscussRows, true);
assert.equal(readyRoadmap.conceptCards.length, 4);
assert.equal(readyRoadmap.conceptCards.every((card) => card.status === "understood"), true);
assert.equal(readyRoadmap.interestAxes.map((axis) => axis.axis).includes("course_content"), true);
assert.equal(readyRoadmap.interestAxes.map((axis) => axis.axis).includes("regret_boundary"), true);
assert.match(readyRoadmap.parentStudentAlignment.questions.join("\n"), /school platform/);
assert.match(readyRoadmap.parentStudentAlignment.hardStops.join("\n"), /Civil Engineering/);
assert.match(readyRoadmap.rowDiscussionGate.nextAction, /row-level discussion/i);
assert.match(readyRoadmap.claimBoundary, /communication and decision-clarity/);

const misconceptionDecisionBrief = {
  ...readyDecisionBrief,
  conceptReadiness: {
    ...readyDecisionBrief.conceptReadiness,
    status: "needs_concept_clarification",
    checkpoints: [
      {
        concept: "professional_group",
        status: "misconception_risk",
        familyQuestion: "Which majors are inside the group, and would the family still accept the group if not assigned to the first major?",
        evidenceNeeded: "Family must restate that the filing unit is a school major group.",
        misconception: "Family appears to treat a professional group as a single major.",
      },
      {
        concept: "safe_anchor",
        status: "misconception_risk",
        familyQuestion: "Which worst-case major, campus, fee, or city outcome would make this row unsafe?",
        evidenceNeeded: "Family must reject score-only safety before safe-anchor use.",
        misconception: "Family appears to use a score-only definition of safe anchor.",
      },
      {
        concept: "interest_tradeoff",
        status: "misconception_risk",
        familyQuestion: "Which course content, work style, or city tradeoff would still make this major unacceptable?",
        evidenceNeeded: "Student must move beyond a hot-major label before interest-fit claims.",
        misconception: "Student appears to define interest only by a hot major label.",
      },
    ],
    nextAction: "Do not show final row ranking until misconception-risk and missing-answer checkpoints are resolved.",
  },
};

const repairRoadmap = roadmapModule.buildFamilyDecisionClarityRoadmap({
  decisionBrief: misconceptionDecisionBrief,
  detailedInterpretation: {
    ...readyInterpretation,
    status: "needs_counselor_review",
    familyDecisionPath: {
      ...readyInterpretation.familyDecisionPath,
      conceptReadinessStatus: "needs_concept_clarification",
    },
  },
});

assert.equal(repairRoadmap.status, "needs_concept_repair");
assert.equal(repairRoadmap.rowDiscussionGate.canDiscussRows, false);
assert.equal(repairRoadmap.conceptCards.some((card) => card.concept === "professional_group" && /single major/.test(card.misconception ?? "")), true);
assert.equal(repairRoadmap.conceptCards.some((card) => card.concept === "safe_anchor" && /score-only/.test(card.repairAction)), true);
assert.equal(repairRoadmap.interestAxes.some((axis) => axis.axis === "work_style" && /hot major label/.test(axis.prompt)), true);
assert.match(repairRoadmap.rowDiscussionGate.nextAction, /Do not show final row ranking/i);
assert.match(repairRoadmap.parentStudentAlignment.hardStops.join("\n"), /not a final recommendation/i);

const blockedRoadmap = roadmapModule.buildFamilyDecisionClarityRoadmap({
  decisionBrief: readyDecisionBrief,
  detailedInterpretation: {
    ...readyInterpretation,
    status: "blocked",
  },
});

assert.equal(blockedRoadmap.status, "blocked");
assert.equal(blockedRoadmap.rowDiscussionGate.canDiscussRows, false);
assert.match(blockedRoadmap.rowDiscussionGate.nextAction, /Resolve evidence and counselor-review blockers/i);

console.log("Family decision clarity roadmap behavior test passed");

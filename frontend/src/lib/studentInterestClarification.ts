import type { CareerAssessmentPayload } from "./careerAssessment";

export type InterestClarificationStatus = "ready_for_plan_discussion" | "needs_clarification";
export type RiskTolerance = "conservative" | "balanced" | "aggressive" | "unknown";

export interface StudentInterestClarificationInput {
  preferredMajors: string[];
  blacklistMajors: string[];
  riskTolerance: RiskTolerance;
  acceptableTradeoffs: string[];
  conceptAnswers?: FamilyConceptAnswers;
  careerAssessment?: CareerAssessmentPayload;
}

export type FamilyConceptKey =
  | "professional_group"
  | "adjustment"
  | "safe_anchor"
  | "interest_tradeoff";

export interface FamilyConceptAnswers {
  professionalGroup?: "understands_group_unit" | "single_major_only";
  adjustment?: "accepts_worst_case_major" | "only_accepts_first_major";
  safeAnchor?: "checks_worst_case" | "score_only";
  interestTradeoff?: "course_industry_city_workstyle" | "hot_major_label_only";
}

export type FamilyConceptReadinessStatus = "ready" | "needs_concept_clarification";
export type FamilyConceptCheckpointStatus = "understood" | "misconception_risk" | "needs_answer";

export interface FamilyConceptReadinessCheckpoint {
  concept: FamilyConceptKey;
  status: FamilyConceptCheckpointStatus;
  familyQuestion: string;
  evidenceNeeded: string;
  misconception?: string;
}

export interface FamilyConceptReadiness {
  protocol: "family_concept_readiness_v1";
  status: FamilyConceptReadinessStatus;
  checkpoints: FamilyConceptReadinessCheckpoint[];
  nextAction: string;
  claimBoundary: string;
}

export interface StudentInterestSoftSignal {
  source: "riasec" | "career_values" | "mbti";
  weight: "soft";
  allowedUse: "major_fit_context" | "communication_only";
  summary: string;
}

export interface StudentInterestClarificationBrief {
  protocol: "student_interest_clarification_v1";
  status: InterestClarificationStatus;
  interestAnchor: string;
  riskToleranceEcho: RiskTolerance;
  hardBoundaries: string[];
  softSignals: StudentInterestSoftSignal[];
  missingInputs: string[];
  tradeoffQuestions: string[];
  conceptExplanations: string[];
  conceptReadiness: FamilyConceptReadiness;
  blockedClaims: string[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Student interest clarification explains preference, tradeoff, and major-fit context. It does not change admission probability, override official requirements, or rescue blacklisted majors.";

const CONCEPT_READINESS_BOUNDARY =
  "Concept readiness is a communication gate for family discussion. It does not prove admission probability, safety, or final recommendation readiness.";

export function buildStudentInterestClarificationBrief(
  input: StudentInterestClarificationInput,
): StudentInterestClarificationBrief {
  const missingInputs = buildMissingInputs(input);
  return {
    protocol: "student_interest_clarification_v1",
    status: missingInputs.length === 0 ? "ready_for_plan_discussion" : "needs_clarification",
    interestAnchor: buildInterestAnchor(input),
    riskToleranceEcho: input.riskTolerance,
    hardBoundaries: buildHardBoundaries(input),
    softSignals: buildSoftSignals(input.careerAssessment),
    missingInputs,
    tradeoffQuestions: buildTradeoffQuestions(input),
    conceptExplanations: buildConceptExplanations(),
    conceptReadiness: buildConceptReadiness(input),
    blockedClaims: [
      "Do not use MBTI or RIASEC to override explicit blacklist majors.",
      "Do not use interest clarification to change admission probability.",
      "Do not call a row safe until adjustment and worst-case major outcomes are acceptable.",
      "Do not present a safe anchor to a family that treats safe as score-only.",
    ],
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildMissingInputs(input: StudentInterestClarificationInput): string[] {
  const missing: string[] = [];
  if (input.preferredMajors.length === 0) missing.push("preferred major direction");
  if (input.blacklistMajors.length === 0) missing.push("blacklist majors");
  if (input.riskTolerance === "unknown" || input.acceptableTradeoffs.length === 0) {
    missing.push("risk and adjustment tolerance");
  }
  return missing;
}

function buildInterestAnchor(input: StudentInterestClarificationInput): string {
  if (input.preferredMajors.length === 0) {
    return "The student's interest direction is not explicit enough for plan discussion.";
  }
  return `Primary interest direction: ${input.preferredMajors.join(", ")}.`;
}

function buildHardBoundaries(input: StudentInterestClarificationInput): string[] {
  const boundaries: string[] = [];
  if (input.blacklistMajors.length > 0) {
    boundaries.push(`Do not recommend majors matching blacklist: ${input.blacklistMajors.join(", ")}.`);
  }
  if (input.riskTolerance === "conservative") {
    boundaries.push("Avoid using high adjustment risk groups as safe anchors.");
  }
  return boundaries;
}

function buildSoftSignals(assessment?: CareerAssessmentPayload): StudentInterestSoftSignal[] {
  if (!assessment || assessment.mode === "skip") return [];
  const signals: StudentInterestSoftSignal[] = [
    {
      source: "riasec",
      weight: "soft",
      allowedUse: "major_fit_context",
      summary: `RIASEC answers are available in ${assessment.mode} mode and can only inform major-fit discussion.`,
    },
  ];
  if (assessment.career_values.length > 0) {
    signals.push({
      source: "career_values",
      weight: "soft",
      allowedUse: "major_fit_context",
      summary: `Career values to discuss: ${assessment.career_values.join(", ")}.`,
    });
  }
  if (assessment.mbti_type) {
    signals.push({
      source: "mbti",
      weight: "soft",
      allowedUse: "communication_only",
      summary: `MBTI ${assessment.mbti_type} is self-reported communication context only.`,
    });
  }
  return signals;
}

function buildTradeoffQuestions(input: StudentInterestClarificationInput): string[] {
  const preferred = input.preferredMajors[0] ?? "the preferred major";
  const questions = [
    `Would you still accept the group if the final major is not ${preferred}?`,
    "If this group protects admission chance but includes adjustment risk, what is the worst acceptable major?",
    "Which matters more for this row: school platform, major certainty, city, tuition, or low regret risk?",
    "Can this row be used as a safe anchor after considering worst-case major, campus, and fees?",
    "Which tradeoff would make you remove this row even if the admission probability is attractive?",
  ];
  if (input.conceptAnswers?.professionalGroup === "single_major_only") {
    questions.unshift("Before seeing rows, can the family explain why a professional group is not a single major?");
  }
  return questions;
}

function buildConceptExplanations(): string[] {
  return [
    "Professional group: the unit of filing is a school major group, not a single favorite major.",
    "Adjustment: accepting adjustment protects admission chance, but the final major may change.",
    "Safe anchor: a safe row is only safe if the worst acceptable outcome is still acceptable.",
    "Interest tradeoff: interest means course content, industry path, city, work style, and regret tolerance, not only a hot major label.",
  ];
}

function buildConceptReadiness(input: StudentInterestClarificationInput): FamilyConceptReadiness {
  const checkpoints = [
    professionalGroupCheckpoint(input.conceptAnswers),
    adjustmentCheckpoint(input),
    safeAnchorCheckpoint(input),
    interestTradeoffCheckpoint(input),
  ];
  const status = checkpoints.every((checkpoint) => checkpoint.status === "understood")
    ? "ready"
    : "needs_concept_clarification";
  return {
    protocol: "family_concept_readiness_v1",
    status,
    checkpoints,
    nextAction: status === "ready"
      ? "Concept readiness supports row-level discussion."
      : "Do not show final row ranking until misconception-risk and missing-answer checkpoints are resolved.",
    claimBoundary: CONCEPT_READINESS_BOUNDARY,
  };
}

function professionalGroupCheckpoint(
  answers?: FamilyConceptAnswers,
): FamilyConceptReadinessCheckpoint {
  if (answers?.professionalGroup === "understands_group_unit") {
    return {
      concept: "professional_group",
      status: "understood",
      familyQuestion: "Can the family explain that filing is by school major group, not by one favorite major?",
      evidenceNeeded: "Family accepts group-level uncertainty before row-level discussion.",
    };
  }
  if (answers?.professionalGroup === "single_major_only") {
    return {
      concept: "professional_group",
      status: "misconception_risk",
      familyQuestion: "Which majors are inside the group, and would the family still accept the group if not assigned to the first major?",
      evidenceNeeded: "Family must restate that the filing unit is a school major group.",
      misconception: "Family appears to treat a professional group as a single major.",
    };
  }
  return needsAnswerCheckpoint(
    "professional_group",
    "Can the family explain the difference between a school major group and a single major?",
    "Family needs to restate the filing unit before row-level discussion.",
  );
}

function adjustmentCheckpoint(input: StudentInterestClarificationInput): FamilyConceptReadinessCheckpoint {
  if (input.conceptAnswers?.adjustment === "accepts_worst_case_major") {
    return {
      concept: "adjustment",
      status: "understood",
      familyQuestion: "Can the family name the worst acceptable adjusted major?",
      evidenceNeeded: "Family accepts at least one worst-case adjusted major.",
    };
  }
  if (input.conceptAnswers?.adjustment === "only_accepts_first_major") {
    return {
      concept: "adjustment",
      status: "misconception_risk",
      familyQuestion: "If adjustment protects admission chance but changes the final major, does this row remain acceptable?",
      evidenceNeeded: "Family must decide whether adjustment is acceptable at all.",
      misconception: "Family appears to accept adjustment only when it still returns the first-choice major.",
    };
  }
  if (input.acceptableTradeoffs.some((tradeoff) => /adjustment/i.test(tradeoff))) {
    return needsAnswerCheckpoint(
      "adjustment",
      "What is the worst acceptable adjusted major in this group?",
      "Risk tolerance mentions adjustment, but the concrete worst-case major is not confirmed.",
    );
  }
  return needsAnswerCheckpoint(
    "adjustment",
    "Would the family accept adjustment if the final major changes?",
    "Family needs to decide adjustment tolerance.",
  );
}

function safeAnchorCheckpoint(input: StudentInterestClarificationInput): FamilyConceptReadinessCheckpoint {
  if (input.conceptAnswers?.safeAnchor === "checks_worst_case") {
    return {
      concept: "safe_anchor",
      status: "understood",
      familyQuestion: "Can the family define safety by the worst acceptable outcome, not only by entry probability?",
      evidenceNeeded: "Family checks worst-case major, campus, fee, and city.",
    };
  }
  if (input.conceptAnswers?.safeAnchor === "score_only") {
    return {
      concept: "safe_anchor",
      status: "misconception_risk",
      familyQuestion: "Which worst-case major, campus, fee, or city outcome would make this row unsafe?",
      evidenceNeeded: "Family must reject score-only safety before safe-anchor use.",
      misconception: "Family appears to use a score-only definition of safe anchor.",
    };
  }
  return needsAnswerCheckpoint(
    "safe_anchor",
    "What worst-case outcome would make this row unsafe even if admission looks likely?",
    "Family needs to define safety by acceptable outcome.",
  );
}

function interestTradeoffCheckpoint(input: StudentInterestClarificationInput): FamilyConceptReadinessCheckpoint {
  if (input.conceptAnswers?.interestTradeoff === "course_industry_city_workstyle") {
    return {
      concept: "interest_tradeoff",
      status: "understood",
      familyQuestion: "Can the student describe interest by courses, industry path, city, work style, and regret tolerance?",
      evidenceNeeded: "Student gives interest reasons beyond a hot major label.",
    };
  }
  if (input.conceptAnswers?.interestTradeoff === "hot_major_label_only") {
    return {
      concept: "interest_tradeoff",
      status: "misconception_risk",
      familyQuestion: "Which course content, work style, or city tradeoff would still make this major unacceptable?",
      evidenceNeeded: "Student must move beyond a hot-major label before interest-fit claims.",
      misconception: "Student appears to define interest only by a hot major label.",
    };
  }
  return needsAnswerCheckpoint(
    "interest_tradeoff",
    "Can the student explain interest beyond the major label?",
    "Student needs to name course, industry, city, work-style, or regret-tolerance preferences.",
  );
}

function needsAnswerCheckpoint(
  concept: FamilyConceptKey,
  familyQuestion: string,
  evidenceNeeded: string,
): FamilyConceptReadinessCheckpoint {
  return {
    concept,
    status: "needs_answer",
    familyQuestion,
    evidenceNeeded,
  };
}

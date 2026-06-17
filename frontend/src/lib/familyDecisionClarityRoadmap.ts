import type { FamilyDecisionBrief } from "./evidenceBackedInterpretationPackage";
import type { DetailedVolunteerPlanInterpretation } from "./detailedVolunteerPlanInterpretation";
import type { FamilyConceptKey, FamilyConceptReadinessCheckpoint } from "./studentInterestClarification";

export type FamilyDecisionClarityRoadmapStatus =
  | "ready_for_row_discussion"
  | "needs_concept_repair"
  | "blocked";

export type InterestAxis =
  | "course_content"
  | "industry_path"
  | "city_life"
  | "work_style"
  | "regret_boundary";

export interface FamilyDecisionConceptCard {
  concept: FamilyConceptKey;
  status: FamilyConceptReadinessCheckpoint["status"];
  plainMeaning: string;
  familyQuestion: string;
  evidenceNeeded: string;
  decisionImpact: string;
  repairAction: string;
  misconception?: string;
}

export interface FamilyDecisionInterestAxis {
  axis: InterestAxis;
  prompt: string;
  whyItMatters: string;
  evidenceToCollect: string;
}

export interface FamilyDecisionClarityRoadmap {
  protocol: "family_decision_clarity_roadmap_v1";
  status: FamilyDecisionClarityRoadmapStatus;
  conceptCards: FamilyDecisionConceptCard[];
  interestAxes: FamilyDecisionInterestAxis[];
  parentStudentAlignment: {
    questions: string[];
    hardStops: string[];
  };
  rowDiscussionGate: {
    canDiscussRows: boolean;
    nextAction: string;
    blockedReasons: string[];
  };
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "This roadmap is for communication and decision-clarity only. It does not estimate admission probability, replace official rules, or make final filing recommendations.";

export function buildFamilyDecisionClarityRoadmap({
  decisionBrief,
  detailedInterpretation,
}: {
  decisionBrief: FamilyDecisionBrief;
  detailedInterpretation: DetailedVolunteerPlanInterpretation;
}): FamilyDecisionClarityRoadmap {
  const status = resolveStatus(decisionBrief, detailedInterpretation);
  const conceptCards = decisionBrief.conceptReadiness.checkpoints.map(buildConceptCard);
  const blockedReasons = buildBlockedReasons(decisionBrief, detailedInterpretation, conceptCards);

  return {
    protocol: "family_decision_clarity_roadmap_v1",
    status,
    conceptCards,
    interestAxes: buildInterestAxes(decisionBrief, conceptCards),
    parentStudentAlignment: {
      questions: unique([
        ...decisionBrief.decisionQuestions,
        ...detailedInterpretation.familyDecisionPath.requiredQuestions,
      ]),
      hardStops: unique([
        ...decisionBrief.hardBoundaries,
        ...decisionBrief.cannotClaim,
        ...detailedInterpretation.familyDecisionPath.hardStops,
        ...detailedInterpretation.planPosition.notARecommendationReasons,
      ]),
    },
    rowDiscussionGate: {
      canDiscussRows: status === "ready_for_row_discussion",
      nextAction: nextActionForStatus(status, decisionBrief),
      blockedReasons,
    },
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function resolveStatus(
  decisionBrief: FamilyDecisionBrief,
  detailedInterpretation: DetailedVolunteerPlanInterpretation,
): FamilyDecisionClarityRoadmapStatus {
  if (
    detailedInterpretation.status === "blocked" ||
    decisionBrief.status === "blocked_by_missing_evidence"
  ) {
    return "blocked";
  }
  if (
    decisionBrief.conceptReadiness.status !== "ready" ||
    detailedInterpretation.familyDecisionPath.conceptReadinessStatus !== "ready"
  ) {
    return "needs_concept_repair";
  }
  return "ready_for_row_discussion";
}

function buildConceptCard(checkpoint: FamilyConceptReadinessCheckpoint): FamilyDecisionConceptCard {
  return {
    concept: checkpoint.concept,
    status: checkpoint.status,
    plainMeaning: plainMeaningFor(checkpoint.concept),
    familyQuestion: checkpoint.familyQuestion,
    evidenceNeeded: checkpoint.evidenceNeeded,
    decisionImpact: decisionImpactFor(checkpoint.concept),
    repairAction: repairActionFor(checkpoint),
    misconception: checkpoint.misconception,
  };
}

function plainMeaningFor(concept: FamilyConceptKey): string {
  if (concept === "professional_group") {
    return "The filing unit is a school major group, so the family must accept the group outcome, not only one favorite major.";
  }
  if (concept === "adjustment") {
    return "Adjustment can protect admission chance, but it may move the student to another eligible major.";
  }
  if (concept === "safe_anchor") {
    return "Safe means the worst acceptable outcome is still acceptable, not merely that the score looks enough.";
  }
  return "Interest should be explained through courses, industry path, city, work style, and regret tolerance, not only a hot label.";
}

function decisionImpactFor(concept: FamilyConceptKey): string {
  if (concept === "professional_group") {
    return "Blocks row discussion when the family treats one group as one single major.";
  }
  if (concept === "adjustment") {
    return "Determines whether adjustment-risk rows can be used as stable or safety options.";
  }
  if (concept === "safe_anchor") {
    return "Determines whether a row can be called safe after major, campus, fee, and city outcomes are checked.";
  }
  return "Determines whether the student is choosing a real direction or reacting to a crowded label.";
}

function repairActionFor(checkpoint: FamilyConceptReadinessCheckpoint): string {
  if (checkpoint.status === "understood") {
    return "Keep this concept visible during row discussion and ask the family to restate it before final signoff.";
  }
  if (checkpoint.concept === "safe_anchor" && /score-only/i.test(checkpoint.misconception ?? "")) {
    return "Repair score-only safety: list the worst acceptable major, campus, fee, and city before using any safe-anchor language.";
  }
  if (checkpoint.concept === "interest_tradeoff" && /hot major label/i.test(checkpoint.misconception ?? "")) {
    return "Repair hot major label thinking: ask for course content, work style, city, and regret-tolerance evidence before interest-fit claims.";
  }
  return `Repair before row discussion: ${checkpoint.evidenceNeeded}`;
}

function buildInterestAxes(
  decisionBrief: FamilyDecisionBrief,
  conceptCards: FamilyDecisionConceptCard[],
): FamilyDecisionInterestAxis[] {
  const hotLabelRisk = conceptCards.some((card) => (
    card.concept === "interest_tradeoff" && /hot major label/i.test(card.misconception ?? "")
  ));
  return [
    {
      axis: "course_content",
      prompt: "Which courses would the student willingly study for four years even when they are difficult?",
      whyItMatters: "Course content turns a major label into a daily learning commitment.",
      evidenceToCollect: decisionBrief.interestFitSummary,
    },
    {
      axis: "industry_path",
      prompt: "Which industry path sounds acceptable after graduation, and which path is only attractive because it sounds popular?",
      whyItMatters: "Industry path separates durable interest from short-term social heat.",
      evidenceToCollect: "Ask the student to name two acceptable work directions and one unacceptable direction.",
    },
    {
      axis: "city_life",
      prompt: "Which city, distance, campus, or living-cost tradeoff would change the choice even if the major looks attractive?",
      whyItMatters: "City and campus constraints often decide whether an apparently good row is actually usable.",
      evidenceToCollect: "Collect city, distance, campus, tuition, and family support constraints.",
    },
    {
      axis: "work_style",
      prompt: hotLabelRisk
        ? "The student currently sounds driven by a hot major label; what work style would still feel acceptable when the label cools?"
        : "What work style does the student prefer: building, research, operations, communication, service, management, or structured execution?",
      whyItMatters: "Work style keeps interest discussion grounded in daily work, not status language.",
      evidenceToCollect: "Ask for one liked work style, one disliked work style, and one tolerated compromise.",
    },
    {
      axis: "regret_boundary",
      prompt: "Which outcome would make the family regret accepting this row even if admission succeeds?",
      whyItMatters: "Regret boundaries define the real blacklist and safe-anchor floor.",
      evidenceToCollect: unique([...decisionBrief.hardBoundaries, ...decisionBrief.cannotClaim]).join(" "),
    },
  ];
}

function buildBlockedReasons(
  decisionBrief: FamilyDecisionBrief,
  detailedInterpretation: DetailedVolunteerPlanInterpretation,
  conceptCards: FamilyDecisionConceptCard[],
): string[] {
  const reasons: string[] = [];
  if (detailedInterpretation.status === "blocked") {
    reasons.push("Detailed interpretation is blocked by evidence or counselor-review gates.");
  }
  if (decisionBrief.status === "blocked_by_missing_evidence") {
    reasons.push("Decision brief is blocked by missing evidence.");
  }
  conceptCards
    .filter((card) => card.status !== "understood")
    .forEach((card) => reasons.push(`${card.concept}: ${card.repairAction}`));
  return unique(reasons);
}

function nextActionForStatus(
  status: FamilyDecisionClarityRoadmapStatus,
  decisionBrief: FamilyDecisionBrief,
): string {
  if (status === "blocked") {
    return "Resolve evidence and counselor-review blockers before concept or row-level presentation.";
  }
  if (status === "needs_concept_repair") {
    return decisionBrief.conceptReadiness.nextAction;
  }
  return "Concept readiness supports row-level discussion; use the interest axes before final counselor signoff.";
}

function unique<T>(values: T[]): T[] {
  return Array.from(new Set(values));
}

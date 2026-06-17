import type { OpportunityDiscoveryInsight, OpportunityDiscoveryLedger } from "./opportunityDiscoveryEngine";
import type { FamilyConceptReadiness, StudentInterestClarificationBrief } from "./studentInterestClarification";
import type { WebEvidenceResearchPlan } from "./webEvidencePlanner";
import type { AcceptedWebEvidence, WebEvidenceIntakeResult } from "./webEvidenceIntake";

type EvidenceStatus = "supported" | "missing" | "hypothesis_only" | "explained";

export interface EvidenceBackedInterpretationInput {
  discoveryLedger: OpportunityDiscoveryLedger;
  evidencePlan: WebEvidenceResearchPlan;
  intakeResult: WebEvidenceIntakeResult;
  interestBrief?: StudentInterestClarificationBrief;
  studentName?: string;
}

export interface InterpretationEvidenceSlot {
  status: EvidenceStatus;
  evidence: string[];
}

export interface InterpretationOpportunityCard {
  id: string;
  status: "counselor_review_ready" | "blocked";
  title: string;
  familyReadableExplanation: string;
  officialEvidence: InterpretationEvidenceSlot;
  rankEvidence: InterpretationEvidenceSlot;
  riskGuardEvidence: InterpretationEvidenceSlot;
  publicOpinionEvidence: InterpretationEvidenceSlot;
  externalPlanEvidence: InterpretationEvidenceSlot;
  familyConcepts: InterpretationEvidenceSlot;
  familyDecisionBrief: FamilyDecisionBrief;
  sourceLinks: Array<{
    title: string;
    url: string;
    claim: string;
  }>;
  nextActions: string[];
}

export interface FamilyDecisionBrief {
  protocol: "family_decision_brief_v1";
  status: "ready_for_family_discussion" | "blocked_by_missing_evidence" | "needs_interest_clarification";
  interestFitSummary: string;
  riskPosture: string;
  hardBoundaries: string[];
  conceptCheckpoints: string[];
  conceptReadiness: FamilyConceptReadiness;
  decisionQuestions: string[];
  cannotClaim: string[];
}

export interface EvidenceBackedInterpretationPackage {
  protocol: "evidence_backed_interpretation_package_v1";
  status: "counselor_review_ready" | "blocked";
  executiveSummary: string;
  opportunityCards: InterpretationOpportunityCard[];
  unresolvedBlockers: string[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "This package is not a final filing recommendation. It is an evidence-backed interpretation package for counselor review.";

export function buildEvidenceBackedInterpretationPackage(
  input: EvidenceBackedInterpretationInput,
): EvidenceBackedInterpretationPackage {
  const cards = input.discoveryLedger.insights.map((insight) => buildCard(insight, input));
  const unresolvedBlockers = input.intakeResult.blockedTasks;
  const status = unresolvedBlockers.length === 0 && cards.every((card) => card.status === "counselor_review_ready")
    ? "counselor_review_ready"
    : "blocked";

  return {
    protocol: "evidence_backed_interpretation_package_v1",
    status,
    executiveSummary: buildExecutiveSummary(status, input.studentName),
    opportunityCards: cards,
    unresolvedBlockers,
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildCard(
  insight: OpportunityDiscoveryInsight,
  input: EvidenceBackedInterpretationInput,
): InterpretationOpportunityCard {
  const officialEvidence = evidenceSlot(input.intakeResult, "official_diff");
  const rankEvidence = evidenceSlot(input.intakeResult, "rank_delta");
  const riskGuardEvidence = evidenceSlot(input.intakeResult, "risk_guard");
  const externalPlanEvidence = evidenceSlot(input.intakeResult, "competitor_missed");
  const publicOpinionEvidence = evidenceSlot(input.intakeResult, "hypothesis_only", "hypothesis_only");
  const familyConcepts = evidenceSlot(input.intakeResult, "parent_understanding", "explained");
  const blockingMissing = [officialEvidence, rankEvidence, riskGuardEvidence, externalPlanEvidence].some(
    (slot) => slot.status === "missing",
  );

  return {
    id: insight.id,
    status: blockingMissing ? "blocked" : "counselor_review_ready",
    title: `${insight.officialEvidence.diffType}: ${insight.officialEvidence.auditKey}`,
    familyReadableExplanation: buildFamilyExplanation(insight),
    officialEvidence,
    rankEvidence,
    riskGuardEvidence,
    publicOpinionEvidence,
    externalPlanEvidence,
    familyConcepts,
    familyDecisionBrief: buildFamilyDecisionBrief({
      insight,
      interestBrief: input.interestBrief,
      blockingMissing,
    }),
    sourceLinks: input.intakeResult.acceptedEvidence.map((item) => ({
      title: item.sourceTitle,
      url: item.sourceUrl,
      claim: item.claim,
    })),
    nextActions: buildNextActions({
      officialEvidence,
      rankEvidence,
      riskGuardEvidence,
      externalPlanEvidence,
      publicOpinionEvidence,
      familyConcepts,
    }),
  };
}

function buildFamilyDecisionBrief({
  insight,
  interestBrief,
  blockingMissing,
}: {
  insight: OpportunityDiscoveryInsight;
  interestBrief?: StudentInterestClarificationBrief;
  blockingMissing: boolean;
}): FamilyDecisionBrief {
  const status = !interestBrief || interestBrief.status === "needs_clarification"
    ? "needs_interest_clarification"
    : blockingMissing
      ? "blocked_by_missing_evidence"
      : "ready_for_family_discussion";

  return {
    protocol: "family_decision_brief_v1",
    status,
    interestFitSummary: buildInterestFitSummary(insight, interestBrief),
    riskPosture: buildRiskPosture(insight, interestBrief),
    hardBoundaries: interestBrief?.hardBoundaries ?? [
      "Confirm blacklist majors and worst acceptable adjustment outcome before discussing this row.",
    ],
    conceptCheckpoints: interestBrief?.conceptExplanations ?? [
      "Professional group: the application unit is a school major group, not one favorite major.",
      "Adjustment: accepting adjustment protects admission chance but may change the final major.",
      "Safe anchor: the worst acceptable outcome must still be acceptable.",
      "Interest tradeoff: interest includes course content, industry path, city, work style, and regret tolerance.",
    ],
    conceptReadiness: interestBrief?.conceptReadiness ?? defaultConceptReadiness(),
    decisionQuestions: interestBrief?.tradeoffQuestions ?? [
      "Would the family still accept this group if the final major is not the first-choice major?",
      "What worst-case major, campus, fee, or city outcome would make this row unacceptable?",
      "Is this row a real safe anchor after adjustment risk is considered?",
    ],
    cannotClaim: [
      "This is not a final recommendation.",
      "Public-opinion evidence cannot prove admission probability or demand.",
      "Interest signals cannot override blacklist majors, subject requirements, or official rules.",
    ],
  };
}

function defaultConceptReadiness(): FamilyConceptReadiness {
  return {
    protocol: "family_concept_readiness_v1",
    status: "needs_concept_clarification",
    checkpoints: [
      {
        concept: "professional_group",
        status: "needs_answer",
        familyQuestion: "Can the family explain that filing is by school major group, not by one favorite major?",
        evidenceNeeded: "Family must restate the filing unit before row-level discussion.",
      },
      {
        concept: "adjustment",
        status: "needs_answer",
        familyQuestion: "Would the family accept adjustment if the final major changes?",
        evidenceNeeded: "Family needs to decide adjustment tolerance.",
      },
      {
        concept: "safe_anchor",
        status: "needs_answer",
        familyQuestion: "What worst-case outcome would make this row unsafe even if admission looks likely?",
        evidenceNeeded: "Family needs to define safety by acceptable outcome.",
      },
      {
        concept: "interest_tradeoff",
        status: "needs_answer",
        familyQuestion: "Can the student explain interest beyond the major label?",
        evidenceNeeded: "Student needs to name course, industry, city, work-style, or regret-tolerance preferences.",
      },
    ],
    nextAction: "Do not show final row ranking until concept questions are answered.",
    claimBoundary: "Concept readiness is a communication gate for family discussion.",
  };
}

function buildInterestFitSummary(
  insight: OpportunityDiscoveryInsight,
  interestBrief?: StudentInterestClarificationBrief,
): string {
  if (!interestBrief || interestBrief.status === "needs_clarification") {
    return "Student interest is not clear enough; clarify preferred direction, blacklist majors, and adjustment tolerance before family discussion.";
  }
  return `${interestBrief.interestAnchor} Student fit for this opportunity is ${insight.studentFit.status}: ${insight.studentFit.reasons.join(" ")}`;
}

function buildRiskPosture(
  insight: OpportunityDiscoveryInsight,
  interestBrief?: StudentInterestClarificationBrief,
): string {
  const riskText = interestBrief
    ? `Interest brief is ${interestBrief.status}; risk tolerance is ${interestBrief.riskToleranceEcho}.`
    : "Risk tolerance is not yet explicit.";
  return `${riskText} Discovery student fit is ${insight.studentFit.status}; rank impact is ${insight.rankImpact.direction} with ${insight.rankImpact.confidence} confidence.`;
}

function evidenceSlot(
  intakeResult: WebEvidenceIntakeResult,
  claim: AcceptedWebEvidence["claim"],
  supportedStatus: EvidenceStatus = "supported",
): InterpretationEvidenceSlot {
  const evidence = intakeResult.acceptedEvidence
    .filter((item) => item.claim === claim)
    .flatMap((item) => item.excerpts.map((excerpt) => `${item.sourceTitle}: ${excerpt}`));

  return {
    status: evidence.length > 0 ? supportedStatus : "missing",
    evidence,
  };
}

function buildExecutiveSummary(status: EvidenceBackedInterpretationPackage["status"], studentName?: string): string {
  const subject = studentName ? `${studentName}'s case` : "This case";
  if (status === "counselor_review_ready") {
    return `${subject} has a review-ready opportunity hypothesis with official, rank, risk, external-plan, public-opinion, and concept evidence attached. Counselor signoff is still required before filing.`;
  }
  return `${subject} is not ready for a detailed recommendation package because required evidence is missing.`;
}

function buildFamilyExplanation(insight: OpportunityDiscoveryInsight): string {
  return [
    "Professional group: the application unit is the school major group, not a single major.",
    "Adjustment: accepting adjustment protects admission chance but may change the final major.",
    "Safe anchor: a safe row must be acceptable after admission, not merely easy to enter.",
    "Interest tradeoff: this row should match the student's preferred direction and avoid blacklist majors.",
    `Current hypothesis: ${insight.parentExplanation.summary}`,
  ].join(" ");
}

function buildNextActions(slots: {
  officialEvidence: InterpretationEvidenceSlot;
  rankEvidence: InterpretationEvidenceSlot;
  riskGuardEvidence: InterpretationEvidenceSlot;
  externalPlanEvidence: InterpretationEvidenceSlot;
  publicOpinionEvidence: InterpretationEvidenceSlot;
  familyConcepts: InterpretationEvidenceSlot;
}): string[] {
  const actions: string[] = [];
  if (slots.officialEvidence.status === "missing") {
    actions.push("Attach official plan verification before claiming official change.");
  }
  if (slots.rankEvidence.status === "missing") {
    actions.push("Attach historical rank calibration before estimating rank impact.");
  }
  if (slots.riskGuardEvidence.status === "missing") {
    actions.push("Attach school rule and adjustment guard before counselor signoff.");
  }
  if (slots.externalPlanEvidence.status === "missing") {
    actions.push("Attach external-plan comparison before claiming competitors missed it.");
  }
  if (slots.familyConcepts.status === "missing") {
    actions.push("Explain professional group, adjustment, safe anchor, and interest tradeoff to the family.");
  }
  actions.push("Counselor must review attached official source rows before signoff.");
  actions.push("Keep public-opinion trend as a hypothesis, not as proof of demand.");
  return actions;
}

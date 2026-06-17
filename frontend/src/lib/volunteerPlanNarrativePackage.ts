import type {
  DetailedVolunteerPlanClaim,
  DetailedVolunteerPlanClaimStance,
  DetailedVolunteerPlanInterpretation,
} from "./detailedVolunteerPlanInterpretation";
import type { FamilyDecisionClarityRoadmap } from "./familyDecisionClarityRoadmap";
import type { HiddenOpportunityAudit } from "./hiddenOpportunityAudit";
import type { PlanChangeOpportunityLedger } from "./planChangeOpportunityLedger";
import type { WebEvidenceResearchStrategy } from "./webEvidenceResearchStrategy";

export type VolunteerPlanNarrativePackageStatus =
  | "ready_for_family_delivery"
  | "needs_research"
  | "blocked";

export type VolunteerPlanNarrativeRowPosition =
  | "audited_opportunity_candidate"
  | "family_discussion_only"
  | "blocked";

export interface VolunteerPlanNarrativeEvidencePillar {
  claim: DetailedVolunteerPlanClaim | "plan_change_ledger";
  stance: DetailedVolunteerPlanClaimStance | "ledger_ready" | "ledger_blocked";
  familyWording: string;
  evidenceBasis: string[];
  sourceRefs: string[];
  counterChecks: string[];
  claimBoundary: string;
}

export interface VolunteerPlanNarrativeRow {
  id: string;
  displayName: string;
  position: VolunteerPlanNarrativeRowPosition;
  labelPermission: HiddenOpportunityAudit["labelPermission"];
  mustStayHypothesisOnly: boolean;
  familyWording: string;
  evidencePillars: VolunteerPlanNarrativeEvidencePillar[];
  searchFollowUps: string[];
  conceptPrompts: string[];
  interestPrompts: string[];
  riskGuard: string[];
}

export interface VolunteerPlanNarrativePackage {
  protocol: "volunteer_plan_narrative_package_v1";
  status: VolunteerPlanNarrativePackageStatus;
  headline: string;
  planRows: VolunteerPlanNarrativeRow[];
  conversationFlow: string[];
  deliveryGate: {
    canShowToFamily: boolean;
    counselorSignoffRequired: boolean;
    blockedReasons: string[];
  };
  forbiddenClaims: string[];
  nextActions: string[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Volunteer plan narrative package organizes evidence, search follow-ups, and family discussion prompts. It does not make final filing recommendations, estimate admission probability, or convert public-opinion hypotheses into proof.";

export function buildVolunteerPlanNarrativePackage({
  detailedInterpretation,
  researchStrategy,
  familyClarityRoadmap,
  hiddenOpportunityAudit,
  planChangeOpportunityLedger,
}: {
  detailedInterpretation: DetailedVolunteerPlanInterpretation;
  researchStrategy: WebEvidenceResearchStrategy;
  familyClarityRoadmap: FamilyDecisionClarityRoadmap;
  hiddenOpportunityAudit: HiddenOpportunityAudit;
  planChangeOpportunityLedger: PlanChangeOpportunityLedger;
}): VolunteerPlanNarrativePackage {
  const blockedReasons = buildBlockedReasons({
    detailedInterpretation,
    researchStrategy,
    familyClarityRoadmap,
    hiddenOpportunityAudit,
    planChangeOpportunityLedger,
  });
  const status = blockedReasons.length > 0
    ? "blocked"
    : isReady({
        detailedInterpretation,
        researchStrategy,
        familyClarityRoadmap,
        hiddenOpportunityAudit,
        planChangeOpportunityLedger,
      })
      ? "ready_for_family_delivery"
      : "needs_research";
  const planRows = status === "blocked"
    ? []
    : planChangeOpportunityLedger.opportunities.map((opportunity) => ({
        id: opportunity.id,
        displayName: `${opportunity.affectedRows[0]?.schoolName ?? "Unknown school"} / ${opportunity.affectedRows[0]?.majorGroupCode ?? "unknown group"}`,
        position: rowPositionFor(detailedInterpretation, hiddenOpportunityAudit, planChangeOpportunityLedger),
        labelPermission: hiddenOpportunityAudit.labelPermission,
        mustStayHypothesisOnly: hiddenOpportunityAudit.reviewGate.mustStayHypothesisOnly,
        familyWording: buildFamilyWording(detailedInterpretation, hiddenOpportunityAudit),
        evidencePillars: buildEvidencePillars(detailedInterpretation, planChangeOpportunityLedger),
        searchFollowUps: buildSearchFollowUps(researchStrategy),
        conceptPrompts: familyClarityRoadmap.conceptCards.map((card) => card.familyQuestion),
        interestPrompts: familyClarityRoadmap.interestAxes.map((axis) => axis.prompt),
        riskGuard: opportunity.riskGuard.checks,
      }));

  return {
    protocol: "volunteer_plan_narrative_package_v1",
    status,
    headline: `${detailedInterpretation.headline}: evidence-backed family narrative`,
    planRows,
    conversationFlow: buildConversationFlow(familyClarityRoadmap, researchStrategy),
    deliveryGate: {
      canShowToFamily: status === "ready_for_family_delivery",
      counselorSignoffRequired: true,
      blockedReasons,
    },
    forbiddenClaims: unique([
      ...hiddenOpportunityAudit.forbiddenClaims,
      ...detailedInterpretation.planPosition.notARecommendationReasons,
      ...familyClarityRoadmap.parentStudentAlignment.hardStops,
      ...researchStrategy.minimumEvidenceRules.filter((rule) => /forbidden|hypothesis-only|final recommendation/i.test(rule)),
    ]),
    nextActions: status === "blocked"
      ? unique(["Resolve blockers before family delivery.", ...blockedReasons])
      : unique([
          ...detailedInterpretation.nextActions,
          familyClarityRoadmap.rowDiscussionGate.nextAction,
          ...researchStrategy.operatorBrief,
        ]),
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function isReady({
  detailedInterpretation,
  researchStrategy,
  familyClarityRoadmap,
  hiddenOpportunityAudit,
  planChangeOpportunityLedger,
}: {
  detailedInterpretation: DetailedVolunteerPlanInterpretation;
  researchStrategy: WebEvidenceResearchStrategy;
  familyClarityRoadmap: FamilyDecisionClarityRoadmap;
  hiddenOpportunityAudit: HiddenOpportunityAudit;
  planChangeOpportunityLedger: PlanChangeOpportunityLedger;
}): boolean {
  return detailedInterpretation.status === "ready_for_family_review" &&
    researchStrategy.status === "ready_to_run" &&
    familyClarityRoadmap.status === "ready_for_row_discussion" &&
    hiddenOpportunityAudit.status === "candidate_for_counselor_review" &&
    planChangeOpportunityLedger.status === "ready" &&
    planChangeOpportunityLedger.hiddenOpportunityGate.canEnterLedger;
}

function buildBlockedReasons({
  detailedInterpretation,
  researchStrategy,
  familyClarityRoadmap,
  hiddenOpportunityAudit,
  planChangeOpportunityLedger,
}: {
  detailedInterpretation: DetailedVolunteerPlanInterpretation;
  researchStrategy: WebEvidenceResearchStrategy;
  familyClarityRoadmap: FamilyDecisionClarityRoadmap;
  hiddenOpportunityAudit: HiddenOpportunityAudit;
  planChangeOpportunityLedger: PlanChangeOpportunityLedger;
}): string[] {
  const reasons: string[] = [];
  if (detailedInterpretation.status === "blocked") {
    reasons.push("Detailed interpretation is blocked.");
  }
  if (researchStrategy.status === "blocked_by_evidence_quality") {
    reasons.push("Web evidence research strategy is blocked by evidence quality.");
  }
  if (familyClarityRoadmap.status === "blocked") {
    reasons.push(...familyClarityRoadmap.rowDiscussionGate.blockedReasons, "Family row discussion is blocked.");
  }
  if (hiddenOpportunityAudit.status === "blocked" || !hiddenOpportunityAudit.reviewGate.canEnterLedger) {
    reasons.push(...hiddenOpportunityAudit.reviewGate.reasons, "Hidden opportunity audit blocked narrative delivery.");
  }
  if (planChangeOpportunityLedger.status === "blocked") {
    reasons.push(...planChangeOpportunityLedger.blockedClaims, "Plan change opportunity ledger is blocked.");
  }
  return unique(reasons);
}

function rowPositionFor(
  detailedInterpretation: DetailedVolunteerPlanInterpretation,
  hiddenOpportunityAudit: HiddenOpportunityAudit,
  planChangeOpportunityLedger: PlanChangeOpportunityLedger,
): VolunteerPlanNarrativeRowPosition {
  if (
    detailedInterpretation.planPosition.rowUse === "candidate_for_counselor_review" &&
    hiddenOpportunityAudit.reviewGate.canEnterLedger &&
    planChangeOpportunityLedger.hiddenOpportunityGate.canEnterLedger
  ) {
    return "audited_opportunity_candidate";
  }
  if (detailedInterpretation.planPosition.rowUse === "blocked") {
    return "blocked";
  }
  return "family_discussion_only";
}

function buildFamilyWording(
  detailedInterpretation: DetailedVolunteerPlanInterpretation,
  hiddenOpportunityAudit: HiddenOpportunityAudit,
): string {
  return [
    detailedInterpretation.summary,
    `Use ${hiddenOpportunityAudit.labelPermission} wording only; this is not a final recommendation.`,
    "Keep public-opinion language hypothesis-only and preserve counselor signoff.",
  ].join(" ");
}

function buildEvidencePillars(
  detailedInterpretation: DetailedVolunteerPlanInterpretation,
  planChangeOpportunityLedger: PlanChangeOpportunityLedger,
): VolunteerPlanNarrativeEvidencePillar[] {
  const claimPillars = detailedInterpretation.claimRows.map((row) => ({
    claim: row.claim,
    stance: row.stance,
    familyWording: row.familyWording,
    evidenceBasis: row.evidenceBasis,
    sourceRefs: row.sourceRefs,
    counterChecks: row.counterChecks,
    claimBoundary: row.claimBoundary,
  }));
  const ledgerPillars = planChangeOpportunityLedger.opportunities.map((opportunity) => ({
    claim: "plan_change_ledger" as const,
    stance: "ledger_ready" as const,
    familyWording: `${opportunity.diffType} is in the plan-change ledger with audit score ${opportunity.auditScore}.`,
    evidenceBasis: [
      opportunity.evidence,
      opportunity.rankDeltaEstimate.explanation,
      opportunity.competitorMissed.evidence,
    ],
    sourceRefs: [opportunity.officialSource, ...opportunity.competitorMissed.checkedSources],
    counterChecks: opportunity.riskGuard.checks,
    claimBoundary: planChangeOpportunityLedger.claimBoundary,
  }));
  return [...ledgerPillars, ...claimPillars];
}

function buildSearchFollowUps(researchStrategy: WebEvidenceResearchStrategy): string[] {
  return unique([
    ...researchStrategy.priorityQueries
      .filter((query) => query.priority === "critical" || query.priority === "high")
      .map((query) => `${readableIntent(query.searchIntent ?? query.taskType)}: ${query.evidenceQuestion}`),
    ...researchStrategy.contradictionTests,
  ]);
}

function readableIntent(intent: string): string {
  return intent.replace(/_/g, "-");
}

function buildConversationFlow(
  familyClarityRoadmap: FamilyDecisionClarityRoadmap,
  researchStrategy: WebEvidenceResearchStrategy,
): string[] {
  return [
    "Start with the official plan change, then show what is verified and what is still bounded.",
    "Explain why public-opinion evidence stays hypothesis-only before discussing opportunity wording.",
    "Use the interest axes to test whether the student wants the course content, industry path, city, work style, and regret boundary.",
    familyClarityRoadmap.rowDiscussionGate.nextAction,
    researchStrategy.presentationGate,
  ];
}

function unique(items: string[]): string[] {
  return Array.from(new Set(items.filter(Boolean)));
}

import {
  diffEnrollmentPlans,
  type EnrollmentPlanRow,
  type PlanChangeDiffEngineResult,
} from "./planChangeDiffEngine";
import {
  analyzePublicOpinionTrends,
  type PublicOpinionObservation,
  type PublicOpinionTrendAnalysis,
} from "./publicOpinionTrendAnalyzer";
import {
  buildOpportunityDiscoveryLedger,
  type DiscoveryRankDeltaEstimate,
  type OpportunityDiscoveryLedger,
} from "./opportunityDiscoveryEngine";
import { buildWebEvidenceResearchPlan, type WebEvidenceResearchPlan } from "./webEvidencePlanner";
import {
  buildStudentInterestClarificationBrief,
  type StudentInterestClarificationBrief,
  type StudentInterestClarificationInput,
} from "./studentInterestClarification";

export type AdmissionsOpportunityWorkflowStatus =
  | "needs_student_clarification"
  | "needs_official_diff"
  | "needs_evidence_research";

export interface AdmissionsOpportunityWorkflowInput {
  priorYear: number;
  currentYear: number;
  province: string;
  officialSource: string;
  priorRows: EnrollmentPlanRow[];
  currentRows: EnrollmentPlanRow[];
  publicOpinionObservations: PublicOpinionObservation[];
  studentProfile: StudentInterestClarificationInput;
  rankDeltaEstimates?: Record<string, DiscoveryRankDeltaEstimate>;
  externalPlanSources: string[];
}

export interface AdmissionsOpportunityWorkflow {
  protocol: "admissions_opportunity_workflow_v1";
  status: AdmissionsOpportunityWorkflowStatus;
  interestBrief: StudentInterestClarificationBrief;
  planDiffResult: PlanChangeDiffEngineResult;
  trendAnalysis: PublicOpinionTrendAnalysis;
  discoveryLedger: OpportunityDiscoveryLedger;
  evidencePlan: WebEvidenceResearchPlan;
  gateReasons: string[];
  nextAction: string;
  claimBoundary: string;
  inputEcho: {
    priorRows: EnrollmentPlanRow[];
    currentRows: EnrollmentPlanRow[];
  };
}

const CLAIM_BOUNDARY =
  "Admissions opportunity workflow orchestrates evidence modules. It does not prove final recommendation readiness without evidence intake and counselor review.";

export function buildAdmissionsOpportunityWorkflow(
  input: AdmissionsOpportunityWorkflowInput,
): AdmissionsOpportunityWorkflow {
  const interestBrief = buildStudentInterestClarificationBrief(input.studentProfile);
  const planDiffResult = diffEnrollmentPlans({
    priorYear: input.priorYear,
    currentYear: input.currentYear,
    priorRows: input.priorRows,
    currentRows: input.currentRows,
    officialSource: input.officialSource,
  });
  const targetRow = input.currentRows[0] ?? input.priorRows[0];
  const trendAnalysis = analyzePublicOpinionTrends({
    targetYear: input.currentYear,
    province: input.province,
    schoolCode: targetRow?.schoolCode,
    schoolName: targetRow?.schoolName ?? "unknown school",
    majorKeywords: input.studentProfile.preferredMajors.length > 0 ? input.studentProfile.preferredMajors : [targetRow?.majorName ?? "major"],
    observations: input.publicOpinionObservations,
  });
  const discoveryLedger = buildOpportunityDiscoveryLedger({
    trendSignals: trendAnalysis.signals,
    trendProfiles: [
      {
        schoolCode: targetRow?.schoolCode,
        majorKeywords: input.studentProfile.preferredMajors.length > 0 ? input.studentProfile.preferredMajors : [targetRow?.majorName ?? "major"],
        opportunitySignal: trendAnalysis.trendProfile.opportunitySignal,
        confidence: trendAnalysis.trendProfile.confidence,
        familySafeSummary: trendAnalysis.trendProfile.familySafeSummary,
        requiredFollowUps: trendAnalysis.trendProfile.requiredFollowUps,
      },
    ],
    planDiffs: planDiffResult.diffs,
    rankDeltaEstimates: input.rankDeltaEstimates,
    studentProfile: {
      preferredMajorKeywords: input.studentProfile.preferredMajors,
      blacklistMajorKeywords: input.studentProfile.blacklistMajors,
      riskTolerance: normalizeDiscoveryRisk(input.studentProfile.riskTolerance),
      acceptableTradeoffs: input.studentProfile.acceptableTradeoffs,
    },
  });

  if (interestBrief.status === "needs_clarification") {
    return buildResult({
      input,
      status: "needs_student_clarification",
      interestBrief,
      planDiffResult,
      trendAnalysis,
      discoveryLedger,
      evidencePlan: emptyEvidencePlan(),
      gateReasons: ["Student interest and tradeoff inputs are incomplete."],
      nextAction: "Clarify student interest, blacklist majors, risk tolerance, and acceptable tradeoffs before plan discussion.",
    });
  }

  if (planDiffResult.diffs.length === 0 || discoveryLedger.insights.length === 0) {
    return buildResult({
      input,
      status: "needs_official_diff",
      interestBrief,
      planDiffResult,
      trendAnalysis,
      discoveryLedger,
      evidencePlan: emptyEvidencePlan(),
      gateReasons: ["Official plan diff or opportunity insight is missing."],
      nextAction: "Attach official 2025->2026 enrollment-plan diffs before evidence research.",
    });
  }

  const evidencePlan = buildWebEvidenceResearchPlan({
    discoveryLedger,
    targetYear: input.currentYear,
    province: input.province,
    externalPlanSources: input.externalPlanSources,
  });

  return buildResult({
    input,
    status: "needs_evidence_research",
    interestBrief,
    planDiffResult,
    trendAnalysis,
    discoveryLedger,
    evidencePlan,
    gateReasons: ["Evidence research is required before counselor review."],
    nextAction: "Run evidence research tasks, then evaluate returned evidence before counselor review.",
  });
}

function buildResult({
  input,
  status,
  interestBrief,
  planDiffResult,
  trendAnalysis,
  discoveryLedger,
  evidencePlan,
  gateReasons,
  nextAction,
}: Omit<AdmissionsOpportunityWorkflow, "protocol" | "claimBoundary" | "inputEcho"> & {
  input: AdmissionsOpportunityWorkflowInput;
}): AdmissionsOpportunityWorkflow {
  return {
    protocol: "admissions_opportunity_workflow_v1",
    status,
    interestBrief,
    planDiffResult,
    trendAnalysis,
    discoveryLedger,
    evidencePlan,
    gateReasons,
    nextAction,
    claimBoundary: CLAIM_BOUNDARY,
    inputEcho: {
      priorRows: input.priorRows,
      currentRows: input.currentRows,
    },
  };
}

function emptyEvidencePlan(): WebEvidenceResearchPlan {
  return {
    protocol: "web_evidence_research_plan_v1",
    status: "blocked",
    tasks: [],
    interpretationChecklist: [],
    claimBoundary: "Evidence research plan is not created until upstream gates pass.",
  };
}

function normalizeDiscoveryRisk(
  value: StudentInterestClarificationInput["riskTolerance"],
): "conservative" | "balanced" | "aggressive" {
  return value === "conservative" || value === "aggressive" ? value : "balanced";
}

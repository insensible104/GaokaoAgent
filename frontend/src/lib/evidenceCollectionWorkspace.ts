import type { AdmissionsOpportunityWorkflow } from "./admissionsOpportunityWorkflow";
import {
  completeAdmissionsOpportunityWorkflow,
  type AdmissionsOpportunityWorkflowCompletion,
} from "./admissionsOpportunityWorkflowCompletion";
import {
  buildWebEvidenceSearchBrief,
  type WebEvidenceResultTemplate,
  type WebEvidenceSearchBrief,
  type WebEvidenceTaskSearchBrief,
} from "./webEvidenceSearchBrief";
import type { WebEvidenceSearchResult } from "./webEvidenceIntake";
import type { EvidenceClaimSupport, WebEvidenceTaskType } from "./webEvidencePlanner";
import {
  buildEvidenceTriangulationReport,
  type EvidenceTriangulationReport,
} from "./evidenceTriangulationReport";
import {
  buildEvidenceGapSearchPlan,
  type EvidenceGapSearchPlan,
} from "./evidenceGapSearchPlan";

export interface EvidenceCollectionWorkspaceInput {
  workflow: AdmissionsOpportunityWorkflow;
  evidenceResults: WebEvidenceSearchResult[];
  studentName?: string;
}

export interface EvidenceCollectionCoverageSummary {
  totalTasks: number;
  blockingTasks: number;
  completedBlockingTasks: number;
  acceptedEvidenceCount: number;
  rejectedEvidenceCount: number;
  missingClaims: EvidenceClaimSupport[];
}

export interface EvidenceCollectionTaskRow {
  taskId: string;
  taskType: WebEvidenceTaskType;
  priority: "blocking" | "context";
  status: "accepted" | "needs_capture" | "rejected_only";
  acceptedEvidenceCount: number;
  rejectedEvidenceCount: number;
  primaryQuery: string;
  preferredDomains: string[];
  operatorChecklist: string[];
  mustReject: string[];
  resultTemplate: WebEvidenceResultTemplate;
}

export interface FamilyConceptReadiness {
  status: "explained" | "needs_explanation";
  nextAction: string;
}

export interface EvidenceCollectionWorkspace {
  protocol: "evidence_collection_workspace_v1";
  status: "ready_for_counselor_review" | "collecting_evidence" | "upstream_blocked";
  searchBrief: WebEvidenceSearchBrief;
  completion: AdmissionsOpportunityWorkflowCompletion;
  triangulationReport: EvidenceTriangulationReport;
  evidenceGapSearchPlan: EvidenceGapSearchPlan;
  coverageSummary: EvidenceCollectionCoverageSummary;
  taskRows: EvidenceCollectionTaskRow[];
  nextSearchActions: string[];
  familyConceptReadiness: FamilyConceptReadiness;
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Evidence collection workspace coordinates collection and readiness. It does not make final recommendations or replace counselor review.";

export function buildEvidenceCollectionWorkspace(
  input: EvidenceCollectionWorkspaceInput,
): EvidenceCollectionWorkspace {
  const searchBrief = buildWebEvidenceSearchBrief({
    evidencePlan: input.workflow.evidencePlan,
    locale: "zh-CN",
  });
  const completion = completeAdmissionsOpportunityWorkflow({
    workflow: input.workflow,
    evidenceResults: input.evidenceResults,
    studentName: input.studentName,
  });
  const triangulationReport = buildEvidenceTriangulationReport({
    intakeResult: completion.intakeResult,
  });
  const taskRows = searchBrief.taskBriefs.map((taskBrief) => buildTaskRow(taskBrief, completion));
  const evidenceGapSearchPlan = buildEvidenceGapSearchPlan({
    triangulationReport,
    taskRows,
  });
  const status = input.workflow.status !== "needs_evidence_research"
    ? "upstream_blocked"
    : completion.status === "interpretation_ready" && evidenceGapSearchPlan.status === "no_gaps"
      ? "ready_for_counselor_review"
      : "collecting_evidence";

  return {
    protocol: "evidence_collection_workspace_v1",
    status,
    searchBrief,
    completion,
    triangulationReport,
    evidenceGapSearchPlan,
    coverageSummary: buildCoverageSummary(taskRows, completion),
    taskRows,
    nextSearchActions: buildNextSearchActions(taskRows, completion, evidenceGapSearchPlan),
    familyConceptReadiness: buildFamilyConceptReadiness(completion),
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildTaskRow(
  taskBrief: WebEvidenceTaskSearchBrief,
  completion: AdmissionsOpportunityWorkflowCompletion,
): EvidenceCollectionTaskRow {
  const acceptedEvidenceCount = completion.intakeResult.acceptedEvidence
    .filter((item) => item.taskId === taskBrief.taskId)
    .length;
  const rejectedEvidenceCount = completion.intakeResult.rejectedEvidence
    .filter((item) => item.taskId === taskBrief.taskId)
    .length;

  return {
    taskId: taskBrief.taskId,
    taskType: taskBrief.taskType,
    priority: taskBrief.priority,
    status: acceptedEvidenceCount > 0 ? "accepted" : rejectedEvidenceCount > 0 ? "rejected_only" : "needs_capture",
    acceptedEvidenceCount,
    rejectedEvidenceCount,
    primaryQuery: taskBrief.searchQueries[0] ?? "",
    preferredDomains: taskBrief.preferredDomains,
    operatorChecklist: taskBrief.acceptanceCriteria,
    mustReject: taskBrief.mustReject,
    resultTemplate: taskBrief.evidenceResultTemplate,
  };
}

function buildCoverageSummary(
  taskRows: EvidenceCollectionTaskRow[],
  completion: AdmissionsOpportunityWorkflowCompletion,
): EvidenceCollectionCoverageSummary {
  const blockingRows = taskRows.filter((row) => row.priority === "blocking");
  const missingClaims = Object.entries(completion.intakeResult.claimSupport)
    .filter(([, support]) => support.status === "unsupported")
    .map(([claim]) => claim as EvidenceClaimSupport);

  return {
    totalTasks: taskRows.length,
    blockingTasks: blockingRows.length,
    completedBlockingTasks: blockingRows.filter((row) => row.status === "accepted").length,
    acceptedEvidenceCount: completion.intakeResult.acceptedEvidence.length,
    rejectedEvidenceCount: completion.intakeResult.rejectedEvidence.length,
    missingClaims,
  };
}

function buildNextSearchActions(
  taskRows: EvidenceCollectionTaskRow[],
  completion: AdmissionsOpportunityWorkflowCompletion,
  evidenceGapSearchPlan: EvidenceGapSearchPlan,
): string[] {
  if (completion.status === "interpretation_ready" && evidenceGapSearchPlan.status === "no_gaps") {
    return [completion.nextAction];
  }

  const actions = evidenceGapSearchPlan.followUps.map((followUp) => (
    `Resolve ${followUp.claim} ${followUp.gapStatus} using: ${followUp.query}`
  ));

  actions.push(...taskRows
    .filter((row) => row.priority === "blocking" && row.status !== "accepted")
    .map((row) => `Capture ${row.taskType} evidence using: ${row.primaryQuery}`));

  if (actions.length === 0) {
    actions.push(completion.nextAction);
  }
  actions.push("Keep public-opinion evidence as hypothesis-only until official, rank, risk, and external-plan evidence pass intake.");
  return actions;
}

function buildFamilyConceptReadiness(
  completion: AdmissionsOpportunityWorkflowCompletion,
): FamilyConceptReadiness {
  const conceptSupport = completion.intakeResult.claimSupport.parent_understanding;
  if (conceptSupport?.status === "supported") {
    return {
      status: "explained",
      nextAction: "Family concepts have supporting explanation evidence attached.",
    };
  }
  return {
    status: "needs_explanation",
    nextAction: "Explain professional group, adjustment, safe anchor, interest boundaries, and tradeoffs before final row discussion.",
  };
}

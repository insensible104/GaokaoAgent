import type { AdmissionsOpportunityWorkflow } from "./admissionsOpportunityWorkflow";
import {
  buildEvidenceCollectionWorkspace,
  type EvidenceCollectionWorkspace,
} from "./evidenceCollectionWorkspace";
import type { WebEvidenceSearchResult } from "./webEvidenceIntake";
import type { WebEvidenceAdapterResponse } from "./webEvidenceSearchAdapter";
import {
  buildWebEvidenceSearchRun,
  type WebEvidenceSearchRun,
} from "./webEvidenceSearchRun";

export interface EvidenceGapSearchRerunInput {
  workflow: AdmissionsOpportunityWorkflow;
  workspace: EvidenceCollectionWorkspace;
  currentEvidenceResults: WebEvidenceSearchResult[];
  responses: WebEvidenceAdapterResponse[];
  capturedAt: string;
  studentName?: string;
}

export interface EvidenceGapSearchRerun {
  protocol: "evidence_gap_search_rerun_v1";
  searchRun: WebEvidenceSearchRun;
  mergedEvidenceResults: WebEvidenceSearchResult[];
  refreshedWorkspace: EvidenceCollectionWorkspace;
  nextActions: string[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Evidence gap search reruns merge follow-up search evidence and refresh triangulation. They do not make final recommendations or replace counselor review.";

export function rerunEvidenceGapSearch(input: EvidenceGapSearchRerunInput): EvidenceGapSearchRerun {
  const searchRun = buildWebEvidenceSearchRun({
    workspace: input.workspace,
    responses: input.responses,
    capturedAt: input.capturedAt,
  });
  const mergedEvidenceResults = [
    ...input.currentEvidenceResults,
    ...searchRun.acceptedEvidenceResults,
  ];
  const refreshedWorkspace = buildEvidenceCollectionWorkspace({
    workflow: input.workflow,
    evidenceResults: mergedEvidenceResults,
    studentName: input.studentName,
  });

  return {
    protocol: "evidence_gap_search_rerun_v1",
    searchRun,
    mergedEvidenceResults,
    refreshedWorkspace,
    nextActions: buildNextActions(searchRun, refreshedWorkspace),
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildNextActions(
  searchRun: WebEvidenceSearchRun,
  refreshedWorkspace: EvidenceCollectionWorkspace,
): string[] {
  if (refreshedWorkspace.status === "ready_for_counselor_review") {
    return [refreshedWorkspace.completion.nextAction];
  }
  return [
    ...searchRun.nextActions,
    ...refreshedWorkspace.nextSearchActions,
  ];
}

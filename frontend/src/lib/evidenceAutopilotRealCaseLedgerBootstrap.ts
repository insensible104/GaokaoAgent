import type { DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import {
  fetchReviewedEvidenceRecords,
  submitReviewedEvidenceCard,
  type ReviewedEvidenceListingResponse,
  type ReviewedEvidenceSubmissionResponse,
} from "./evidenceAutopilotApi";
import {
  buildRealCaseReviewedEvidenceSubmissions,
} from "./evidenceAutopilotRealCaseReviewedEvidence";
import type { EvidenceAutopilotRealCaseFixture } from "./evidenceAutopilotRealCaseProvider";
import {
  buildReviewedEvidenceCaseBrowser,
  type ReviewedEvidenceCaseBrowserView,
} from "./reviewedEvidenceCaseBrowser";

type FetchLike = Parameters<typeof submitReviewedEvidenceCard>[0]["fetchImpl"];

export interface RealCaseReviewedEvidenceLedgerBootstrapResult {
  protocol: "real_case_reviewed_evidence_bootstrap_v1";
  caseId: string;
  submittedCount: number;
  recordCount: number;
  submissions: ReviewedEvidenceSubmissionResponse[];
  listing: ReviewedEvidenceListingResponse;
  browser: ReviewedEvidenceCaseBrowserView;
  claimBoundary: string;
}

export async function bootstrapRealCaseReviewedEvidenceLedger({
  fixture,
  caseId,
  plan,
  fetchImpl,
}: {
  fixture: EvidenceAutopilotRealCaseFixture;
  caseId: string;
  plan?: DeepEvidenceCollectionPlan | { tasks?: Array<{ id: string; priority?: string; claim?: string; title?: string }> };
  fetchImpl?: FetchLike;
}): Promise<RealCaseReviewedEvidenceLedgerBootstrapResult> {
  if (!caseId.trim()) {
    throw new Error("real case reviewed evidence ledger bootstrap requires caseId");
  }
  const payloads = buildRealCaseReviewedEvidenceSubmissions({ fixture, caseId });
  const submissions: ReviewedEvidenceSubmissionResponse[] = [];
  for (const payload of payloads) {
    submissions.push(await submitReviewedEvidenceCard({ payload, fetchImpl }));
  }
  const listing = await fetchReviewedEvidenceRecords({ caseId, fetchImpl });
  const browser = buildReviewedEvidenceCaseBrowser({
    caseId,
    records: listing.records,
    plan,
  });
  return {
    protocol: "real_case_reviewed_evidence_bootstrap_v1",
    caseId,
    submittedCount: submissions.length,
    recordCount: listing.recordCount,
    submissions,
    listing,
    browser,
    claimBoundary:
      "Real Case reviewed-evidence bootstrap only submits completed public fixture evidence into the case-scoped reviewed evidence ledger and builds a readiness view; it does not prove admission probability, employment outcomes, or source freshness.",
  };
}

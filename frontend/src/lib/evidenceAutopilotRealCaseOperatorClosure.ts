import type { DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { ReviewedEvidenceListingResponse } from "./evidenceAutopilotApi";
import {
  buildRealCaseOpportunityAuditPacket,
  type RealCaseOpportunityAuditPacket,
} from "./evidenceAutopilotRealCaseAuditPacket";
import {
  bootstrapRealCaseReviewedEvidenceLedger,
  type RealCaseReviewedEvidenceLedgerBootstrapResult,
} from "./evidenceAutopilotRealCaseLedgerBootstrap";
import type { EvidenceAutopilotRealCaseFixture } from "./evidenceAutopilotRealCaseProvider";
import {
  buildRealCaseOpportunityReportBrief,
  type RealCaseOpportunityReportBrief,
} from "./evidenceAutopilotRealCaseReportBrief";
import {
  executeOperatorEvidenceCaptureRoundtrip,
  type OperatorEvidenceCaptureRoundtripResult,
} from "./operatorEvidenceCaptureRoundtrip";
import type { OperatorReviewedEvidenceCaptureInput } from "./evidenceAutopilotApi";
import {
  buildReviewedEvidenceCaseBrowser,
  type ReviewedEvidenceCaseBrowserView,
} from "./reviewedEvidenceCaseBrowser";

type FetchLike = Parameters<typeof bootstrapRealCaseReviewedEvidenceLedger>[0]["fetchImpl"];

interface PlanLike {
  tasks?: Array<{
    id: string;
    priority?: string;
    claim?: string;
    title?: string;
  }>;
}

export interface RealCaseOperatorClosureReview {
  protocol: "real_case_operator_closure_review_v1";
  caseId: string;
  listing: ReviewedEvidenceListingResponse;
  browser: ReviewedEvidenceCaseBrowserView;
  auditPacket: RealCaseOpportunityAuditPacket;
  reportBrief: RealCaseOpportunityReportBrief;
  claimBoundary: string;
}

export interface RealCaseOperatorClosureWorkflowResult {
  protocol: "real_case_operator_closure_workflow_v1";
  caseId: string;
  publicBootstrap: RealCaseReviewedEvidenceLedgerBootstrapResult;
  operatorRoundtrip: OperatorEvidenceCaptureRoundtripResult;
  closureReview: RealCaseOperatorClosureReview;
  claimBoundary: string;
}

export async function executeRealCaseOperatorClosureWorkflow({
  fixture,
  caseId,
  plan,
  operatorInput,
  fetchImpl,
}: {
  fixture: EvidenceAutopilotRealCaseFixture;
  caseId: string;
  plan: DeepEvidenceCollectionPlan;
  operatorInput: OperatorReviewedEvidenceCaptureInput;
  fetchImpl?: FetchLike;
}): Promise<RealCaseOperatorClosureWorkflowResult> {
  if (fixture.caseId !== caseId || operatorInput.caseId !== caseId) {
    throw new Error("real case operator closure workflow requires matching caseId");
  }

  const publicBootstrap = await bootstrapRealCaseReviewedEvidenceLedger({
    fixture,
    caseId,
    plan,
    fetchImpl,
  });
  const operatorRoundtrip = await executeOperatorEvidenceCaptureRoundtrip({
    plan,
    input: operatorInput,
    fetchImpl,
  });
  const closureReview = buildRealCaseOperatorClosureReview({
    fixture,
    plan,
    publicBootstrap,
    operatorRoundtrip,
  });

  return {
    protocol: "real_case_operator_closure_workflow_v1",
    caseId,
    publicBootstrap,
    operatorRoundtrip,
    closureReview,
    claimBoundary:
      "Real Case operator closure workflow runs public evidence bootstrap, one operator capture roundtrip, and readiness recomputation; it does not prove admission probability, does not prove employment outcomes, source representativeness, or source freshness.",
  };
}

export function buildRealCaseOperatorClosureReview({
  fixture,
  plan,
  publicBootstrap,
  operatorRoundtrip,
}: {
  fixture: EvidenceAutopilotRealCaseFixture;
  plan?: DeepEvidenceCollectionPlan | PlanLike;
  publicBootstrap: RealCaseReviewedEvidenceLedgerBootstrapResult;
  operatorRoundtrip: OperatorEvidenceCaptureRoundtripResult;
}): RealCaseOperatorClosureReview {
  if (fixture.caseId !== publicBootstrap.caseId || fixture.caseId !== operatorRoundtrip.caseId) {
    throw new Error("real case operator closure review requires matching caseId");
  }

  const listing: ReviewedEvidenceListingResponse = {
    ...publicBootstrap.listing,
    caseId: fixture.caseId,
    records: uniqueRecordsByReviewId([
      ...publicBootstrap.listing.records,
      ...operatorRoundtrip.listing.records,
    ]),
    recordCount: 0,
  };
  listing.recordCount = listing.records.length;
  const browser = buildReviewedEvidenceCaseBrowser({
    caseId: fixture.caseId,
    records: listing.records,
    plan,
  });
  const auditPacket = buildRealCaseOpportunityAuditPacket({
    fixture,
    bootstrap: {
      ...publicBootstrap,
      listing,
      browser,
      recordCount: listing.recordCount,
      submittedCount: publicBootstrap.submittedCount + (operatorRoundtrip.submission.reviewId ? 1 : 0),
    },
  });
  const reportBrief = buildRealCaseOpportunityReportBrief(auditPacket);

  return {
    protocol: "real_case_operator_closure_review_v1",
    caseId: fixture.caseId,
    listing,
    browser,
    auditPacket,
    reportBrief,
    claimBoundary:
      "Real Case operator closure review composes public reviewed evidence with operator-captured evidence readiness; it does not prove admission probability, does not prove employment outcomes, and does not replace counselor review or source freshness checks.",
  };
}

function uniqueRecordsByReviewId(
  records: ReviewedEvidenceListingResponse["records"],
): ReviewedEvidenceListingResponse["records"] {
  const byReviewId = new Map<string, ReviewedEvidenceListingResponse["records"][number]>();
  for (const record of records) {
    byReviewId.set(record.reviewId, record);
  }
  return [...byReviewId.values()];
}

import type { DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { ReviewedEvidenceListingResponse } from "./evidenceAutopilotApi";
import {
  buildRealCaseOpportunityAuditPacket,
  type RealCaseOpportunityAuditPacket,
} from "./evidenceAutopilotRealCaseAuditPacket";
import type { RealCaseReviewedEvidenceLedgerBootstrapResult } from "./evidenceAutopilotRealCaseLedgerBootstrap";
import type { EvidenceAutopilotRealCaseFixture } from "./evidenceAutopilotRealCaseProvider";
import {
  buildRealCaseOpportunityReportBrief,
  type RealCaseOpportunityReportBrief,
} from "./evidenceAutopilotRealCaseReportBrief";
import type { OperatorEvidenceCaptureRoundtripResult } from "./operatorEvidenceCaptureRoundtrip";
import {
  buildReviewedEvidenceCaseBrowser,
  type ReviewedEvidenceCaseBrowserView,
} from "./reviewedEvidenceCaseBrowser";

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
    records: [
      ...publicBootstrap.listing.records,
      ...operatorRoundtrip.listing.records,
    ],
    recordCount: publicBootstrap.listing.records.length + operatorRoundtrip.listing.records.length,
  };
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
      submittedCount: publicBootstrap.submittedCount + operatorRoundtrip.listing.records.length,
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

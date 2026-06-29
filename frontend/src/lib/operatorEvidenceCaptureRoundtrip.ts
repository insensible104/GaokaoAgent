import type { DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import {
  captureAndSubmitOperatorReviewedEvidence,
  fetchReviewedEvidenceRecords,
  type OperatorReviewedEvidenceCaptureInput,
  type OperatorReviewedEvidenceCaptureResult,
  type ReviewedEvidenceListingResponse,
} from "./evidenceAutopilotApi";
import {
  buildOperatorEvidenceCaptureGate,
  buildOperatorEvidenceCaptureWorklist,
  type OperatorEvidenceCaptureGate,
  type OperatorEvidenceCaptureWorklist,
} from "./operatorEvidenceCaptureWorklist";

type FetchLike = Parameters<typeof captureAndSubmitOperatorReviewedEvidence>[0]["fetchImpl"];

export interface OperatorEvidenceCaptureRoundtripResult {
  protocol: "operator_evidence_capture_roundtrip_v1";
  caseId: string;
  capture: OperatorReviewedEvidenceCaptureResult;
  submission: OperatorReviewedEvidenceCaptureResult["submission"];
  listing: ReviewedEvidenceListingResponse;
  worklist: OperatorEvidenceCaptureWorklist;
  gate: OperatorEvidenceCaptureGate;
  claimBoundary: string;
}

export async function executeOperatorEvidenceCaptureRoundtrip({
  plan,
  input,
  fetchImpl,
}: {
  plan: DeepEvidenceCollectionPlan;
  input: OperatorReviewedEvidenceCaptureInput;
  fetchImpl?: FetchLike;
}): Promise<OperatorEvidenceCaptureRoundtripResult> {
  if (!input.caseId?.trim()) {
    throw new Error("operator evidence capture roundtrip requires caseId");
  }

  const capture = await captureAndSubmitOperatorReviewedEvidence({
    ...input,
    fetchImpl,
  });
  const listing = await fetchReviewedEvidenceRecords({
    caseId: input.caseId,
    fetchImpl,
  });
  const worklist = buildOperatorEvidenceCaptureWorklist({
    caseId: input.caseId,
    plan,
    records: listing.records,
  });
  const gate = buildOperatorEvidenceCaptureGate(worklist);

  return {
    protocol: "operator_evidence_capture_roundtrip_v1",
    caseId: input.caseId,
    capture,
    submission: capture.submission,
    listing,
    worklist,
    gate,
    claimBoundary:
      "Operator evidence capture roundtrip verifies upload, ledger submission, case readback, and delivery-gate recomputation; it does not prove admission or employment outcomes.",
  };
}

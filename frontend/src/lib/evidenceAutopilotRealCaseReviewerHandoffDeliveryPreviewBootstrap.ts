import type { DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { EvidenceAutopilotRealCaseFixture } from "./evidenceAutopilotRealCaseProvider";
import {
  bootstrapRealCaseReviewerHandoff,
  type RealCaseReviewerHandoffBootstrapResult,
} from "./evidenceAutopilotRealCaseReviewerHandoff";
import {
  buildRealCaseReviewerHandoffArtifactManifest,
  type RealCaseReviewerHandoffArtifactManifest,
} from "./evidenceAutopilotRealCaseReviewerHandoffArtifact";
import {
  buildRealCaseReviewerHandoffDeliveryBundle,
  buildRealCaseReviewerHandoffDeliveryPreview,
  listRealCaseReviewerClientFacingArtifacts,
  type RealCaseReviewerHandoffDeliveryBundle,
  type RealCaseReviewerHandoffDeliveryPreview,
} from "./evidenceAutopilotRealCaseReviewerHandoffDeliveryBundle";

type FetchLike = Parameters<typeof bootstrapRealCaseReviewerHandoff>[0]["fetchImpl"];

export interface RealCaseReviewerHandoffDeliveryPreviewBootstrapResult {
  protocol: "real_case_reviewer_handoff_delivery_preview_bootstrap_v1";
  caseId: string;
  handoffBootstrap: RealCaseReviewerHandoffBootstrapResult;
  artifactManifest: RealCaseReviewerHandoffArtifactManifest;
  deliveryBundle: RealCaseReviewerHandoffDeliveryBundle;
  preview: RealCaseReviewerHandoffDeliveryPreview;
  clientFacingArtifacts: Array<[string, string]>;
  claimBoundary: string;
}

export async function bootstrapRealCaseReviewerHandoffDeliveryPreview({
  fixture,
  caseId,
  plan,
  fetchImpl,
}: {
  fixture: EvidenceAutopilotRealCaseFixture;
  caseId: string;
  plan: DeepEvidenceCollectionPlan;
  fetchImpl?: FetchLike;
}): Promise<RealCaseReviewerHandoffDeliveryPreviewBootstrapResult> {
  const handoffBootstrap = await bootstrapRealCaseReviewerHandoff({
    fixture,
    caseId,
    plan,
    fetchImpl,
  });
  const artifactManifest = buildRealCaseReviewerHandoffArtifactManifest(handoffBootstrap);
  const deliveryBundle = buildRealCaseReviewerHandoffDeliveryBundle(artifactManifest);
  const preview = buildRealCaseReviewerHandoffDeliveryPreview(deliveryBundle);
  const clientFacingArtifacts = listRealCaseReviewerClientFacingArtifacts(deliveryBundle);

  return {
    protocol: "real_case_reviewer_handoff_delivery_preview_bootstrap_v1",
    caseId,
    handoffBootstrap,
    artifactManifest,
    deliveryBundle,
    preview,
    clientFacingArtifacts,
    claimBoundary:
      "Real Case reviewer handoff delivery preview bootstrap prepares an internal preview only; it does not prove admission probability, does not prove employment outcomes, and does not allow client-facing delivery.",
  };
}

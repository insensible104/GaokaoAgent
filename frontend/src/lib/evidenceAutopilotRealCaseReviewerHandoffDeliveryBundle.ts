import type {
  RealCaseReviewerHandoffArtifact,
  RealCaseReviewerHandoffArtifactManifest,
} from "./evidenceAutopilotRealCaseReviewerHandoffArtifact";

export interface RealCaseReviewerHandoffDeliveryArtifact {
  id: string;
  label: string;
  path: string;
  required: boolean;
  audience: "internal_review";
}

export interface RealCaseReviewerHandoffDeliveryManifest {
  case_id: string;
  status: "blocked_by_operator_capture";
  client_delivery: {
    allowed: false;
    status: "blocked";
    artifact_audiences: ["client_confirmation", "client_final"];
    blocked_reason: string;
  };
  artifacts: RealCaseReviewerHandoffDeliveryArtifact[];
  delivery_gates: Array<{
    gate: "real_case_reviewer_handoff";
    status: "blocked";
    requirement: string;
  }>;
  next_actions: string[];
}

export interface RealCaseReviewerHandoffDeliveryBundle {
  protocol: "real_case_reviewer_handoff_delivery_bundle_v1";
  success: true;
  message: string;
  caseId: string;
  manifest: RealCaseReviewerHandoffDeliveryManifest;
  artifacts: Record<string, string>;
  claimBoundary: string;
}

const CLIENT_FACING_AUDIENCES = new Set(["client_confirmation", "client_final"]);

export function buildRealCaseReviewerHandoffDeliveryBundle(
  artifactManifest: RealCaseReviewerHandoffArtifactManifest,
): RealCaseReviewerHandoffDeliveryBundle {
  if (artifactManifest.protocol !== "real_case_reviewer_handoff_artifact_manifest_v1") {
    throw new Error("real case reviewer handoff delivery bundle requires artifact manifest");
  }

  const artifacts = Object.fromEntries(
    artifactManifest.artifacts.map((artifact) => [deliveryArtifactId(artifact), artifact.content]),
  );
  const manifestArtifacts = artifactManifest.artifacts.map((artifact) => ({
    id: deliveryArtifactId(artifact),
    label: deliveryArtifactLabel(artifact),
    path: artifact.filename,
    required: true,
    audience: "internal_review" as const,
  }));
  const requirement = `Close reviewer-only evidence blockers before any client delivery: ${artifactManifest.blockedReason}`;

  return {
    protocol: "real_case_reviewer_handoff_delivery_bundle_v1",
    success: true,
    message: "Real Case reviewer handoff artifacts are packaged for internal delivery review only.",
    caseId: artifactManifest.caseId,
    manifest: {
      case_id: artifactManifest.caseId,
      status: "blocked_by_operator_capture",
      client_delivery: {
        allowed: false,
        status: "blocked",
        artifact_audiences: ["client_confirmation", "client_final"],
        blocked_reason: artifactManifest.blockedReason,
      },
      artifacts: manifestArtifacts,
      delivery_gates: [
        {
          gate: "real_case_reviewer_handoff",
          status: "blocked",
          requirement,
        },
      ],
      next_actions: [
        artifactManifest.blockedReason,
        "Run executeRealCaseOperatorClosureWorkflow only after reviewer-captured evidence is complete.",
        "Keep the package internal until counselor review clears counter-evidence and source freshness.",
      ],
    },
    artifacts,
    claimBoundary: artifactManifest.claimBoundary,
  };
}

export function listRealCaseReviewerClientFacingArtifacts(
  bundle: RealCaseReviewerHandoffDeliveryBundle,
): Array<[string, string]> {
  const audienceById = new Map(
    bundle.manifest.artifacts.map((artifact) => [artifact.id, artifact.audience]),
  );

  return Object.entries(bundle.artifacts).filter(([id]) => {
    const audience = audienceById.get(id);
    return audience ? CLIENT_FACING_AUDIENCES.has(audience) : false;
  });
}

function deliveryArtifactId(artifact: RealCaseReviewerHandoffArtifact): string {
  return artifact.kind === "markdown"
    ? "real_case_reviewer_handoff_markdown"
    : "real_case_reviewer_handoff_json";
}

function deliveryArtifactLabel(artifact: RealCaseReviewerHandoffArtifact): string {
  return artifact.kind === "markdown"
    ? "Real Case reviewer handoff Markdown"
    : "Real Case reviewer handoff JSON snapshot";
}

import type { RealCaseReviewerHandoffBootstrapResult } from "./evidenceAutopilotRealCaseReviewerHandoff";

export interface RealCaseReviewerHandoffArtifact {
  id: string;
  kind: "markdown" | "json";
  filename: string;
  contentType: "text/markdown; charset=utf-8" | "application/json";
  audience: "internal_reviewer";
  familyFacingAllowed: false;
  content: string;
  byteLength: number;
  claimBoundary: string;
}

export interface RealCaseReviewerHandoffArtifactManifest {
  protocol: "real_case_reviewer_handoff_artifact_manifest_v1";
  caseId: string;
  artifactCount: number;
  artifacts: RealCaseReviewerHandoffArtifact[];
  familyFacingAllowed: false;
  blockedReason: string;
  claimBoundary: string;
}

export function buildRealCaseReviewerHandoffArtifactManifest(
  bootstrap: RealCaseReviewerHandoffBootstrapResult,
): RealCaseReviewerHandoffArtifactManifest {
  if (bootstrap.protocol !== "real_case_reviewer_handoff_bootstrap_v1") {
    throw new Error("real case reviewer handoff artifact manifest requires handoff bootstrap result");
  }
  if (bootstrap.handoff.protocol !== "real_case_reviewer_handoff_v1") {
    throw new Error("real case reviewer handoff artifact manifest requires reviewer handoff");
  }
  if (bootstrap.brief.protocol !== "real_case_reviewer_handoff_brief_v1") {
    throw new Error("real case reviewer handoff artifact manifest requires reviewer handoff brief");
  }

  const slug = toFilenameSlug(bootstrap.caseId);
  const claimBoundary = [
    bootstrap.claimBoundary,
    "Artifact manifest is for internal reviewer handoff only; it does not prove admission probability, does not prove employment outcomes, and is not family-facing delivery.",
  ].join(" ");
  const markdownContent = bootstrap.brief.markdown;
  const jsonContent = JSON.stringify(bootstrap, null, 2);
  const artifacts: RealCaseReviewerHandoffArtifact[] = [
    {
      id: `${slug}-reviewer-handoff-markdown`,
      kind: "markdown",
      filename: `${slug}-reviewer-handoff.md`,
      contentType: "text/markdown; charset=utf-8",
      audience: "internal_reviewer",
      familyFacingAllowed: false,
      content: markdownContent,
      byteLength: byteLength(markdownContent),
      claimBoundary,
    },
    {
      id: `${slug}-reviewer-handoff-json`,
      kind: "json",
      filename: `${slug}-reviewer-handoff.json`,
      contentType: "application/json",
      audience: "internal_reviewer",
      familyFacingAllowed: false,
      content: jsonContent,
      byteLength: byteLength(jsonContent),
      claimBoundary,
    },
  ];

  return {
    protocol: "real_case_reviewer_handoff_artifact_manifest_v1",
    caseId: bootstrap.caseId,
    artifactCount: artifacts.length,
    artifacts,
    familyFacingAllowed: false,
    blockedReason: buildBlockedReason(bootstrap.handoff.openTaskIds),
    claimBoundary,
  };
}

function buildBlockedReason(openTaskIds: string[]): string {
  if (openTaskIds.length === 0) {
    return "Internal reviewer signoff is still required before any family-facing artifact is allowed.";
  }

  return `Family-facing delivery is blocked until internal reviewer tasks are closed: ${openTaskIds.join(", ")}.`;
}

function toFilenameSlug(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "real-case-reviewer-handoff";
}

function byteLength(value: string): number {
  return new TextEncoder().encode(value).length;
}

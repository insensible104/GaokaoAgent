import { buildDeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";

interface DeliveryReviewedEvidenceProfile {
  preferred_majors?: string[];
}

interface DeliveryReviewedEvidenceGameMatrix {
  volunteer_plan?: unknown;
  major_group_rows?: unknown[];
}

interface DeliveryReviewedEvidencePlanInput {
  profile: DeliveryReviewedEvidenceProfile | null;
  gameMatrix?: DeliveryReviewedEvidenceGameMatrix | null;
}

export function buildDeliveryReviewedEvidencePlan({
  profile,
  gameMatrix,
}: DeliveryReviewedEvidencePlanInput): DeepEvidenceCollectionPlan {
  const volunteerPlan = objectRecord(gameMatrix?.volunteer_plan);
  const choice = firstObject(volunteerPlan?.choices) ?? firstObject(gameMatrix?.major_group_rows);
  const majorChoice = firstObject(choice?.major_choices) ?? firstObject(choice?.suggested_major_choices);

  return buildDeepEvidenceCollectionPlan({
    province: stringField(volunteerPlan, "province") || "Guangdong",
    targetYear: numberField(volunteerPlan, "year") ?? 2026,
    schoolName: stringField(choice, "school_name") || "delivery case target",
    majorName:
      stringField(majorChoice, "major_name")
      || firstString(choice?.major_list)
      || profile?.preferred_majors?.[0]
      || "target major",
  });
}

function objectRecord(value: unknown): Record<string, unknown> | undefined {
  if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
  return value as Record<string, unknown>;
}

function firstObject(value: unknown): Record<string, unknown> | undefined {
  if (!Array.isArray(value)) return undefined;
  return objectRecord(value[0]);
}

function firstString(value: unknown): string {
  if (!Array.isArray(value)) return "";
  const item = value.find((entry) => typeof entry === "string");
  return typeof item === "string" ? item : "";
}

function stringField(record: Record<string, unknown> | undefined, key: string): string {
  const value = record?.[key];
  return typeof value === "string" ? value : "";
}

function numberField(record: Record<string, unknown> | undefined, key: string): number | undefined {
  const value = record?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

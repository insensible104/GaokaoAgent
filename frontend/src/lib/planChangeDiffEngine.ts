import type { PlanChangeDiffType } from "./planChangeOpportunityLedger";

export interface EnrollmentPlanRow {
  officialSource?: string;
  year?: number;
  province?: string;
  batch?: string;
  schoolCode: string;
  schoolName: string;
  majorGroupCode: string;
  majorCode: string;
  majorName: string;
  quota?: number | null;
  subjectRequirements?: string[];
}

export interface PlanChangeDiffEngineInput {
  priorYear: number;
  currentYear: number;
  priorRows: EnrollmentPlanRow[];
  currentRows: EnrollmentPlanRow[];
  officialSource: string;
}

export interface PlanChangeDiff {
  auditKey: string;
  sourceTier: "official";
  officialSource: string;
  diffType: Exclude<PlanChangeDiffType, "unknown" | "major_structure_change">;
  row: EnrollmentPlanRow;
  before: number | string[] | null;
  after: number | string[] | null;
  evidence: string;
}

export interface PlanChangeDiffEngineResult {
  protocol: "plan_change_diff_engine_v1";
  priorYear: number;
  currentYear: number;
  officialSource: string;
  diffs: PlanChangeDiff[];
  claimBoundary: string;
}

export interface PlanChangeDiffConversionOptions {
  rankDeltaEstimates?: Record<
    string,
    {
      direction: "easier" | "harder" | "uncertain";
      rank_delta?: number;
      explanation: string;
    }
  >;
  externalPlanCoverage?: Record<
    string,
    {
      competitor_missed?: boolean;
      checked_sources?: string[];
      evidence?: string;
    }
  >;
  recommendationActions?: Record<string, "promote" | "guard" | "avoid" | "review">;
  riskGuards?: Record<string, { level: "low" | "medium" | "high"; checks: string[] }>;
}

export interface PlanChangeOfficialChange {
  change_type: PlanChangeDiff["diffType"];
  before: PlanChangeDiff["before"];
  after: PlanChangeDiff["after"];
  evidence: string;
  official_source: string;
  source_tier: "official";
  applied_to_ranking: boolean;
  rank_delta_estimate?: {
    direction: "easier" | "harder" | "uncertain";
    rank_delta?: number;
    explanation: string;
  };
  external_plan_coverage?: {
    competitor_missed?: boolean;
    checked_sources?: string[];
    evidence?: string;
  };
  recommendation_action?: "promote" | "guard" | "avoid" | "review";
  risk_guard?: {
    level: "low" | "medium" | "high";
    checks: string[];
  };
}

const CLAIM_BOUNDARY =
  "Plan change diff engine only compares official enrollment-plan rows. It does not prove demand, competitor omission, or final recommendation readiness without downstream audit evidence.";

export function diffEnrollmentPlans(input: PlanChangeDiffEngineInput): PlanChangeDiffEngineResult {
  const priorByRow = indexBy(input.priorRows, rowKey);
  const currentByRow = indexBy(input.currentRows, rowKey);
  const priorGroupsByMajor = groupsByMajor(input.priorRows);
  const currentGroupsByMajor = groupsByMajor(input.currentRows);
  const splitMajorKeys = changedMajorKeys(priorGroupsByMajor, currentGroupsByMajor, "split");
  const mergeMajorKeys = changedMajorKeys(priorGroupsByMajor, currentGroupsByMajor, "merge");
  const diffs: PlanChangeDiff[] = [];

  for (const currentRow of input.currentRows) {
    const priorRow = priorByRow.get(rowKey(currentRow));
    if (!priorRow) continue;
    if (isNumber(priorRow.quota) && isNumber(currentRow.quota) && priorRow.quota !== currentRow.quota) {
      diffs.push(
        buildDiff({
          input,
          diffType: currentRow.quota > priorRow.quota ? "quota_expansion" : "quota_reduction",
          row: currentRow,
          before: priorRow.quota,
          after: currentRow.quota,
        }),
      );
    }

    const priorSubjects = normalizeSubjects(priorRow.subjectRequirements);
    const currentSubjects = normalizeSubjects(currentRow.subjectRequirements);
    if (!sameList(priorSubjects, currentSubjects)) {
      diffs.push(
        buildDiff({
          input,
          diffType: "subject_requirement_change",
          row: currentRow,
          before: priorSubjects,
          after: currentSubjects,
        }),
      );
    }
  }

  for (const currentRow of input.currentRows) {
    if (priorByRow.has(rowKey(currentRow))) continue;
    const key = majorKey(currentRow);
    if (splitMajorKeys.has(key)) {
      diffs.push(
        buildDiff({
          input,
          diffType: "group_split",
          row: currentRow,
          before: priorGroupsByMajor.get(key) ?? [],
          after: currentGroupsByMajor.get(key) ?? [],
        }),
      );
    } else if (!mergeMajorKeys.has(key)) {
      diffs.push(
        buildDiff({
          input,
          diffType: "new_major",
          row: currentRow,
          before: null,
          after: currentRow.quota ?? null,
        }),
      );
    }
  }

  for (const priorRow of input.priorRows) {
    if (currentByRow.has(rowKey(priorRow))) continue;
    const key = majorKey(priorRow);
    if (!splitMajorKeys.has(key) && !mergeMajorKeys.has(key)) {
      diffs.push(
        buildDiff({
          input,
          diffType: "discontinued_major",
          row: priorRow,
          before: priorRow.quota ?? null,
          after: null,
        }),
      );
    }
  }

  for (const currentRow of input.currentRows) {
    const key = majorKey(currentRow);
    if (!mergeMajorKeys.has(key)) continue;
    diffs.push(
      buildDiff({
        input,
        diffType: "group_merge",
        row: currentRow,
        before: priorGroupsByMajor.get(key) ?? [],
        after: currentGroupsByMajor.get(key) ?? [],
      }),
    );
  }

  return {
    protocol: "plan_change_diff_engine_v1",
    priorYear: input.priorYear,
    currentYear: input.currentYear,
    officialSource: input.officialSource,
    diffs,
    claimBoundary: CLAIM_BOUNDARY,
  };
}

export function convertDiffsToOfficialChanges(
  diffs: PlanChangeDiff[],
  options: PlanChangeDiffConversionOptions = {},
): PlanChangeOfficialChange[] {
  return diffs.map((diff) => ({
    change_type: diff.diffType,
    before: diff.before,
    after: diff.after,
    evidence: diff.evidence,
    official_source: diff.officialSource,
    source_tier: "official",
    applied_to_ranking: Boolean(options.rankDeltaEstimates?.[diff.auditKey]),
    rank_delta_estimate: options.rankDeltaEstimates?.[diff.auditKey],
    external_plan_coverage: options.externalPlanCoverage?.[diff.auditKey],
    recommendation_action: options.recommendationActions?.[diff.auditKey],
    risk_guard: options.riskGuards?.[diff.auditKey],
  }));
}

function buildDiff({
  input,
  diffType,
  row,
  before,
  after,
}: {
  input: PlanChangeDiffEngineInput;
  diffType: PlanChangeDiff["diffType"];
  row: EnrollmentPlanRow;
  before: PlanChangeDiff["before"];
  after: PlanChangeDiff["after"];
}): PlanChangeDiff {
  return {
    auditKey: `${row.schoolCode}-${row.majorGroupCode}-${row.majorCode}-${diffType}`,
    sourceTier: "official",
    officialSource: input.officialSource,
    diffType,
    row,
    before,
    after,
    evidence: `${input.officialSource} ${input.priorYear}->${input.currentYear}: ${diffType} for ${row.schoolName} ${row.majorGroupCode} ${row.majorName}.`,
  };
}

function rowKey(row: EnrollmentPlanRow): string {
  return `${row.schoolCode}-${row.majorGroupCode}-${row.majorCode}`;
}

function majorKey(row: EnrollmentPlanRow): string {
  return `${row.schoolCode}-${row.majorCode}`;
}

function indexBy(rows: EnrollmentPlanRow[], getKey: (row: EnrollmentPlanRow) => string): Map<string, EnrollmentPlanRow> {
  return new Map(rows.map((row) => [getKey(row), row]));
}

function groupsByMajor(rows: EnrollmentPlanRow[]): Map<string, string[]> {
  const groups = new Map<string, Set<string>>();
  for (const row of rows) {
    const key = majorKey(row);
    const existing = groups.get(key) ?? new Set<string>();
    existing.add(row.majorGroupCode);
    groups.set(key, existing);
  }
  return new Map([...groups].map(([key, value]) => [key, [...value].sort()]));
}

function changedMajorKeys(
  priorGroupsByMajor: Map<string, string[]>,
  currentGroupsByMajor: Map<string, string[]>,
  direction: "split" | "merge",
): Set<string> {
  const result = new Set<string>();
  for (const [key, priorGroups] of priorGroupsByMajor) {
    const currentGroups = currentGroupsByMajor.get(key);
    if (!currentGroups) continue;
    if (direction === "split" && priorGroups.length === 1 && currentGroups.length > 1) result.add(key);
    if (direction === "merge" && priorGroups.length > 1 && currentGroups.length === 1) result.add(key);
  }
  return result;
}

function normalizeSubjects(subjects?: string[]): string[] {
  return [...new Set(subjects ?? [])].sort();
}

function sameList(left: string[], right: string[]): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

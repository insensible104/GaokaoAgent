export type ExternalPlanStrategy = "rush" | "target" | "safe" | "unknown";

export interface ExternalPlanEntry {
  index: number;
  rawLine: string;
  schoolName: string;
  majorGroupCode?: string;
  strategyTag: ExternalPlanStrategy;
  normalizedKey: string;
}

export interface ExternalPlanFinding {
  type:
    | "empty_input"
    | "low_overlap"
    | "unmatched_entries"
    | "duplicate_entries"
    | "missing_strategy_tags"
    | "missing_safe_anchor"
    | "ready_for_review";
  severity: "info" | "review" | "blocker";
  title: string;
  detail: string;
  action: string;
}

export interface ExternalPlanAuditSummary {
  protocol: "external_plan_audit_v1";
  metricKeys: {
    overlapRate: "overlap_rate";
    unmatchedEntries: "unmatched_entries";
    strategyMix: "strategy_mix";
  };
  parsedCount: number;
  matchedCount: number;
  overlapRate: number;
  unmatchedEntries: ExternalPlanEntry[];
  duplicateEntries: ExternalPlanEntry[];
  strategyMix: Record<ExternalPlanStrategy, number>;
  findings: ExternalPlanFinding[];
  claimBoundary: string;
}

interface GameMatrixLike {
  major_group_rows?: Array<{
    school_name?: string;
    major_group_code?: string;
    strategy_tag?: string;
  }>;
  volunteer_plan?: {
    choices?: Array<{
      school_name?: string;
      major_group_code?: string;
      strategy_tag?: string;
    }>;
    [key: string]: unknown;
  } | null;
}

export const EXTERNAL_PLAN_CLAIM_BOUNDARY =
  "不判断外部方案对错，不使用2026官方数据生成新结论，只做结构审计和复核提示。";

const STRATEGY_MARKERS: Array<[ExternalPlanStrategy, RegExp]> = [
  ["rush", /(^|[\s:：|｜-])(冲|冲刺|rush)([\s:：|｜-]|$)/i],
  ["target", /(^|[\s:：|｜-])(稳|稳妥|target|match)([\s:：|｜-]|$)/i],
  ["safe", /(^|[\s:：|｜-])(保|保底|safe)([\s:：|｜-]|$)/i],
];

const SCHOOL_SUFFIX = /(大学|学院|学校|职业技术学院|医科大学|师范大学|理工大学|工业大学|农业大学|财经大学|外国语大学)/;

export function normalizePlanKey(schoolName?: string, majorGroupCode?: string): string {
  const school = (schoolName ?? "")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]/gu, "");
  const group = (majorGroupCode ?? "")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]/gu, "");
  return group ? `${school}#${group}` : school;
}

export function parseExternalPlanText(text: string): ExternalPlanEntry[] {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, offset) => parseExternalPlanLine(line, offset + 1))
    .filter((entry): entry is ExternalPlanEntry => Boolean(entry));
}

function parseExternalPlanLine(line: string, index: number): ExternalPlanEntry | null {
  const cleaned = line
    .replace(/^\s*(第?\d+[\s.、)]*|[（(]?\d+[）)]\s*)/, "")
    .replace(/\s+/g, " ")
    .trim();
  if (!cleaned) {
    return null;
  }

  const strategyTag = inferStrategy(cleaned);
  const majorGroupCode = inferMajorGroupCode(cleaned);
  const schoolName = inferSchoolName(cleaned, majorGroupCode);
  if (!schoolName) {
    return null;
  }

  return {
    index,
    rawLine: line,
    schoolName,
    majorGroupCode,
    strategyTag,
    normalizedKey: normalizePlanKey(schoolName, majorGroupCode),
  };
}

function inferStrategy(line: string): ExternalPlanStrategy {
  const found = STRATEGY_MARKERS.find(([, pattern]) => pattern.test(line));
  return found?.[0] ?? "unknown";
}

function inferMajorGroupCode(line: string): string | undefined {
  const explicit = line.match(/(?:专业组|院校专业组|group|组)\s*[:：#-]?\s*([A-Za-z]?\d{2,4}[A-Za-z]?)/i);
  if (explicit?.[1]) {
    return explicit[1].toUpperCase();
  }
  const compact = line.match(/(?:^|[\s,，、|｜-])([A-Za-z]?\d{2,4}[A-Za-z]?)(?:[\s,，、|｜-]|$)/);
  return compact?.[1]?.toUpperCase();
}

function inferSchoolName(line: string, majorGroupCode?: string): string {
  const withoutPrefix = line.replace(/^(冲|冲刺|稳|稳妥|保|保底|rush|target|match|safe)[\s:：|｜-]*/i, "");
  const beforeGroup = majorGroupCode ? withoutPrefix.split(majorGroupCode)[0] : withoutPrefix;
  const suffixMatch = beforeGroup.match(new RegExp(`^(.+?${SCHOOL_SUFFIX.source})`));
  if (suffixMatch?.[1]) {
    return trimSchoolNoise(suffixMatch[1]);
  }
  return trimSchoolNoise(beforeGroup.split(/[，,、|｜/]/)[0] ?? "");
}

function trimSchoolNoise(value: string): string {
  return value
    .replace(/(?:专业组|院校专业组|group|组)\s*[:：#-]?\s*$/i, "")
    .replace(/[：:|-]\s*$/g, "")
    .trim();
}

export function auditExternalPlan({
  text,
  gameMatrix,
}: {
  text: string;
  gameMatrix: GameMatrixLike;
}): ExternalPlanAuditSummary {
  const entries = parseExternalPlanText(text);
  const currentPlanKeys = buildCurrentPlanKeySet(gameMatrix);
  const schoolOnlyKeys = buildCurrentSchoolKeySet(gameMatrix);
  const seen = new Map<string, ExternalPlanEntry>();
  const duplicateEntries: ExternalPlanEntry[] = [];
  const unmatchedEntries: ExternalPlanEntry[] = [];
  let matchedCount = 0;

  for (const entry of entries) {
    if (seen.has(entry.normalizedKey)) {
      duplicateEntries.push(entry);
    } else {
      seen.set(entry.normalizedKey, entry);
    }

    const schoolOnlyKey = normalizePlanKey(entry.schoolName);
    const matched =
      currentPlanKeys.has(entry.normalizedKey) ||
      (!entry.majorGroupCode && schoolOnlyKeys.has(schoolOnlyKey));
    if (matched) {
      matchedCount += 1;
    } else {
      unmatchedEntries.push(entry);
    }
  }

  const strategyMix = entries.reduce<Record<ExternalPlanStrategy, number>>(
    (acc, entry) => {
      acc[entry.strategyTag] += 1;
      return acc;
    },
    { rush: 0, target: 0, safe: 0, unknown: 0 },
  );
  const overlapRate = entries.length > 0 ? matchedCount / entries.length : 0;

  return {
    protocol: "external_plan_audit_v1",
    metricKeys: {
      overlapRate: "overlap_rate",
      unmatchedEntries: "unmatched_entries",
      strategyMix: "strategy_mix",
    },
    parsedCount: entries.length,
    matchedCount,
    overlapRate,
    unmatchedEntries,
    duplicateEntries,
    strategyMix,
    findings: buildFindings(entries, {
      overlapRate,
      unmatchedEntries,
      duplicateEntries,
      strategyMix,
    }),
    claimBoundary: EXTERNAL_PLAN_CLAIM_BOUNDARY,
  };
}

function buildCurrentPlanKeySet(gameMatrix: GameMatrixLike): Set<string> {
  const rows = [
    ...(gameMatrix.major_group_rows ?? []),
    ...(gameMatrix.volunteer_plan?.choices ?? []),
  ];
  return new Set(rows.map((row) => normalizePlanKey(row.school_name, row.major_group_code)).filter(Boolean));
}

function buildCurrentSchoolKeySet(gameMatrix: GameMatrixLike): Set<string> {
  const rows = [
    ...(gameMatrix.major_group_rows ?? []),
    ...(gameMatrix.volunteer_plan?.choices ?? []),
  ];
  return new Set(rows.map((row) => normalizePlanKey(row.school_name)).filter(Boolean));
}

function buildFindings(
  entries: ExternalPlanEntry[],
  audit: Pick<
    ExternalPlanAuditSummary,
    "overlapRate" | "unmatchedEntries" | "duplicateEntries" | "strategyMix"
  >,
): ExternalPlanFinding[] {
  if (entries.length === 0) {
    return [
      {
        type: "empty_input",
        severity: "info",
        title: "等待外部方案",
        detail: "粘贴千问、家长或人工方案后，系统会解析学校和专业组结构。",
        action: "复制外部方案中的志愿行，每行保留学校名、专业组和冲稳保标签。",
      },
    ];
  }

  const findings: ExternalPlanFinding[] = [];
  if (audit.overlapRate < 0.3) {
    findings.push({
      type: "low_overlap",
      severity: "review",
      title: "结构重合偏低",
      detail: `当前只匹配 ${(audit.overlapRate * 100).toFixed(0)}% 的外部条目。`,
      action: "优先核对院校专业组代码、地域约束和是否误把学校层级当成专业组层级。",
    });
  }
  if (audit.unmatchedEntries.length > 0) {
    findings.push({
      type: "unmatched_entries",
      severity: "review",
      title: "存在未匹配条目",
      detail: `有 ${audit.unmatchedEntries.length} 行没有出现在 PathFinder 当前方案结构中。`,
      action: "逐行复核这些条目的选科要求、专业黑名单、风险档位和是否属于候补池外学校。",
    });
  }
  if (audit.duplicateEntries.length > 0) {
    findings.push({
      type: "duplicate_entries",
      severity: "review",
      title: "外部方案存在重复",
      detail: `检测到 ${audit.duplicateEntries.length} 行重复学校专业组。`,
      action: "确认重复是刻意保留不同专业方向，还是复制方案时产生的冗余。",
    });
  }
  if (audit.strategyMix.unknown > 0) {
    findings.push({
      type: "missing_strategy_tags",
      severity: "review",
      title: "冲稳保标签不完整",
      detail: `${audit.strategyMix.unknown} 行未解析出冲、稳、保标签。`,
      action: "给外部方案补充策略标签，再比较尾部安全垫是否足够。",
    });
  }
  if (audit.strategyMix.safe === 0) {
    findings.push({
      type: "missing_safe_anchor",
      severity: "review",
      title: "缺少保底锚点",
      detail: "外部方案中没有识别到保底行。",
      action: "人工检查尾部是否有真实可接受的保底学校专业组，而不是只依赖前序高分方案。",
    });
  }

  if (findings.length === 0) {
    findings.push({
      type: "ready_for_review",
      severity: "info",
      title: "结构审计未发现明显冲突",
      detail: "外部方案与当前结构有可比性，但仍需要人工核对招生章程和最新官方数据。",
      action: "进入人工复核，不把该结果直接升级为正式填报建议。",
    });
  }

  return findings;
}

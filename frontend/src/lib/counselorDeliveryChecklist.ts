export type CounselorChecklistStatus = "ready" | "needs_review" | "blocked";

export type CounselorChecklistOwner = "counselor" | "student_family" | "data_update";

export interface CounselorDeliveryChecklistItem {
  id:
    | "data_boundary"
    | "profile_completeness"
    | "plan_structure"
    | "evidence_integrity"
    | "external_comparison"
    | "report_package";
  label: string;
  status: CounselorChecklistStatus;
  owner: CounselorChecklistOwner;
  evidence: string;
  action: string;
}

export interface CounselorDeliveryChecklistSummary {
  protocol: "counselor_delivery_checklist_v1";
  status: CounselorChecklistStatus;
  readyCount: number;
  reviewCount: number;
  blockedCount: number;
  leadAction: string;
  items: CounselorDeliveryChecklistItem[];
  claimBoundary: string;
}

interface CounselorGameMatrixLike {
  major_group_rows?: Array<{
    quant_evidence?: string[];
    is_key_prefix?: boolean;
    prefix_role?: string;
  }>;
  rows?: unknown[];
  data_vintage?: {
    formal_recommendation_ready?: boolean;
    limitations?: string[];
  } | null;
  volunteer_plan?: {
    choices?: Array<{
      quant_evidence?: string[];
    }>;
    key_prefix_count?: number;
    shadowed_choice_count?: number;
    blacklist_violation_count?: number;
    human_review_items?: string[];
    [key: string]: unknown;
  } | null;
  plan_audit_summary?: {
    status?: string;
    key_prefix?: {
      count?: number;
    };
    shadowed_choice_count?: number;
    coverage?: {
      coverage_sufficient?: boolean;
      deficits?: Record<string, number>;
      actions?: string[];
    };
    data_boundary?: {
      formal_recommendation_ready?: boolean;
      limitations?: string[];
    };
    student_facing_items?: Array<{
      severity?: string;
      title?: string;
      detail?: string;
      type?: string;
    }>;
  } | null;
}

interface CounselorProfileLike {
  score?: number;
  rank?: number;
  subject_group?: string;
  preferred_cities?: string[];
  preferred_majors?: string[];
  blacklist_majors?: string[];
  field_provenance?: Record<string, string>;
  career_assessment_status?: string;
  riasec_top_codes?: string[];
  career_values?: string[];
}

export interface CounselorDeliveryChecklistInput {
  gameMatrix?: CounselorGameMatrixLike | null;
  userProfile?: CounselorProfileLike | null;
  reportReady?: boolean;
  externalPlanCompared?: boolean;
  externalPlanAuditSummary?: {
    parsedCount?: number;
    matchedCount?: number;
    overlapRate?: number;
    unmatchedEntries?: unknown[];
    duplicateEntries?: unknown[];
    findings?: unknown[];
  } | null;
}

export const COUNSELOR_DELIVERY_CLAIM_BOUNDARY =
  "顾问交付清单只做交付复核编排，不生成新的录取结论，不替代人工复核。";

const statusScore: Record<CounselorChecklistStatus, number> = {
  ready: 2,
  needs_review: 1,
  blocked: 0,
};

export function buildCounselorDeliveryChecklist(
  input: CounselorDeliveryChecklistInput,
): CounselorDeliveryChecklistSummary {
  const gameMatrix = input.gameMatrix;
  const profile = input.userProfile;
  const audit = gameMatrix?.plan_audit_summary;
  const plan = gameMatrix?.volunteer_plan;
  const dataBoundary = audit?.data_boundary ?? gameMatrix?.data_vintage;
  const formalReady = dataBoundary?.formal_recommendation_ready === true;
  const limitations = dataBoundary?.limitations ?? [];
  const rowCount = (gameMatrix?.major_group_rows?.length ?? 0) || (gameMatrix?.rows?.length ?? 0);
  const keyPrefixCount =
    audit?.key_prefix?.count ??
    plan?.key_prefix_count ??
    gameMatrix?.major_group_rows?.filter((row) => row.is_key_prefix).length ??
    0;
  const shadowedCount =
    audit?.shadowed_choice_count ??
    plan?.shadowed_choice_count ??
    gameMatrix?.major_group_rows?.filter((row) => row.prefix_role === "shadowed").length ??
    0;
  const hasCoverageDeficit =
    audit?.coverage?.coverage_sufficient === false ||
    Object.values(audit?.coverage?.deficits ?? {}).some((value) => Number(value) > 0);
  const blacklistViolations = Number(plan?.blacklist_violation_count ?? 0);
  const explicitProfileFacts = countExplicitProfileFacts(profile);
  const hasCareerSignal =
    profile?.career_assessment_status === "completed" ||
    Boolean(profile?.riasec_top_codes?.length) ||
    Boolean(profile?.career_values?.length);
  const evidenceCount =
    countRowEvidence(gameMatrix?.major_group_rows) +
    countChoiceEvidence(plan?.choices) +
    (audit?.student_facing_items?.length ?? 0);
  const externalAudit = input.externalPlanAuditSummary;
  const externalParsedCount = externalAudit?.parsedCount ?? 0;
  const externalUnmatchedCount = externalAudit?.unmatchedEntries?.length ?? 0;
  const externalDuplicateCount = externalAudit?.duplicateEntries?.length ?? 0;
  const externalCompared = input.externalPlanCompared === true || externalParsedCount > 0;
  const externalNeedsReview = externalUnmatchedCount > 0 || externalDuplicateCount > 0;

  const items: CounselorDeliveryChecklistItem[] = [
    {
      id: "data_boundary",
      label: "数据边界",
      status: formalReady ? "ready" : "blocked",
      owner: formalReady ? "counselor" : "data_update",
      evidence: formalReady
        ? "当前数据边界允许进入正式交付复核"
        : limitations[0] ?? "2026 当前年招生/录取数据仍不完整",
      action: formalReady
        ? "保留数据年份和来源记录"
        : "正式填报前复核招生计划、位次表、章程和考试院公告",
    },
    {
      id: "profile_completeness",
      label: "画像完整度",
      status: profile?.score && profile?.rank && profile?.subject_group
        ? explicitProfileFacts >= 2 || hasCareerSignal
          ? "ready"
          : "needs_review"
        : "blocked",
      owner: profile?.score && profile?.rank && profile?.subject_group ? "student_family" : "counselor",
      evidence: `分数/位次/科类${profile?.score && profile?.rank && profile?.subject_group ? "已具备" : "缺失"}，显式偏好 ${explicitProfileFacts} 项`,
      action:
        explicitProfileFacts >= 2 || hasCareerSignal
          ? "确认画像摘要可进入方案解释"
          : "补问城市、专业黑名单、风险承受度或职业兴趣证据",
    },
    {
      id: "plan_structure",
      label: "方案结构",
      status:
        rowCount === 0 || blacklistViolations > 0
          ? "blocked"
          : hasCoverageDeficit || keyPrefixCount === 0
            ? "needs_review"
            : "ready",
      owner: "counselor",
      evidence:
        blacklistViolations > 0
          ? `存在 ${blacklistViolations} 个硬边界冲突`
          : `方案 ${rowCount} 行，关键前缀 ${keyPrefixCount} 行，遮蔽 ${shadowedCount} 行`,
      action:
        rowCount === 0
          ? "重新生成或导入志愿方案"
          : hasCoverageDeficit
            ? "补齐冲稳保覆盖缺口或记录顾问接受该缺口的理由"
            : "复核关键前缀是否符合家庭真实接受度",
    },
    {
      id: "evidence_integrity",
      label: "证据完整性",
      status: evidenceCount > 0 ? "ready" : "needs_review",
      owner: "counselor",
      evidence: evidenceCount > 0 ? `已找到 ${evidenceCount} 条结构化证据` : "缺少可追溯证据项",
      action: evidenceCount > 0 ? "保留证据账本和风险口径" : "补齐 quant_evidence 或 plan_audit_summary",
    },
    {
      id: "external_comparison",
      label: "外部方案对照",
      status: externalCompared ? (externalNeedsReview ? "needs_review" : "ready") : "needs_review",
      owner: "counselor",
      evidence: externalCompared
        ? `已审计外部方案 ${externalParsedCount} 行，未匹配 ${externalUnmatchedCount} 行，重复 ${externalDuplicateCount} 行`
        : "尚未记录千问/老师方案对照",
      action: externalCompared
        ? externalNeedsReview
          ? "把外部方案未匹配条目、重复条目和低重合信号写入人工复核记录"
          : "保留外部方案审计快照并进入人工复核"
        : "若家长带来千问/老师方案，粘贴到外部方案审计器做结构对照",
    },
    {
      id: "report_package",
      label: "报告交付包",
      status: input.reportReady ? "ready" : "needs_review",
      owner: "counselor",
      evidence: input.reportReady ? "报告包已生成" : "报告包需要最终预览",
      action: input.reportReady ? "发送前检查风险披露和版本号" : "打开 A4 报告预览并检查证据、风险、边界声明",
    },
  ];

  const blockedCount = items.filter((item) => item.status === "blocked").length;
  const reviewCount = items.filter((item) => item.status === "needs_review").length;
  const readyCount = items.filter((item) => item.status === "ready").length;
  const status = blockedCount > 0 ? "blocked" : reviewCount > 0 ? "needs_review" : "ready";
  const leadAction =
    items.find((item) => item.status === "blocked")?.action ??
    items.find((item) => item.status === "needs_review")?.action ??
    "交付前保留复核记录和版本快照";

  return {
    protocol: "counselor_delivery_checklist_v1",
    status,
    readyCount,
    reviewCount,
    blockedCount,
    leadAction,
    items: items.sort((a, b) => statusScore[a.status] - statusScore[b.status]),
    claimBoundary: COUNSELOR_DELIVERY_CLAIM_BOUNDARY,
  };
}

function countExplicitProfileFacts(profile?: CounselorProfileLike | null): number {
  const provenance = profile?.field_provenance ?? {};
  const fields = ["risk_tolerance", "preferred_cities", "preferred_majors", "blacklist_majors"];
  return fields.filter((field) => provenance[field] === "user_explicit").length;
}

function countRowEvidence(rows?: Array<{ quant_evidence?: string[] }>): number {
  return (rows ?? []).reduce((sum, row) => sum + (row.quant_evidence?.length ?? 0), 0);
}

function countChoiceEvidence(choices?: Array<{ quant_evidence?: string[] }>): number {
  return (choices ?? []).reduce((sum, choice) => sum + (choice.quant_evidence?.length ?? 0), 0);
}

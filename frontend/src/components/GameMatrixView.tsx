import React, { useCallback, useMemo, useState } from "react";
import { CompetitiveDifferentiationPanel } from "./CompetitiveDifferentiationPanel";
import { CounselorDeliveryChecklist } from "./CounselorDeliveryChecklist";
import { DeliveryCaseStatusPanel } from "./DeliveryCaseStatusPanel";
import { DeliveryReviewRecord } from "./DeliveryReviewRecord";
import { ExternalPlanComparator } from "./ExternalPlanComparator";
import { PaidValuePanel } from "./PaidValuePanel";
import type { ExternalPlanAuditSummary } from "../lib/externalPlanAudit";

export interface MajorOption {
  major_code?: string;
  major_name: string;
  user_utility?: number;
  is_blacklisted?: boolean;
  career_fit_score?: number | null;
}

interface DecisionTraceFactor {
  code: string;
  label: string;
  value: number;
}

interface DecisionTrace {
  verdict?: "recommended" | "recommended_with_caution" | string;
  summary?: string;
  confidence_level?: "high" | "medium" | "low" | string;
  data_confidence_score?: number;
  supporting_factors?: DecisionTraceFactor[];
  risk_factors?: DecisionTraceFactor[];
  supporting_evidence?: string[];
  warnings?: string[];
}

interface PlanChangeItem {
  change_type?: string;
  major_name?: string;
  before?: unknown;
  after?: unknown;
  evidence?: string;
  source_tier?: string;
  applied_to_ranking?: boolean;
}

interface PlanChangeExplanation {
  status?: string;
  summary?: string;
  ranking_impact?: string;
  official_changes?: PlanChangeItem[];
  reference_claims?: Array<{
    claim?: string;
    source?: string;
    applied_to_ranking?: boolean;
  }>;
  review_items?: string[];
}

export interface MajorGroupRow {
  school_name: string;
  major_group_code: string;
  major_list: string[];
  major_count?: number;
  suggested_major_choices?: MajorOption[];
  admission_prob: number;
  raw_admission_prob?: number | null;
  probability_is_calibrated?: boolean;
  probability_method?: string;
  probability_calibration_year?: number | null;
  probability_calibration_source?: string;
  min_rank_pred: number;
  rank_ci_lower: number;
  rank_ci_upper: number;
  volatility: "low" | "medium" | "high";
  adjustment_risk: number;
  worst_case_major: string | null;
  is_blacklist_risk: boolean;
  strategy_tag: "rush" | "target" | "safe";
  sentiment_score?: number;
  news_summary?: string | null;
  is_selected?: boolean;
  choice_index?: number | null;
  survival_before_prob?: number;
  first_hit_prob?: number;
  cumulative_hit_prob?: number;
  prefix_role?: "key_result" | "active_backup" | "safety_anchor" | "shadowed" | "unclassified" | string;
  is_key_prefix?: boolean;
  tail_assignment_risk?: number;
  quant_score?: number;
  rank_buffer_score?: number;
  data_confidence_score?: number;
  deterministic_risk_band?: string;
  quant_evidence?: string[];
  decision_trace?: DecisionTrace;
  plan_change_explanation?: PlanChangeExplanation;
}

export interface GameMatrix {
  major_group_rows: MajorGroupRow[];
  rows: unknown[];
  total_rush: number;
  total_target: number;
  total_safe: number;
  expected_utility: number;
  portfolio_risk: number;
  is_balanced: boolean;
  agentic_rl_used?: boolean;
  selection_method?: string;
  volunteer_plan?: {
    expected_admission_prob?: number;
    admission_probability_lower_bound?: number;
    admission_probability_upper_bound?: number;
    probability_method?: string;
    probability_is_calibrated?: boolean;
    probability_calibration_year?: number | null;
    subsequent_choice_hazard_scale?: number;
    probability_warning?: string;
    expected_first_hit_utility?: number;
    expected_tail_risk?: number;
    expected_plan_value?: number;
    key_prefix_count?: number;
    key_choice_indexes?: number[];
    shadowed_choice_count?: number;
    plan_summary?: string;
    human_review_items?: string[];
  } | null;
  plan_audit_summary?: {
    protocol_version?: string;
    status?: string;
    total_score?: number;
    key_prefix?: {
      count?: number;
      choice_indexes?: number[];
    };
    shadowed_choice_count?: number;
    coverage?: {
      coverage_sufficient?: boolean;
      selected?: { rush?: number; target?: number; safe?: number };
      desired?: { rush?: number; target?: number; safe?: number };
      deficits?: Record<string, number>;
      actions?: string[];
    };
    data_boundary?: {
      target_year?: number;
      formal_recommendation_ready?: boolean;
      limitations?: string[];
    };
    student_facing_items?: Array<{
      type?: string;
      severity?: string;
      title?: string;
      detail?: string;
    }>;
  } | null;
  data_vintage?: {
    target_year?: number;
    latest_historical_admission_year?: number | null;
    enrollment_plan_year?: number | null;
    rank_table_year?: number | null;
    formal_recommendation_ready?: boolean;
    limitations?: string[];
  } | null;
  optimization_summary?: {
    checkpoint_loaded?: boolean;
    policy_source?: string;
    mix?: {
      rush?: number;
      target?: number;
      safe?: number;
      total?: number;
    };
    effective_params?: {
      risk_tolerance?: number;
      diversity_weight?: number;
      prestige_weight?: number;
    };
    portfolio?: {
      generated?: boolean;
      style_name?: string;
      style_description?: string;
      admission_guarantee?: number;
      avg_admission_prob?: number;
    };
    capacity_fill?: {
      requested_count?: number;
      initial_count?: number;
      filled_count?: number;
      final_count?: number;
      remaining_shortfall?: number;
    };
    coverage_report?: {
      desired?: { rush?: number; target?: number; safe?: number };
      classified?: { rush?: number; target?: number; safe?: number };
      post_pareto?: { rush?: number; target?: number; safe?: number };
      selected?: { rush?: number; target?: number; safe?: number };
      deficits?: Record<string, number>;
      coverage_sufficient?: boolean;
      actions?: string[];
    };
  } | null;
}

export interface RecommendationProfileSummary {
  risk_tolerance?: string;
  school_major_preference?: string;
  preferred_cities?: string[];
  excluded_cities?: string[];
  preferred_majors?: string[];
  blacklist_majors?: string[];
  field_provenance?: Record<string, string>;
  holland_code?: Record<string, number>;
  riasec_top_codes?: string[];
  career_assessment_status?: string;
  mbti_type?: string;
  mbti_source?: string;
  career_values?: string[];
}

interface GameMatrixViewProps {
  gameMatrix: GameMatrix;
  userProfile?: RecommendationProfileSummary | null;
}

const strategyStyles = {
  rush: {
    bg: "bg-orange-50",
    border: "border-orange-200",
    text: "text-orange-700",
    badge: "bg-orange-100 text-orange-800",
    label: "冲刺",
  },
  target: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    text: "text-blue-700",
    badge: "bg-blue-100 text-blue-800",
    label: "稳妥",
  },
  safe: {
    bg: "bg-green-50",
    border: "border-green-200",
    text: "text-green-700",
    badge: "bg-green-100 text-green-800",
    label: "保底",
  },
};

const volatilityLabels = {
  low: "低波动",
  medium: "中波动",
  high: "高波动",
};

const prefixRoleLabels: Record<string, string> = {
  key_result: "关键结果",
  active_backup: "有效后援",
  safety_anchor: "安全锚点",
  shadowed: "被前序遮蔽",
  unclassified: "未分类",
};

const formatPercent = (value?: number | null, digits = 1) => {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "-";
  }
  return `${(value * 100).toFixed(digits)}%`;
};

const formatRank = (value?: number | null) => {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "-";
  }
  return value.toLocaleString();
};

const riskLabels: Record<string, string> = {
  conservative: "保守",
  balanced: "均衡",
  aggressive: "激进",
};

const riasecLabels: Record<string, string> = {
  R: "实用型",
  I: "研究型",
  A: "艺术型",
  S: "社会型",
  E: "企业型",
  C: "常规型",
};

const careerValueLabels: Record<string, string> = {
  stability: "稳定保障",
  income: "收入回报",
  growth: "成长空间",
  autonomy: "自主选择",
  creativity: "创造表达",
  social_impact: "社会价值",
  work_life_balance: "工作生活平衡",
  leadership: "影响力与领导",
};

const GameMatrixViewComponent: React.FC<GameMatrixViewProps> = ({ gameMatrix, userProfile }) => {
  const [selectedStrategy, setSelectedStrategy] = useState<"all" | "rush" | "target" | "safe">("all");
  const [sortBy, setSortBy] = useState<"choice" | "prob" | "rank" | "firstHit" | "quant">("choice");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [externalPlanAuditSummary, setExternalPlanAuditSummary] = useState<ExternalPlanAuditSummary | null>(null);

  const dataSource = useMemo(
    () => (gameMatrix.major_group_rows && gameMatrix.major_group_rows.length > 0 ? gameMatrix.major_group_rows : []),
    [gameMatrix.major_group_rows],
  );
  const optimizationSummary = gameMatrix.optimization_summary;
  const portfolioSummary = optimizationSummary?.portfolio;
  const coverageReport = optimizationSummary?.coverage_report;
  const capacityFill = optimizationSummary?.capacity_fill;
  const volunteerPlan = gameMatrix.volunteer_plan;
  const dataVintage = gameMatrix.data_vintage;
  const planAuditSummary = gameMatrix.plan_audit_summary;
  const probabilityRange = volunteerPlan
    ? `${formatPercent(volunteerPlan.admission_probability_lower_bound)}-${formatPercent(
        volunteerPlan.admission_probability_upper_bound,
      )}`
    : "-";
  const explicitPreferenceFacts = useMemo(() => {
    const provenance = userProfile?.field_provenance ?? {};
    const isExplicit = (field: string) => provenance[field] === "user_explicit";
    const facts: Array<{ label: string; value: string }> = [];

    if (userProfile?.risk_tolerance && isExplicit("risk_tolerance")) {
      facts.push({
        label: "风险策略",
        value: riskLabels[userProfile.risk_tolerance] ?? userProfile.risk_tolerance,
      });
    }
    if (userProfile?.preferred_cities?.length && isExplicit("preferred_cities")) {
      facts.push({ label: "优先城市", value: userProfile.preferred_cities.join("、") });
    }
    if (userProfile?.preferred_majors?.length && isExplicit("preferred_majors")) {
      facts.push({ label: "优先专业", value: userProfile.preferred_majors.join("、") });
    }
    if (userProfile?.blacklist_majors?.length && isExplicit("blacklist_majors")) {
      facts.push({ label: "不接受专业", value: userProfile.blacklist_majors.join("、") });
    }
    return facts;
  }, [userProfile]);
  const inferredFieldCount = Object.values(userProfile?.field_provenance ?? {}).filter(
    (source) => source === "inferred",
  ).length;
  const careerProfileFacts = useMemo(() => {
    const facts: Array<{ label: string; value: string }> = [];
    if (userProfile?.career_assessment_status === "completed" && userProfile.riasec_top_codes?.length) {
      facts.push({
        label: "RIASEC 兴趣倾向",
        value: userProfile.riasec_top_codes
          .map((code) => `${code} ${riasecLabels[code] ?? code}`)
          .join(" · "),
      });
    }
    if (userProfile?.mbti_type) {
      facts.push({ label: "MBTI 自报", value: userProfile.mbti_type });
    }
    if (userProfile?.career_values?.length) {
      facts.push({
        label: "职业价值观",
        value: userProfile.career_values.map((item) => careerValueLabels[item] ?? item).join("、"),
      });
    }
    return facts;
  }, [userProfile]);
  const keyPrefixAudit = useMemo(() => {
    const rows = dataSource.filter((row) => row.is_key_prefix);
    return {
      count: planAuditSummary?.key_prefix?.count ?? volunteerPlan?.key_prefix_count ?? rows.length,
      indexes:
        planAuditSummary?.key_prefix?.choice_indexes ??
        volunteerPlan?.key_choice_indexes ??
        rows.map((row) => row.choice_index).filter(Boolean),
      rows,
    };
  }, [dataSource, planAuditSummary, volunteerPlan]);
  const shadowedAudit = useMemo(() => {
    const rows = dataSource.filter((row) => row.prefix_role === "shadowed" || row.is_key_prefix === false);
    return {
      count: planAuditSummary?.shadowed_choice_count ?? volunteerPlan?.shadowed_choice_count ?? rows.length,
      rows,
    };
  }, [dataSource, planAuditSummary, volunteerPlan]);
  const auditItems = useMemo(() => {
    const items: Array<{ label: string; value: string; tone: "green" | "amber" | "red" | "slate"; detail: string }> = [];
    const auditCoverage = planAuditSummary?.coverage ?? coverageReport;
    const auditBoundary = planAuditSummary?.data_boundary ?? dataVintage;
    const coverageSufficient = auditCoverage?.coverage_sufficient ?? true;
    items.push({
      label: "关键前缀",
      value: `${keyPrefixAudit.count ?? 0} 行`,
      tone: (keyPrefixAudit.count ?? 0) >= 2 ? "green" : "amber",
      detail: `真正影响首个录取结果的志愿行：${(keyPrefixAudit.indexes ?? []).join("、") || "待计算"}`,
    });
    items.push({
      label: "被遮蔽志愿",
      value: `${shadowedAudit.count ?? 0} 行`,
      tone: (shadowedAudit.count ?? 0) > dataSource.length * 0.7 ? "amber" : "slate",
      detail: "这些行大概率被前序志愿消耗，只适合作为尾部结构检查。",
    });
    items.push({
      label: "覆盖缺口",
      value: coverageSufficient ? "无明显缺口" : "需要复核",
      tone: coverageSufficient ? "green" : "red",
      detail: coverageSufficient
        ? "当前冲稳保供给满足目标结构。"
        : `缺口：${Object.entries(auditCoverage?.deficits ?? {})
            .filter(([, value]) => Number(value) > 0)
            .map(([key, value]) => `${key} ${value}`)
            .join("、") || "未列明"}`,
    });
    items.push({
      label: "数据边界",
      value: auditBoundary?.formal_recommendation_ready ? "正式数据就绪" : "仅供预研",
      tone: auditBoundary?.formal_recommendation_ready ? "green" : "amber",
      detail:
        auditBoundary?.formal_recommendation_ready
          ? "当前数据年份满足正式推荐口径。"
          : "当前年份官方数据尚不完整，正式填报前必须重新生成并人工复核。",
    });
    return items;
  }, [coverageReport, dataSource.length, dataVintage, keyPrefixAudit, planAuditSummary, shadowedAudit]);
  const comparisonSignals = useMemo(() => {
    const desired = coverageReport?.desired ?? {};
    const selected = coverageReport?.selected ?? {};
    return (["rush", "target", "safe"] as const).map((bucket) => ({
      bucket,
      desired: desired[bucket] ?? 0,
      selected: selected[bucket] ?? 0,
      delta: (selected[bucket] ?? 0) - (desired[bucket] ?? 0),
    }));
  }, [coverageReport]);

  const filteredAndSortedRows = useMemo(() => {
    const filtered =
      selectedStrategy === "all" ? dataSource : dataSource.filter((row) => row.strategy_tag === selectedStrategy);

    const sorted = [...filtered].sort((a, b) => {
      let comparison = 0;
      if (sortBy === "choice") {
        comparison = (a.choice_index ?? Number.MAX_SAFE_INTEGER) - (b.choice_index ?? Number.MAX_SAFE_INTEGER);
      } else if (sortBy === "prob") {
        comparison = a.admission_prob - b.admission_prob;
      } else if (sortBy === "firstHit") {
        comparison = (a.first_hit_prob ?? 0) - (b.first_hit_prob ?? 0);
      } else if (sortBy === "quant") {
        comparison = (a.quant_score ?? 0) - (b.quant_score ?? 0);
      } else {
        comparison = a.min_rank_pred - b.min_rank_pred;
      }
      return sortOrder === "asc" ? comparison : -comparison;
    });

    return sorted;
  }, [dataSource, selectedStrategy, sortBy, sortOrder]);

  const toggleExpand = useCallback((groupKey: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupKey)) {
        next.delete(groupKey);
      } else {
        next.add(groupKey);
      }
      return next;
    });
  }, []);

  if (dataSource.length === 0) {
    return (
      <div className="rounded-lg bg-white p-6 shadow-md">
        <p className="text-gray-600">暂无专业组推荐数据</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {explicitPreferenceFacts.length > 0 && (
        <section className="border-l-4 border-sky-500 bg-sky-50 px-5 py-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="font-bold text-gray-900">本次方案已锁定的显式偏好</h3>
              <p className="mt-1 text-sm text-gray-700">
                以下约束来自你明确填写，优先级高于系统从对话中的推断。
              </p>
            </div>
            {inferredFieldCount > 0 && (
              <span className="text-xs text-gray-600">
                系统另补充 {inferredFieldCount} 项解释信号，不覆盖这些约束
              </span>
            )}
          </div>
          <dl className="mt-4 grid grid-cols-1 gap-x-6 gap-y-3 border-t border-sky-200 pt-3 sm:grid-cols-2 lg:grid-cols-4">
            {explicitPreferenceFacts.map((fact) => (
              <div key={fact.label} className="min-w-0">
                <dt className="text-xs font-semibold text-sky-800">{fact.label}</dt>
                <dd className="mt-1 break-words text-sm text-gray-900">{fact.value}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {careerProfileFacts.length > 0 && (
        <section className="border-l-4 border-teal-600 bg-teal-50 px-5 py-4">
          <h3 className="font-bold text-gray-900">职业兴趣与价值观档案</h3>
          <p className="mt-1 text-sm text-gray-700">
            RIASEC 仅参与专业方向的辅助排序；MBTI 仅用于沟通和自我描述，不决定专业或录取概率。
          </p>
          <dl className="mt-4 grid grid-cols-1 gap-x-6 gap-y-3 border-t border-teal-200 pt-3 sm:grid-cols-3">
            {careerProfileFacts.map((fact) => (
              <div key={fact.label} className="min-w-0">
                <dt className="text-xs font-semibold text-teal-800">{fact.label}</dt>
                <dd className="mt-1 break-words text-sm text-gray-900">{fact.value}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {dataVintage && (
        <section
          className={`border-l-4 px-5 py-4 ${
            dataVintage.formal_recommendation_ready
              ? "border-emerald-500 bg-emerald-50"
              : "border-amber-500 bg-amber-50"
          }`}
        >
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="font-bold text-gray-900">数据适用边界</h3>
              <p className="mt-1 text-sm text-gray-700">
                目标年份 {dataVintage.target_year ?? "-"} / 招生计划 {dataVintage.enrollment_plan_year ?? "-"} /
                一分一段表 {dataVintage.rank_table_year ?? "-"} / 录取结果 {dataVintage.latest_historical_admission_year ?? "-"}
              </p>
            </div>
            <span className="text-sm font-semibold text-gray-800">
              {dataVintage.formal_recommendation_ready ? "正式数据已就绪" : "当前仅供方案预研"}
            </span>
          </div>
          {!dataVintage.formal_recommendation_ready && (
            <p className="mt-3 text-sm text-amber-900">
              当前年份官方数据尚不完整，不能直接作为正式填报依据。请在数据更新后重新生成并人工复核。
            </p>
          )}
        </section>
      )}

      <section className="rounded-lg bg-white p-6 shadow-md">
        <h3 className="mb-2 text-xl font-bold text-gray-900">专业组推荐总览</h3>
        <p className="mb-4 text-sm text-gray-600">
          按广东院校专业组填报规则展示推荐结果，并区分冲刺、稳妥、保底结构。
        </p>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
          <MetricCard label="推荐总数" value={dataSource.length} tone="gray" />
          <MetricCard label="冲刺" value={gameMatrix.total_rush} tone="orange" />
          <MetricCard label="稳妥" value={gameMatrix.total_target} tone="blue" />
          <MetricCard label="保底" value={gameMatrix.total_safe} tone="green" />
          <div className={`rounded-lg p-4 ${gameMatrix.is_balanced ? "bg-green-50" : "bg-yellow-50"}`}>
            <div className="mb-1 text-sm text-gray-600">策略平衡</div>
            <div className={`text-lg font-semibold ${gameMatrix.is_balanced ? "text-green-700" : "text-yellow-700"}`}>
              {gameMatrix.is_balanced ? "均衡" : "待优化"}
            </div>
          </div>
        </div>
      </section>

      {volunteerPlan && (
        <section className="rounded-lg bg-white p-6 shadow-md">
          <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-xl font-bold text-gray-900">核心推荐证据链</h3>
              <p className="mt-1 text-sm text-gray-600">
                从历史校准单组命中率切到有序志愿结果：看首命中、关键前缀、尾部调剂风险和量化证据。
              </p>
            </div>
            {volunteerPlan.plan_summary && (
              <p className="max-w-2xl text-sm text-gray-700">{volunteerPlan.plan_summary}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetricCard
              label={volunteerPlan.probability_is_calibrated ? "历史校准命中区间" : "启发式命中区间"}
              value={probabilityRange}
              tone="sky"
            />
            <MetricCard label="关键前缀" value={`${volunteerPlan.key_prefix_count ?? "-"} 行`} tone="indigo" />
            <MetricCard label="期望尾部风险" value={formatPercent(volunteerPlan.expected_tail_risk, 0)} tone="amber" />
            <MetricCard label="被遮蔽行" value={`${volunteerPlan.shadowed_choice_count ?? "-"} 行`} tone="slate" />
          </div>

          {volunteerPlan.probability_warning && (
            <p className="mt-4 border-l-2 border-sky-400 pl-3 text-sm text-gray-700">
              {volunteerPlan.probability_warning}
            </p>
          )}

          {volunteerPlan.human_review_items && volunteerPlan.human_review_items.length > 0 && (
            <div className="mt-4 border-t border-gray-200 pt-4">
              <div className="mb-2 text-sm font-semibold text-gray-800">人工复核重点</div>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                {volunteerPlan.human_review_items.slice(0, 3).map((item, index) => (
                  <div key={index} className="rounded-md bg-gray-50 px-3 py-2 text-xs text-gray-700">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-md">
        <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-gray-900">志愿表审计工作台</h3>
            <p className="mt-1 text-sm text-gray-600">
              这里不是再生成一张新表，而是检查当前方案的关键前缀、遮蔽行、覆盖缺口和数据边界。
            </p>
          </div>
          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">
            Plan Audit
          </span>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          {auditItems.map((item) => (
            <AuditTile key={item.label} {...item} />
          ))}
        </div>

        <div className="mt-5 border-t border-gray-200 pt-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h4 className="font-semibold text-gray-900">方案对比</h4>
              <p className="text-sm text-gray-600">
                当前方案与目标冲稳保结构对比；后续可接入千问方案、家长方案或人工方案做 A/B 审计。
              </p>
            </div>
            {(capacityFill?.filled_count ?? 0) > 0 && (
              <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-900">
                已容量补齐 {capacityFill?.filled_count} 行
              </span>
            )}
          </div>
          <div className="grid grid-cols-3 gap-3">
            {comparisonSignals.map((signal) => (
              <div key={signal.bucket} className="rounded-lg bg-gray-50 px-4 py-3">
                <div className="text-xs font-semibold uppercase text-gray-500">{signal.bucket}</div>
                <div className="mt-1 text-sm text-gray-700">
                  目标 {signal.desired} / 当前 {signal.selected}
                </div>
                <div
                  className={`mt-1 text-sm font-bold ${
                    signal.delta < 0 ? "text-amber-700" : signal.delta > 0 ? "text-sky-700" : "text-emerald-700"
                  }`}
                >
                  {signal.delta === 0 ? "匹配目标" : signal.delta > 0 ? `多 ${signal.delta}` : `缺 ${Math.abs(signal.delta)}`}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <CounselorDeliveryChecklist
        gameMatrix={gameMatrix}
        userProfile={userProfile}
        externalPlanAuditSummary={externalPlanAuditSummary}
      />

      <DeliveryCaseStatusPanel
        gameMatrix={gameMatrix}
        userProfile={userProfile}
        externalPlanCompared={Boolean(externalPlanAuditSummary)}
        externalPlanAuditSummary={externalPlanAuditSummary}
      />

      <DeliveryReviewRecord
        gameMatrix={gameMatrix}
        userProfile={userProfile}
        externalPlanAuditSummary={externalPlanAuditSummary}
      />

      <ExternalPlanComparator gameMatrix={gameMatrix} onAuditChange={setExternalPlanAuditSummary} />

      <CompetitiveDifferentiationPanel
        gameMatrix={gameMatrix}
        userProfile={userProfile}
        externalPlanAuditSummary={externalPlanAuditSummary}
      />

      <PaidValuePanel
        gameMatrix={gameMatrix}
        userProfile={userProfile}
        externalPlanAuditSummary={externalPlanAuditSummary}
      />

      {optimizationSummary && (
        <section className="min-w-0 overflow-hidden rounded-lg bg-slate-900 p-6 text-slate-50 shadow-md">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <h4 className="text-lg font-semibold">运行时组合策略</h4>
              <p className="mt-1 text-sm text-slate-300">
                {gameMatrix.agentic_rl_used ? "已加载学习策略 checkpoint" : "未加载 checkpoint，当前使用启发式回退"}
              </p>
            </div>
            <div className="max-w-full break-all text-sm text-slate-300 sm:max-w-md sm:text-right">
              {gameMatrix.selection_method || "pareto+runtime_rl"}
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
            <DarkMetric
              label="冲稳保配比"
              value={`冲刺 ${optimizationSummary.mix?.rush ?? "-"} / 稳妥 ${
                optimizationSummary.mix?.target ?? "-"
              } / 保底 ${optimizationSummary.mix?.safe ?? "-"}`}
            />
            <DarkMetric
              label="策略参数"
              value={`风险 ${optimizationSummary.effective_params?.risk_tolerance ?? "-"} / 多样性 ${
                optimizationSummary.effective_params?.diversity_weight ?? "-"
              } / 院校权重 ${optimizationSummary.effective_params?.prestige_weight ?? "-"}`}
            />
            <DarkMetric
              label="组合优化"
              value={
                portfolioSummary?.generated
                  ? `${portfolioSummary.style_name ?? "已生成组合"} / ${
                      volunteerPlan?.probability_is_calibrated
                        ? "最高单组历史校准命中率"
                        : "最高单组模拟概率"
                    } ${formatPercent(
                      portfolioSummary.admission_guarantee,
                      0,
                    )}`
                  : "候选不足，未生成最终志愿组合"
              }
              description={portfolioSummary?.style_description}
            />
          </div>

          {coverageReport && (
            <div className="mt-5 border-t border-slate-700 pt-4">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                <div>
                  <div className="text-xs text-slate-400">目标配比</div>
                  <div className="mt-1 text-sm font-semibold">
                    冲 {coverageReport.desired?.rush ?? 0} / 稳 {coverageReport.desired?.target ?? 0} / 保 {coverageReport.desired?.safe ?? 0}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">实际入选</div>
                  <div className="mt-1 text-sm font-semibold">
                    冲 {coverageReport.selected?.rush ?? 0} / 稳 {coverageReport.selected?.target ?? 0} / 保 {coverageReport.selected?.safe ?? 0}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400">候选覆盖</div>
                  <div className={`mt-1 text-sm font-semibold ${coverageReport.coverage_sufficient ? "text-emerald-300" : "text-amber-300"}`}>
                    {coverageReport.coverage_sufficient ? "满足目标配比" : "存在候选缺口"}
                  </div>
                </div>
              </div>
              {(capacityFill?.filled_count ?? 0) > 0 && (
                <p className="mt-3 text-xs leading-5 text-slate-200">
                  为填满志愿表，补入 {capacityFill?.filled_count} 个真实候选；原冲稳保标签未改，目标配比缺口仍保留。
                </p>
              )}
              {!coverageReport.coverage_sufficient && coverageReport.actions && (
                <div className="mt-3 space-y-1 text-xs text-amber-100">
                  {coverageReport.actions
                    .filter((action) => action.includes("only") || action.includes("review"))
                    .map((action, index) => (
                      <p key={index}>{action}</p>
                    ))}
                </div>
              )}
            </div>
          )}
        </section>
      )}

      <section className="rounded-lg bg-white p-4 shadow-md">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">筛选</label>
            <div className="flex gap-2">
              <FilterButton active={selectedStrategy === "all"} onClick={() => setSelectedStrategy("all")}>
                全部
              </FilterButton>
              {(["rush", "target", "safe"] as const).map((strategy) => (
                <FilterButton
                  key={strategy}
                  active={selectedStrategy === strategy}
                  className={selectedStrategy === strategy ? strategyStyles[strategy].badge : undefined}
                  onClick={() => setSelectedStrategy(strategy)}
                >
                  {strategyStyles[strategy].label}
                </FilterButton>
              ))}
            </div>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">排序</label>
            <select
              value={sortBy}
              onChange={(event) => {
                const value = event.target.value as "choice" | "prob" | "rank" | "firstHit" | "quant";
                setSortBy(value);
                setSortOrder(value === "choice" || value === "rank" ? "asc" : "desc");
              }}
              className="rounded-md border border-gray-300 px-3 py-1 text-sm"
            >
              <option value="choice">志愿顺序</option>
              <option value="prob">录取概率</option>
              <option value="firstHit">首命中概率</option>
              <option value="quant">量化分</option>
              <option value="rank">预测位次</option>
            </select>
            <button
              onClick={() => setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"))}
              className="rounded-md bg-gray-100 px-3 py-1 text-sm font-medium hover:bg-gray-200"
            >
              {sortOrder === "asc" ? "升序" : "降序"}
            </button>
          </div>
        </div>

        <div className="mt-2 text-sm text-gray-600">显示 {filteredAndSortedRows.length} 个专业组</div>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredAndSortedRows.map((row, index) => {
          const colors = strategyStyles[row.strategy_tag];
          const groupKey = `${row.school_name}-${row.major_group_code}`;
          const isExpanded = expandedGroups.has(groupKey);
          const prefixRole = row.prefix_role || "unclassified";
          const tailRisk = row.tail_assignment_risk ?? row.adjustment_risk;
          const quantEvidence = row.quant_evidence ?? [];
          const decisionTrace = row.decision_trace;
          const planChange = row.plan_change_explanation;
          const displayedMajors = row.major_list || [];

          return (
            <article
              key={`${groupKey}-${index}`}
              className={`${colors.bg} ${colors.border} rounded-lg border-2 p-5 transition-shadow hover:shadow-lg`}
            >
              <div className="mb-3 flex items-start justify-between">
                <div className="min-w-0 flex-1">
                  <h4 className="truncate text-lg font-bold text-gray-900">{row.school_name}</h4>
                  <p className="mt-1 text-sm text-gray-600">专业组 {row.major_group_code}</p>
                  {row.choice_index && (
                    <p className="mt-1 text-xs text-gray-600">
                      第{row.choice_index}志愿 / {prefixRoleLabels[prefixRole] ?? prefixRole}
                    </p>
                  )}
                  <p className="mt-1 text-xs text-gray-500">{row.major_count ?? displayedMajors.length} 个专业</p>
                </div>
                <span className={`${colors.badge} ml-2 flex-shrink-0 rounded px-2 py-1 text-xs font-semibold`}>
                  {colors.label}
                </span>
              </div>

              <div className="mb-3 space-y-2">
                <div>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      {row.probability_is_calibrated ? "历史校准单组命中率" : "单组投档概率"}
                    </span>
                    <span className={`text-lg font-bold ${colors.text}`}>{formatPercent(row.admission_prob)}</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-gray-200">
                    <div
                      className={`h-2 rounded-full ${
                        row.strategy_tag === "rush"
                          ? "bg-orange-500"
                          : row.strategy_tag === "target"
                            ? "bg-blue-500"
                            : "bg-green-500"
                      }`}
                      style={{ width: `${Math.max(0, Math.min(100, row.admission_prob * 100))}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <SmallMetric label="首命中" value={formatPercent(row.first_hit_prob)} />
                  <SmallMetric label="量化分" value={typeof row.quant_score === "number" ? row.quant_score.toFixed(2) : "-"} />
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">预测位次</span>
                  <span className="text-sm font-semibold text-gray-900">{formatRank(row.min_rank_pred)}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">位次区间</span>
                  <span className="text-xs text-gray-500">
                    {formatRank(row.rank_ci_lower)} - {formatRank(row.rank_ci_upper)}
                  </span>
                </div>

                {row.deterministic_risk_band && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">量化风险档</span>
                    <span className="text-xs font-semibold text-gray-700">{row.deterministic_risk_band}</span>
                  </div>
                )}
                {decisionTrace?.summary && (
                  <p className="text-xs leading-5 text-gray-700">{decisionTrace.summary}</p>
                )}
                {planChange && planChange.status !== "none" && (
                  <div className="flex items-center justify-between border-l-2 border-emerald-500 pl-2 text-xs text-gray-700">
                    <span className="font-semibold">方案变化证据</span>
                    <span>
                      {planChange.ranking_impact === "official_diff_applied" ? "已纳入排序" : "已核对，未加分"}
                    </span>
                  </div>
                )}
              </div>

              <div className="border-t border-gray-200 pt-3">
                <button
                  onClick={() => toggleExpand(groupKey)}
                  className="flex w-full items-center justify-between text-left text-sm font-medium text-gray-700 hover:text-gray-900"
                >
                  <span>包含专业 ({row.major_count ?? displayedMajors.length}个)</span>
                  <span className="text-xl">{isExpanded ? "-" : "+"}</span>
                </button>

                {isExpanded && (
                  <div className="mt-2 space-y-1">
                    {displayedMajors.map((major, idx) => (
                      <div key={`${major}-${idx}`} className="rounded bg-white bg-opacity-50 py-1 pl-2 text-xs text-gray-600">
                        {idx + 1}. {major}
                      </div>
                    ))}
                    {(row.major_count ?? 0) > displayedMajors.length && (
                      <div className="pl-2 text-xs italic text-gray-500">
                        还有 {(row.major_count ?? 0) - displayedMajors.length} 个专业
                      </div>
                    )}
                    {quantEvidence.length > 0 && (
                      <div className="mt-2 space-y-1">
                        <div className="text-xs font-semibold text-gray-700">量化证据</div>
                        {quantEvidence.slice(0, 3).map((evidence, idx) => (
                          <div key={idx} className="rounded bg-white bg-opacity-70 py-1 pl-2 text-xs text-gray-700">
                            {evidence}
                          </div>
                        ))}
                      </div>
                    )}
                    {row.probability_is_calibrated && typeof row.raw_admission_prob === "number" && (
                      <div className="mt-2 border-l-2 border-sky-400 pl-2 text-xs text-gray-700">
                        原始历史模拟 {formatPercent(row.raw_admission_prob)}，经
                        {row.probability_calibration_year ?? "历史"} 年真实结果校准后展示；原始模拟仅作内部特征。
                      </div>
                    )}
                    {decisionTrace && (
                      <div className="mt-3 grid grid-cols-1 gap-3 border-t border-gray-200 pt-3 sm:grid-cols-2">
                        <div>
                          <div className="text-xs font-semibold text-green-800">推荐依据</div>
                          <ul className="mt-1 space-y-1 text-xs text-gray-700">
                            {(decisionTrace.supporting_factors ?? []).slice(0, 3).map((factor) => (
                              <li key={factor.code}>
                                {factor.label}：{factor.value.toFixed(2)}
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <div className="text-xs font-semibold text-red-700">主要风险</div>
                          <ul className="mt-1 space-y-1 text-xs text-gray-700">
                            {(decisionTrace.risk_factors ?? []).slice(0, 3).map((factor) => (
                              <li key={factor.code}>
                                {factor.label}：{factor.value.toFixed(2)}
                              </li>
                            ))}
                            {(decisionTrace.warnings ?? []).slice(0, 2).map((warning, idx) => (
                              <li key={`warning-${idx}`}>{warning}</li>
                            ))}
                            {(decisionTrace.risk_factors ?? []).length === 0 &&
                              (decisionTrace.warnings ?? []).length === 0 && <li>未触发显著惩罚项</li>}
                          </ul>
                        </div>
                      </div>
                    )}
                    {planChange?.summary && planChange.status !== "none" && (
                      <div className="mt-3 border-t border-gray-200 pt-3">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="text-xs font-semibold text-gray-800">方案变化</div>
                          <span
                            className={`text-xs font-semibold ${
                              planChange.ranking_impact === "official_diff_applied"
                                ? "text-emerald-700"
                                : "text-gray-500"
                            }`}
                          >
                            {planChange.ranking_impact === "official_diff_applied" ? "影响排序" : "仅作解释"}
                          </span>
                        </div>
                        <p className="mt-1 text-xs leading-5 text-gray-700">{planChange.summary}</p>
                        {(planChange.review_items ?? []).length > 0 && (
                          <div className="mt-2 space-y-1 border-l-2 border-amber-400 pl-2 text-xs text-amber-900">
                            {(planChange.review_items ?? []).slice(0, 2).map((item, idx) => (
                              <p key={`plan-review-${idx}`}>{item}</p>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="mt-3 space-y-1 border-t border-gray-200 pt-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">波动性</span>
                  <span className="text-xs text-gray-700">{volatilityLabels[row.volatility]}</span>
                </div>

                {typeof row.survival_before_prob === "number" && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-600">前序失败概率</span>
                    <span className="text-xs text-gray-700">{formatPercent(row.survival_before_prob)}</span>
                  </div>
                )}

                {typeof row.cumulative_hit_prob === "number" && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-600">累计命中</span>
                    <span className="text-xs text-gray-700">{formatPercent(row.cumulative_hit_prob)}</span>
                  </div>
                )}

                {tailRisk > 0.1 && (
                  <div className="text-xs text-yellow-700">尾部调剂风险: {formatPercent(tailRisk, 0)}</div>
                )}

                {row.is_blacklist_risk && (
                  <div className="text-xs font-medium text-red-600">
                    可能调剂到 {row.worst_case_major || "非偏好专业"}
                  </div>
                )}

                {row.news_summary && <div className="mt-2 text-xs italic text-gray-600">{row.news_summary}</div>}
              </div>
            </article>
          );
        })}
      </div>

      {filteredAndSortedRows.length === 0 && (
        <div className="rounded-lg bg-white py-12 text-center shadow-md">
          <p className="mt-2 text-gray-600">当前筛选条件下没有专业组</p>
        </div>
      )}
    </div>
  );
};

function MetricCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: React.ReactNode;
  tone: "gray" | "orange" | "blue" | "green" | "sky" | "indigo" | "amber" | "slate";
}) {
  const tones = {
    gray: "bg-gray-50 text-gray-900",
    orange: "bg-orange-50 text-orange-700",
    blue: "bg-blue-50 text-blue-700",
    green: "bg-green-50 text-green-700",
    sky: "bg-sky-50 text-sky-900",
    indigo: "bg-indigo-50 text-indigo-900",
    amber: "bg-amber-50 text-amber-900",
    slate: "bg-slate-50 text-slate-900",
  };

  return (
    <div className={`rounded-lg p-4 ${tones[tone]}`}>
      <div className="mb-1 text-sm opacity-80">{label}</div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

function AuditTile({
  label,
  value,
  tone,
  detail,
}: {
  label: string;
  value: string;
  tone: "green" | "amber" | "red" | "slate";
  detail: string;
}) {
  const tones = {
    green: "border-emerald-200 bg-emerald-50 text-emerald-900",
    amber: "border-amber-200 bg-amber-50 text-amber-900",
    red: "border-red-200 bg-red-50 text-red-900",
    slate: "border-slate-200 bg-slate-50 text-slate-900",
  };
  return (
    <div className={`rounded-lg border px-4 py-3 ${tones[tone]}`}>
      <div className="text-xs font-semibold text-gray-600">{label}</div>
      <div className="mt-1 text-lg font-bold">{value}</div>
      <p className="mt-2 text-xs leading-5 text-gray-700">{detail}</p>
    </div>
  );
}

function DarkMetric({ label, value, description }: { label: string; value: React.ReactNode; description?: string }) {
  return (
    <div className="rounded-lg bg-slate-800 p-4">
      <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className="text-sm text-slate-100">{value}</div>
      {description && <p className="mt-2 text-xs text-slate-400">{description}</p>}
    </div>
  );
}

function SmallMetric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md bg-white bg-opacity-60 px-3 py-2">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-sm font-bold text-gray-900">{value}</div>
    </div>
  );
}

function FilterButton({
  active,
  className,
  onClick,
  children,
}: {
  active: boolean;
  className?: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
        active ? className || "bg-gray-800 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
      }`}
    >
      {children}
    </button>
  );
}

export const GameMatrixView = React.memo(GameMatrixViewComponent);

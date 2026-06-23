/* eslint-disable react-refresh/only-export-components */
import { buildDeliveryReadinessSummary, type DeliveryReadinessSummary } from "@/lib/deliveryReadiness";
import { buildDeepEvidenceCollectionPlan, exampleCollectionContext } from "@/lib/deepEvidenceCollectionPlan";
import { buildDeepOpportunityCard, exampleDeepOpportunityInput } from "@/lib/deepOpportunityCard";
import { buildEvidenceAutopilotRun } from "@/lib/evidenceAutopilot";
import {
  buildEvidenceAutopilotRealCaseProviderResults,
  loadEvidenceAutopilotRealCaseFixture,
  type EvidenceAutopilotRealCaseFixture,
} from "@/lib/evidenceAutopilotRealCaseProvider";
import { buildEvidenceAutopilotSnapshotProviderResults } from "@/lib/evidenceAutopilotSnapshotProvider";

type Metric = {
  label: string;
  value: string;
  note: string;
  tone?: "blue" | "green" | "orange" | "ink";
};

type VolunteerCard = {
  order: string;
  systemCode: string;
  school: string;
  group: string;
  strategy: string;
  gap: string;
  firstHit: string;
  risk: string;
  reason: string;
};

type EvidenceItem = {
  source: string;
  usage: string;
  boundary: string;
};

type DeepOpportunityEvidenceAuditTrailItem = {
  reviewId: string;
  caseId: string;
  taskId: string;
  sourceTitle: string;
  sourceUrl: string;
  sourceType: string;
  capturedAt: string;
  confidence: string;
  reviewAction: string;
};

type ReportReviewedEvidenceRecord = {
  reviewId: string;
  caseId: string;
  reviewedEvidenceCard: {
    taskId: string;
    status: "requires_capture" | "operator_review" | "captured_candidate";
    sourceTitle: string;
    sourceUrl: string;
    sourceType: string;
    excerpt: string;
    capturedAt: string;
    confidence: string;
    reviewAction: string;
  };
};

type RiskItem = {
  risk: string;
  level: "High" | "Medium" | "Low" | "高" | "中" | "低";
  signal: string;
  action: string;
};

type EvaluationItem = {
  row: string;
  target: string;
  probability: string;
  fit: string;
  risk: string;
  evidence: string;
  decision: string;
};

type PortfolioDimension = {
  label: string;
  value: string;
  note: string;
  tone?: "blue" | "green" | "orange" | "ink";
};

type PortfolioDiagnosis = {
  verdict: string;
  summary: string;
  dimensions: PortfolioDimension[];
  nextAction: string;
};

type CounterEvidenceItem = {
  question: string;
  status: "已过" | "待补" | "阻塞";
  whyItMatters: string;
  requiredAction: string;
};

type ReportChoice = {
  choice_index?: number;
  school_name?: string;
  school_code?: string;
  major_group_code?: string;
  strategy_tag?: string;
  group_admission_prob?: number;
  admission_probability_lower_bound?: number;
  admission_probability_upper_bound?: number;
  first_hit_prob?: number;
  tail_assignment_risk?: number;
  quant_evidence?: string[];
};

type ReportMajorGroupRow = {
  school_name?: string;
  school_code?: string;
  major_group_code?: string;
  strategy_tag?: string;
  admission_prob?: number;
  first_hit_prob?: number;
  tail_assignment_risk?: number;
  quant_evidence?: string[];
};

export type PathFinderReportPayload = {
  gameMatrix?: {
    major_group_rows?: ReportMajorGroupRow[];
    total_rush?: number;
    total_target?: number;
    total_safe?: number;
    volunteer_plan?: {
      choices?: ReportChoice[];
      admission_probability_lower_bound?: number;
      admission_probability_upper_bound?: number;
      expected_admission_prob?: number;
      key_prefix_count?: number;
      shadowed_choice_count?: number;
      blacklist_violation_count?: number;
    } | null;
    plan_audit_summary?: {
      status?: string;
      student_facing_items?: Array<{
        title?: string;
        detail?: string;
        severity?: string;
        type?: string;
      }>;
      coverage?: {
        coverage_sufficient?: boolean;
        deficits?: Record<string, number>;
      };
      data_boundary?: {
        target_year?: number;
        formal_recommendation_ready?: boolean;
        limitations?: string[];
      };
    } | null;
    data_vintage?: {
      target_year?: number;
      latest_historical_admission_year?: number | null;
      enrollment_plan_year?: number | null;
      rank_table_year?: number | null;
      formal_recommendation_ready?: boolean;
      limitations?: string[];
    } | null;
  } | null;
  evidenceAutopilot?: {
    caseId?: string;
    reviewedEvidenceRecords?: ReportReviewedEvidenceRecord[];
  } | null;
  deliveryProfile?: {
    score?: number;
    rank?: number;
    subject_group?: string;
    preferred_cities?: string[];
    preferred_majors?: string[];
    blacklist_majors?: string[];
    riasec_top_codes?: string[];
    mbti_type?: string;
  } | null;
  report?: string | null;
  deliveryReadiness?: DeliveryReadinessSummary;
  generatedAt?: string;
};

type ReportRenderData = {
  metrics: Metric[];
  cards: VolunteerCard[];
  evaluations: EvaluationItem[];
  portfolioDiagnosis: PortfolioDiagnosis;
  counterEvidence: CounterEvidenceItem[];
  evidence: EvidenceItem[];
  risks: RiskItem[];
  deliveryReadiness: DeliveryReadinessSummary;
  studentLabel: string;
  scoreRankLabel: string;
  subjectLabel: string;
  mbtiLabel: string;
  profileLine: string;
  advisorLine: string;
  comfortLine: string;
  dataBoundaryText: string;
};

const formatPercent = (value?: number) => {
  if (typeof value !== "number" || !Number.isFinite(value)) return "待测算";
  return `${Math.round(value * 100)}%`;
};

const formatRange = (low?: number, high?: number, fallback?: number) => {
  if (typeof low === "number" || typeof high === "number") {
    return `${formatPercent(low)} - ${formatPercent(high)}`;
  }
  return formatPercent(fallback);
};

const formatStrategyLabel = (value?: string) => {
  const key = String(value ?? "").toLowerCase();
  if (key === "rush") return "冲刺";
  if (key === "target") return "稳健";
  if (key === "safe") return "保底";
  if (key === "unclassified") return "待研判";
  return value || "待研判";
};

const strategyToneClass = (value?: string) => {
  const label = formatStrategyLabel(value);
  if (label === "冲刺") return "rush";
  if (label === "保底") return "safe";
  return "target";
};

const riskToneClass = (value?: string) => {
  const key = String(value ?? "").toLowerCase();
  if (key === "high" || value === "高") return "high";
  if (key === "medium" || value === "中") return "medium";
  if (key === "low" || value === "低") return "low";
  return "medium";
};

const formatRiskLabel = (value?: string) => {
  const key = String(value ?? "").toLowerCase();
  if (key === "high") return "高";
  if (key === "medium") return "中";
  if (key === "low") return "低";
  return value || "中";
};

const formatSubject = (value?: string) => {
  if (value === "history") return "历史类";
  if (value === "physics") return "物理类";
  return value || "物化生";
};

const defaultMetrics: Metric[] = [
  { label: "985 院校", value: "24", note: "可进入评估池", tone: "blue" },
  { label: "211 院校", value: "4", note: "稳健层次补充", tone: "green" },
  { label: "A+ 学科", value: "36", note: "专业实力优先看", tone: "orange" },
  { label: "一线 / 新一线", value: "12", note: "城市平台可选择", tone: "ink" },
];

const defaultCards: VolunteerCard[] = [
  {
    order: "01",
    systemCode: "10006",
    school: "北京航空航天大学",
    group: "003 专业组｜物理+化学｜计算机类 / 软件工程 / 人工智能",
    strategy: "冲刺",
    gap: "刚刚好",
    firstHit: "12%",
    risk: "中",
    reason: "院校平台和计算机方向都很强，适合放在前序冲刺位；需要重点看专业组内分流和调剂承受度。",
  },
  {
    order: "02",
    systemCode: "10007",
    school: "北京理工大学",
    group: "005 专业组｜物理+化学｜电子信息类 / 自动化类",
    strategy: "冲刺",
    gap: "超过 1 分",
    firstHit: "10%",
    risk: "中",
    reason: "工科气质鲜明，适合工程实践倾向强的学生；作为冲刺位，需要和后续稳健志愿形成承接。",
  },
  {
    order: "03",
    systemCode: "10614",
    school: "电子科技大学",
    group: "007 专业组｜物理+化学｜电子信息类 / 半导体方向",
    strategy: "稳健",
    gap: "压线",
    firstHit: "18%",
    risk: "低",
    reason: "电子信息优势明显，和物化生、半导体兴趣方向匹配度高，是本方案里最值得重点解释的一行。",
  },
  {
    order: "04",
    systemCode: "10286",
    school: "东南大学",
    group: "006 专业组｜物理+化学｜仪器类 / 电子信息类",
    strategy: "稳健",
    gap: "超过 2 分",
    firstHit: "16%",
    risk: "低",
    reason: "院校层次、城市平台、专业方向三者较均衡，适合作为前序冲刺失败后的主要承接。",
  },
  {
    order: "05",
    systemCode: "11845",
    school: "广东工业大学",
    group: "206 专业组｜物理+化学｜计算机类 / 自动化类",
    strategy: "保底",
    gap: "超过 6 分",
    firstHit: "9%",
    risk: "低",
    reason: "作为保底层次补足工科平台，不把学校层次包装过高，但能有效降低尾部风险。",
  },
];

const defaultEvidence: EvidenceItem[] = [
  {
    source: "历史录取与位次区间",
    usage: "判断分差、位次缓冲和冲稳保结构",
    boundary: "只能作为参考区间，不构成当年录取承诺",
  },
  {
    source: "学生画像与家庭约束",
    usage: "锁定选科、城市、专业偏好和不建议调剂方向",
    boundary: "正式填报前仍需由家庭确认风险承受度",
  },
  {
    source: "招生章程与专业备注",
    usage: "复核体检、单科、校区、分流和调剂规则",
    boundary: "最终以当年官方文件和考试院公告为准",
  },
];

const defaultRisks: RiskItem[] = [
  {
    risk: "冲刺段过集中",
    level: "中",
    signal: "前两行都接近分数边界",
    action: "保留冲刺价值，但不要把它们写成稳妥选择。",
  },
  {
    risk: "宽口径专业分流",
    level: "中",
    signal: "工科试验班、电子信息类内部方向较多",
    action: "填报前列出 1-6 专业顺序，并复核是否服从调剂。",
  },
  {
    risk: "当年计划变化",
    level: "高",
    signal: "招生计划、校区、专业备注可能调整",
    action: "出分后以当年招生计划和章程重新复核。",
  },
];

const defaultEvaluations: EvaluationItem[] = [
  {
    row: "01",
    target: "北京航空航天大学 003",
    probability: "12%",
    fit: "专业方向强匹配",
    risk: "冲刺失败概率高",
    evidence: "历史位次接近边界，专业组尾部需要复核",
    decision: "保留为前序冲刺，不承担最终落点",
  },
  {
    row: "02",
    target: "北京理工大学 005",
    probability: "10%",
    fit: "工程实践匹配",
    risk: "需要后续稳健行承接",
    evidence: "院校层次和专业方向成立，但概率不足以单独支撑",
    decision: "可冲，但必须与第 03/04 行绑定讨论",
  },
  {
    row: "03",
    target: "电子科技大学 007",
    probability: "18%",
    fit: "电子信息主线最强",
    risk: "同组调剂方向需确认",
    evidence: "专业方向、选科背景和长期就业路径一致",
    decision: "作为核心解释行，优先补招生章程证据",
  },
  {
    row: "04",
    target: "东南大学 006",
    probability: "16%",
    fit: "平台和城市均衡",
    risk: "专业组内部分流待确认",
    evidence: "承接前序冲刺失败后的主要落点",
    decision: "保留为稳健层核心行",
  },
];

const defaultPortfolioDiagnosis: PortfolioDiagnosis = {
  verdict: "可以讨论，但还不能当作最终填报稿",
  summary:
    "当前结构有明确冲刺价值，也有稳健承接和尾部缓冲；真正的问题不是学校数量，而是第 03/04 行能否承接前两行冲刺失败后的录取落点。",
  dimensions: [
    { label: "冲稳保结构", value: "2 / 2 / 1", note: "前序有冲刺，尾部有缓冲，但保底数量偏少。", tone: "blue" },
    { label: "关键落点", value: "第 03-04 行", note: "需要证明不是装饰性志愿，而是真正承接失败风险。", tone: "green" },
    { label: "尾部风险", value: "可控但需复核", note: "服从调剂前必须列出不接受专业。", tone: "orange" },
    { label: "交付结论", value: "顾问复核后交付", note: "还需当年计划、章程和体检限制复核。", tone: "ink" },
  ],
  nextAction: "先补第 03/04 行的专业组明细、近三年位次波动和调剂去向，再决定是否提高冲刺比例。",
};

const defaultCounterEvidence: CounterEvidenceItem[] = [
  {
    question: "当年招生计划是否缩招或专业组重组？",
    status: "待补",
    whyItMatters: "计划变化会直接改变历史位次的可比性。",
    requiredAction: "补 2026 招生计划和 2025 专业组口径对照。",
  },
  {
    question: "专业组尾部是否混入明确不接受方向？",
    status: "待补",
    whyItMatters: "服从调剂风险不是抽象风险，而是具体落到某些专业。",
    requiredAction: "列出组内全部专业，标记黑名单和可接受兜底专业。",
  },
  {
    question: "公众号/舆情趋势能否被官方数据支持？",
    status: "阻塞",
    whyItMatters: "舆情只能生成假设，不能直接证明分数变化。",
    requiredAction: "至少补官方计划变化、往年位次波动和多源公开讨论截图。",
  },
  {
    question: "家庭是否理解专业组与单专业的区别？",
    status: "已过",
    whyItMatters: "如果概念没过，家长会把专业组误读成单一理想专业。",
    requiredAction: "交付时保留一页概念解释和调剂确认签字。",
  },
];

const toVolunteerCard = (row: ReportChoice | ReportMajorGroupRow, index: number): VolunteerCard => {
  const school = row.school_name ?? "待定院校";
  const code = row.school_code ?? String(10000 + index).padStart(5, "0");
  const strategy = formatStrategyLabel(row.strategy_tag);
  const gap =
    "admission_probability_lower_bound" in row
      ? formatRange(row.admission_probability_lower_bound, row.admission_probability_upper_bound, row.group_admission_prob)
      : "admission_prob" in row
        ? formatPercent(row.admission_prob)
        : "待测算";
  return {
    order: String("choice_index" in row ? row.choice_index ?? index + 1 : index + 1).padStart(2, "0"),
    systemCode: code,
    school,
    group: row.major_group_code ?? "专业组待补｜选科要求待补｜专业方向待补",
    strategy,
    gap,
    firstHit: formatPercent(row.first_hit_prob),
    risk: formatPercent(row.tail_assignment_risk),
    reason: row.quant_evidence?.[0] ?? "证据说明待补充，正式交付前需要补齐该行推荐理由。",
  };
};

const toEvaluationItem = (row: ReportChoice | ReportMajorGroupRow, index: number): EvaluationItem => {
  const card = toVolunteerCard(row, index);
  const probability =
    "group_admission_prob" in row
      ? formatPercent(row.group_admission_prob)
      : "admission_prob" in row
        ? formatPercent(row.admission_prob)
        : card.gap;
  const riskValue = typeof row.tail_assignment_risk === "number" ? row.tail_assignment_risk : undefined;
  const risk =
    typeof riskValue === "number"
      ? riskValue >= 0.22
        ? "尾部风险高"
        : riskValue >= 0.12
          ? "尾部风险中"
          : "尾部风险低"
      : "尾部风险待测";
  const strategy = formatStrategyLabel(row.strategy_tag);
  const fit =
    strategy === "冲刺"
      ? "机会价值高，不能承担落点"
      : strategy === "保底"
        ? "用于风险缓冲，不包装成同等推荐"
        : "承担主要录取落点";
  return {
    row: card.order,
    target: `${card.school} ${card.group}`,
    probability,
    fit,
    risk,
    evidence: row.quant_evidence?.slice(0, 2).join("；") || card.reason,
    decision:
      strategy === "冲刺"
        ? "保留冲刺，但必须由稳健行承接"
        : strategy === "保底"
          ? "保留兜底，复核可接受专业"
          : "作为核心解释行，优先补齐证据",
  };
};

const buildPortfolioDiagnosis = (
  gameMatrix: PathFinderReportPayload["gameMatrix"] | undefined | null,
  cards: VolunteerCard[],
  deliveryReadiness: DeliveryReadinessSummary,
): PortfolioDiagnosis => {
  if (!gameMatrix) return defaultPortfolioDiagnosis;
  const plan = gameMatrix.volunteer_plan;
  const structure = `${gameMatrix.total_rush ?? 0} / ${gameMatrix.total_target ?? 0} / ${gameMatrix.total_safe ?? 0}`;
  const lower = formatPercent(plan?.admission_probability_lower_bound);
  const upper = formatPercent(plan?.admission_probability_upper_bound);
  const expected = formatPercent(plan?.expected_admission_prob);
  const safeCount = gameMatrix.total_safe ?? cards.filter((card) => card.strategy === "保底").length;
  const shadowed = plan?.shadowed_choice_count ?? 0;
  const blacklist = plan?.blacklist_violation_count ?? 0;
  return {
    verdict:
      deliveryReadiness.status === "ready" ? "可以进入家庭沟通版" : "只能作为顾问复核稿，不能直接交付",
    summary: `当前组合的预估命中为 ${expected}，保守区间 ${lower} - ${upper}。真正需要解释的是关键前序是否承接得住，以及尾部风险是否被具体专业组吸收。`,
    dimensions: [
      { label: "冲稳保结构", value: structure, note: "判断是否有冲刺价值、稳健承接和尾部缓冲。", tone: "blue" },
      { label: "关键前序", value: String(plan?.key_prefix_count ?? 0), note: "只解释真正影响录取落点的行。", tone: "green" },
      { label: "遮蔽/重复", value: String(shadowed), note: "如果过多，说明志愿顺序没有真实增益。", tone: shadowed > 0 ? "orange" : "green" },
      { label: "保底与黑名单", value: `${safeCount} / ${blacklist}`, note: "保底不足或黑名单冲突都不能交付。", tone: safeCount < 1 || blacklist > 0 ? "orange" : "ink" },
    ],
    nextAction:
      deliveryReadiness.nextAction ||
      "逐行复核当年计划、专业组明细、调剂风险和家庭不可接受方向，再生成家庭版结论。",
  };
};

const buildCounterEvidence = (
  gameMatrix: PathFinderReportPayload["gameMatrix"] | undefined | null,
  deliveryReadiness: DeliveryReadinessSummary,
): CounterEvidenceItem[] => {
  if (!gameMatrix) return defaultCounterEvidence;
  const dataBoundary = gameMatrix.plan_audit_summary?.data_boundary ?? gameMatrix.data_vintage;
  const formalReady = dataBoundary?.formal_recommendation_ready === true;
  const hasCoverageDeficit = Object.values(gameMatrix.plan_audit_summary?.coverage?.deficits ?? {}).some((value) => value > 0);
  return [
    {
      question: "当年招生计划、章程、体检和单科限制是否已复核？",
      status: formalReady ? "已过" : "待补",
      whyItMatters: "这些文件决定历史位次能否外推到当年。",
      requiredAction: formalReady ? "保留证据截图和版本日期。" : "补齐官方文件后再转家庭版。",
    },
    {
      question: "证据覆盖是否足够支撑每一行志愿解释？",
      status: hasCoverageDeficit ? "阻塞" : "已过",
      whyItMatters: "没有逐行证据，报告会退化成漂亮但不可审计的建议。",
      requiredAction: hasCoverageDeficit ? "先补缺口最多的证据类型。" : "保留证据账本编号。",
    },
    {
      question: "服从调剂风险是否落到具体专业？",
      status: "待补",
      whyItMatters: "家长需要知道最差可能落到哪里，而不是只看学校名。",
      requiredAction: "列出每个专业组内不接受专业和可接受兜底专业。",
    },
    {
      question: "趋势机会是否通过反证检查？",
      status: deliveryReadiness.status === "ready" ? "待补" : "阻塞",
      whyItMatters: "趋势只能提高研究优先级，不能替代位次和官方计划证据。",
      requiredAction: "补计划变化、位次波动和公开舆情的相互印证。",
    },
  ];
};

export function buildReportPayload(payload?: PathFinderReportPayload | null): ReportRenderData {
  const gameMatrix = payload?.gameMatrix;
  const deliveryProfile = payload?.deliveryProfile;
  const plan = gameMatrix?.volunteer_plan;
  const audit = gameMatrix?.plan_audit_summary;
  const dataBoundary = audit?.data_boundary ?? gameMatrix?.data_vintage;
  const choices = plan?.choices ?? [];
  const majorRows = gameMatrix?.major_group_rows ?? [];
  const sourceCards =
    choices.length > 0
      ? choices.slice(0, 6).map(toVolunteerCard)
      : majorRows.slice(0, 6).map(toVolunteerCard);
  const cards = sourceCards.length ? sourceCards : defaultCards;
  const isSampleMode = !gameMatrix;
  const scoreRankLabel = deliveryProfile?.score
    ? `${deliveryProfile.score} 分 / ${deliveryProfile.rank ?? "位次待补"} 位`
    : "672 分 / 3184 位";
  const subjectLabel = formatSubject(deliveryProfile?.subject_group) || "物化生";
  const preferredCities = deliveryProfile?.preferred_cities?.join(" / ") || "北京 / 南京 / 成都 / 广州";
  const preferredMajors = deliveryProfile?.preferred_majors?.join("、") || "半导体、电子信息、计算机、自动化";
  const blacklist = deliveryProfile?.blacklist_majors?.join("、") || "土木、化工、纯材料";
  const metrics: Metric[] = gameMatrix
    ? [
        { label: "冲刺志愿", value: String(gameMatrix.total_rush ?? 0), note: "前序机会位", tone: "orange" },
        { label: "稳健志愿", value: String(gameMatrix.total_target ?? 0), note: "主要承接位", tone: "blue" },
        { label: "保底志愿", value: String(gameMatrix.total_safe ?? 0), note: "风险缓冲位", tone: "green" },
        {
          label: "关键前序",
          value: String(plan?.key_prefix_count ?? 0),
          note: "真正影响落点",
          tone: "ink",
        },
      ]
    : defaultMetrics;
  const risks: RiskItem[] = audit?.student_facing_items?.length
    ? audit.student_facing_items.slice(0, 4).map((item) => ({
        risk: item.title ?? item.type ?? "计划审计项",
        level: item.severity === "P1" ? "高" : item.severity === "P2" ? "中" : "低",
        signal: item.type ?? audit.status ?? "结构待复核",
        action: item.detail ?? "正式填报前复核。",
      }))
    : defaultRisks;
  const evidence: EvidenceItem[] = gameMatrix
    ? [
        {
          source: "当前志愿分析结果",
          usage: "生成志愿卡片、命中概率、调剂风险与结构提示",
          boundary: "来自本次分析结果，正式交付前仍需人工复核。",
        },
        {
          source: "结构化学生画像",
          usage: "锁定选科、城市、专业偏好、黑名单与职业适配",
          boundary: "用户明确填写的信息优先于对话推断。",
        },
        {
          source: "志愿结构审计",
          usage: "风险提示、数据边界与关键前序披露",
          boundary: "审计只说明结构和证据边界，不保证录取结果。",
        },
      ]
    : defaultEvidence;
  const deliveryReadiness =
    payload?.deliveryReadiness ??
    buildDeliveryReadinessSummary({
      gameMatrix,
      deliveryProfile,
      report: payload?.report,
    });
  const evaluations = sourceCards.length
    ? (choices.length > 0 ? choices : majorRows).slice(0, 6).map(toEvaluationItem)
    : defaultEvaluations;
  const portfolioDiagnosis = buildPortfolioDiagnosis(gameMatrix, cards, deliveryReadiness);
  const counterEvidence = buildCounterEvidence(gameMatrix, deliveryReadiness);
  return {
    metrics,
    cards,
    evaluations,
    portfolioDiagnosis,
    counterEvidence,
    evidence,
    risks,
    deliveryReadiness,
    studentLabel: deliveryProfile?.score ? "当前分析学生" : "示例29 同学",
    scoreRankLabel,
    subjectLabel,
    mbtiLabel: deliveryProfile?.mbti_type || "INTJ",
    profileLine: `选科 ${subjectLabel}；意向城市 ${preferredCities}；重点方向 ${preferredMajors}；不建议调剂方向 ${blacklist}。`,
    advisorLine: isSampleMode
      ? "这组方案的核心不是盲目冲高，而是在不浪费 672 分的前提下，把院校层次、专业方向、城市平台和调剂风险放在同一张图里看清楚。"
      : "这组方案优先解释真正影响录取落点的前序志愿；尾部保底只作为风险缓冲，不包装成同等推荐。",
    comfortLine: "对家庭来说，真正重要的不是看起来选择很多，而是知道每一行为什么放在这里、风险在哪里、下一步要复核什么。",
    dataBoundaryText:
      dataBoundary?.limitations?.join("；") ||
      "本报告给出的是可审计的升学规划建议，不是录取承诺。正式填报前必须复核当年招生计划、招生章程、考试院公告和家庭风险承受记录。",
  };
}

const reportCoverCampusUrl = `${import.meta.env.BASE_URL}report-cover-campus.svg`;

const ReportStyles = () => (
  <style>{`
    @page {
      size: A4;
      margin: 0;
    }

    :root {
      --brochure-ink: #102033;
      --brochure-blue: #35506B;
      --brochure-sky: #E7F1FF;
      --brochure-mint: #E7F7F2;
      --brochure-orange: #C14E2A;
      --brochure-paper: #F8FBFF;
      --brochure-soft: #EAF3FF;
      --brochure-line: #C8D8EA;
      --brochure-muted: #64748B;
    }

    .report-preview-shell {
      background: #EDF5FF;
      min-height: 100vh;
      padding: 24px;
    }

    .report-toolbar {
      align-items: center;
      background: #F8FBFF;
      border: 1px solid var(--brochure-line);
      border-radius: 0;
      display: flex;
      justify-content: space-between;
      margin: 0 auto 18px;
      max-width: 210mm;
      padding: 12px 14px;
    }

    .report-toolbar p {
      color: #405166;
      font-size: 13px;
      margin: 0;
    }

    .report-toolbar button {
      background: var(--brochure-ink);
      border: 0;
      border-radius: 0;
      color: white;
      cursor: pointer;
      font-weight: 800;
      padding: 9px 14px;
    }

    .report-document {
      color: var(--brochure-ink);
      display: grid;
      gap: 18px;
      justify-content: center;
      text-rendering: geometricPrecision;
    }

    .report-page {
      background:
        linear-gradient(180deg, rgba(255,255,255,.92), rgba(246,250,255,.96)),
        var(--brochure-paper);
      box-shadow: 0 18px 42px rgba(27, 27, 26, .14);
      height: 297mm;
      overflow: hidden;
      page-break-after: always;
      position: relative;
      width: 210mm;
    }

    .report-page::after {
      background:
        linear-gradient(180deg, transparent 0, rgba(31, 94, 153, .025) 58%, rgba(31, 94, 153, .06) 100%);
      bottom: 0;
      content: "";
      height: 64mm;
      left: 0;
      pointer-events: none;
      position: absolute;
      width: 100%;
    }

    .report-page__inner {
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      height: 100%;
      padding: 17mm 18mm 15mm;
      position: relative;
      z-index: 1;
    }

    .report-page--dense .report-page__inner {
      padding: 14mm 16mm 13mm;
    }

    .report-page--dense::before {
      color: rgba(31, 94, 153, .032);
      content: "PATHFINDER";
      font-family: Georgia, "Times New Roman", serif;
      font-size: 56px;
      font-weight: 900;
      letter-spacing: .05em;
      position: absolute;
      right: -9mm;
      top: 14mm;
      transform: rotate(90deg);
      transform-origin: right top;
      white-space: nowrap;
    }

    .research-report,
    .modern-education-brochure {
      font-family: "Microsoft YaHei", "Noto Sans SC", "Source Han Sans SC", "PingFang SC", sans-serif;
    }

    .cover-modern {
      background: #F8FBFF;
    }

    .cover-modern::before {
      background: #123E68;
      content: "";
      height: 4mm;
      left: 0;
      position: absolute;
      top: 0;
      width: 100%;
    }

    .cover-modern::after {
      background:
        radial-gradient(circle at 86% 72%, rgba(31, 94, 153, .08), transparent 22%),
        radial-gradient(circle at 14% 92%, rgba(15, 118, 110, .08), transparent 20%);
      content: "";
      height: 118mm;
      left: 0;
      position: absolute;
      bottom: 0;
      width: 100%;
    }

    .cover-modern .report-page__inner {
      padding: 0;
    }

    .cover-top,
    .page-footer,
    .section-title,
    .pill-row,
    .score-panel,
    .volunteer-card__head,
    .risk-row,
    .evidence-grid {
      display: flex;
      justify-content: space-between;
    }

    .cover-top {
      align-items: center;
      border-bottom: 1px solid rgba(255, 255, 255, .38);
      color: #FFFFFF;
      left: 18mm;
      padding-bottom: 10px;
      position: absolute;
      right: 18mm;
      top: 15mm;
      z-index: 3;
    }

    .cover-top strong {
      font-size: 20px;
      letter-spacing: 0;
    }

    .cover-top span,
    .cover-kicker,
    .small-label,
    .page-footer {
      color: var(--brochure-muted);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: .04em;
    }

    .cover-visual {
      margin: -24mm 18mm 0;
      max-width: none;
      position: relative;
      z-index: 2;
    }

    .cover-media {
      background:
        linear-gradient(180deg, rgba(12, 47, 84, .34), rgba(12, 47, 84, .03) 46%, rgba(12, 47, 84, .12)),
        url("${reportCoverCampusUrl}") center 68% / cover no-repeat;
      height: 126mm;
      overflow: hidden;
      position: relative;
    }

    .cover-media::after {
      background: #F8FBFF;
      bottom: -1px;
      clip-path: polygon(0 66%, 100% 22%, 100% 100%, 0 100%);
      content: "";
      height: 38mm;
      left: 0;
      position: absolute;
      width: 100%;
    }

    .cover-media__seal {
      border: 1px solid rgba(255, 255, 255, .72);
      border-radius: 50%;
      height: 28mm;
      position: absolute;
      right: 18mm;
      top: 54mm;
      width: 28mm;
    }

    .cover-media__seal::before,
    .cover-media__seal::after {
      border-radius: 50%;
      content: "";
      position: absolute;
    }

    .cover-media__seal::before {
      border: 1px solid rgba(255, 255, 255, .52);
      inset: 5mm;
    }

    .cover-media__seal::after {
      background: rgba(255, 255, 255, .74);
      height: 4mm;
      left: 12mm;
      top: 12mm;
      width: 4mm;
    }

    .cover-title-card {
      align-items: end;
      background: rgba(255, 255, 255, .97);
      border: 1px solid rgba(200, 216, 234, .9);
      border-left: 5mm solid #1F5E99;
      box-shadow: 0 18px 42px rgba(31, 94, 153, .13);
      display: grid;
      gap: 14mm;
      grid-template-columns: 34mm minmax(0, 1fr);
      min-height: 82mm;
      padding: 13mm 14mm 12mm;
      position: relative;
    }

    .cover-title-card::after {
      background:
        linear-gradient(90deg, rgba(31, 94, 153, .12) 1px, transparent 1px),
        linear-gradient(0deg, rgba(31, 94, 153, .1) 1px, transparent 1px);
      background-size: 8mm 8mm;
      bottom: 8mm;
      content: "";
      height: 30mm;
      opacity: .24;
      position: absolute;
      right: 10mm;
      width: 48mm;
    }

    .cover-title-card > * {
      position: relative;
      z-index: 1;
    }

    .cover-lead {
      color: var(--brochure-blue);
      font-size: 18px;
      font-weight: 800;
      line-height: 1.76;
      margin: 0 0 1mm;
      max-width: 106mm;
      text-wrap: pretty;
    }

    .cover-card-label {
      align-items: center;
      color: #1F5E99;
      display: flex;
      font-size: 12px;
      font-weight: 900;
      gap: 8px;
      margin-bottom: 10px;
    }

    .cover-card-label::before {
      background: #1F5E99;
      content: "";
      height: 2px;
      width: 24px;
    }

    .cover-focus-summary {
      border-bottom: 1px solid var(--brochure-line);
      border-top: 1px solid var(--brochure-line);
      display: grid;
      gap: 16px;
      grid-template-columns: 24mm minmax(0, 1fr);
      margin: 8mm 0 0;
      padding: 6mm 7mm;
      position: relative;
    }

    .cover-title h1,
    .report-title-cn {
      color: var(--brochure-ink);
      font-size: 52px;
      letter-spacing: 0;
      line-height: 1.08;
      margin: 8px 0 0;
      text-orientation: upright;
      white-space: nowrap;
      writing-mode: vertical-rl;
    }

    .cover-title {
      position: relative;
    }

    .cover-title p {
      color: var(--brochure-blue);
      font-size: 12px;
      font-weight: 800;
      line-height: 1.6;
      margin: 0;
      max-width: 34mm;
      text-wrap: pretty;
    }

    .cover-focus-summary span {
      color: var(--brochure-muted);
      display: block;
      font-size: 12px;
      font-weight: 900;
      letter-spacing: .04em;
      margin-bottom: 8px;
    }

    .cover-focus-summary strong {
      color: var(--brochure-ink);
      display: block;
      font-size: 21px;
      line-height: 1.22;
      margin-bottom: 10px;
      white-space: normal;
    }

    .cover-focus-summary p {
      color: var(--brochure-blue);
      font-size: 13px;
      font-weight: 700;
      line-height: 1.72;
      margin: 0;
      max-width: 100mm;
      text-wrap: pretty;
    }

    .cover-meta-line {
      align-items: center;
      border-top: 3px solid var(--brochure-blue);
      box-sizing: border-box;
      color: var(--brochure-ink);
      display: flex;
      flex-wrap: wrap;
      gap: 12px 18px;
      margin: 6mm 18mm 0;
      padding-top: 12px;
    }

    .cover-meta-line span {
      color: var(--brochure-blue);
      font-size: 13px;
      font-weight: 900;
      white-space: nowrap;
    }

    .cover-meta-line b {
      color: var(--brochure-ink);
      font-size: 14px;
      margin-left: 4px;
    }

    .section-title {
      align-items: flex-end;
      border-bottom: 2px solid var(--brochure-ink);
      margin-bottom: 16px;
      padding-bottom: 10px;
    }

    .section-title h2 {
      font-size: 34px;
      line-height: 1;
      margin: 0 0 7px;
      white-space: nowrap;
    }

    .section-title p {
      color: var(--brochure-muted);
      font-size: 13px;
      font-weight: 800;
      margin: 0;
    }

    .section-title b {
      color: var(--brochure-blue);
      font-family: Georgia, "Times New Roman", serif;
      font-size: 48px;
      line-height: .9;
    }

    .score-panel {
      align-items: stretch;
      background: white;
      border: 1px solid var(--brochure-line);
      border-radius: 0;
      box-shadow: 0 16px 34px rgba(31, 68, 103, .09);
      gap: 18px;
      padding: 18px;
    }

    .score-main {
      background: var(--brochure-ink);
      border-radius: 0;
      color: white;
      flex: 0 0 66mm;
      padding: 20px;
    }

    .score-main span {
      display: block;
      font-size: 13px;
      font-weight: 900;
      margin-bottom: 20px;
    }

    .score-main strong {
      display: block;
      font-size: 48px;
      line-height: 1;
      margin-bottom: 8px;
    }

    .score-main p,
    .advisor-note p,
    .emotion-value-strip p,
    .data-boundary p,
    .volunteer-card p,
    .path-card p,
    .risk-row p,
    .evidence-grid p {
      color: #4d6072;
      font-size: 14px;
      line-height: 1.72;
      margin: 0;
      text-wrap: pretty;
    }

    .score-main p {
      color: rgba(255,255,255,.78);
      font-size: 14px;
    }

    .metric-grid {
      display: grid;
      flex: 1;
      gap: 10px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .metric {
      background: #f8fbfc;
      border: 1px solid #dce6ec;
      border-radius: 0;
      padding: 13px;
    }

    .metric--blue { background: #edf6fc; }
    .metric--green { background: #eef8f2; }
    .metric--orange { background: #fff3e7; }
    .metric--ink { background: #f3f4f6; }

    .metric span {
      color: var(--brochure-muted);
      display: block;
      font-size: 12px;
      font-weight: 900;
      margin-bottom: 6px;
    }

    .metric strong {
      display: block;
      font-size: 31px;
      line-height: 1;
      margin-bottom: 6px;
    }

    .metric p {
      color: #607083;
      font-size: 12px;
      line-height: 1.45;
      margin: 0;
    }

    .portfolio-diagnosis {
      background: white;
      border: 1px solid var(--brochure-line);
      box-shadow: 0 12px 28px rgba(31, 68, 103, .08);
      margin-top: 14px;
      padding: 15px;
    }

    .portfolio-diagnosis__main {
      border-bottom: 1px solid var(--brochure-line);
      padding-bottom: 12px;
    }

    .portfolio-diagnosis__main h3 {
      font-size: 22px;
      line-height: 1.12;
      margin: 6px 0 8px;
    }

    .portfolio-diagnosis__main p,
    .evaluation-matrix__head span,
    .portfolio-diagnosis__action span {
      color: #4d6072;
      font-size: 13px;
      font-weight: 700;
      line-height: 1.62;
    }

    .portfolio-diagnosis__grid {
      display: grid;
      gap: 9px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      margin-top: 12px;
    }

    .portfolio-diagnosis__grid .metric {
      padding: 10px;
    }

    .portfolio-diagnosis__grid .metric strong {
      font-size: 20px;
      white-space: nowrap;
    }

    .portfolio-diagnosis__action {
      align-items: flex-start;
      background: #F2F7FF;
      border: 1px solid var(--brochure-line);
      display: grid;
      gap: 10px;
      grid-template-columns: 25mm 1fr;
      margin-top: 11px;
      padding: 10px 12px;
    }

    .portfolio-diagnosis__action b {
      color: var(--brochure-ink);
      font-size: 14px;
      white-space: nowrap;
    }

    .evaluation-matrix {
      background: white;
      border: 1px solid var(--brochure-line);
      margin-top: 13px;
      padding: 13px;
    }

    .evaluation-matrix__head {
      align-items: baseline;
      border-bottom: 1px solid var(--brochure-line);
      display: flex;
      gap: 12px;
      justify-content: space-between;
      padding-bottom: 9px;
    }

    .evaluation-matrix__table {
      display: grid;
      gap: 7px;
      margin-top: 10px;
    }

    .evaluation-matrix__table article {
      align-items: stretch;
      border: 1px solid #DCE8F5;
      display: grid;
      gap: 0;
      grid-template-columns: 9mm minmax(0, 1fr) 18mm 26mm 24mm 35mm;
      min-height: 42px;
    }

    .evaluation-matrix__table b {
      align-items: center;
      background: var(--brochure-ink);
      color: white;
      display: flex;
      font-size: 13px;
      justify-content: center;
    }

    .evaluation-matrix__table div {
      min-width: 0;
      padding: 7px 9px;
    }

    .evaluation-matrix__table strong {
      display: block;
      font-size: 13px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .evaluation-matrix__table p {
      color: var(--brochure-muted);
      font-size: 10px;
      line-height: 1.35;
      margin: 2px 0 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .evaluation-matrix__table span,
    .evaluation-matrix__table em {
      align-items: center;
      border-left: 1px solid #DCE8F5;
      color: #35506B;
      display: flex;
      font-size: 10px;
      font-style: normal;
      font-weight: 800;
      justify-content: center;
      line-height: 1.28;
      padding: 6px;
      text-align: center;
    }

    .evaluation-matrix__table em {
      color: var(--brochure-ink);
      justify-content: flex-start;
      text-align: left;
    }

    .advisor-note,
    .emotion-value-strip,
    .data-boundary {
      border-radius: 0;
      margin-top: 14px;
      padding: 16px 18px;
    }

    .advisor-note {
      background: #F2F7FF;
      border: 1px solid #C8D8EA;
    }

    .emotion-value-strip {
      align-items: center;
      background: #eaf5fb;
      border: 1px solid #cde2ef;
      display: grid;
      gap: 16px;
      grid-template-columns: 42mm 1fr;
    }

    .emotion-value-strip strong {
      font-size: 24px;
      line-height: 1.2;
    }

    .toc-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin-top: 12px;
    }

    .toc-grid article,
    .path-card,
    .evidence-grid article {
      background: white;
      border: 1px solid var(--brochure-line);
      border-radius: 0;
      padding: 16px;
    }

    .toc-grid span {
      color: var(--brochure-blue);
      font-size: 25px;
      font-weight: 900;
    }

    .toc-grid h3,
    .path-card h3,
    .evidence-grid h3 {
      font-size: 20px;
      margin: 8px 0 8px;
    }

    .toc-grid p {
      color: var(--brochure-muted);
      font-size: 13px;
      line-height: 1.65;
      margin: 0;
    }

    .contents-layout {
      display: grid;
      flex: 1;
      gap: 16mm;
      grid-template-columns: 30mm minmax(0, 1fr);
      min-height: 0;
    }

    .contents-rail {
      background: linear-gradient(180deg, #F0F8FF, #FFFFFF);
      border-right: 1px solid #BFD4EA;
      color: #1F5E99;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      margin: -14mm 0 -13mm -16mm;
      padding: 18mm 5mm 16mm 10mm;
    }

    .contents-rail strong {
      font-family: Georgia, "Times New Roman", serif;
      font-size: 44px;
      line-height: .82;
    }

    .contents-rail span {
      font-size: 12px;
      font-weight: 900;
      letter-spacing: .12em;
      writing-mode: vertical-rl;
    }

    .contents-main h2 {
      color: var(--brochure-ink);
      font-size: 36px;
      line-height: 1;
      margin: 0 0 6px;
    }

    .contents-main > p {
      color: var(--brochure-muted);
      font-size: 14px;
      font-weight: 800;
      margin: 0 0 18px;
    }

    .contents-list {
      display: grid;
      gap: 9px;
      margin-top: 10mm;
    }

    .contents-list article {
      align-items: baseline;
      border-bottom: 1px solid #DCE8F5;
      display: grid;
      gap: 12px;
      grid-template-columns: 18mm minmax(0, 1fr) 14mm;
      padding: 8px 0;
    }

    .contents-list b {
      color: #1F5E99;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 26px;
      line-height: 1;
    }

    .contents-list h3 {
      font-size: 18px;
      margin: 0 0 4px;
    }

    .contents-list p {
      color: #607083;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.5;
      margin: 0;
    }

    .contents-list span {
      color: #1F5E99;
      font-size: 14px;
      font-weight: 900;
      text-align: right;
    }

    .report-boundary-panel {
      background: #F8FBFF;
      border: 1px solid #C8D8EA;
      margin-top: 12mm;
      padding: 14px 16px;
    }

    .report-boundary-panel strong {
      display: block;
      font-size: 16px;
      margin-bottom: 8px;
    }

    .report-boundary-panel p {
      color: #4d6072;
      font-size: 13px;
      font-weight: 700;
      line-height: 1.68;
      margin: 0;
      text-wrap: pretty;
    }

    .volunteer-card-deck {
      display: grid;
      gap: 11px;
    }

    .volunteer-card {
      background: white;
      border: 1px solid #d8e3eb;
      border-radius: 0;
      box-shadow: 0 10px 24px rgba(31, 68, 103, .07);
      padding: 14px 16px;
    }

    .volunteer-card__head {
      align-items: flex-start;
      gap: 14px;
    }

    .volunteer-card__index {
      background: var(--brochure-ink);
      border-radius: 0;
      color: white;
      flex: 0 0 38px;
      font-size: 18px;
      font-weight: 900;
      padding: 8px 0;
      text-align: center;
    }

    .volunteer-card__school {
      flex: 1;
      min-width: 0;
    }

    .volunteer-card__school strong {
      display: block;
      font-size: 26px;
      line-height: 1.08;
      margin-bottom: 6px;
      white-space: nowrap;
    }

    .volunteer-card__school span {
      color: var(--brochure-muted);
      display: block;
      font-size: 13px;
      font-weight: 800;
      line-height: 1.45;
    }

    .strategy {
      border-radius: 0;
      display: inline-block;
      font-size: 13px;
      font-weight: 900;
      padding: 6px 10px;
      white-space: nowrap;
    }

    .strategy--rush,
    .risk--high {
      background: #fff0e2;
      color: #a85d18;
    }

    .strategy--target,
    .risk--medium {
      background: #e9f4fb;
      color: #226296;
    }

    .strategy--safe,
    .risk--low {
      background: #e8f4ed;
      color: #39765e;
    }

    .pill-row {
      gap: 8px;
      justify-content: flex-start;
      margin: 12px 0 10px;
    }

    .pill-row span {
      background: #f4f7f9;
      border: 1px solid #dde8ee;
      border-radius: 0;
      color: #40566e;
      font-size: 12px;
      font-weight: 800;
      padding: 6px 9px;
    }

    .path-grid {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .path-card strong {
      color: var(--brochure-blue);
      display: block;
      font-size: 31px;
      line-height: 1;
      margin-bottom: 12px;
    }

    .risk-table {
      display: grid;
      gap: 12px;
      margin-top: 10px;
    }

    .risk-row {
      align-items: center;
      background: white;
      border: 1px solid var(--brochure-line);
      border-radius: 0;
      gap: 14px;
      padding: 14px;
    }

    .risk-row strong {
      flex: 0 0 39mm;
      font-size: 18px;
    }

    .risk {
      border-radius: 0;
      flex: 0 0 36px;
      font-size: 13px;
      font-weight: 900;
      padding: 6px 0;
      text-align: center;
    }

    .evidence-grid {
      gap: 12px;
      margin-top: 12px;
    }

    .evidence-grid article {
      flex: 1;
    }

    .counter-evidence {
      background: white;
      border: 1px solid var(--brochure-line);
      margin-top: 13px;
      padding: 13px;
    }

    .counter-evidence__grid {
      display: grid;
      gap: 9px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin-top: 10px;
    }

    .counter-evidence__item {
      border: 1px solid #DCE8F5;
      padding: 10px;
    }

    .counter-evidence__item div {
      align-items: center;
      display: flex;
      gap: 10px;
      justify-content: space-between;
      margin-bottom: 7px;
    }

    .counter-evidence__item strong {
      font-size: 13px;
      line-height: 1.35;
    }

    .counter-evidence__item span {
      background: #EAF3FF;
      color: #1F5E99;
      flex: 0 0 auto;
      font-size: 11px;
      font-weight: 900;
      padding: 4px 7px;
    }

    .counter-evidence__item--阻塞 span {
      background: #FFF0E7;
      color: #C14E2A;
    }

    .counter-evidence__item--已过 span {
      background: #E7F7F2;
      color: #0F766E;
    }

    .counter-evidence__item p,
    .counter-evidence__item b {
      color: #4d6072;
      display: block;
      font-size: 11px;
      line-height: 1.48;
      margin: 0;
    }

    .counter-evidence__item b {
      color: var(--brochure-ink);
      margin-top: 5px;
    }

    .data-boundary {
      background: #F2F7FF;
      border: 1px solid #C8D8EA;
    }

    .page-footer {
      align-items: center;
      border-top: 1px solid var(--brochure-line);
      margin-top: auto;
      padding-top: 10px;
    }

    @media print {
      body {
        background: white !important;
      }

      .report-preview-shell {
        background: white;
        padding: 0;
      }

      .report-toolbar {
        display: none;
      }

      .report-document {
        display: block;
      }

      .report-page {
        box-shadow: none;
        break-after: page;
        margin: 0;
      }
    }

    @media (max-width: 900px) {
      .report-preview-shell {
        overflow-x: auto;
        padding: 12px;
      }

      .report-toolbar {
        min-width: 210mm;
      }
    }
  `}</style>
);

const PageFooter = ({ page }: { page: string }) => (
  <footer className="page-footer">
    <span>研究报告 · 证据化交付</span>
    <span>{page}</span>
  </footer>
);

const SectionTitle = ({ index, title, subtitle }: { index: string; title: string; subtitle: string }) => (
  <div className="section-title">
    <div>
      <h2>{title}</h2>
      <p>{subtitle}</p>
    </div>
    <b>{index}</b>
  </div>
);

const MetricGrid = ({ metrics }: { metrics: Metric[] }) => (
  <div className="metric-grid reference-summary-strip">
    {metrics.map((metric) => (
      <article className={`metric metric--${metric.tone ?? "blue"}`} key={metric.label}>
        <span>{metric.label}</span>
        <strong>{metric.value}</strong>
        <p>{metric.note}</p>
      </article>
    ))}
  </div>
);

const PortfolioDiagnosisPanel = ({ diagnosis }: { diagnosis: PortfolioDiagnosis }) => (
  <section className="portfolio-diagnosis PortfolioDiagnosis">
    <div className="portfolio-diagnosis__main">
      <p className="small-label">组合诊断</p>
      <h3>{diagnosis.verdict}</h3>
      <p>{diagnosis.summary}</p>
    </div>
    <div className="portfolio-diagnosis__grid">
      {diagnosis.dimensions.map((dimension) => (
        <article className={`metric metric--${dimension.tone ?? "blue"}`} key={dimension.label}>
          <span>{dimension.label}</span>
          <strong>{dimension.value}</strong>
          <p>{dimension.note}</p>
        </article>
      ))}
    </div>
    <div className="portfolio-diagnosis__action">
      <b>下一步复核</b>
      <span>{diagnosis.nextAction}</span>
    </div>
  </section>
);

const EvaluationMatrix = ({ items }: { items: EvaluationItem[] }) => (
  <section className="evaluation-matrix EvaluationMatrix">
    <div className="evaluation-matrix__head">
      <p className="small-label">行级评估矩阵</p>
      <span>不是只看学校名，而是逐行评估概率、适配、风险、证据强度和处理意见。</span>
    </div>
    <div className="evaluation-matrix__table">
      {items.slice(0, 4).map((item) => (
        <article key={`${item.row}-${item.target}`}>
          <b>{item.row}</b>
          <div>
            <strong>{item.target}</strong>
            <p>{item.evidence}</p>
          </div>
          <span>{item.probability}</span>
          <span>{item.fit}</span>
          <span>{item.risk}</span>
          <em>{item.decision}</em>
        </article>
      ))}
    </div>
  </section>
);

const CounterEvidenceChecklist = ({ items }: { items: CounterEvidenceItem[] }) => (
  <section className="counter-evidence CounterEvidenceChecklist">
    <div className="evaluation-matrix__head">
      <p className="small-label">反证清单</p>
      <span>趋势判断必须先过反证检查；没有通过的项只能写成假设，不能写成确定机会。</span>
    </div>
    <div className="counter-evidence__grid">
      {items.map((item) => (
        <article className={`counter-evidence__item counter-evidence__item--${item.status}`} key={item.question}>
          <div>
            <strong>{item.question}</strong>
            <span>{item.status}</span>
          </div>
          <p>{item.whyItMatters}</p>
          <b>{item.requiredAction}</b>
        </article>
      ))}
    </div>
  </section>
);

const VolunteerCardDeck = ({ cards }: { cards: VolunteerCard[] }) => (
  <div className="volunteer-card-deck VolunteerMatrix">
    {cards.map((card) => (
      <article className="volunteer-card" key={`${card.order}-${card.systemCode}`}>
        <div className="volunteer-card__head">
          <div className="volunteer-card__index">{card.order}</div>
          <div className="volunteer-card__school">
            <strong>{card.systemCode} {card.school}</strong>
            <span>{card.group}</span>
          </div>
          <span className={`strategy strategy--${strategyToneClass(card.strategy)}`}>{formatStrategyLabel(card.strategy)}</span>
        </div>
        <div className="pill-row">
          <span>分数差距：{card.gap}</span>
          <span>关键命中：{card.firstHit}</span>
          <span>调剂风险：{card.risk}</span>
        </div>
        <p>{card.reason}</p>
      </article>
    ))}
  </div>
);

const EvidenceLedger = ({ items }: { items: EvidenceItem[] }) => (
  <div className="evidence-grid EvidenceLedger">
    {items.map((item) => (
      <article key={item.source}>
        <h3>{item.source}</h3>
        <p><b>用途：</b>{item.usage}</p>
        <p><b>边界：</b>{item.boundary}</p>
      </article>
    ))}
  </div>
);

const RiskLedger = ({ items }: { items: RiskItem[] }) => (
  <div className="risk-table RiskLedger">
    {items.map((item) => (
      <article className="risk-row" key={item.risk}>
        <strong>{item.risk}</strong>
        <span className={`risk risk--${riskToneClass(item.level)}`}>{formatRiskLabel(item.level)}</span>
        <p>{item.signal}；{item.action}</p>
      </article>
    ))}
  </div>
);

const DecisionEvidenceCard = ({ data }: { data: ReportRenderData }) => (
  <section className="advisor-note DecisionEvidenceCard">
    <p className="small-label">顾问判断</p>
    <p>{data.advisorLine}</p>
  </section>
);

const DataBoundary = ({ text }: { text: string }) => (
  <section className="data-boundary DataBoundary">
    <p className="small-label">交付边界</p>
    <p>{text}</p>
  </section>
);

const ReportContentsPage = ({ data }: { data: ReportRenderData }) => {
  const contents = [
    {
      index: "01",
      title: "决策摘要",
      note: "先判断这张志愿表能否进入家庭讨论，而不是先堆学校清单。",
      page: "03",
    },
    {
      index: "02",
      title: "志愿表总览",
      note: "逐行看学校代码、专业组、策略位置、概率区间和承接关系。",
      page: "04",
    },
    {
      index: "03",
      title: "风险缓冲与交付边界",
      note: "把兜底、调剂、计划变化和不接受方向放到可复核清单里。",
      page: "05",
    },
    {
      index: "04",
      title: "趋势机会雷达",
      note: "趋势只作为假设入口，必须接受官方数据和反证条件约束。",
      page: "06",
    },
    {
      index: "05",
      title: "风险账本与证据账本",
      note: "说明每个判断来自哪里、能支持什么、不能证明什么。",
      page: "07",
    },
  ];

  return (
    <section className="report-page report-page--dense report-page--contents">
      <div className="report-page__inner">
        <div className="contents-layout">
          <aside className="contents-rail">
            <strong>00</strong>
            <span>REPORT GUIDE</span>
          </aside>
          <main className="contents-main">
            <h2>报告阅读顺序</h2>
            <p>给家庭看的不是一组漂亮截图，而是一份能被逐项复核的选择之书。</p>
            <div className="contents-list">
              {contents.map((item) => (
                <article key={item.index}>
                  <b>{item.index}</b>
                  <div>
                    <h3>{item.title}</h3>
                    <p>{item.note}</p>
                  </div>
                  <span>{item.page}</span>
                </article>
              ))}
            </div>
            <section className="report-boundary-panel">
              <strong>本报告先给结论，再给证据边界。</strong>
              <p>{data.dataBoundaryText}</p>
            </section>
          </main>
        </div>
        <PageFooter page="02" />
      </div>
    </section>
  );
};

export function buildDeepOpportunityEvidenceAuditTrail(
  fixture: EvidenceAutopilotRealCaseFixture,
): DeepOpportunityEvidenceAuditTrailItem[] {
  return fixture.evidenceCards
    .filter((card) => card.status === "captured_candidate" && card.excerpt.trim())
    .map((card, index) => ({
      reviewId: `${fixture.caseId}-review-${String(index + 1).padStart(2, "0")}`,
      caseId: fixture.caseId,
      taskId: card.taskId,
      sourceTitle: card.sourceTitle,
      sourceUrl: card.sourceUrl.trim() || `operator-review://${fixture.caseId}-${card.taskId}`,
      sourceType: card.sourceType,
      capturedAt: card.capturedAt,
      confidence: card.confidence,
      reviewAction: card.reviewAction,
    }));
}

export function buildDeepOpportunityEvidenceAuditTrailFromRecords(
  records: ReportReviewedEvidenceRecord[] = [],
): DeepOpportunityEvidenceAuditTrailItem[] {
  return records
    .filter((record) =>
      record.reviewedEvidenceCard.status === "captured_candidate"
      && record.reviewedEvidenceCard.excerpt.trim()
    )
    .map((record) => {
      const card = record.reviewedEvidenceCard;
      return {
        reviewId: record.reviewId,
        caseId: record.caseId,
        taskId: card.taskId,
        sourceTitle: card.sourceTitle,
        sourceUrl: card.sourceUrl.trim() || `operator-review://${record.reviewId}`,
        sourceType: card.sourceType,
        capturedAt: card.capturedAt,
        confidence: card.confidence,
        reviewAction: card.reviewAction,
      };
    });
}

const DeepOpportunityReportPage = ({
  reviewedEvidenceRecords = [],
}: {
  reviewedEvidenceRecords?: ReportReviewedEvidenceRecord[];
}) => {
  const card = buildDeepOpportunityCard(exampleDeepOpportunityInput);
  const plan = buildDeepEvidenceCollectionPlan(exampleCollectionContext);
  const draftRun = buildEvidenceAutopilotRun({ plan });
  const realCaseFixture = loadEvidenceAutopilotRealCaseFixture();
  const realCaseProviderResults = buildEvidenceAutopilotRealCaseProviderResults(realCaseFixture);
  const realCaseEvidenceMode = "Real Case v0 auditable opportunity hypothesis";
  const liveReviewedEvidenceAuditTrail = buildDeepOpportunityEvidenceAuditTrailFromRecords(reviewedEvidenceRecords);
  const reviewedEvidenceAuditTrail = (
    liveReviewedEvidenceAuditTrail.length > 0
      ? liveReviewedEvidenceAuditTrail
      : buildDeepOpportunityEvidenceAuditTrail(realCaseFixture)
  ).slice(0, 4);
  const providerResults = realCaseProviderResults.length > 0
    ? realCaseProviderResults
    : buildEvidenceAutopilotSnapshotProviderResults({
      plan,
      searchTasks: draftRun.searchTasks,
      targetLabel: plan.targetLabel,
    });
  const autopilotRun = buildEvidenceAutopilotRun({ plan, providerResults });
  const autopilotSourceExcerpt: Array<{ claim: string; excerpt: string }> = autopilotRun.evidenceResults
    .flatMap((item) => item.excerpts.map((excerpt) => ({ claim: item.claim, excerpt })));
  const sourceExcerpt = autopilotSourceExcerpt.slice(0, 3).concat(
    reviewedEvidenceAuditTrail.slice(0, 2).map((item) => ({
      claim: "Reviewed Evidence Ledger",
      excerpt: `case-scoped audit trail ${item.reviewId} ${item.taskId} ${item.sourceTitle} ${item.sourceUrl} reviewAction: ${item.reviewAction}`,
    })),
  );
  const pillarByLabel = (label: string) => card.evidencePillars.find((item) => item.label === label);

  return (
    <section className="report-page report-page--dense DeepOpportunityReportPage">
      <div className="report-page__inner">
        <SectionTitle
          index="05"
          title="深度机会证据页"
          subtitle="把机会判断拆成量化定位、科研资源、师资论文、本科可获得性、真实就业、升学路径、反证与降权"
        />
        <div className="path-grid">
          {["量化定位", "科研资源", "本科生可获得性", "真实就业"].map((label) => {
            const pillar = pillarByLabel(label);
            if (!pillar) return null;
            return (
              <article className="path-card" key={label}>
                <strong>{pillar.score}</strong>
                <h3>{label}</h3>
                <p>{pillar.interpretation}</p>
              </article>
            );
          })}
        </div>
        <div className="counter-evidence">
          <p className="small-label">Evidence Autopilot · 机会雷达</p>
          <p>短期录取 / 中期升学 / 长期职业</p>
          <p>{realCaseEvidenceMode}: {realCaseFixture.claimBoundary}</p>
          <div className="path-grid">
            <article className="path-card">
              <strong>{autopilotRun.evaluation.opportunityScore}</strong>
              <h3>机会雷达分</h3>
              <p>{autopilotRun.evaluation.claimBoundary}</p>
            </article>
            <article className="path-card">
              <strong>{autopilotRun.evaluation.p0Gate.passedCount}/{autopilotRun.evaluation.p0Gate.totalCount}</strong>
              <h3>P0 门槛</h3>
              <p>官方招生、位次、科研方向、本科可获得性、真实就业和反证检查必须先过门槛。</p>
            </article>
            <article className="path-card">
              <strong>{autopilotRun.evaluation.counterEvidence.hit ? "命中" : "未命中"}</strong>
              <h3>反证命中</h3>
              <p>{autopilotRun.evaluation.counterEvidence.reasons[0] ?? "未发现阻断推荐的 P0 反证，仍需顾问复核原始来源。"}</p>
            </article>
          </div>
          <div className="counter-evidence__grid">
            {autopilotRun.evaluation.horizonSignals.map((signal) => (
              <article className="counter-evidence__item" key={signal.horizon}>
                <div><strong>{signal.horizon}</strong><span>{signal.status}</span></div>
                <p>{signal.summary}</p>
              </article>
            ))}
          </div>
          <div className="evidence-grid sourceExcerpt">
            {sourceExcerpt.map((item) => (
              <article key={`${item.claim}-${item.excerpt}`}>
                <h3>{item.claim}</h3>
                <p><b>sourceExcerpt：</b>{item.excerpt}</p>
              </article>
            ))}
          </div>
        </div>
        <div className="counter-evidence">
          <p className="small-label">科研视角</p>
          <div className="counter-evidence__grid">
            <article className="counter-evidence__item">
              <div><strong>研究方向</strong><span>课题组</span></div>
              <p>{card.researchSignals[0]}</p>
            </article>
            <article className="counter-evidence__item">
              <div><strong>师资与论文</strong><span>导师</span></div>
              <p>{card.researchSignals[2]}</p>
            </article>
            <article className="counter-evidence__item">
              <div><strong>升学路径</strong><span>读研</span></div>
              <p>{card.graduateSignals[0]}</p>
            </article>
            <article className="counter-evidence__item">
              <div><strong>反证与降权</strong><span>先降权</span></div>
              <p>{card.counterEvidenceChecks[0]}</p>
            </article>
          </div>
        </div>
        <DataBoundary text={`证据缺口：${card.evidenceGaps.join("；")} 下一步采集：${card.nextActions[0]}`} />
        <PageFooter page="07" />
      </div>
    </section>
  );
};

export function PathFinderReportTemplate({ payload }: { payload?: PathFinderReportPayload | null }) {
  const reportData = buildReportPayload(payload);
  const primaryCards = reportData.cards.slice(0, 3);
  const secondaryCards = reportData.cards.slice(3);
  return (
    <div className="report-document research-report ChineseFirstReport sample-student-29 subject-combo-wuhuasheng mbti-intj">
      <section className="report-page cover-modern canva-editorial-cover">
        <div className="report-page__inner">
          <div className="cover-media" aria-hidden="true">
            <span className="cover-media__seal" />
          </div>
          <div className="cover-top">
            <strong>寻径升学</strong>
            <span>研究报告 · 家庭决策版</span>
          </div>
          <div className="cover-visual cover-visual--focused">
            <div className="cover-title-card">
              <div className="cover-title">
                <p className="cover-kicker report-kicker-en">证据工作台</p>
                <h1 className="report-title-cn">升学质量报告</h1>
              </div>
              <div>
                <p className="cover-card-label">示例29 · 物化生 · 672分 · 3184位</p>
                <p className="cover-lead">{reportData.comfortLine}</p>
              </div>
            </div>
            <section className="cover-focus-summary">
              <span>顾问判断</span>
              <div>
                <strong>先体检志愿表，再进入逐行评估。</strong>
                <p>{reportData.advisorLine}</p>
              </div>
            </section>
          </div>
          <div className="cover-meta-line">
            <span>学生 <b>{reportData.studentLabel}</b></span>
            <span>选科 <b>{reportData.subjectLabel}</b></span>
            <span>分数 / 位次 <b>{reportData.scoreRankLabel}</b></span>
            <span>MBTI <b>{reportData.mbtiLabel}</b></span>
          </div>
        </div>
      </section>

      <ReportContentsPage data={reportData} />

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <SectionTitle index="01" title="决策摘要" subtitle="先看志愿表体检结论，再看证据账本和交付边界" />
          <div className="score-panel">
            <div className="score-main">
              <span>当前样例分数</span>
              <strong>{reportData.scoreRankLabel.split(" / ")[0]}</strong>
              <p>{reportData.profileLine}</p>
            </div>
            <MetricGrid metrics={reportData.metrics} />
          </div>
          <DecisionEvidenceCard data={reportData} />
          <PortfolioDiagnosisPanel diagnosis={reportData.portfolioDiagnosis} />
          <section className="emotion-value-strip">
            <strong>复核重点<br />先明确判断边界</strong>
            <p>{reportData.comfortLine}</p>
          </section>
          <PageFooter page="03" />
        </div>
      </section>

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <SectionTitle index="02" title="志愿表总览" subtitle="把高考系统序号、学校代码、策略位置和风险放在同一张卡里" />
          <VolunteerCardDeck cards={primaryCards} />
          <EvaluationMatrix items={reportData.evaluations} />
          <section className="emotion-value-strip">
            <strong>不是简单排名<br />而是承接关系</strong>
            <p>前序冲刺失败后，稳健段要能真实承接；如果某一行不会影响最终落点，就不应该在报告里被过度包装。</p>
          </section>
          <PageFooter page="04" />
        </div>
      </section>

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <SectionTitle index="03" title="风险缓冲与交付边界" subtitle="降低焦虑感，但不把保底说成同等推荐" />
          <VolunteerCardDeck cards={secondaryCards.length ? secondaryCards : reportData.cards.slice(2, 5)} />
          <DataBoundary text={reportData.dataBoundaryText} />
          <PageFooter page="05" />
        </div>
      </section>

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <SectionTitle index="04" title="趋势机会雷达" subtitle="趋势分析必须带置信度、反证条件和顾问复核动作" />
          <div className="path-grid">
            <article className="path-card">
              <strong>01</strong>
              <h3>半导体 / 电子信息</h3>
              <p>和物化生路径、理工兴趣、未来产业方向匹配度高，适合重点解释院校平台和专业实力。</p>
            </article>
            <article className="path-card">
              <strong>02</strong>
              <h3>计算机 / 自动化</h3>
              <p>就业面更宽，适合作为主线方向；需要确认专业组内是否混入明显不接受的调剂方向。</p>
            </article>
            <article className="path-card">
              <strong>03</strong>
              <h3>仪器类 / 智能制造</h3>
              <p>不是冷门兜底，而是工程技术路径的一种稳健选择，要结合学校学科和城市产业判断。</p>
            </article>
            <article className="path-card">
              <strong>04</strong>
              <h3>不建议方向</h3>
              <p>土木、化工、纯材料等方向若进入专业组，需要在服从调剂前单独标红复核。</p>
            </article>
          </div>
          <CounterEvidenceChecklist items={reportData.counterEvidence} />
          <PageFooter page="06" />
        </div>
      </section>

      <DeepOpportunityReportPage reviewedEvidenceRecords={payload?.evidenceAutopilot?.reviewedEvidenceRecords ?? []} />

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <SectionTitle index="06" title="风险账本与证据账本" subtitle="让家长知道风险在哪里，也知道下一步该做什么" />
          <RiskLedger items={reportData.risks} />
          <EvidenceLedger items={reportData.evidence} />
          <DataBoundary text={`交付准备度：${reportData.deliveryReadiness.score}。${reportData.deliveryReadiness.nextAction}`} />
          <PageFooter page="08" />
        </div>
      </section>
    </div>
  );
}

export function InvestmentResearchReportPreview() {
  const storedPayload =
    typeof window !== "undefined"
      ? window.sessionStorage.getItem("pathfinder-report-preview")
      : null;
  const payload = storedPayload ? (JSON.parse(storedPayload) as PathFinderReportPayload) : null;
  return (
    <main className="report-preview-shell">
      <ReportStyles />
      <div className="report-toolbar">
        <p>研究报告 · A4 可打印 · 志愿表体检 / 趋势机会 / 证据账本 / 交付边界</p>
        <button type="button" onClick={() => window.print()}>打印 / 导出 PDF</button>
      </div>
      <PathFinderReportTemplate payload={payload} />
    </main>
  );
}

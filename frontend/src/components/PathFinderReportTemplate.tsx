/* eslint-disable react-refresh/only-export-components */
import { buildDeliveryReadinessSummary, type DeliveryReadinessSummary } from "@/lib/deliveryReadiness";

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

type RiskItem = {
  risk: string;
  level: "High" | "Medium" | "Low" | "高" | "中" | "低";
  signal: string;
  action: string;
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
  return {
    metrics,
    cards,
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

const ReportStyles = () => (
  <style>{`
    @page {
      size: A4;
      margin: 0;
    }

    :root {
      --brochure-ink: #1B1B1A;
      --brochure-blue: #3E4A5C;
      --brochure-sky: #EFE8D8;
      --brochure-mint: #E6EFE8;
      --brochure-orange: #A6300E;
      --brochure-paper: #FBFAF6;
      --brochure-soft: #F1ECDE;
      --brochure-line: #D8D2C2;
      --brochure-muted: #736D5A;
    }

    .report-preview-shell {
      background: #E7E0D0;
      min-height: 100vh;
      padding: 24px;
    }

    .report-toolbar {
      align-items: center;
      background: #FBFAF6;
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
      background: var(--brochure-paper);
      box-shadow: 0 18px 42px rgba(27, 27, 26, .14);
      height: 297mm;
      overflow: hidden;
      page-break-after: always;
      position: relative;
      width: 210mm;
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

    .research-report,
    .modern-education-brochure {
      font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "Microsoft YaHei", serif;
    }

    .cover-modern {
      background: #FBFAF6;
    }

    .cover-modern::before {
      background: var(--brochure-ink);
      content: "";
      height: 4mm;
      left: 0;
      position: absolute;
      top: 0;
      width: 100%;
    }

    .cover-modern::after {
      background: rgba(166, 48, 14, .9);
      content: "";
      height: 1.6mm;
      left: 18mm;
      position: absolute;
      top: 147mm;
      width: 44mm;
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
      border-bottom: 1px solid var(--brochure-line);
      padding-bottom: 11px;
    }

    .cover-top strong {
      font-size: 20px;
      letter-spacing: .04em;
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
      display: block;
      margin-top: 24mm;
      max-width: 162mm;
    }

    .cover-title h1,
    .report-title-cn {
      color: var(--brochure-ink);
      font-size: 54px;
      letter-spacing: 0;
      line-height: 1.04;
      margin: 10px 0 18px;
      white-space: nowrap;
    }

    .cover-title p {
      color: var(--brochure-blue);
      font-size: 17px;
      font-weight: 800;
      line-height: 1.8;
      margin: 0;
      max-width: 136mm;
      text-wrap: pretty;
    }

    .campus-window {
      background:
        linear-gradient(90deg, rgba(27, 27, 26, .06) 1px, transparent 1px),
        linear-gradient(0deg, rgba(27, 27, 26, .05) 1px, transparent 1px),
        #F1ECDE;
      background-size: 12px 12px;
      border: 1px solid var(--brochure-line);
      border-radius: 0;
      display: grid;
      grid-template-columns: 30mm 1fr;
      margin-top: 28px;
      max-width: 152mm;
      min-height: auto;
      overflow: hidden;
      padding: 13px 16px;
      position: relative;
    }

    .campus-window::before {
      background: linear-gradient(90deg, transparent, rgba(166, 48, 14, .12));
      content: "";
      inset: 0;
      opacity: 1;
      position: absolute;
    }

    .campus-window b {
      color: var(--brochure-blue);
      display: block;
      font-size: 28px;
      line-height: 1;
      position: relative;
      z-index: 1;
    }

    .campus-window span {
      color: var(--brochure-ink);
      font-size: 13px;
      font-weight: 900;
      line-height: 1.55;
      position: relative;
      z-index: 1;
    }

    .cover-decision-panel {
      display: grid;
      gap: 12px;
      grid-template-columns: 1fr;
      margin-top: 18px;
      max-width: 162mm;
    }

    .cover-decision-main,
    .cover-decision-metric {
      background: rgba(255,255,255,.96);
      border: 1px solid var(--brochure-line);
      border-radius: 0;
      box-sizing: border-box;
    }

    .cover-decision-main {
      border-left: 5px solid var(--brochure-orange);
      min-height: 96px;
      padding: 15px 17px 14px;
    }

    .cover-decision-main span,
    .cover-decision-metric span {
      color: var(--brochure-muted);
      display: block;
      font-size: 11px;
      font-weight: 900;
      letter-spacing: .04em;
      margin-bottom: 7px;
    }

    .cover-decision-main strong {
      color: var(--brochure-ink);
      display: block;
      font-size: 23px;
      line-height: 1.16;
      margin-bottom: 8px;
      white-space: nowrap;
    }

    .cover-decision-main p {
      color: var(--brochure-blue);
      font-size: 13px;
      font-weight: 700;
      line-height: 1.65;
      margin: 0;
      text-wrap: pretty;
    }

    .cover-decision-metrics {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }

    .cover-decision-metric {
      min-height: 72px;
      padding: 12px 12px 10px;
    }

    .cover-decision-metric b {
      color: var(--brochure-ink);
      display: block;
      font-size: 16px;
      line-height: 1.12;
      white-space: nowrap;
    }

    .cover-roadmap {
      border-bottom: 1px solid var(--brochure-line);
      border-top: 1px solid var(--brochure-line);
      display: grid;
      gap: 0;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-top: 15px;
      max-width: 162mm;
    }

    .cover-roadmap article {
      border-right: 1px solid var(--brochure-line);
      min-height: 84px;
      padding: 13px 13px 12px;
    }

    .cover-roadmap article:last-child {
      border-right: 0;
    }

    .cover-roadmap span {
      color: var(--brochure-orange);
      display: block;
      font-size: 15px;
      font-weight: 900;
      margin-bottom: 6px;
    }

    .cover-roadmap h3 {
      color: var(--brochure-ink);
      font-size: 16px;
      line-height: 1.15;
      margin: 0 0 6px;
      white-space: nowrap;
    }

    .cover-roadmap p {
      color: var(--brochure-blue);
      font-size: 11px;
      font-weight: 700;
      line-height: 1.45;
      margin: 0;
      text-wrap: pretty;
    }

    .cover-volunteer-sample {
      align-items: center;
      background: #0A0E1A;
      color: white;
      display: grid;
      gap: 10px;
      grid-template-columns: 32mm 1fr;
      margin-top: 13px;
      max-width: 162mm;
      min-height: 64px;
      padding: 13px 16px;
    }

    .cover-volunteer-sample span {
      color: rgba(255,255,255,.66);
      font-size: 12px;
      font-weight: 900;
    }

    .cover-volunteer-sample strong {
      display: block;
      font-size: 24px;
      line-height: 1.1;
      margin-bottom: 5px;
      white-space: nowrap;
    }

    .cover-volunteer-sample b {
      color: rgba(255,255,255,.78);
      display: block;
      font-size: 13px;
      line-height: 1.2;
      white-space: nowrap;
    }

    .identity-strip {
      background: rgba(255,255,255,.94);
      border-top: 5px solid var(--brochure-orange);
      box-shadow: 0 10px 24px rgba(31, 68, 103, .08);
      display: grid;
      gap: 0;
      grid-template-columns: 1.16fr .82fr 1.38fr .66fr;
      margin-top: auto;
      padding: 17px 0 13px;
    }

    .identity-strip div {
      border-right: 1px solid var(--brochure-line);
      min-width: 0;
      padding: 0 14px;
    }

    .identity-strip div:last-child {
      border-right: 0;
    }

    .identity-strip span {
      color: var(--brochure-muted);
      display: block;
      font-size: 12px;
      font-weight: 900;
      margin-bottom: 8px;
    }

    .identity-strip b {
      display: block;
      font-size: 21px;
      line-height: 1.15;
      white-space: nowrap;
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

    .advisor-note,
    .emotion-value-strip,
    .data-boundary {
      border-radius: 0;
      margin-top: 14px;
      padding: 16px 18px;
    }

    .advisor-note {
      background: #fff4e7;
      border: 1px solid #f1d2aa;
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

    .data-boundary {
      background: #f6f2e9;
      border: 1px solid #dfd3bd;
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

export function PathFinderReportTemplate({ payload }: { payload?: PathFinderReportPayload | null }) {
  const reportData = buildReportPayload(payload);
  const primaryCards = reportData.cards.slice(0, 3);
  const secondaryCards = reportData.cards.slice(3);
  return (
    <div className="report-document research-report ChineseFirstReport sample-student-29 subject-combo-wuhuasheng mbti-intj">
      <section className="report-page cover-modern canva-editorial-cover">
        <div className="report-page__inner">
          <div className="cover-top">
            <strong>PathFinder</strong>
            <span>研究报告 · 家庭决策版</span>
          </div>
          <div className="cover-visual">
            <div className="cover-title">
              <p className="cover-kicker report-kicker-en">证据工作台 · 示例29 · 物化生 · 672分 · 3184位</p>
              <h1 className="report-title-cn">升学规划研究报告</h1>
              <p>{reportData.comfortLine}</p>
            </div>
            <div className="campus-window">
              <b>2026</b>
              <span>把分数、城市、专业和风险放在一张图里看清楚</span>
            </div>
            <div className="cover-decision-panel">
              <div className="cover-decision-main">
                <span>顾问判断</span>
                <strong>先稳住家庭判断，再讨论冲高</strong>
                <p>{reportData.advisorLine}</p>
              </div>
              <div className="cover-decision-metrics">
                <div className="cover-decision-metric">
                  <span>志愿结构</span>
                  <b>冲2｜稳2｜保1</b>
                </div>
                <div className="cover-decision-metric">
                  <span>专业主线</span>
                  <b>电子信息</b>
                </div>
                <div className="cover-decision-metric">
                  <span>城市半径</span>
                  <b>北｜南｜成｜广</b>
                </div>
                <div className="cover-decision-metric">
                  <span>复核重点</span>
                  <b>顾问复核签字</b>
                </div>
              </div>
            </div>
            <div className="cover-roadmap">
              <article>
                <span>01</span>
                <h3>先定安全边界</h3>
                <p>看清楚哪些学校适合冲，哪些组合承担兜底。</p>
              </article>
              <article>
                <span>02</span>
                <h3>再看专业路径</h3>
                <p>围绕电子信息、半导体、自动化展开，而不是只看校名。</p>
              </article>
              <article>
                <span>03</span>
                <h3>最后复核风险</h3>
                <p>逐项检查调剂、分流、计划变化和身体条件限制。</p>
              </article>
            </div>
            <div className="cover-volunteer-sample">
              <span>样例志愿</span>
              <div>
                <strong>11845 广东工业大学</strong>
                <b>206 专业组｜物理+化学｜计算机类 / 自动化类</b>
              </div>
            </div>
          </div>
          <div className="identity-strip">
            <div><span>学生</span><b>{reportData.studentLabel}</b></div>
            <div><span>选科</span><b>{reportData.subjectLabel}</b></div>
            <div><span>分数 / 位次</span><b>{reportData.scoreRankLabel}</b></div>
            <div><span>MBTI</span><b>{reportData.mbtiLabel}</b></div>
          </div>
        </div>
      </section>

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
          <section className="emotion-value-strip">
            <strong>这一版方案<br />先稳住家庭判断</strong>
            <p>{reportData.comfortLine}</p>
          </section>
          <div className="toc-grid">
            <article><span>01</span><h3>志愿卡片</h3><p>院校代码、院校名称、专业组和风险放在同一张卡里，接近真实填报系统。</p></article>
            <article><span>02</span><h3>专业路径</h3><p>解释为什么半导体、电子信息、自动化更适合当前画像。</p></article>
            <article><span>03</span><h3>风险提示</h3><p>不只说能不能上，也说调剂、分流、计划变化怎么处理。</p></article>
            <article><span>04</span><h3>交付边界</h3><p>正式填报前必须复核当年计划、章程、体检和单科限制。</p></article>
          </div>
          <PageFooter page="02" />
        </div>
      </section>

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <SectionTitle index="02" title="志愿表总览" subtitle="把高考系统序号、学校代码、策略位置和风险放在同一张卡里" />
          <VolunteerCardDeck cards={primaryCards} />
          <section className="emotion-value-strip">
            <strong>不是简单排名<br />而是承接关系</strong>
            <p>前序冲刺失败后，稳健段要能真实承接；如果某一行不会影响最终落点，就不应该在报告里被过度包装。</p>
          </section>
          <PageFooter page="03" />
        </div>
      </section>

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <SectionTitle index="03" title="风险缓冲与交付边界" subtitle="降低焦虑感，但不把保底说成同等推荐" />
          <VolunteerCardDeck cards={secondaryCards.length ? secondaryCards : reportData.cards.slice(2, 5)} />
          <DataBoundary text={reportData.dataBoundaryText} />
          <PageFooter page="04" />
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
          <PageFooter page="05" />
        </div>
      </section>

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <SectionTitle index="05" title="风险账本与证据账本" subtitle="让家长知道风险在哪里，也知道下一步该做什么" />
          <RiskLedger items={reportData.risks} />
          <EvidenceLedger items={reportData.evidence} />
          <DataBoundary text={`交付准备度：${reportData.deliveryReadiness.score}。${reportData.deliveryReadiness.nextAction}`} />
          <PageFooter page="06" />
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

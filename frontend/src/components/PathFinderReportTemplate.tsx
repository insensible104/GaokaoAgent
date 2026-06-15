/* eslint-disable react-refresh/only-export-components */
import { buildDeliveryReadinessSummary, type DeliveryReadinessSummary } from "@/lib/deliveryReadiness";

type Metric = {
  label: string;
  value: string;
  note: string;
  tone?: "neutral" | "positive" | "warning";
};

type MatrixRow = {
  order: string;
  school: string;
  group: string;
  strategy: string;
  probability_range: string;
  first_hit_prob: string;
  tail_assignment_risk: string;
  evidence: string;
};

type EvidenceItem = {
  source: string;
  usage: string;
  boundary: string;
};

type RiskItem = {
  risk: string;
  level: "High" | "Medium" | "Low";
  signal: string;
  action: string;
};

type ReportChoice = {
  choice_index?: number;
  school_name?: string;
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
  rows: MatrixRow[];
  evidence: EvidenceItem[];
  risks: RiskItem[];
  deliveryReadiness: DeliveryReadinessSummary;
  profileLine: string;
  strategyLine: string;
  focusLine: string;
  studentLabel: string;
  scoreRankLabel: string;
  dataBoundaryText: string;
  careerCards: Array<{ score: string; title: string; body: string }>;
};

const formatPercent = (value?: number) => {
  if (typeof value !== "number" || !Number.isFinite(value)) return "N/A";
  return `${Math.round(value * 100)}%`;
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
  const key = String(value ?? "").toLowerCase();
  if (key === "rush" || value === "冲刺") return "rush";
  if (key === "target" || value === "稳健") return "target";
  if (key === "safe" || value === "保底") return "safe";
  return "target";
};

const formatRiskLabel = (value?: string) => {
  const key = String(value ?? "").toLowerCase();
  if (key === "high") return "高";
  if (key === "medium") return "中";
  if (key === "low") return "低";
  return value || "待复核";
};

const riskToneClass = (value?: string) => {
  const key = String(value ?? "").toLowerCase();
  if (key === "high" || value === "高") return "high";
  if (key === "medium" || value === "中") return "medium";
  if (key === "low" || value === "低") return "low";
  return "medium";
};

const formatGateStatus = (value?: string) => {
  const key = String(value ?? "").toLowerCase();
  if (key === "ready") return "已就绪";
  if (key === "needs_review") return "待复核";
  if (key === "blocked") return "暂不可交付";
  return value || "待复核";
};

const formatRiasecLabel = (value?: string) => {
  const normalized = String(value ?? "").replace(/\s/g, "");
  if (!normalized) return "研究型 / 实用型";
  const labels: Record<string, string> = {
    R: "实用型",
    I: "研究型",
    A: "艺术型",
    S: "社会型",
    E: "企业型",
    C: "常规型",
  };
  return normalized
    .split("/")
    .map((code) => labels[code.toUpperCase()] ?? code)
    .join(" / ");
};

const defaultSummaryMetrics: Metric[] = [
  { label: "985 院校", value: "24", note: "覆盖 985 层次可达院校与专业组", tone: "positive" },
  { label: "211 院校", value: "4", note: "补充稳健层次与区域选择", tone: "neutral" },
  { label: "A+ 学科", value: "36", note: "参考学科实力与王牌专业筛选", tone: "positive" },
  { label: "A级学科", value: "46", note: "专业质量仍具备明显优势", tone: "neutral" },
  { label: "一线城市", value: "4", note: "兼顾城市平台与就业半径", tone: "warning" },
  { label: "选科路径", value: "物化生", note: "物理 / 化学 / 生物，可覆盖主流理工医方向", tone: "positive" },
];

const defaultMatrixRows: MatrixRow[] = [
  {
    order: "01",
    school: "北京航空航天大学",
    group: "计算机类 / 软件工程 / 人工智能",
    strategy: "冲刺",
    probability_range: "刚刚好",
    first_hit_prob: "12%",
    tail_assignment_risk: "中",
    evidence: "985；A+ 学科；物化生路径可报，需重点复核专业组内分流。",
  },
  {
    order: "02",
    school: "北京理工大学",
    group: "电子信息类 / 自动化类 / 兵器类",
    strategy: "冲刺",
    probability_range: "超过1分",
    first_hit_prob: "10%",
    tail_assignment_risk: "中",
    evidence: "985；工科平台强，适合偏工程实践和国防科技方向。",
  },
  {
    order: "03",
    school: "电子科技大学",
    group: "电子信息类 / 半导体方向",
    strategy: "稳健",
    probability_range: "压线",
    first_hit_prob: "18%",
    tail_assignment_risk: "低",
    evidence: "211/985 平台；电子信息优势明显，半导体方向作为重点解释对象。",
  },
  {
    order: "04",
    school: "东南大学",
    group: "仪器类 / 电子信息类 / 计算机类",
    strategy: "稳健",
    probability_range: "超过2分",
    first_hit_prob: "16%",
    tail_assignment_risk: "低",
    evidence: "985；仪器类与电子信息方向形成稳健组合。",
  },
  {
    order: "05",
    school: "大连理工大学",
    group: "机械类 / 材料类 / 自动化类",
    strategy: "保底",
    probability_range: "超过6分",
    first_hit_prob: "9%",
    tail_assignment_risk: "低",
    evidence: "985；作为保底层次补足工科平台，不与黑名单方向冲突。",
  },
];

const defaultEvidenceLedger: EvidenceItem[] = [
  {
    source: "历史录取与位次区间",
    usage: "用于判断“刚刚好 / 超过1分 / 压线”等位次表达",
    boundary: "只能作为参考区间，不构成当年录取承诺",
  },
  {
    source: "学生画像与家庭约束",
    usage: "锁定选科、城市、专业偏好、黑名单和风险承受度",
    boundary: "显式填写内容优先于对话推断",
  },
  {
    source: "霍兰德兴趣测评",
    usage: "解释半导体、仪器类、电子信息等方向的适配原因",
    boundary: "不改变录取概率，不覆盖黑名单",
  },
  {
    source: "招生章程与专业备注",
    usage: "复核体检、单科、校区、分流和调剂规则",
    boundary: "正式填报以当年官方文件为准",
  },
];

const defaultRiskLedger: RiskItem[] = [
  {
    risk: "冲刺段过集中",
    level: "Medium",
    signal: "北京航空航天大学、北京理工大学均接近分数边界",
    action: "保留冲刺价值，但不能把它们写成稳妥选择。",
  },
  {
    risk: "宽口径专业分流",
    level: "Medium",
    signal: "工科试验班、电子信息类内部方向较多",
    action: "正式填报前列出 1-6 专业顺序，并复核是否服从调剂。",
  },
  {
    risk: "当年计划变化",
    level: "High",
    signal: "招生计划、校区、专业备注可能调整",
    action: "出分后以当年招生计划和章程重新复核。",
  },
  {
    risk: "MBTI 被过度解释",
    level: "Low",
    signal: "本样例模拟 INTJ 作为沟通画像",
    action: "只用于表达风格和自我理解，不进入排序和概率。",
  },
];

export function buildReportPayload(payload?: PathFinderReportPayload | null): ReportRenderData {
  const gameMatrix = payload?.gameMatrix;
  const deliveryProfile = payload?.deliveryProfile;
  const plan = gameMatrix?.volunteer_plan;
  const audit = gameMatrix?.plan_audit_summary;
  const dataBoundary = audit?.data_boundary ?? gameMatrix?.data_vintage;
  const choices = plan?.choices ?? [];
  const majorRows = gameMatrix?.major_group_rows ?? [];
  const sourceRows: MatrixRow[] =
    choices.length > 0
      ? choices.slice(0, 10).map((choice, index) => ({
          order: String(choice.choice_index ?? index + 1).padStart(2, "0"),
          school: choice.school_name ?? "待定院校",
          group: choice.major_group_code ?? "待定专业组",
          strategy: formatStrategyLabel(choice.strategy_tag),
          probability_range:
            choice.admission_probability_lower_bound !== undefined || choice.admission_probability_upper_bound !== undefined
              ? `${formatPercent(choice.admission_probability_lower_bound)}-${formatPercent(choice.admission_probability_upper_bound)}`
              : formatPercent(choice.group_admission_prob),
          first_hit_prob: formatPercent(choice.first_hit_prob),
          tail_assignment_risk: formatPercent(choice.tail_assignment_risk),
          evidence: choice.quant_evidence?.[0] ?? "证据说明待补充",
        }))
      : majorRows.slice(0, 10).map((row, index) => ({
          order: String(index + 1).padStart(2, "0"),
          school: row.school_name ?? "待定院校",
          group: row.major_group_code ?? "待定专业组",
          strategy: formatStrategyLabel(row.strategy_tag),
          probability_range: formatPercent(row.admission_prob),
          first_hit_prob: formatPercent(row.first_hit_prob),
          tail_assignment_risk: formatPercent(row.tail_assignment_risk),
          evidence: row.quant_evidence?.[0] ?? "证据说明待补充",
        }));
  const deficits = audit?.coverage?.deficits ?? {};
  const deficitCount = Object.values(deficits).reduce((total, value) => total + Number(value || 0), 0);
  const formalReady = dataBoundary?.formal_recommendation_ready ?? false;
  const metrics: Metric[] = gameMatrix
    ? [
        {
          label: "正式行数",
          value: String(choices.length || majorRows.length || 0),
          note: "当前已纳入分析的志愿行",
          tone: "neutral",
        },
        {
          label: "预计区间",
          value:
            plan?.admission_probability_lower_bound !== undefined || plan?.admission_probability_upper_bound !== undefined
              ? `${formatPercent(plan?.admission_probability_lower_bound)}-${formatPercent(plan?.admission_probability_upper_bound)}`
              : formatPercent(plan?.expected_admission_prob),
          note: "整表层面的校准区间",
          tone: "positive",
        },
        {
          label: "关键前序",
          value: String(plan?.key_prefix_count ?? 0),
          note: "真正影响录取落点的行",
          tone: "warning",
        },
        {
          label: "硬性排除",
          value: String(plan?.blacklist_violation_count ?? 0),
          note: "黑名单方向暴露情况",
          tone: (plan?.blacklist_violation_count ?? 0) > 0 ? "warning" : "positive",
        },
        {
          label: "覆盖缺口",
          value: String(deficitCount),
          note: audit?.coverage?.coverage_sufficient ? "冲稳保结构暂无明显缺口" : "需要人工复核结构",
          tone: deficitCount > 0 ? "warning" : "positive",
        },
        {
          label: "数据年份",
          value: String(dataBoundary?.target_year ?? gameMatrix.data_vintage?.latest_historical_admission_year ?? "N/A"),
          note: formalReady ? "当年正式数据已可用" : "仍需披露数据边界",
          tone: formalReady ? "positive" : "warning",
        },
      ]
    : defaultSummaryMetrics;
  const evidence: EvidenceItem[] = gameMatrix
    ? [
        {
          source: "当前志愿分析结果",
          usage: "志愿矩阵、命中概率、调剂风险与结构审计",
          boundary: "来自本次分析结果，正式交付前仍需人工复核。",
        },
        {
          source: "结构化学生画像",
          usage: "锁定选科、城市、专业偏好、黑名单与职业适配附录",
          boundary: "用户明确填写的信息优先于对话推断。",
        },
        {
          source: "志愿结构审计",
          usage: "风险账本、数据边界、覆盖缺口与关键前序披露",
          boundary: "审计只说明结构和证据边界，不保证录取结果。",
        },
      ]
    : defaultEvidenceLedger;
  const risks: RiskItem[] = audit?.student_facing_items?.length
    ? audit.student_facing_items.slice(0, 6).map((item) => ({
        risk: item.title ?? item.type ?? "计划审计项",
        level: item.severity === "P1" ? "High" : item.severity === "P2" ? "Medium" : "Low",
        signal: item.type ?? audit.status ?? "audit",
        action: item.detail ?? "正式提交前复核。",
      }))
    : defaultRiskLedger;
  const isSampleMode = !gameMatrix;
  const preferredCities = deliveryProfile?.preferred_cities?.join("/") || (isSampleMode ? "北京 / 南京 / 成都 / 大连" : "未锁定城市");
  const preferredMajors = deliveryProfile?.preferred_majors?.join("、") || (isSampleMode ? "半导体、仪器类、电子信息、自动化" : "未锁定专业");
  const blacklist = deliveryProfile?.blacklist_majors?.join("、") || (isSampleMode ? "土木、化工、纯材料" : "无明确黑名单");
  const subjectGroup =
    deliveryProfile?.subject_group === "history"
      ? "历史类"
      : deliveryProfile?.subject_group === "physics"
        ? "物理类"
        : isSampleMode
          ? "物化生"
          : deliveryProfile?.subject_group || "科类待补";
  const riasec = formatRiasecLabel(deliveryProfile?.riasec_top_codes?.join("/") || "I/R");
  const mbti = deliveryProfile?.mbti_type || "INTJ";
  const deliveryReadiness =
    payload?.deliveryReadiness ??
    buildDeliveryReadinessSummary({
      gameMatrix,
      deliveryProfile,
      report: payload?.report,
    });
  return {
    metrics,
    rows: sourceRows.length ? sourceRows : defaultMatrixRows,
    evidence,
    risks,
    deliveryReadiness,
    profileLine: isSampleMode
      ? `示例29；选科：${subjectGroup}；城市：${preferredCities}；专业：${preferredMajors}；不建议调剂方向：${blacklist}。`
      : `选科：${subjectGroup}；城市：${preferredCities}；专业：${preferredMajors}；黑名单：${blacklist}。`,
    strategyLine: isSampleMode
      ? "参考报告口径：985 院校 24 所 / 211 院校 4 所 / A+ 学科 36 个；本模板仍保留概率边界与复核动作。"
      : `冲刺 ${gameMatrix?.total_rush ?? 0} / 稳健 ${gameMatrix?.total_target ?? 0} / 保底 ${gameMatrix?.total_safe ?? 0}；覆盖缺口 ${deficitCount}；本模板保留概率边界与复核动作。`,
    focusLine: isSampleMode
      ? "优先解释半导体、仪器类、电子信息等可落地专业方向；尾部保底只作为风险缓冲，不包装成同等推荐。"
      : `优先解释关键前缀 ${plan?.key_prefix_count ?? audit?.student_facing_items?.length ?? 0} 行；被遮蔽 ${plan?.shadowed_choice_count ?? 0} 行不包装成同等推荐。`,
    studentLabel: deliveryProfile?.score ? "当前分析学生" : "示例29 同学",
    scoreRankLabel: deliveryProfile?.score
      ? `${deliveryProfile.score} / ${deliveryProfile.rank ?? "位次待补"}`
      : "672 / 3184",
    dataBoundaryText:
      dataBoundary?.limitations?.join("；") ||
      "分数区间、关键命中与调剂风险均为基于历史数据、学生约束和当前候选池的启发式决策信号。正式填报前必须复核当年招生计划、招生章程和考试院公告。",
    careerCards: [
      {
        score: riasec,
        title: "霍兰德兴趣",
        body: "用于解释专业兴趣与志愿选择之间的软匹配，不覆盖录取概率和硬过滤条件。",
      },
      {
        score: subjectGroup,
        title: "选科口径",
        body: "报告只在当前选科口径下解释院校专业组，不跨科类外推。",
      },
      {
        score: "MBTI",
        title: mbti,
        body: "MBTI 只作为自我描述和沟通风格参考，不改变录取概率、专业效用或硬过滤条件。",
      },
    ],
  };
}

const DeliveryReadiness = ({ summary }: { summary: DeliveryReadinessSummary }) => (
  <section className="report-readiness">
    <div className="section-heading">
      <p>01</p>
      <div>
        <h2 className="section-heading__cn">交付准备度</h2>
        <span className="section-heading__en">交付前复核门槛</span>
      </div>
    </div>
    <div className="readiness-summary">
      <div>
        <span>交付准备度</span>
        <strong>{summary.score}</strong>
      </div>
      <p>{summary.claimBoundary}</p>
    </div>
    <div className="readiness-grid">
      {summary.gates.map((gate) => (
        <article key={gate.id} className={`readiness-gate readiness-gate--${gate.status}`}>
          <span>{formatGateStatus(gate.status)}</span>
          <h3>{gate.label}</h3>
          <p>{gate.signal}</p>
          <b>{gate.action}</b>
        </article>
      ))}
    </div>
    <p className="readiness-next">正式交付前必须复核：{summary.nextAction}</p>
  </section>
);

const DataBoundary = ({ text }: { text: string }) => (
  <section className="report-callout">
    <div>
      <p className="eyebrow">数据边界</p>
      <h3>本报告给出的是可审计决策建议，不是录取承诺</h3>
    </div>
    <p>{text}</p>
  </section>
);

const CompactEvidencePanel = ({ title, items }: { title: string; items: string[] }) => (
  <section className="compact-evidence-panel">
    <h3>{title}</h3>
    <div>
      {items.map((item, index) => (
        <p key={item}><b>{String(index + 1).padStart(2, "0")}</b>{item}</p>
      ))}
    </div>
  </section>
);

const DecisionEvidenceCard = () => (
  <section className="decision-card">
    <div className="decision-card__header">
      <div>
        <p className="eyebrow">关键志愿解释</p>
        <h3>关键前缀志愿解释</h3>
      </div>
      <span>第 06 行</span>
    </div>
    <div className="decision-card__grid">
      <div>
        <span>机会判断</span>
        <strong>深圳大学 214 计算机类</strong>
        <p>命中概率与城市偏好同时满足，且专业方向与霍兰德工程/研究倾向一致。</p>
      </div>
      <div>
        <span>风险控制</span>
        <strong>尾部风险低</strong>
        <p>组内专业没有黑名单碰撞，建议服从调剂，但需复核当年单科和体检规则。</p>
      </div>
      <div>
        <span>排序原因</span>
        <strong>前序失败后的主要承接</strong>
        <p>该行不是装饰性推荐，关键命中概率达 28%，会真实影响整张表的落点。</p>
      </div>
    </div>
  </section>
);

const VolunteerMatrix = ({ rows }: { rows: MatrixRow[] }) => (
  <section>
    <div className="section-heading">
      <p>02</p>
      <div>
        <h2 className="section-heading__cn">志愿矩阵</h2>
        <span className="section-heading__en">院校专业组对比</span>
      </div>
    </div>
    <table className="report-table">
      <thead>
        <tr>
          <th>序号</th>
          <th>院校</th>
          <th>专业方向</th>
          <th>定位</th>
          <th>分数差距<span className="th-en">区间口径</span></th>
          <th>关键命中<span className="th-en">首轮承接</span></th>
          <th>调剂风险<span className="th-en">尾部风险</span></th>
          <th>选择理由</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={`${row.order}-${row.school}`}>
            <td>{row.order}</td>
            <td>{row.school}</td>
            <td>{row.group}</td>
            <td><span className={`strategy strategy--${strategyToneClass(row.strategy)}`}>{formatStrategyLabel(row.strategy)}</span></td>
            <td>{row.probability_range}</td>
            <td>{row.first_hit_prob}</td>
            <td>{row.tail_assignment_risk}</td>
            <td>{row.evidence}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </section>
);

const EvidenceLedger = ({ items }: { items: EvidenceItem[] }) => (
  <section>
    <div className="section-heading">
      <p>03</p>
      <div>
        <h2 className="section-heading__cn">证据账本</h2>
        <span className="section-heading__en">证据来源与使用边界</span>
      </div>
    </div>
    <div className="ledger">
      {items.map((item) => (
        <article key={item.source}>
          <h3>{item.source}</h3>
          <p><b>用途</b> {item.usage}</p>
          <p><b>边界</b> {item.boundary}</p>
        </article>
      ))}
    </div>
  </section>
);

const RiskLedger = ({ items }: { items: RiskItem[] }) => (
  <section>
    <div className="section-heading">
      <p>04</p>
      <div>
        <h2 className="section-heading__cn">风险账本</h2>
        <span className="section-heading__en">风险触发与处理动作</span>
      </div>
    </div>
    <table className="report-table report-table--risk">
      <thead>
        <tr>
          <th>风险项</th>
          <th>等级</th>
          <th>触发信号</th>
          <th>处理动作</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.risk}>
            <td>{item.risk}</td>
            <td><span className={`risk risk--${riskToneClass(item.level)}`}>{formatRiskLabel(item.level)}</span></td>
            <td>{item.signal}</td>
            <td>{item.action}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </section>
);

const DeliveryReviewWorksheet = () => (
  <section className="compact-table-block">
    <h3>人工复核工作表</h3>
    <table className="mini-table">
      <tbody>
        <tr><th>输入锁定</th><td>分数、位次、选科、城市、专业偏好、黑名单</td><td>交付前确认</td></tr>
        <tr><th>概率口径</th><td>历史校准年份、区间解释、非承诺边界</td><td>必须披露</td></tr>
        <tr><th>志愿动作</th><td>关键前缀行、1-6 专业顺序、是否服从调剂</td><td>人工复核</td></tr>
        <tr><th>官方规则</th><td>招生计划、章程、体检、单科、校区备注</td><td>最终复核</td></tr>
      </tbody>
    </table>
  </section>
);

const RiskScenarioTable = () => (
  <section className="compact-table-block">
    <h3>情景压力测试</h3>
    <table className="mini-table">
      <tbody>
        <tr><th>前序冲刺全失效</th><td>观察稳健段能否承接主要落点</td><td>优先检查第 06 行 / 第 12 行</td></tr>
        <tr><th>热门专业抬升</th><td>观察计算机、电子信息组内尾部风险</td><td>必要时调整专业顺序</td></tr>
        <tr><th>招生计划缩量</th><td>重新计算位次缓冲与覆盖缺口</td><td>触发二次排序</td></tr>
        <tr><th>家庭城市约束收紧</th><td>省外或远距离院校降权</td><td>保底池需补充</td></tr>
      </tbody>
    </table>
  </section>
);

const CareerDirectionTable = () => (
  <section className="compact-table-block">
    <h3>专业方向建议</h3>
    <table className="mini-table">
      <tbody>
        <tr><th>优先解释</th><td>计算机类、电子信息类、自动化类</td><td>霍兰德兴趣可支持</td></tr>
        <tr><th>谨慎解释</th><td>宽口径工科试验班、跨校区培养</td><td>需要补充课程结构</td></tr>
        <tr><th>硬性排除</th><td>学生明确黑名单专业</td><td>不可由测评救回</td></tr>
        <tr><th>沟通材料</th><td>MBTI、职业价值观、自我描述</td><td>只用于沟通，不进排序</td></tr>
      </tbody>
    </table>
  </section>
);

const ReportStyles = () => (
  <style>{`
    :root {
      --pf-ink: #172033;
      --pf-muted: #627084;
      --pf-line: #d8dee8;
      --pf-paper: #f5f2ec;
      --pf-surface: #ffffff;
      --pf-navy: #112747;
      --pf-cyan: #167b8a;
      --pf-amber: #b7791f;
      --pf-red: #9f2f2f;
      --pf-green: #2d7a52;
    }

    @page {
      size: A4;
      margin: 0;
    }

    .report-preview-shell {
      min-height: 100vh;
      background: #dfe5ec;
      color: var(--pf-ink);
      padding: 24px;
      font-family: "Noto Sans SC", "Microsoft YaHei", "PingFang SC", sans-serif;
    }

    .report-toolbar {
      align-items: center;
      display: flex;
      justify-content: space-between;
      margin: 0 auto 18px;
      max-width: 210mm;
    }

    .report-toolbar p {
      color: #435066;
      font-size: 13px;
      margin: 0;
    }

    .report-toolbar button {
      background: var(--pf-navy);
      border: 0;
      border-radius: 6px;
      color: white;
      cursor: pointer;
      font-size: 14px;
      font-weight: 700;
      padding: 10px 14px;
    }

    .report-document {
      display: grid;
      gap: 18px;
      justify-content: center;
    }

    .report-page {
      background: var(--pf-surface);
      box-shadow: 0 18px 42px rgba(27, 39, 59, 0.20);
      min-height: 297mm;
      overflow: hidden;
      page-break-after: always;
      position: relative;
      width: 210mm;
    }

    .report-page__inner {
      display: flex;
      flex-direction: column;
      min-height: calc(297mm - 42mm);
      padding: 21mm 18mm;
      position: relative;
      z-index: 1;
    }

    .report-page--dense .report-page__inner {
      min-height: calc(297mm - 30mm);
      padding: 15mm 16mm;
    }

    .report-page--overview .report-page__inner {
      min-height: calc(297mm - 24mm);
      padding: 12mm 16mm;
    }

    .cover {
      background:
        linear-gradient(90deg, #112747 0 28mm, transparent 28mm),
        #f6f0e6;
      color: var(--pf-navy);
    }

    .canva-editorial-cover {
      border: 0;
    }

    .cover::after {
      background:
        linear-gradient(90deg, rgba(183, 121, 31, .92), rgba(183, 121, 31, .18));
      content: "";
      height: 3px;
      position: absolute;
      left: 42mm;
      top: 116mm;
      width: 116mm;
    }

    .cover .report-page__inner {
      justify-content: space-between;
      min-height: calc(297mm - 42mm);
      padding: 20mm 18mm 22mm 42mm;
    }

    .brand-row,
    .cover-meta,
    .page-footer,
    .section-heading,
    .decision-card__header,
    .data-strip {
      display: flex;
      justify-content: space-between;
    }

    .brand-row {
      align-items: center;
      border-bottom: 1px solid rgba(17, 39, 71, .18);
      color: var(--pf-navy);
      padding-bottom: 14px;
    }

    .brand-row strong {
      font-size: 20px;
      letter-spacing: 0.06em;
    }

    .brand-row span,
    .cover-meta span,
    .page-footer,
    .eyebrow {
      font-size: 11px;
      letter-spacing: .12em;
      text-transform: uppercase;
    }

    .report-kicker-en {
      color: rgba(17, 39, 71, .54);
      font-size: 8px;
      font-weight: 700;
      letter-spacing: .12em;
      margin: 0 0 10px;
      text-transform: uppercase;
    }

    .cover-title h1,
    .report-title-cn {
      color: #112747;
      font-size: 70px;
      letter-spacing: 0;
      line-height: 1.05;
      margin: 0 0 20px;
      max-width: 620px;
    }

    .cover-title > p:not(.report-kicker-en) {
      color: #374151;
      font-size: 18px;
      font-weight: 700;
      line-height: 1.85;
      margin: 0;
      max-width: 660px;
    }

    .cover-meta {
      background: rgba(255, 250, 241, .86);
      border-bottom: 1px solid rgba(17, 39, 71, .18);
      border-top: 4px solid var(--pf-amber);
      gap: 20px;
      padding: 18px 0 14px;
    }

    .cover-meta div {
      min-width: 0;
    }

    .cover-meta b {
      display: block;
      font-size: 24px;
      margin-top: 8px;
    }

    .page-footer {
      align-items: center;
      border-top: 1px solid var(--pf-line);
      color: var(--pf-muted);
      margin-top: auto;
      padding-top: 10px;
    }

    .toc-grid,
    .metric-grid,
    .ledger,
    .career-grid,
    .decision-card__grid {
      display: grid;
      gap: 12px;
    }

    .toc-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin-top: 28px;
    }

    .toc-grid article,
    .metric,
    .ledger article,
    .career-grid article,
    .decision-card {
      border: 1px solid var(--pf-line);
      border-radius: 6px;
      background: #fff;
    }

    .toc-grid article {
      padding: 18px;
    }

    .toc-grid span {
      color: var(--pf-cyan);
      font-size: 26px;
      font-weight: 800;
    }

    .toc-grid h3 {
      font-size: 20px;
      margin: 10px 0 8px;
    }

    .toc-grid p,
    .metric p,
    .ledger p,
    .decision-card p,
    .career-grid p,
    .report-callout p {
      color: var(--pf-muted);
      font-size: 12px;
      line-height: 1.65;
      margin: 0;
    }

    .section-heading {
      align-items: flex-end;
      border-bottom: 2px solid var(--pf-ink);
      gap: 20px;
      margin-bottom: 14px;
      padding-bottom: 10px;
    }

    .section-heading p {
      color: var(--pf-cyan);
      font-size: 46px;
      font-weight: 900;
      line-height: .9;
      margin: 0;
    }

    .section-heading h2 {
      font-size: 34px;
      line-height: 1;
      margin: 0 0 6px;
    }

    .section-heading span,
    .section-heading__en {
      color: var(--pf-muted);
      font-size: 10px;
      letter-spacing: .12em;
      text-transform: uppercase;
    }

    .section-heading__cn {
      color: var(--pf-ink);
      font-size: 34px;
      font-weight: 900;
      letter-spacing: 0;
    }

    .metric-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin: 14px 0;
    }

    .metric {
      border-top: 4px solid var(--pf-navy);
      padding: 11px;
    }

    .metric--positive { border-top-color: var(--pf-green); }
    .metric--warning { border-top-color: var(--pf-amber); }

    .metric span {
      color: var(--pf-muted);
      display: block;
      font-size: 11px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }

    .metric strong {
      display: block;
      font-size: 28px;
      margin: 5px 0 2px;
    }

    .data-strip {
      background: #eef3f6;
      border-left: 5px solid var(--pf-cyan);
      color: var(--pf-ink);
      gap: 16px;
      margin: 12px 0 16px;
      padding: 11px 13px;
    }

    .data-strip b {
      display: block;
      font-size: 13px;
      margin-bottom: 4px;
    }

    .data-strip span {
      color: var(--pf-muted);
      font-size: 11px;
    }

    .report-table {
      border-collapse: collapse;
      font-size: 10px;
      line-height: 1.35;
      width: 100%;
    }

    .report-table th {
      background: var(--pf-navy);
      color: white;
      font-weight: 700;
      padding: 7px 6px;
      text-align: left;
    }

    .th-en {
      color: rgba(255,255,255,.58);
      display: block;
      font-size: 8px;
      font-weight: 600;
      letter-spacing: .04em;
      margin-top: 2px;
      text-transform: lowercase;
    }

    .report-table td {
      border-bottom: 1px solid var(--pf-line);
      color: #263247;
      padding: 6px;
      vertical-align: top;
    }

    .compact-table-block {
      border: 1px solid var(--pf-line);
      border-radius: 4px;
      margin-top: 14px;
      overflow: hidden;
    }

    .compact-table-block h3 {
      background: #f0f4f7;
      border-bottom: 1px solid var(--pf-line);
      color: var(--pf-ink);
      font-size: 17px;
      margin: 0;
      padding: 9px 12px;
    }

    .mini-table {
      border-collapse: collapse;
      font-size: 11px;
      line-height: 1.45;
      width: 100%;
    }

    .mini-table th,
    .mini-table td {
      border-bottom: 1px solid var(--pf-line);
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }

    .mini-table tr:last-child th,
    .mini-table tr:last-child td {
      border-bottom: 0;
    }

    .mini-table th {
      color: var(--pf-navy);
      font-weight: 900;
      width: 118px;
    }

    .strategy,
    .risk {
      border-radius: 999px;
      display: inline-block;
      font-size: 10px;
      font-weight: 800;
      padding: 3px 7px;
    }

    .strategy--rush,
    .risk--high {
      background: #f8e7e5;
      color: var(--pf-red);
    }

    .strategy--target,
    .risk--medium {
      background: #f6ecd9;
      color: var(--pf-amber);
    }

    .strategy--safe,
    .risk--low {
      background: #e5f1eb;
      color: var(--pf-green);
    }

    .decision-card {
      margin-top: 18px;
      padding: 18px;
    }

    .decision-card__header {
      align-items: center;
      border-bottom: 1px solid var(--pf-line);
      margin-bottom: 14px;
      padding-bottom: 10px;
    }

    .decision-card__header h3,
    .report-callout h3,
    .ledger h3,
    .career-grid h3 {
      margin: 0;
    }

    .decision-card__header span {
      color: var(--pf-cyan);
      font-size: 28px;
      font-weight: 900;
    }

    .decision-card__grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .decision-card__grid span {
      color: var(--pf-muted);
      display: block;
      font-size: 11px;
      margin-bottom: 6px;
      text-transform: uppercase;
    }

    .decision-card__grid strong {
      display: block;
      font-size: 15px;
      margin-bottom: 6px;
    }

    .ledger {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .ledger article,
    .career-grid article {
      padding: 14px;
    }

    .ledger h3,
    .career-grid h3 {
      font-size: 15px;
      margin-bottom: 8px;
    }

    .report-callout {
      align-items: center;
      background: #f7f4ed;
      border: 1px solid #e1d7c3;
      border-radius: 6px;
      display: grid;
      gap: 16px;
      grid-template-columns: 220px 1fr;
      margin-top: 18px;
      padding: 16px;
    }

    .compact-evidence-panel {
      background: #f8fafb;
      border: 1px solid var(--pf-line);
      border-left: 5px solid var(--pf-cyan);
      border-radius: 4px;
      margin-top: 14px;
      padding: 12px 14px;
    }

    .compact-evidence-panel h3 {
      color: var(--pf-ink);
      font-size: 17px;
      margin: 0 0 8px;
    }

    .compact-evidence-panel div {
      display: grid;
      gap: 7px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .compact-evidence-panel p {
      color: #3e4a5d;
      font-size: 11px;
      line-height: 1.55;
      margin: 0;
    }

    .compact-evidence-panel b {
      color: var(--pf-cyan);
      display: block;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 14px;
      margin-bottom: 2px;
    }

    .report-page--overview .section-heading {
      margin-bottom: 10px;
      padding-bottom: 8px;
    }

    .report-page--overview .section-heading p {
      font-size: 40px;
    }

    .report-page--overview .section-heading h2,
    .report-page--overview .section-heading__cn {
      font-size: 30px;
    }

    .report-page--overview .metric-grid {
      margin: 10px 0;
    }

    .report-page--overview .metric {
      padding: 8px 9px;
    }

    .report-page--overview .metric strong {
      font-size: 24px;
      margin: 3px 0 1px;
    }

    .report-page--overview .metric p {
      font-size: 10px;
      line-height: 1.45;
    }

    .report-page--overview .data-strip {
      gap: 12px;
      margin: 8px 0 10px;
      padding: 8px 10px;
    }

    .report-page--overview .data-strip b {
      font-size: 12px;
      margin-bottom: 2px;
    }

    .report-page--overview .data-strip span {
      font-size: 10px;
      line-height: 1.45;
    }

    .report-page--overview .report-table {
      font-size: 9px;
      line-height: 1.22;
    }

    .report-page--overview .report-table th,
    .report-page--overview .report-table td {
      padding: 4px 5px;
    }

    .report-page--overview .compact-evidence-panel {
      margin-top: 10px;
      padding: 8px 10px;
    }

    .report-page--overview .compact-evidence-panel h3 {
      font-size: 14px;
      margin-bottom: 5px;
    }

    .report-page--overview .compact-evidence-panel div {
      gap: 5px;
    }

    .report-page--overview .compact-evidence-panel p {
      font-size: 10px;
      line-height: 1.35;
    }

    .report-page--overview .compact-evidence-panel b {
      font-size: 12px;
      margin-bottom: 1px;
    }

    .report-readiness {
      margin-top: 18px;
    }

    .readiness-summary {
      align-items: center;
      background: #eef3f6;
      border-left: 5px solid var(--pf-navy);
      display: grid;
      gap: 18px;
      grid-template-columns: 150px 1fr;
      margin-bottom: 14px;
      padding: 14px 16px;
    }

    .readiness-summary span {
      color: var(--pf-muted);
      display: block;
      font-size: 11px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }

    .readiness-summary strong {
      display: block;
      font-size: 42px;
      line-height: 1;
      margin-top: 5px;
    }

    .readiness-summary p,
    .readiness-next {
      color: var(--pf-muted);
      font-size: 12px;
      line-height: 1.65;
      margin: 0;
    }

    .readiness-grid {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(5, minmax(0, 1fr));
    }

    .readiness-gate {
      border: 1px solid var(--pf-line);
      border-radius: 6px;
      padding: 11px;
    }

    .readiness-gate--ready { border-top: 4px solid var(--pf-green); }
    .readiness-gate--needs_review { border-top: 4px solid var(--pf-amber); }
    .readiness-gate--blocked { border-top: 4px solid var(--pf-red); }

    .readiness-gate span {
      color: var(--pf-muted);
      font-size: 9px;
      font-weight: 900;
      text-transform: uppercase;
    }

    .readiness-gate h3 {
      font-size: 13px;
      margin: 6px 0;
    }

    .readiness-gate p,
    .readiness-gate b {
      display: block;
      font-size: 10px;
      line-height: 1.45;
    }

    .readiness-gate p {
      color: var(--pf-muted);
      margin: 0 0 6px;
    }

    .readiness-next {
      margin-top: 12px;
    }

    .career-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-top: 18px;
    }

    .career-score {
      background: var(--pf-navy);
      border-radius: 4px;
      color: white;
      display: inline-block;
      font-size: 20px;
      font-weight: 900;
      margin-bottom: 10px;
      padding: 6px 9px;
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
    <span>升学规划定制报告 · 决策版</span>
    <span>{page}</span>
  </footer>
);

export function PathFinderReportTemplate({ payload }: { payload?: PathFinderReportPayload | null }) {
  const reportData = buildReportPayload(payload);
  return (
    <div className="report-document ChineseFirstReport sample-student-29 subject-combo-wuhuasheng mbti-intj" aria-label="PathFinder Chinese-first investment research style report">
      <section className="report-page cover canva-editorial-cover">
        <div className="report-page__inner">
          <div className="brand-row">
            <strong>升学规划</strong>
            <span>定制报告样本 · 仅供内部评审</span>
          </div>
          <div className="cover-title">
            <p className="report-kicker-en">示例29 · 选科物化生 · 2026参考样本</p>
            <h1 className="report-title-cn">升学规划定制报告</h1>
            <p>
              示例29同学，672分，3184位，选科物化生。报告以院校层次、专业实力、城市平台、
              就业方向和风险复核为主线，形成可直接交付给学生家庭的升学规划样本。
            </p>
          </div>
          <div className="cover-meta">
            <div><span>学生</span><b>{reportData.studentLabel}</b></div>
            <div><span>选科</span><b>物化生</b></div>
            <div><span>分数 / 位次</span><b>{reportData.scoreRankLabel}</b></div>
            <div><span>MBTI</span><b>INTJ</b></div>
          </div>
        </div>
      </section>

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <div className="section-heading">
            <p>01</p>
            <div>
              <h2 className="section-heading__cn">报告目录</h2>
              <span className="section-heading__en">阅读顺序与交付结构</span>
            </div>
          </div>
          <div className="toc-grid">
            <article><span>01</span><h3>选择总览</h3><p>先给出整张志愿表的决策摘要、覆盖情况和不可忽略的风险。</p></article>
            <article><span>02</span><h3>院校专业组矩阵</h3><p>用投研式表格展示概率区间、首命中概率、尾部调剂风险和证据说明。</p></article>
            <article><span>03</span><h3>证据账本</h3><p>把官方数据、历史校准、结构化画像和测评信号分层披露。</p></article>
            <article><span>04</span><h3>风险账本</h3><p>明确每个风险的触发信号、严重程度和下一步复核动作。</p></article>
            <article><span>05</span><h3>职业适配</h3><p>霍兰德兴趣只影响专业解释和软排序；MBTI 不进入推荐算法。</p></article>
            <article><span>06</span><h3>最终复核</h3><p>正式填报前按招生计划、章程、体检和单科要求完成人工复核。</p></article>
          </div>
          <DataBoundary text={reportData.dataBoundaryText} />
          <CompactEvidencePanel
            title="读者先看这三处"
            items={[
              "先确认学生输入约束是否被正确锁定，再看推荐表。",
              "先看关键前缀志愿，不要把尾部填充行当作同等重要推荐。",
              "所有概率均为决策信号，正式填报前仍需官方章程复核。",
            ]}
          />
          <PageFooter page="02" />
        </div>
      </section>

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <DeliveryReadiness summary={reportData.deliveryReadiness} />
          <CompactEvidencePanel
            title="交付前复核口径"
            items={[
              "数据年份、招生计划、位次口径必须在同一页披露。",
              "黑名单专业不得出现在建议填报的 1-6 专业顺序中。",
              "霍兰德兴趣只解释专业偏好，MBTI 不参与概率和排序。",
            ]}
          />
          <DeliveryReviewWorksheet />
          <PageFooter page="03" />
        </div>
      </section>

      <section className="report-page report-page--dense report-page--overview">
        <div className="report-page__inner">
          <div className="section-heading">
            <p>02</p>
            <div>
              <h2 className="section-heading__cn">选择总览</h2>
              <span className="section-heading__en">院校层次、专业实力与风险总览</span>
            </div>
          </div>
          <div className="metric-grid reference-summary-strip">
            {reportData.metrics.map((metric) => (
              <article className={`metric metric--${metric.tone ?? "neutral"}`} key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
                <p>{metric.note}</p>
              </article>
            ))}
          </div>
          <div className="data-strip">
            <div><b>学生画像</b><span>{reportData.profileLine}</span></div>
            <div><b>样例摘要</b><span>{reportData.strategyLine}</span></div>
            <div><b>决策重点</b><span>{reportData.focusLine}</span></div>
          </div>
          <VolunteerMatrix rows={reportData.rows} />
          <CompactEvidencePanel
            title="矩阵阅读方法"
            items={[
              "分数差距看区间，不看单点承诺。",
              "关键命中用于识别真正会改变录取结果的行。",
              "调剂风险决定是否需要人工调整专业顺序。",
            ]}
          />
          <PageFooter page="04" />
        </div>
      </section>

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <div className="section-heading">
            <p>03</p>
            <div>
              <h2 className="section-heading__cn">关键志愿解释</h2>
              <span className="section-heading__en">为什么这样排序</span>
            </div>
          </div>
          <DecisionEvidenceCard />
          <EvidenceLedger items={reportData.evidence} />
          <PageFooter page="05" />
        </div>
      </section>

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <div className="section-heading">
            <p>04</p>
            <div>
              <h2 className="section-heading__cn">风险控制附录</h2>
              <span className="section-heading__en">正式填报前必须复核</span>
            </div>
          </div>
          <RiskLedger items={reportData.risks} />
          <RiskScenarioTable />
          <CompactEvidencePanel
            title="风险处理原则"
            items={[
              "高风险不等于删除，必须说明保留条件和失败后果。",
              "保底志愿也要检查调剂尾部风险，不能只看学校层次。",
              "任何官方规则不完整时，报告只能给复核清单，不能给承诺。",
            ]}
          />
          <PageFooter page="06" />
        </div>
      </section>

      <section className="report-page report-page--dense">
        <div className="report-page__inner">
          <div className="section-heading">
            <p>05</p>
            <div>
              <h2 className="section-heading__cn">专业适配附录</h2>
              <span className="section-heading__en">兴趣画像与专业解释边界</span>
            </div>
          </div>
          <div className="career-grid">
            {reportData.careerCards.map((card) => (
              <article key={`${card.title}-${card.score}`}>
                <span className="career-score">{card.score}</span>
                <h3>{card.title}</h3>
                <p>{card.body}</p>
              </article>
            ))}
          </div>
          <DataBoundary text={reportData.dataBoundaryText} />
          <CareerDirectionTable />
          <CompactEvidencePanel
            title="专业解释边界"
            items={[
              "兴趣测评用于解释专业方向，不用于替代录取数据。",
              "显式偏好权重大于测评软信号，黑名单仍是硬边界。",
              "职业价值观用于沟通取舍，不应伪装成算法结论。",
            ]}
          />
          <PageFooter page="07" />
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
        <p>升学规划网页报告模板 · A4 可打印 · 投研报告风格</p>
        <button type="button" onClick={() => window.print()}>打印 / 导出 PDF</button>
      </div>
      <PathFinderReportTemplate payload={payload} />
    </main>
  );
}

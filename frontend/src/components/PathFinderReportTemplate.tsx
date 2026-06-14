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
  generatedAt?: string;
};

type ReportRenderData = {
  metrics: Metric[];
  rows: MatrixRow[];
  evidence: EvidenceItem[];
  risks: RiskItem[];
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

const defaultSummaryMetrics: Metric[] = [
  { label: "Formal rows", value: "45", note: "Guangdong major-group draft", tone: "neutral" },
  { label: "Expected range", value: "62-74%", note: "Heuristic calibrated band", tone: "positive" },
  { label: "Key prefix rows", value: "7", note: "Rows that materially decide outcome", tone: "warning" },
  { label: "Hard exclusions", value: "0", note: "Blacklist exposure after audit", tone: "positive" },
  { label: "Coverage deficit", value: "2", note: "Target bucket supply gap", tone: "warning" },
  { label: "Data vintage", value: "2025", note: "Retrospective Guangdong evidence", tone: "neutral" },
];

const defaultMatrixRows: MatrixRow[] = [
  {
    order: "01",
    school: "华南理工大学",
    group: "206 物理+化学",
    strategy: "Rush",
    probability_range: "18-24%",
    first_hit_prob: "19%",
    tail_assignment_risk: "Medium",
    evidence: "Rank buffer -410; official plan pending",
  },
  {
    order: "06",
    school: "深圳大学",
    group: "214 计算机类",
    strategy: "Target",
    probability_range: "41-49%",
    first_hit_prob: "28%",
    tail_assignment_risk: "Low",
    evidence: "2025 subject beta calibration; city preference explicit",
  },
  {
    order: "12",
    school: "广东工业大学",
    group: "208 自动化类",
    strategy: "Target",
    probability_range: "56-64%",
    first_hit_prob: "17%",
    tail_assignment_risk: "Medium",
    evidence: "Major fit +0.07; no blacklist collision",
  },
  {
    order: "22",
    school: "广州大学",
    group: "203 电子信息",
    strategy: "Safe",
    probability_range: "73-81%",
    first_hit_prob: "9%",
    tail_assignment_risk: "Low",
    evidence: "Historical floor stable; family city constraint satisfied",
  },
  {
    order: "36",
    school: "佛山科学技术学院",
    group: "205 工科试验",
    strategy: "Safe",
    probability_range: "84-90%",
    first_hit_prob: "4%",
    tail_assignment_risk: "Low",
    evidence: "Capacity recovery row; protects downside",
  },
];

const defaultEvidenceLedger: EvidenceItem[] = [
  {
    source: "2025 Guangdong admissions replay",
    usage: "probability_range and first_hit_prob calibration",
    boundary: "Retrospective validation only; not a 2026 guarantee",
  },
  {
    source: "Structured delivery_profile",
    usage: "city, major, blacklist, and risk preference constraints",
    boundary: "Explicit user fields override inferred conversation text",
  },
  {
    source: "RIASEC quick assessment",
    usage: "soft major utility adjustment and explanation wording",
    boundary: "Does not change admission probability or hard filters",
  },
  {
    source: "Official enrollment rules",
    usage: "manual review checkpoint for health, single-subject, and adjustment rules",
    boundary: "Final decision must follow current-year official documents",
  },
];

const defaultRiskLedger: RiskItem[] = [
  {
    risk: "Target bucket supply gap",
    level: "Medium",
    signal: "Two target rows filled through capacity recovery",
    action: "Keep the rows, but disclose that original rush/target/safe labels were not relabeled.",
  },
  {
    risk: "Tail assignment exposure",
    level: "Medium",
    signal: "Two early rows carry medium tail risk under adjustment",
    action: "Require 1-6 major ordering and adjustment decision review before submission.",
  },
  {
    risk: "Current-year data incompleteness",
    level: "High",
    signal: "2026 official plan and rule changes are not fully loaded",
    action: "Add a final official-data verification gate after招生计划 release.",
  },
  {
    risk: "MBTI over-interpretation",
    level: "Low",
    signal: "Self-reported MBTI exists but is not measured evidence",
    action: "Use MBTI for communication tone only; keep scoring untouched.",
  },
];

function buildReportPayload(payload?: PathFinderReportPayload | null): ReportRenderData {
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
          strategy: String(choice.strategy_tag ?? "unclassified"),
          probability_range:
            choice.admission_probability_lower_bound !== undefined || choice.admission_probability_upper_bound !== undefined
              ? `${formatPercent(choice.admission_probability_lower_bound)}-${formatPercent(choice.admission_probability_upper_bound)}`
              : formatPercent(choice.group_admission_prob),
          first_hit_prob: formatPercent(choice.first_hit_prob),
          tail_assignment_risk: formatPercent(choice.tail_assignment_risk),
          evidence: choice.quant_evidence?.[0] ?? "Awaiting detailed evidence note",
        }))
      : majorRows.slice(0, 10).map((row, index) => ({
          order: String(index + 1).padStart(2, "0"),
          school: row.school_name ?? "待定院校",
          group: row.major_group_code ?? "待定专业组",
          strategy: String(row.strategy_tag ?? "unclassified"),
          probability_range: formatPercent(row.admission_prob),
          first_hit_prob: formatPercent(row.first_hit_prob),
          tail_assignment_risk: formatPercent(row.tail_assignment_risk),
          evidence: row.quant_evidence?.[0] ?? "Awaiting detailed evidence note",
        }));
  const deficits = audit?.coverage?.deficits ?? {};
  const deficitCount = Object.values(deficits).reduce((total, value) => total + Number(value || 0), 0);
  const formalReady = dataBoundary?.formal_recommendation_ready ?? false;
  const metrics: Metric[] = gameMatrix
    ? [
        {
          label: "Formal rows",
          value: String(choices.length || majorRows.length || 0),
          note: "Current analyzed volunteer slate",
          tone: "neutral",
        },
        {
          label: "Expected range",
          value:
            plan?.admission_probability_lower_bound !== undefined || plan?.admission_probability_upper_bound !== undefined
              ? `${formatPercent(plan?.admission_probability_lower_bound)}-${formatPercent(plan?.admission_probability_upper_bound)}`
              : formatPercent(plan?.expected_admission_prob),
          note: "Plan-level calibrated or heuristic band",
          tone: "positive",
        },
        {
          label: "Key prefix rows",
          value: String(plan?.key_prefix_count ?? 0),
          note: "Rows that materially decide outcome",
          tone: "warning",
        },
        {
          label: "Hard exclusions",
          value: String(plan?.blacklist_violation_count ?? 0),
          note: "Blacklist exposure after audit",
          tone: (plan?.blacklist_violation_count ?? 0) > 0 ? "warning" : "positive",
        },
        {
          label: "Coverage deficit",
          value: String(deficitCount),
          note: audit?.coverage?.coverage_sufficient ? "No obvious rush/target/safe gap" : "Needs manual mix review",
          tone: deficitCount > 0 ? "warning" : "positive",
        },
        {
          label: "Data vintage",
          value: String(dataBoundary?.target_year ?? gameMatrix.data_vintage?.latest_historical_admission_year ?? "N/A"),
          note: formalReady ? "Current-year formal data ready" : "Current-year data boundary applies",
          tone: formalReady ? "positive" : "warning",
        },
      ]
    : defaultSummaryMetrics;
  const evidence: EvidenceItem[] = gameMatrix
    ? [
        {
          source: "Current GameMatrix response",
          usage: "VolunteerMatrix, probability_range, first_hit_prob, and plan audit metrics",
          boundary: "Rendered from the latest analyzed response stored in sessionStorage.",
        },
        {
          source: "Structured deliveryProfile",
          usage: "Profile lock, city preference, major preference, blacklist, and career appendix",
          boundary: "Explicit user fields override inferred conversation text.",
        },
        {
          source: "Plan audit summary",
          usage: "RiskLedger, DataBoundary, coverage deficit, and key-prefix disclosure",
          boundary: "Audit diagnoses structure and evidence boundaries; it does not guarantee outcomes.",
        },
      ]
    : defaultEvidenceLedger;
  const risks: RiskItem[] = audit?.student_facing_items?.length
    ? audit.student_facing_items.slice(0, 6).map((item) => ({
        risk: item.title ?? item.type ?? "Plan audit item",
        level: item.severity === "P1" ? "High" : item.severity === "P2" ? "Medium" : "Low",
        signal: item.type ?? audit.status ?? "audit",
        action: item.detail ?? "Review before final submission.",
      }))
    : defaultRiskLedger;
  const preferredCities = deliveryProfile?.preferred_cities?.join("/") || "未锁定城市";
  const preferredMajors = deliveryProfile?.preferred_majors?.join("、") || "未锁定专业";
  const blacklist = deliveryProfile?.blacklist_majors?.join("、") || "无明确黑名单";
  const subjectGroup = deliveryProfile?.subject_group === "history" ? "历史类" : "物理类";
  const riasec = deliveryProfile?.riasec_top_codes?.join("/") || "I/R";
  const mbti = deliveryProfile?.mbti_type || "未填写";
  return {
    metrics,
    rows: sourceRows.length ? sourceRows : defaultMatrixRows,
    evidence,
    risks,
    profileLine: `城市：${preferredCities}；专业：${preferredMajors}；黑名单：${blacklist}。`,
    strategyLine: `Rush ${gameMatrix?.total_rush ?? 8} / Target ${gameMatrix?.total_target ?? 20} / Safe ${gameMatrix?.total_safe ?? 17}；容量恢复不改变原始策略标签。`,
    focusLine: `解释关键前缀志愿，不把被前序遮蔽的 ${plan?.shadowed_choice_count ?? 0} 行尾部志愿当作同等重要推荐。`,
    studentLabel: deliveryProfile?.score ? "当前分析学生" : "示例学生 A",
    scoreRankLabel: deliveryProfile?.score
      ? `${deliveryProfile.score} / ${deliveryProfile.rank ?? "位次待补"}`
      : "672 / 3184",
    dataBoundaryText:
      dataBoundary?.limitations?.join("；") ||
      "probability_range、first_hit_prob 与 tail_assignment_risk 均为基于历史数据、学生约束和当前候选池的启发式决策信号。正式填报前必须复核当年招生计划、招生章程和考试院公告。",
    careerCards: [
      {
        score: riasec,
        title: "RIASEC",
        body: "用于解释专业兴趣与志愿选择之间的软匹配，不覆盖录取概率和硬过滤条件。",
      },
      {
        score: subjectGroup,
        title: "Subject track",
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

const DataBoundary = ({ text }: { text: string }) => (
  <section className="report-callout">
    <div>
      <p className="eyebrow">DataBoundary</p>
      <h3>本报告给出的是可审计决策建议，不是录取承诺</h3>
    </div>
    <p>{text}</p>
  </section>
);

const DecisionEvidenceCard = () => (
  <section className="decision-card">
    <div className="decision-card__header">
      <div>
        <p className="eyebrow">DecisionEvidenceCard</p>
        <h3>关键前缀志愿解释</h3>
      </div>
      <span>Row 06</span>
    </div>
    <div className="decision-card__grid">
      <div>
        <span>机会 thesis</span>
        <strong>深圳大学 214 计算机类</strong>
        <p>命中概率与城市偏好同时满足，且专业方向与 RIASEC 工程/研究倾向一致。</p>
      </div>
      <div>
        <span>风险 guard</span>
        <strong>尾部风险低</strong>
        <p>组内专业没有黑名单碰撞，建议服从调剂，但需复核当年单科和体检规则。</p>
      </div>
      <div>
        <span>排序 reason</span>
        <strong>前序失败后的主要承接</strong>
        <p>该行不是装饰性推荐，first_hit_prob 达 28%，会真实影响整张表的落点。</p>
      </div>
    </div>
  </section>
);

const VolunteerMatrix = ({ rows }: { rows: MatrixRow[] }) => (
  <section>
    <div className="section-heading">
      <p>02</p>
      <div>
        <h2>VolunteerMatrix</h2>
        <span>院校专业组志愿矩阵</span>
      </div>
    </div>
    <table className="report-table">
      <thead>
        <tr>
          <th>Order</th>
          <th>School</th>
          <th>Major group</th>
          <th>Strategy</th>
          <th>probability_range</th>
          <th>first_hit_prob</th>
          <th>tail_assignment_risk</th>
          <th>Evidence note</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={`${row.order}-${row.school}`}>
            <td>{row.order}</td>
            <td>{row.school}</td>
            <td>{row.group}</td>
            <td><span className={`strategy strategy--${row.strategy.toLowerCase()}`}>{row.strategy}</span></td>
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
        <h2>EvidenceLedger</h2>
        <span>证据账本与使用边界</span>
      </div>
    </div>
    <div className="ledger">
      {items.map((item) => (
        <article key={item.source}>
          <h3>{item.source}</h3>
          <p><b>Used for</b> {item.usage}</p>
          <p><b>Boundary</b> {item.boundary}</p>
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
        <h2>RiskLedger</h2>
        <span>风险账本与复核动作</span>
      </div>
    </div>
    <table className="report-table report-table--risk">
      <thead>
        <tr>
          <th>Risk</th>
          <th>Level</th>
          <th>Signal</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.risk}>
            <td>{item.risk}</td>
            <td><span className={`risk risk--${item.level.toLowerCase()}`}>{item.level}</span></td>
            <td>{item.signal}</td>
            <td>{item.action}</td>
          </tr>
        ))}
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

    .cover {
      background:
        linear-gradient(90deg, rgba(17, 39, 71, 0.96), rgba(17, 39, 71, 0.78)),
        repeating-linear-gradient(0deg, transparent 0, transparent 23px, rgba(255,255,255,.05) 24px);
      color: white;
    }

    .cover::after {
      background: linear-gradient(180deg, rgba(255,255,255,.18), rgba(255,255,255,0));
      content: "";
      height: 46%;
      position: absolute;
      right: -12%;
      top: -8%;
      transform: rotate(-18deg);
      width: 42%;
    }

    .cover .report-page__inner {
      justify-content: space-between;
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
      border-bottom: 1px solid rgba(255,255,255,.18);
      padding-bottom: 16px;
    }

    .brand-row strong {
      font-size: 19px;
      letter-spacing: 0.08em;
    }

    .brand-row span,
    .cover-meta span,
    .page-footer,
    .eyebrow {
      font-size: 11px;
      letter-spacing: .12em;
      text-transform: uppercase;
    }

    .cover-title h1 {
      font-size: 58px;
      letter-spacing: 0;
      line-height: 1.05;
      margin: 0 0 18px;
      max-width: 620px;
    }

    .cover-title p {
      color: rgba(255,255,255,.76);
      font-size: 17px;
      line-height: 1.75;
      margin: 0;
      max-width: 560px;
    }

    .cover-meta {
      border-top: 1px solid rgba(255,255,255,.18);
      gap: 20px;
      padding-top: 20px;
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
      margin-bottom: 18px;
      padding-bottom: 12px;
    }

    .section-heading p {
      color: var(--pf-cyan);
      font-size: 46px;
      font-weight: 900;
      line-height: .9;
      margin: 0;
    }

    .section-heading h2 {
      font-size: 28px;
      line-height: 1;
      margin: 0 0 6px;
    }

    .section-heading span {
      color: var(--pf-muted);
      font-size: 12px;
      letter-spacing: .08em;
      text-transform: uppercase;
    }

    .metric-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin: 18px 0;
    }

    .metric {
      border-top: 4px solid var(--pf-navy);
      padding: 14px;
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
      font-size: 32px;
      margin: 8px 0 2px;
    }

    .data-strip {
      background: #eef3f6;
      border-left: 5px solid var(--pf-cyan);
      color: var(--pf-ink);
      gap: 16px;
      margin: 16px 0 22px;
      padding: 14px 16px;
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
      font-size: 10.5px;
      line-height: 1.45;
      width: 100%;
    }

    .report-table th {
      background: var(--pf-navy);
      color: white;
      font-weight: 700;
      padding: 9px 7px;
      text-align: left;
    }

    .report-table td {
      border-bottom: 1px solid var(--pf-line);
      color: #263247;
      padding: 8px 7px;
      vertical-align: top;
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
    <span>PathFinder decision-grade report template</span>
    <span>{page}</span>
  </footer>
);

export function PathFinderReportTemplate({ payload }: { payload?: PathFinderReportPayload | null }) {
  const reportData = buildReportPayload(payload);
  return (
    <div className="report-document" aria-label="PathFinder investment research style report">
      <section className="report-page cover">
        <div className="report-page__inner">
          <div className="brand-row">
            <strong>PATHFINDER</strong>
            <span>Guangdong New Gaokao Decision Research</span>
          </div>
          <div className="cover-title">
            <h1>升学规划定制报告</h1>
            <p>
              对标顶级投研报告的志愿决策模板：以学生约束、概率区间、证据账本和风险边界组织交付，
              复现样例报告的完整度，但用更克制、更可信的研究报告风格表达。
            </p>
          </div>
          <div className="cover-meta">
            <div><span>Student</span><b>{reportData.studentLabel}</b></div>
            <div><span>Province</span><b>广东 / 物理类</b></div>
            <div><span>Score / Rank</span><b>{reportData.scoreRankLabel}</b></div>
            <div><span>Version</span><b>2026.06</b></div>
          </div>
        </div>
      </section>

      <section className="report-page">
        <div className="report-page__inner">
          <div className="section-heading">
            <p>01</p>
            <div>
              <h2>Decision Overview</h2>
              <span>目录与交付口径</span>
            </div>
          </div>
          <div className="toc-grid">
            <article><span>01</span><h3>选择总览</h3><p>先给出整张志愿表的决策摘要、覆盖情况和不可忽略的风险。</p></article>
            <article><span>02</span><h3>院校专业组矩阵</h3><p>用投研式表格展示概率区间、首命中概率、尾部调剂风险和证据说明。</p></article>
            <article><span>03</span><h3>证据账本</h3><p>把官方数据、历史校准、结构化画像和测评信号分层披露。</p></article>
            <article><span>04</span><h3>风险账本</h3><p>明确每个风险的触发信号、严重程度和下一步复核动作。</p></article>
            <article><span>05</span><h3>职业适配</h3><p>RIASEC 只影响专业解释和软排序；MBTI 不进入推荐算法。</p></article>
            <article><span>06</span><h3>最终复核</h3><p>正式填报前按招生计划、章程、体检和单科要求完成人工复核。</p></article>
          </div>
          <DataBoundary text={reportData.dataBoundaryText} />
          <PageFooter page="02" />
        </div>
      </section>

      <section className="report-page">
        <div className="report-page__inner">
          <div className="section-heading">
            <p>02</p>
            <div>
              <h2>Admission Plan Overview</h2>
              <span>选择总览与关键指标</span>
            </div>
          </div>
          <div className="metric-grid">
            {reportData.metrics.map((metric) => (
              <article className={`metric metric--${metric.tone ?? "neutral"}`} key={metric.label}>
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
                <p>{metric.note}</p>
              </article>
            ))}
          </div>
          <div className="data-strip">
            <div><b>Profile lock</b><span>{reportData.profileLine}</span></div>
            <div><b>Strategy mix</b><span>{reportData.strategyLine}</span></div>
            <div><b>Decision focus</b><span>{reportData.focusLine}</span></div>
          </div>
          <VolunteerMatrix rows={reportData.rows} />
          <DecisionEvidenceCard />
          <PageFooter page="03" />
        </div>
      </section>

      <section className="report-page">
        <div className="report-page__inner">
          <EvidenceLedger items={reportData.evidence} />
          <RiskLedger items={reportData.risks} />
          <PageFooter page="04" />
        </div>
      </section>

      <section className="report-page">
        <div className="report-page__inner">
          <div className="section-heading">
            <p>05</p>
            <div>
              <h2>Career Fit Appendix</h2>
              <span>专业兴趣与解释边界</span>
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
          <PageFooter page="05" />
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
        <p>PathFinder HTML report template · A4 print-ready · investment research style</p>
        <button type="button" onClick={() => window.print()}>Print / Export PDF</button>
      </div>
      <PathFinderReportTemplate payload={payload} />
    </main>
  );
}

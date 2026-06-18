export type CareerRouteType = "employment" | "graduate" | "civil_service" | "research";

export interface CareerSimulationProfile {
  preferred_majors?: string[];
  blacklist_majors?: string[];
  riasec_top_codes?: string[];
  career_values?: string[];
  risk_tolerance?: string;
}

export interface CareerSimulationMajorRow {
  school_name?: string;
  major_group_code?: string;
  major_list?: string[];
  suggested_major_choices?: Array<{ major_name?: string; career_fit_score?: number | null }>;
}

interface CareerSeed {
  id: string;
  title: string;
  workScene: string;
  majorKeywords: string[];
  riasec: string[];
  values: string[];
  routes: CareerRouteType[];
  dayParts: Array<{ time: string; task: string; output: string }>;
  coreSkills: string[];
  skillSignals: string[];
  mismatchSignals: string[];
  routesDetail: Array<{ route: CareerRouteType; label: string; reality: string; evidenceToCollect: string }>;
  sourceRefs: string[];
}

export interface CareerSimulation {
  id: string;
  title: string;
  workScene: string;
  fitScore: number;
  fitLevel: "high" | "medium" | "low";
  matchReasons: string[];
  dayParts: CareerSeed["dayParts"];
  coreSkills: string[];
  skillSignals: string[];
  mismatchSignals: string[];
  routesDetail: CareerSeed["routesDetail"];
  sourceRefs: string[];
}

const careerSeeds: CareerSeed[] = [
  {
    id: "ai_product_engineer",
    title: "AI 产品 / 算法工程师",
    workScene: "把业务问题拆成数据、模型、评估和上线闭环，日常既写方案也看指标。",
    majorKeywords: ["计算机", "软件", "人工智能", "数据科学", "电子信息", "自动化", "信息安全"],
    riasec: ["I", "R", "C"],
    values: ["growth", "income", "autonomy"],
    routes: ["employment", "graduate", "research"],
    dayParts: [
      { time: "上午", task: "复盘模型效果、错误样例和用户反馈", output: "问题清单与下一轮实验假设" },
      { time: "中午", task: "和产品、数据、后端确认口径", output: "指标定义、灰度策略和边界说明" },
      { time: "下午", task: "写实验脚本、调参或设计提示词评测集", output: "可复现实验记录与评估表" },
      { time: "晚上", task: "整理上线风险、成本和替代方案", output: "发布说明或回滚预案" },
    ],
    coreSkills: ["编程与数据结构", "概率统计", "机器学习评估", "工程协作", "指标拆解"],
    skillSignals: ["愿意长期处理抽象问题", "能接受结果不确定和反复实验", "数学与英语阅读不能太弱"],
    mismatchSignals: ["只喜欢使用软件、不喜欢排查问题", "极度抗拒代码细节", "不能接受快速变化"],
    routesDetail: [
      { route: "employment", label: "就业", reality: "本科可入门开发/测试/数据岗位，但高质量算法岗通常要求项目和实习强证据。", evidenceToCollect: "课程项目、GitHub/竞赛、实习 JD 与校招去向" },
      { route: "graduate", label: "考研/保研", reality: "读研能显著提高算法和研究岗上限，但要提前看学院保研率、导师方向和近年去向。", evidenceToCollect: "学院保研率、导师论文方向、实验室毕业去向" },
      { route: "research", label: "科研", reality: "真正做科研不是泛泛学 AI，而是围绕一个问题持续复现、消融和写作。", evidenceToCollect: "本科科研入口、实验室开放情况、论文/开源要求" },
    ],
    sourceRefs: ["O*NET: Software Developers / Data Scientists task-skill schema", "Lightcast Open Skills: software, data, machine learning skills taxonomy"],
  },
  {
    id: "clinical_medicine",
    title: "临床医学 / 医学科研",
    workScene: "在高责任、强规范和长培养周期里做诊疗、病历、值班和临床学习。",
    majorKeywords: ["临床医学", "口腔医学", "医学影像", "麻醉学", "基础医学", "生物医学"],
    riasec: ["I", "S", "R"],
    values: ["stability", "social_impact", "growth"],
    routes: ["graduate", "research", "employment"],
    dayParts: [
      { time: "上午", task: "查房、问诊、记录病程变化", output: "病历记录和诊疗计划" },
      { time: "中午", task: "学习指南、讨论疑难病例", output: "诊疗依据和风险提醒" },
      { time: "下午", task: "门诊、操作、影像/检验沟通", output: "医嘱、检查解释和随访安排" },
      { time: "夜间", task: "值班处理突发情况", output: "应急判断与上级汇报" },
    ],
    coreSkills: ["生物与化学基础", "记忆与规范执行", "沟通同理心", "抗压值班", "长期学习"],
    skillSignals: ["能接受长周期培养", "对生命健康责任有敬畏", "愿意在规范中做判断"],
    mismatchSignals: ["只看职业稳定但抗压弱", "无法接受夜班和高强度学习", "不愿与患者家属沟通"],
    routesDetail: [
      { route: "graduate", label: "考研/规培", reality: "医学路径高度依赖升学、规培和医院层级，本科院校平台差异会持续影响上限。", evidenceToCollect: "执业路径、规培基地、附属医院、升学率" },
      { route: "research", label: "保研/科研", reality: "保研和科研对英语、实验室资源和导师网络要求高，不是只靠高考分数。", evidenceToCollect: "学院推免名额、导师组、科研训练计划" },
      { route: "employment", label: "就业", reality: "本科直接就业空间有限，更多要看城市、医院层级和规培衔接。", evidenceToCollect: "近三年就业质量报告、医院招聘学历要求" },
    ],
    sourceRefs: ["O*NET: Physicians and Healthcare Practitioners task-skill schema"],
  },
  {
    id: "civil_service_policy",
    title: "公务员 / 选调 / 公共政策",
    workScene: "围绕政策执行、材料写作、协调沟通和群众事务做稳定但高约束的工作。",
    majorKeywords: ["法学", "公共管理", "汉语言", "马克思主义", "经济学", "财政", "审计", "统计", "计算机"],
    riasec: ["S", "E", "C"],
    values: ["stability", "social_impact", "leadership"],
    routes: ["civil_service", "graduate", "employment"],
    dayParts: [
      { time: "上午", task: "处理通知、会议纪要、政策材料", output: "材料初稿和任务清单" },
      { time: "中午", task: "跨部门沟通数据口径和责任边界", output: "协同记录" },
      { time: "下午", task: "基层调研、窗口答复或项目推进", output: "问题台账和反馈意见" },
      { time: "晚上", task: "修改材料、准备汇报", output: "汇报稿和风险提示" },
    ],
    coreSkills: ["公文写作", "政策理解", "沟通协调", "结构化表达", "规则意识"],
    skillSignals: ["能接受流程和层级", "愿意长期写材料", "对公共事务有耐心"],
    mismatchSignals: ["追求高度自由", "厌恶重复协调", "只把考公当作逃避就业"],
    routesDetail: [
      { route: "civil_service", label: "考公/选调", reality: "岗位限制常由专业、党员、应届、基层经历决定，不能只看专业名称热门。", evidenceToCollect: "近三年国考省考职位表、选调公告、专业限制" },
      { route: "graduate", label: "考研/保研", reality: "读研对选调和政策研究有帮助，但要看学校层级、城市和岗位门槛。", evidenceToCollect: "定向选调高校名单、学院升学去向" },
      { route: "employment", label: "就业", reality: "公共管理/法学等专业也要准备企业法务、咨询、运营等备选路径。", evidenceToCollect: "就业质量报告、实习岗位、职业资格要求" },
    ],
    sourceRefs: ["O*NET: Public Administration / Policy task-skill schema"],
  },
  {
    id: "finance_audit",
    title: "财务审计 / 金融风控",
    workScene: "在规则、数据和风险之间做核查，旺季强度高，长期看证书和行业经验。",
    majorKeywords: ["会计", "审计", "财务管理", "金融", "经济", "统计", "精算"],
    riasec: ["C", "E", "I"],
    values: ["income", "stability", "growth"],
    routes: ["employment", "graduate", "civil_service"],
    dayParts: [
      { time: "上午", task: "核对凭证、报表、合同和异常数据", output: "底稿和异常清单" },
      { time: "中午", task: "向客户或业务部门追问口径", output: "补充材料和确认记录" },
      { time: "下午", task: "做风险测算、抽样和复核", output: "审计发现或风控建议" },
      { time: "晚上", task: "整理报告和合规说明", output: "项目报告版本" },
    ],
    coreSkills: ["会计准则", "Excel/数据分析", "审计抽样", "商业理解", "证书规划"],
    skillSignals: ["细致、守规则", "能接受周期性加班", "对数字和商业逻辑敏感"],
    mismatchSignals: ["讨厌重复核对", "抗拒证书考试", "只看金融光环不看基层工作"],
    routesDetail: [
      { route: "employment", label: "就业", reality: "四大、事务所、银行和企业财务路径差异很大，起点不等于长期上限。", evidenceToCollect: "校招名单、CPA/ACCA要求、实习转正率" },
      { route: "graduate", label: "考研/保研", reality: "读研可提升金融风控、研究和央国企门槛，但要衡量学校层级溢价。", evidenceToCollect: "保研去向、金融专硕就业报告" },
      { route: "civil_service", label: "考公", reality: "财政、税务、审计系统专业匹配度高，但竞争强，职位表比宣传更重要。", evidenceToCollect: "税务/审计职位表、专业代码匹配" },
    ],
    sourceRefs: ["O*NET: Accountants and Auditors task-skill schema", "Lightcast Open Skills: accounting, audit, risk skills taxonomy"],
  },
  {
    id: "teacher_education",
    title: "教师 / 教研 / 教育产品",
    workScene: "围绕学生理解、课程设计、课堂管理和长期反馈做高沟通密度工作。",
    majorKeywords: ["师范", "教育", "汉语言", "数学", "英语", "物理", "化学", "历史", "地理", "心理"],
    riasec: ["S", "A", "I"],
    values: ["stability", "social_impact", "work_life_balance"],
    routes: ["employment", "graduate", "civil_service"],
    dayParts: [
      { time: "上午", task: "备课、授课、课堂观察", output: "课堂记录和学生问题清单" },
      { time: "中午", task: "批改作业、答疑、和家长沟通", output: "反馈记录" },
      { time: "下午", task: "教研活动、试题分析、班级事务", output: "教学改进方案" },
      { time: "晚上", task: "准备第二天课程和个别学生跟进", output: "教案与跟进安排" },
    ],
    coreSkills: ["学科基础", "表达与课堂组织", "学生观察", "情绪稳定", "长期反馈"],
    skillSignals: ["愿意解释复杂概念", "能接受被评价和沟通压力", "有耐心做重复训练"],
    mismatchSignals: ["只看寒暑假", "不喜欢公开表达", "无法接受家校沟通"],
    routesDetail: [
      { route: "employment", label: "就业", reality: "教师招聘要看学科、教师资格证、地区编制和学校层级。", evidenceToCollect: "教师招聘公告、学科需求、就业地区" },
      { route: "graduate", label: "考研/保研", reality: "教育学、学科教学和心理方向分化明显，读研目的要提前明确。", evidenceToCollect: "学科教学专硕去向、推免率、导师方向" },
      { route: "civil_service", label: "考编/事业单位", reality: "师范路径并不等于稳定，关键是地区编制供给和学科缺口。", evidenceToCollect: "各地教师招聘岗位表、近三年招录人数" },
    ],
    sourceRefs: ["O*NET: Teachers and Instructional Coordinators task-skill schema"],
  },
  {
    id: "intelligent_manufacturing",
    title: "智能制造 / 新能源工程",
    workScene: "在工厂、实验室和供应链现场解决设备、工艺、质量和交付问题。",
    majorKeywords: ["机械", "自动化", "电气", "车辆", "能源", "材料", "工业工程", "测控"],
    riasec: ["R", "I", "C"],
    values: ["growth", "income", "stability"],
    routes: ["employment", "graduate", "research"],
    dayParts: [
      { time: "上午", task: "查看产线数据、设备状态和质量异常", output: "问题定位和优先级" },
      { time: "中午", task: "和工艺、供应商、研发沟通方案", output: "改进方案和责任人" },
      { time: "下午", task: "现场验证、调试设备或分析样件", output: "测试记录和参数版本" },
      { time: "晚上", task: "整理复盘、成本和良率影响", output: "工程变更或复盘报告" },
    ],
    coreSkills: ["工程制图/电路基础", "现场问题定位", "数据记录", "供应链理解", "安全规范"],
    skillSignals: ["不排斥现场和设备", "喜欢把问题落到实物", "能接受制造业节奏"],
    mismatchSignals: ["只想坐办公室", "对物理和工程基础厌烦", "不能接受出差或现场沟通"],
    routesDetail: [
      { route: "employment", label: "就业", reality: "新能源、半导体和先进制造机会多，但城市、现场强度和岗位内容差异极大。", evidenceToCollect: "企业校招 JD、工作地点、岗位轮岗安排" },
      { route: "graduate", label: "考研/保研", reality: "读研可切到控制、机器人、材料、电力电子等更细方向。", evidenceToCollect: "实验室项目、导师企业合作、毕业去向" },
      { route: "research", label: "科研", reality: "工程科研更看实验平台、项目经费和产业连接，不只是学科名称。", evidenceToCollect: "重点实验室、横向课题、论文/专利" },
    ],
    sourceRefs: ["O*NET: Industrial Engineers / Electrical Engineers task-skill schema", "Lightcast Open Skills: manufacturing, automation, energy skills taxonomy"],
  },
];

const routeWeight: Record<CareerRouteType, number> = {
  employment: 4,
  graduate: 3,
  civil_service: 3,
  research: 2,
};

function normalizeText(items?: Array<string | undefined>): string {
  return (items ?? []).filter(Boolean).join(" ").toLowerCase();
}

function clampScore(value: number): number {
  return Math.max(0, Math.min(92, Math.round(value)));
}

function fitLevel(score: number): CareerSimulation["fitLevel"] {
  if (score >= 72) return "high";
  if (score >= 48) return "medium";
  return "low";
}

function rowMajorText(rows: CareerSimulationMajorRow[]): string {
  return normalizeText(
    rows.flatMap((row) => [
      ...(row.major_list ?? []),
      ...(row.suggested_major_choices ?? []).map((choice) => choice.major_name),
    ]),
  );
}

export function buildCareerSimulations({
  profile,
  rows = [],
  limit = 3,
}: {
  profile?: CareerSimulationProfile | null;
  rows?: CareerSimulationMajorRow[];
  limit?: number;
}): CareerSimulation[] {
  const preferredText = normalizeText(profile?.preferred_majors);
  const rowText = rowMajorText(rows);
  const blacklistText = normalizeText(profile?.blacklist_majors);
  const riasec = new Set(profile?.riasec_top_codes ?? []);
  const values = new Set(profile?.career_values ?? []);
  const riskTolerance = profile?.risk_tolerance;

  return careerSeeds
    .map((seed) => {
      const majorHits = seed.majorKeywords.filter((keyword) => {
        const normalized = keyword.toLowerCase();
        return preferredText.includes(normalized) || rowText.includes(normalized);
      });
      const blacklistHits = seed.majorKeywords.filter((keyword) => blacklistText.includes(keyword.toLowerCase()));
      const riasecHits = seed.riasec.filter((code) => riasec.has(code));
      const valueHits = seed.values.filter((value) => values.has(value));
      const stableRouteBoost =
        riskTolerance === "conservative" && seed.routes.includes("civil_service")
          ? 4
          : riskTolerance === "aggressive" && seed.routes.includes("research")
            ? 3
            : 0;
      const score = clampScore(
        28 +
          majorHits.length * 14 +
          riasecHits.length * 10 +
          valueHits.length * 7 +
          seed.routes.reduce((sum, route) => sum + routeWeight[route], 0) * 0.4 +
          stableRouteBoost -
          blacklistHits.length * 18,
      );
      const reasons = [
        majorHits.length ? `专业关键词命中：${majorHits.slice(0, 3).join("、")}` : "",
        riasecHits.length ? `兴趣信号匹配：${riasecHits.join("、")}` : "",
        valueHits.length ? `价值观匹配：${valueHits.join("、")}` : "",
        riskTolerance ? `风险偏好：${riskTolerance}` : "",
        blacklistHits.length ? `黑名单提醒：${blacklistHits.join("、")} 相关方向需复核` : "",
      ].filter(Boolean);

      return {
        id: seed.id,
        title: seed.title,
        workScene: seed.workScene,
        fitScore: score,
        fitLevel: fitLevel(score),
        matchReasons: reasons.length ? reasons : ["当前信息不足，仅按通用职业路径展示；需要补充专业偏好和职业兴趣。"],
        dayParts: seed.dayParts,
        coreSkills: seed.coreSkills,
        skillSignals: seed.skillSignals,
        mismatchSignals: seed.mismatchSignals,
        routesDetail: seed.routesDetail,
        sourceRefs: seed.sourceRefs,
      };
    })
    .sort((a, b) => b.fitScore - a.fitScore)
    .slice(0, Math.max(1, limit));
}

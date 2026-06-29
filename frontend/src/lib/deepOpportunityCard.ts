export type DeepOpportunityPillarLabel =
  | "量化定位"
  | "科研资源"
  | "本科生可获得性"
  | "真实就业"
  | "升学路径"
  | "低估可能"
  | "反证边界";

export interface DeepOpportunitySignal {
  label: DeepOpportunityPillarLabel;
  score: number;
  weight: number;
  status: "strong" | "medium" | "needs_check";
  evidence: string[];
  interpretation: string;
}

export interface AlphaBoardRow {
  factor: string;
  score: number;
  exposure: "正向" | "中性" | "负向";
  evidence: string;
}

export interface DeepOpportunityInput {
  student: {
    province: string;
    subjectGroup: string;
    rank: number;
    targetRankBand: string;
    preference: string[];
  };
  target: {
    schoolName: string;
    majorName: string;
    city: string;
    opportunityType: string;
  };
  evidencePillars: DeepOpportunitySignal[];
  researchSignals: string[];
  employmentSignals: string[];
  graduateSignals: string[];
  undergradAccessSignals: string[];
  counterEvidenceChecks: string[];
  evidenceGaps: string[];
  nextActions: string[];
}

export interface DeepOpportunityCardModel {
  protocol: "deep_opportunity_card_v1";
  targetLabel: string;
  province: string;
  opportunityType: string;
  totalScore: number;
  confidence: "高" | "中" | "低";
  alphaBoard: AlphaBoardRow[];
  evidencePillars: DeepOpportunitySignal[];
  researchSignals: string[];
  employmentSignals: string[];
  graduateSignals: string[];
  undergradAccessSignals: string[];
  fitFor: string[];
  notFitFor: string[];
  counterEvidenceChecks: string[];
  evidenceGaps: string[];
  nextActions: string[];
  claimBoundary: string;
}

const clampScore = (score: number) => Math.max(0, Math.min(100, Math.round(score)));

const weightedScore = (pillars: DeepOpportunitySignal[]) => {
  const totalWeight = pillars.reduce((sum, item) => sum + item.weight, 0);
  if (totalWeight <= 0) return 0;
  const rawScore = pillars.reduce((sum, item) => sum + clampScore(item.score) * item.weight, 0) / totalWeight;
  return clampScore(rawScore);
};

export const exampleDeepOpportunityInput: DeepOpportunityInput = {
  student: {
    province: "广东",
    subjectGroup: "物理类",
    rank: 38200,
    targetRankBand: "36000-43000",
    preference: ["计算机相关", "愿意读研", "接受非一线城市岗位路径"],
  },
  target: {
    schoolName: "华南理工示例校",
    majorName: "智能制造与数据工程",
    city: "广州",
    opportunityType: "科研资源被低估型机会",
  },
  evidencePillars: [
    {
      label: "量化定位",
      score: 86,
      weight: 1.2,
      status: "strong",
      evidence: ["近三年同位次样本落在目标讨论区间内", "专业组计划数增加后，等位分压力方向性下降"],
      interpretation: "从位次角度看，这是可以进入冲稳讨论的候选，不是盲目冲高。",
    },
    {
      label: "科研资源",
      score: 90,
      weight: 1.4,
      status: "strong",
      evidence: ["学院长期覆盖智能制造、工业软件、数据驱动优化方向", "近年论文和项目集中在制造业数字化与工程智能交叉"],
      interpretation: "专业标签不一定热门，但研究方向贴近真实产业技术升级。",
    },
    {
      label: "本科生可获得性",
      score: 83,
      weight: 1.1,
      status: "medium",
      evidence: ["公开材料显示有本科生科研训练计划", "部分课题组长期招收本科助研或竞赛队成员"],
      interpretation: "机会是否真正落到本科生身上，仍需逐个课题组核验。",
    },
    {
      label: "真实就业",
      score: 84,
      weight: 1,
      status: "medium",
      evidence: ["岗位侧能对应工业软件、数据分析、质量工程、算法工程化", "制造业数字化岗位对工程背景更友好"],
      interpretation: "就业不是只看互联网大厂，而要看区域产业和岗位任务是否匹配。",
    },
    {
      label: "升学路径",
      score: 87,
      weight: 1,
      status: "strong",
      evidence: ["方向可衔接控制、计算机、机械电子、工业工程等交叉读研路径", "保研和考研可围绕导师方向提前构建项目经历"],
      interpretation: "适合把本科当作科研训练平台，而不是只拿一个专业名称。",
    },
    {
      label: "低估可能",
      score: 82,
      weight: 0.9,
      status: "medium",
      evidence: ["专业名称不如计算机直接，家长搜索时容易低估", "外部方案常按专业热度排序，忽略导师和产业方向"],
      interpretation: "低估来自信息维度不足，不来自录取概率保证。",
    },
    {
      label: "反证边界",
      score: 78,
      weight: 0.8,
      status: "needs_check",
      evidence: ["需核验毕业去向是否集中在目标岗位", "需确认专业组内调剂风险和校区安排"],
      interpretation: "任何反证命中都要降权，不能把样板卡当最终推荐。",
    },
  ],
  researchSignals: [
    "实验室方向覆盖工业软件、智能制造系统、数据驱动优化，适合做本科科研切入。",
    "课题组成果更偏工程落地和交叉应用，和高考志愿里的专业名称不完全同维度。",
    "导师论文主题可以拆成算法、系统、制造场景三类，用来判断学生是否真的愿意长期投入。",
  ],
  undergradAccessSignals: [
    "本科生科研训练、创新创业项目、竞赛队和课题组助研是需要优先核验的入口。",
    "如果官网只展示研究生培养，必须继续找学院新闻、实验室公众号和本科培养方案。",
  ],
  employmentSignals: [
    "岗位锚点包括工业软件实施、制造数据分析、质量工程、算法工程化和智能装备产品经理。",
    "需要用 Boss直聘、国聘、校招官网等岗位样本核验城市、薪资、技能栈和学历要求。",
  ],
  graduateSignals: [
    "考研可转向控制科学、计算机应用、机械电子、工业工程与管理科学交叉方向。",
    "保研竞争力取决于早期项目、竞赛、论文或软件著作权，而不是专业名称本身。",
  ],
  counterEvidenceChecks: [
    "如果 2026 招生章程显示专业组可调剂到学生黑名单专业，直接降级。",
    "如果就业质量报告只给大类就业率，没有岗位和升学去向，不能宣称真实就业优势。",
    "如果导师团队近三年公开成果断档，科研资源评分必须下调。",
  ],
  evidenceGaps: [
    "补齐 2026 年招生章程、专业组代码、计划数、选科要求和校区安排。",
    "补齐学院近三年就业质量报告中的升学、就业单位、岗位类型和地区分布。",
    "补齐实验室公众号、本科生项目名单、导师主页和近三年论文题目。",
  ],
  nextActions: [
    "先核验官方招生计划和专业组风险，再讨论是否进入冲稳组合。",
    "按导师方向建立 5 条证据链：主页、论文、项目、学生培养、毕业去向。",
    "采样 20 条国内岗位，拆出学历门槛、技能栈、城市和工作内容。",
  ],
};

export function buildDeepOpportunityCard(input: DeepOpportunityInput): DeepOpportunityCardModel {
  const normalizedPillars = input.evidencePillars.map((pillar) => ({
    ...pillar,
    score: clampScore(pillar.score),
  }));
  const totalScore = weightedScore(normalizedPillars);
  const confidence = totalScore >= 84 ? "高" : totalScore >= 72 ? "中" : "低";

  return {
    protocol: "deep_opportunity_card_v1",
    targetLabel: `${input.target.schoolName} · ${input.target.majorName}`,
    province: input.student.province,
    opportunityType: input.target.opportunityType,
    totalScore,
    confidence,
    alphaBoard: buildAlphaBoard(normalizedPillars),
    evidencePillars: normalizedPillars,
    researchSignals: input.researchSignals,
    employmentSignals: input.employmentSignals,
    graduateSignals: input.graduateSignals,
    undergradAccessSignals: input.undergradAccessSignals,
    fitFor: [
      "愿意考研、保研或较早进入课题组训练的学生。",
      "能接受专业名称不够热门，但愿意看研究方向和岗位任务的家庭。",
      "目标是工程技术、产业数字化、算法工程化等复合路径的学生。",
    ],
    notFitFor: [
      "只想本科稳定就业，且不愿投入科研、竞赛或项目经历的学生。",
      "无法接受专业组调剂、校区变化或非互联网岗位路径的家庭。",
      "只按热门专业标签决策，不愿逐条核验证据的家庭。",
    ],
    counterEvidenceChecks: input.counterEvidenceChecks,
    evidenceGaps: input.evidenceGaps,
    nextActions: input.nextActions,
    claimBoundary:
      "这不是最终志愿推荐，而是一张可复核的深度机会卡；必须补齐官方计划、位次、专业组风险、导师与就业证据后，才能进入最终方案排序。",
  };
}

function buildAlphaBoard(pillars: DeepOpportunitySignal[]): AlphaBoardRow[] {
  const pillarScore = (label: DeepOpportunityPillarLabel) =>
    pillars.find((pillar) => pillar.label === label)?.score ?? 0;

  return [
    {
      factor: "同分段相对提升",
      score: pillarScore("量化定位"),
      exposure: "正向",
      evidence: "同位次基准允许进入冲稳讨论，但仍受当年计划和选科口径约束。",
    },
    {
      factor: "科研资源折价",
      score: pillarScore("科研资源"),
      exposure: "正向",
      evidence: "研究方向与导师项目比专业名称更能解释中长期价值。",
    },
    {
      factor: "职业路径兑现度",
      score: Math.round((pillarScore("真实就业") + pillarScore("升学路径")) / 2),
      exposure: "正向",
      evidence: "岗位任务、考研保研方向和本科能力建设能形成连续路径。",
    },
    {
      factor: "本科可获得性",
      score: pillarScore("本科生可获得性"),
      exposure: "中性",
      evidence: "公开入口存在，但必须核验本科生是否真的能进入课题组和项目。",
    },
    {
      factor: "市场低关注",
      score: pillarScore("低估可能"),
      exposure: "正向",
      evidence: "普通家长和通用 AI 容易按专业名称热度排序，忽略导师和产业场景。",
    },
    {
      factor: "反证风险暴露",
      score: 100 - pillarScore("反证边界"),
      exposure: "负向",
      evidence: "专业组调剂、校区、就业去向或导师断档任一命中都要降权。",
    },
  ];
}

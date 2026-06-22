export type DeepEvidenceClaim =
  | "official_admission"
  | "rank_history"
  | "faculty_research"
  | "publication_trace"
  | "undergrad_access"
  | "employment_market"
  | "graduate_progression"
  | "civil_service_path"
  | "wechat_public_account"
  | "counter_evidence";

export interface DeepEvidenceCollectionContext {
  province: string;
  schoolName: string;
  majorName: string;
  targetYear: number;
}

export interface DeepEvidenceTask {
  id: string;
  claim: DeepEvidenceClaim;
  title: string;
  sourceFamily: string;
  accessMethod: string;
  outputFields: string[];
  passRule: string;
  failRule: string;
  priority: "P0" | "P1" | "P2";
}

export interface DeepEvidenceCollectionPlan {
  protocol: "deep_evidence_collection_plan_v1";
  targetLabel: string;
  tasks: DeepEvidenceTask[];
  reviewGates: string[];
  claimBoundary: string;
}

export const exampleCollectionContext: DeepEvidenceCollectionContext = {
  province: "广东",
  schoolName: "华南理工示例校",
  majorName: "智能制造与数据工程",
  targetYear: 2026,
};

export function buildDeepEvidenceCollectionPlan(
  context: DeepEvidenceCollectionContext,
): DeepEvidenceCollectionPlan {
  const targetLabel = `${context.province} ${context.targetYear} · ${context.schoolName} · ${context.majorName}`;
  const tasks: DeepEvidenceTask[] = [
    {
      id: "official-plan-charter",
      claim: "official_admission",
      title: "官方招生计划与章程核验",
      sourceFamily: "考试院、学校本科招生网、招生章程",
      accessMethod: "官方网页或 PDF 人工核验，保留发布日期、学校代码、专业组代码、选科要求和校区安排",
      outputFields: ["来源链接", "发布日期", "学校代码", "专业组代码", "计划数", "选科要求", "校区", "原文摘录"],
      passRule: "官方来源字段齐全，且和机会卡目标一致，才允许进入量化定位。",
      failRule: "专业组包含黑名单专业、校区或选科要求不匹配时，直接降权或移出候选。",
      priority: "P0",
    },
    {
      id: "rank-history-band",
      claim: "rank_history",
      title: "历史位次与计划变化双来源复核",
      sourceFamily: "考试院历史投档表、学校录取分、第三方位次库",
      accessMethod: "至少两类来源交叉核验，记录年份、最低位次、计划数变化和口径差异",
      outputFields: ["年份", "最低分", "最低位次", "计划数", "口径说明", "第二来源", "原文摘录"],
      passRule: "位次区间和计划变化方向一致时，只能支持冲稳讨论，不能承诺录取概率。",
      failRule: "不同来源冲突且无法解释时，量化定位降权为待复核。",
      priority: "P0",
    },
    {
      id: "faculty-research-direction",
      claim: "faculty_research",
      title: "科研方向与课题组地图",
      sourceFamily: "学院官网、实验室主页、导师主页、学院新闻",
      accessMethod: "按导师和实验室建立方向表，拆出研究主题、项目场景和本科可理解关键词",
      outputFields: ["导师", "实验室", "研究方向", "项目场景", "近三年动态", "原文摘录"],
      passRule: "方向能和专业培养、产业岗位或读研路径形成连续证据链，科研资源才加分。",
      failRule: "只有学院宣传口号、没有课题组或导师证据时，科研资源不得高分。",
      priority: "P0",
    },
    {
      id: "publication-trace",
      claim: "publication_trace",
      title: "师资与论文主题追踪",
      sourceFamily: "导师主页、Google Scholar、知网、DBLP、学院成果页",
      accessMethod: "按导师抽取近三年题目和关键词，不评价论文高低，只判断方向是否真实持续",
      outputFields: ["导师", "论文题目", "年份", "关键词", "方向归类", "来源链接", "原文摘录"],
      passRule: "近三年主题连续，且和机会卡研究方向一致，才支持师资与论文加分。",
      failRule: "成果断档、方向漂移或只有行政简介时，师资论文项降权。",
      priority: "P1",
    },
    {
      id: "undergrad-access",
      claim: "undergrad_access",
      title: "本科生可获得性核验",
      sourceFamily: "本科培养方案、创新创业项目、竞赛队、实验室公众号、学院新闻",
      accessMethod: "查本科生是否真实进入项目、竞赛、课题组或导师团队，优先保留学生姓名脱敏后的项目证据",
      outputFields: ["入口类型", "项目名称", "学生参与方式", "年级限制", "报名方式", "原文摘录"],
      passRule: "能说明本科生如何进入、何时进入、产出什么，才算本科生可获得性成立。",
      failRule: "只展示研究生培养或教师成果，不能外推到本科生机会。",
      priority: "P0",
    },
    {
      id: "employment-market",
      claim: "employment_market",
      title: "国内岗位样本与真实就业锚点",
      sourceFamily: "Boss直聘/国聘/校招官网、企业招聘页、学校就业质量报告",
      accessMethod: "人工采样岗位，不绕过平台限制；记录城市、学历门槛、技能栈、工作内容和薪资口径",
      outputFields: ["岗位名", "城市", "学历要求", "技能栈", "工作内容", "薪资口径", "来源链接", "原文摘录"],
      passRule: "岗位任务能和专业课程、科研方向或学生能力建设对应，才支持真实就业加分。",
      failRule: "只看到就业率、没有单位/岗位/学历门槛时，不得宣称就业优势。",
      priority: "P0",
    },
    {
      id: "graduate-progression",
      claim: "graduate_progression",
      title: "升学/保研路径核验",
      sourceFamily: "学院升学去向、保研名单、研究生招生目录、推免办法",
      accessMethod: "拆分校内保研、外校保研、考研方向和跨学科去向，记录可准备的本科经历",
      outputFields: ["去向类型", "目标学科", "保研/考研要求", "项目经历", "课程要求", "原文摘录"],
      passRule: "能指出本科阶段可积累的项目、竞赛、论文或课程路径，才支持升学路径加分。",
      failRule: "只有笼统升学率，不能证明具体专业适合读研或保研。",
      priority: "P1",
    },
    {
      id: "civil-service-path",
      claim: "civil_service_path",
      title: "考公与选调岗位现实核验",
      sourceFamily: "国考/省考职位表、选调公告、事业单位招聘公告",
      accessMethod: "按专业名称、学科门类和岗位限制查可报岗位，记录是否只适合少量不限专业岗位",
      outputFields: ["公告年份", "岗位类别", "专业限制", "学历限制", "地区", "竞争口径", "原文摘录"],
      passRule: "专业名称能命中明确岗位或选调条件，才可作为考公路径支持。",
      failRule: "只能报不限专业岗位时，考公路径必须降权，不能作为推荐理由。",
      priority: "P2",
    },
    {
      id: "wechat-public-account",
      claim: "wechat_public_account",
      title: "微信公众号深层材料采集",
      sourceFamily: "学院公众号、实验室公众号、就业公众号、校友公众号",
      accessMethod: "通过微信客户端、搜一搜、文章链接或可访问的搜索结果人工采集；不绕过登录、付费或平台限制",
      outputFields: ["公众号名称", "文章标题", "发布日期", "涉及导师/项目/就业", "链接或截图编号", "原文摘录"],
      passRule: "公众号材料只能补充官网没有的过程证据，必须和官方或学院来源双来源印证。",
      failRule: "单篇推文、宣传稿或无法追溯来源的截图不能单独支撑机会结论。",
      priority: "P1",
    },
    {
      id: "counter-evidence",
      claim: "counter_evidence",
      title: "反证降权检查",
      sourceFamily: "招生章程、就业报告、学生讨论、投诉/风险公告、专业组调剂规则",
      accessMethod: "先查不利证据：调剂黑名单、校区变化、培养方案断裂、就业去向模糊、导师成果断档",
      outputFields: ["反证类型", "命中证据", "影响范围", "降权动作", "是否阻断推荐", "原文摘录"],
      passRule: "反证未命中且关键证据双来源通过，才允许从候选机会升级为可讨论机会。",
      failRule: "任一 P0 反证命中时必须降权；涉及黑名单或官方规则冲突时阻断推荐。",
      priority: "P0",
    },
  ];

  return {
    protocol: "deep_evidence_collection_plan_v1",
    targetLabel,
    tasks,
    reviewGates: [
      "P0 官方招生、位次、专业组风险、本科生可获得性、就业锚点必须先过。",
      "科研、论文、公众号材料必须至少有第二来源或双来源印证，不能单独成结论。",
      "任何反证命中都先降权，再决定是否继续补证。",
      "所有结论必须保留原文摘录、链接或截图编号，方便顾问和家庭复核。",
    ],
    claimBoundary:
      "这不是自动抓取承诺，而是高维证据采集台账；平台型、半封闭或公众号材料必须人工合规采集，不能绕过登录、付费或访问限制。",
  };
}

export type JobEvidenceSourceType = "manual_jd" | "public_report" | "campus_recruitment" | "civil_service_table";

export interface ParsedJobEvidence {
  jobTitle: string;
  cities: string[];
  educationRequirement: string;
  experienceRequirement: string;
  skillKeywords: string[];
  routeSignals: {
    employment: string[];
    graduate: string[];
    civilService: string[];
  };
  boundaryWarnings: string[];
}

export interface JobEvidenceBrief extends ParsedJobEvidence {
  sourceType: JobEvidenceSourceType;
  normalizedRoleFamily: string;
  summary: string;
  evidenceQuestions: string[];
  platformPolicyNote: string;
  capturedAt?: string;
}

const skillDictionary = [
  "RAG",
  "Agent",
  "LangChain",
  "Prompt Engineering",
  "Prompt",
  "Python",
  "SQL",
  "A/B 实验",
  "向量数据库",
  "模型评测",
  "数据分析",
  "Excel",
  "CPA",
  "GCP",
  "PLC",
  "嵌入式",
  "公文写作",
  "政策分析",
  "教师资格证",
  "课程设计",
];

const platformPolicyNote = "请粘贴你有权查看或保存的 JD；系统只做人工提供文本的结构化解析，不支持绕过平台反爬抓取。";

function cleanValue(value?: string): string {
  return (value ?? "").replace(/[，,。；;].*$/, "").trim();
}

function extractLabeledValue(text: string, labels: string[]): string {
  for (const label of labels) {
    const match = text.match(new RegExp(`${label}\\s*[:：]\\s*([^\\n]+)`, "i"));
    if (match?.[1]) return cleanValue(match[1]);
  }
  return "";
}

function extractJobTitle(text: string): string {
  return extractLabeledValue(text, ["岗位", "职位", "招聘岗位", "职位名称"]) || "待识别岗位";
}

function extractCities(text: string): string[] {
  const raw = extractLabeledValue(text, ["地点", "城市", "工作地点"]);
  if (!raw) return [];
  return raw
    .split(/[\/、，,;；\s]+/)
    .map((item) => item.replace(/市$/, "").trim())
    .filter(Boolean)
    .slice(0, 4);
}

function extractEducationRequirement(text: string): string {
  const patterns = ["博士", "硕士及以上", "硕士", "本科及以上", "本科", "大专及以上", "不限"];
  return patterns.find((pattern) => text.includes(pattern)) ?? "未明确";
}

function extractExperienceRequirement(text: string): string {
  if (/应届生?可投|应届.*优先|校招|应届/.test(text)) return "应届可投";
  const match = text.match(/(\d+\s*[-到至]\s*\d+\s*年|\d+\s*年以上)/);
  return match?.[1]?.replace(/\s+/g, "") ?? "未明确";
}

function extractSkillKeywords(text: string): string[] {
  return skillDictionary.filter((skill) => text.toLowerCase().includes(skill.toLowerCase()));
}

function inferRoleFamily(text: string, skills: string[]): string {
  const joined = `${text} ${skills.join(" ")}`;
  if (/RAG|Agent|LangChain|大模型|Prompt|向量数据库|模型评测/i.test(joined)) return "AI 应用开发";
  if (/医|临床|GCP|CRA|药企|医院/.test(joined)) return "医药健康";
  if (/审计|税务|财务|CPA|风控|银行/.test(joined)) return "财会金融";
  if (/教师|教研|课程|题库|教师资格证/.test(joined)) return "教育教研";
  if (/公务员|事业单位|选调|政策|公文|国企/.test(joined)) return "公共治理";
  if (/PLC|嵌入式|设备|工艺|新能源|自动化/.test(joined)) return "先进制造";
  return "待归类岗位";
}

function buildRouteSignals(text: string, skills: string[]) {
  const employment = [
    skills.length
      ? `本科就业要用项目、实习或作品证明这些技能：${skills.slice(0, 5).join("、")}`
      : "本科就业需要继续补一份真实 JD 或校招岗位表，先确认岗位到底看什么能力。",
  ];
  if (/实习|项目|校招|应届/.test(text)) {
    employment.push("这类岗位对实习、项目经历和可展示产出敏感，不能只看专业名称。");
  }

  const graduate = [
    /算法|模型|评测|深度学习|科研|论文/.test(text)
      ? "涉及模型评测/算法能力，读研可提升上限，但必须对照真实岗位学历门槛。"
      : "是否读研要回到岗位学历门槛、目标城市和院校平台，不应默认所有方向都必须读研。",
  ];
  if (/硕士|博士|研究生/.test(text)) {
    graduate.push("JD 已出现研究生门槛，需要继续核验同类岗位是否普遍如此。");
  }

  const civilService = [
    /公务员|事业单位|编制|选调|公文|政策|国企/.test(text)
      ? "该文本出现体制内或公共部门信号，要进一步查近三年职位表的专业代码限制。"
      : "该 JD 本身不是考公证据；考公仍需单独查国考、省考、事业单位职位表。",
  ];

  return { employment, graduate, civilService };
}

export function parseManualJobDescription(text: string): ParsedJobEvidence {
  const normalizedText = text.trim();
  const skillKeywords = extractSkillKeywords(normalizedText);

  return {
    jobTitle: extractJobTitle(normalizedText),
    cities: extractCities(normalizedText),
    educationRequirement: extractEducationRequirement(normalizedText),
    experienceRequirement: extractExperienceRequirement(normalizedText),
    skillKeywords,
    routeSignals: buildRouteSignals(normalizedText, skillKeywords),
    boundaryWarnings: [
      platformPolicyNote,
      "平台页面、截图和复制文本只能作为单条岗位证据，不能替代官方就业质量报告、校招名单和职位表交叉验证。",
    ],
  };
}

export function buildJobEvidenceBrief({
  sourceType,
  text,
  capturedAt,
}: {
  sourceType: JobEvidenceSourceType;
  text: string;
  capturedAt?: string;
}): JobEvidenceBrief {
  const parsed = parseManualJobDescription(text);
  const normalizedRoleFamily = inferRoleFamily(text, parsed.skillKeywords);

  return {
    ...parsed,
    sourceType,
    normalizedRoleFamily,
    capturedAt,
    platformPolicyNote,
    summary: `${parsed.jobTitle} 被归入「${normalizedRoleFamily}」，当前证据显示学历门槛为「${parsed.educationRequirement}」，经验门槛为「${parsed.experienceRequirement}」。`,
    evidenceQuestions: [
      "同类岗位的学历门槛是否普遍要求本科、硕士或博士？",
      "目标城市是否集中在少数产业城市，还是全国都有入口？",
      "JD 关键词能否被课程项目、实习、竞赛或科研产出证明？",
      "这条证据来自单个岗位、公开报告、校招公告，还是公务员/事业单位职位表？",
    ],
  };
}

export const exampleJobEvidenceText = [
  "岗位：大模型应用工程师",
  "地点：广州/深圳",
  "学历要求：本科及以上，计算机、软件工程、人工智能相关专业优先",
  "经验：应届生可投，有 AI 项目或实习经历优先",
  "职责：负责 RAG 应用、Agent 工作流、模型评测、向量数据库接入和业务指标复盘",
  "技能：Python、SQL、LangChain、Prompt Engineering、A/B 实验",
].join("\n");

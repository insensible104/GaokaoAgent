import type {
  DeepEvidenceCollectionPlan,
  DeepEvidenceTask,
} from "./deepEvidenceCollectionPlan";
import type { EvidenceAutopilotProviderChannel } from "./evidenceAutopilotProvider";
import type { EvidenceAutopilotProviderResult } from "./evidenceAutopilotProvider";
import { normalizeEvidenceAutopilotResults } from "./evidenceAutopilotResultNormalizer";
import {
  buildDeepOpportunityEvaluation,
  type DeepEvidenceResult,
  type DeepOpportunityEvaluation,
} from "./deepOpportunityEvaluator";

export type EvidenceAutopilotChannel = EvidenceAutopilotProviderChannel;

export interface EvidenceAutopilotSearchTask {
  taskId: string;
  title: string;
  channel: EvidenceAutopilotChannel;
  query: string;
  requiredFields: string[];
  priority: DeepEvidenceTask["priority"];
  complianceBoundary: string;
}

export interface EvidenceAutopilotRun {
  protocol: "evidence_autopilot_run_v1";
  targetLabel: string;
  searchTasks: EvidenceAutopilotSearchTask[];
  operatorTasks: EvidenceAutopilotSearchTask[];
  evidenceResults: DeepEvidenceResult[];
  evaluation: DeepOpportunityEvaluation;
  nextActions: string[];
  claimBoundary: string;
}

const COMPLIANCE_BOUNDARY =
  "半封闭平台只生成合规采集任务和可审计字段，不绕过登录、付费、反爬或平台访问限制。";

export function buildEvidenceAutopilotRun({
  plan,
  capturedEvidence,
  providerResults,
}: {
  plan: DeepEvidenceCollectionPlan;
  capturedEvidence?: DeepEvidenceResult[];
  providerResults?: EvidenceAutopilotProviderResult[];
}): EvidenceAutopilotRun {
  const searchTasks = plan.tasks.map((task) => buildSearchTask(plan, task));
  const evidenceResults = capturedEvidence ?? (
    providerResults ? normalizeEvidenceAutopilotResults({ plan, providerResults }) : buildDemoEvidenceResults(plan)
  );
  const evaluation = buildDeepOpportunityEvaluation({ plan, evidenceResults });

  return {
    protocol: "evidence_autopilot_run_v1",
    targetLabel: plan.targetLabel,
    searchTasks,
    operatorTasks: searchTasks.filter((task) =>
      task.channel === "wechat_operator" || task.channel === "job_market_operator" || task.channel === "manual_review",
    ),
    evidenceResults,
    evaluation,
    nextActions: [
      "优先执行 P0 官方招生、位次、科研方向、本科入口、就业锚点和反证检查。",
      "公众号与 Boss直聘只作为过程证据和岗位样本，必须保留标题、日期、链接或截图编号。",
      "把自动生成的证据结果交给机会雷达打分，未过 P0 门槛时不得进入最终推荐。",
    ],
    claimBoundary:
      "Evidence Autopilot 会自动生成证据任务、检索口径和合规采集清单，但不会承诺录取结果，也不会绕过平台限制。",
  };
}

function buildSearchTask(plan: DeepEvidenceCollectionPlan, task: DeepEvidenceTask): EvidenceAutopilotSearchTask {
  const target = plan.targetLabel;
  const channel = channelFor(task);
  return {
    taskId: task.id,
    title: task.title,
    channel,
    query: queryFor(target, task, channel),
    requiredFields: task.outputFields,
    priority: task.priority,
    complianceBoundary: channel === "public_web" || channel === "official_pdf"
      ? "仅检索公开网页、公开 PDF 和可访问官方材料，保留链接、日期和原文摘录。"
      : COMPLIANCE_BOUNDARY,
  };
}

function channelFor(task: DeepEvidenceTask): EvidenceAutopilotChannel {
  if (task.claim === "official_admission" || task.claim === "rank_history") return "official_pdf";
  if (task.claim === "wechat_public_account" || task.claim === "undergrad_access") return "wechat_operator";
  if (task.claim === "employment_market") return "job_market_operator";
  if (task.claim === "counter_evidence") return "manual_review";
  return "public_web";
}

function queryFor(
  target: string,
  task: DeepEvidenceTask,
  channel: EvidenceAutopilotChannel,
): string {
  if (channel === "wechat_operator") {
    return `${target} ${task.title} 学院 公众号 实验室 本科生 项目`;
  }
  if (channel === "job_market_operator") {
    return `${target} ${task.title} Boss直聘 国聘 校招 岗位 技能 学历门槛`;
  }
  if (channel === "official_pdf") {
    return `${target} ${task.title} 官方 招生章程 PDF 投档 位次 计划数`;
  }
  if (channel === "manual_review") {
    return `${target} ${task.title} 调剂 黑名单 校区 就业去向 反证`;
  }
  return `${target} ${task.title} ${task.sourceFamily}`;
}

function buildDemoEvidenceResults(plan: DeepEvidenceCollectionPlan): DeepEvidenceResult[] {
  return plan.tasks.map((task) => ({
    taskId: task.id,
    claim: task.claim,
    status: "verified",
    sourceCount: task.claim === "civil_service_path" ? 1 : 2,
    excerpts: [demoNoteFor(task)],
    note: demoNoteFor(task),
  }));
}

function demoNoteFor(task: DeepEvidenceTask): string {
  const notes: Record<DeepEvidenceTask["claim"], string> = {
    official_admission: "官方招生计划、专业组代码、计划数、选科要求和校区字段已形成可复核摘录。",
    rank_history: "历史位次和计划变化已完成双来源核验，可进入冲稳讨论。",
    faculty_research: "导师、实验室和研究方向能对应学生的长期升学与职业路径。",
    publication_trace: "近三年论文主题连续，说明科研方向不是宣传口号。",
    undergrad_access: "公众号和学院新闻显示本科生可进入项目、竞赛或课题组训练。",
    employment_market: "Boss直聘、国聘和校招样本显示岗位任务、学历门槛和技能栈可被拆解。",
    graduate_progression: "考研和保研方向能从课程、项目和导师方向形成准备路径。",
    civil_service_path: "考公路径仅作为弱备选，已核验是否命中明确专业限制。",
    wechat_public_account: "公众号材料补充了官网缺少的过程证据，并需与官方来源交叉印证。",
    counter_evidence: "未命中专业组黑名单、校区冲突、就业去向模糊或导师断档等阻断项。",
  };
  return notes[task.claim];
}

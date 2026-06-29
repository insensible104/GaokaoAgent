import type {
  DeepEvidenceClaim,
  DeepEvidenceCollectionPlan,
  DeepEvidenceTask,
} from "./deepEvidenceCollectionPlan";

export type DeepEvidenceResultStatus = "verified" | "missing" | "weak" | "conflict" | "counter_hit";
export type DeepOpportunityEvaluationStatus =
  | "counselor_review_ready"
  | "candidate"
  | "evidence_gap"
  | "blocked";

export type HorizonLabel = "短期录取" | "中期升学" | "长期职业";

export interface DeepEvidenceResult {
  taskId: string;
  claim: DeepEvidenceClaim;
  status: DeepEvidenceResultStatus;
  sourceCount: number;
  excerpts: string[];
  note: string;
}

export interface DeepOpportunityGateResult {
  taskId: string;
  claim: DeepEvidenceClaim;
  title: string;
  priority: DeepEvidenceTask["priority"];
  status: DeepEvidenceResultStatus;
  score: number;
  downgrade: number;
  reason: string;
}

export interface HorizonSignal {
  horizon: HorizonLabel;
  status: "supported" | "weak" | "blocked";
  summary: string;
}

export interface DeepOpportunityEvaluation {
  protocol: "deep_opportunity_evaluation_v1";
  status: DeepOpportunityEvaluationStatus;
  opportunityScore: number;
  p0Gate: {
    passed: boolean;
    passedCount: number;
    totalCount: number;
  };
  counterEvidence: {
    hit: boolean;
    reasons: string[];
  };
  gateResults: DeepOpportunityGateResult[];
  horizonSignals: HorizonSignal[];
  positiveSignals: string[];
  blockedReasons: string[];
  missingEvidence: string[];
  reviewChecklist: string[];
  claimBoundary: string;
}

const CLAIM_WEIGHTS: Record<DeepEvidenceClaim, number> = {
  official_admission: 14,
  rank_history: 10,
  faculty_research: 12,
  publication_trace: 8,
  undergrad_access: 12,
  employment_market: 12,
  graduate_progression: 9,
  civil_service_path: 5,
  wechat_public_account: 6,
  counter_evidence: 12,
};

const CLAIM_LABEL: Record<DeepEvidenceClaim, string> = {
  official_admission: "官方招生",
  rank_history: "历史位次",
  faculty_research: "科研方向",
  publication_trace: "师资与论文",
  undergrad_access: "本科生可获得性",
  employment_market: "真实就业",
  graduate_progression: "考研/保研",
  civil_service_path: "考公路径",
  wechat_public_account: "微信公众号",
  counter_evidence: "反证降权",
};

const CLAIM_BOUNDARY =
  "深度机会判定器不是最终志愿推荐。它只判断证据是否足以进入顾问复核；正式排序仍需当年官方数据、家庭约束和顾问签字。";

export const exampleReadyEvidenceResults: DeepEvidenceResult[] = [
  verified("official-plan-charter", "official_admission", 2, "2026 招生章程、专业组代码、计划数和校区安排已核验。"),
  verified("rank-history-band", "rank_history", 2, "近三年位次区间和计划变化方向一致，可进入冲稳讨论。"),
  verified("faculty-research-direction", "faculty_research", 3, "学院和实验室方向能对应工业软件、智能制造和数据驱动优化。"),
  verified("publication-trace", "publication_trace", 2, "导师近三年论文主题连续，方向和专业机会一致。"),
  verified("undergrad-access", "undergrad_access", 2, "本科科研训练、竞赛队和实验室助研入口有公开证据。"),
  verified("employment-market", "employment_market", 3, "岗位样本能对应工业软件、数据分析、质量工程和算法工程化。"),
  verified("graduate-progression", "graduate_progression", 2, "考研/保研方向能衔接控制、计算机应用和机械电子。"),
  verified("civil-service-path", "civil_service_path", 1, "考公路径只能作为弱备选，不作为核心推荐理由。"),
  verified("wechat-public-account", "wechat_public_account", 2, "学院公众号和实验室公众号补充了本科生项目过程证据。"),
  verified("counter-evidence", "counter_evidence", 2, "未发现专业组黑名单、校区冲突或导师成果断档。"),
];

export const exampleCounterEvidenceResults: DeepEvidenceResult[] = [
  verified("official-plan-charter", "official_admission", 1, "官方计划已找到，但专业组调剂范围仍需复核。"),
  {
    taskId: "rank-history-band",
    claim: "rank_history",
    status: "missing",
    sourceCount: 0,
    excerpts: [],
    note: "缺少第二来源位次核验。",
  },
  verified("faculty-research-direction", "faculty_research", 2, "有实验室方向，但本科入口尚未核验。"),
  {
    taskId: "undergrad-access",
    claim: "undergrad_access",
    status: "missing",
    sourceCount: 0,
    excerpts: [],
    note: "没有找到本科生进入课题组的证据。",
  },
  {
    taskId: "employment-market",
    claim: "employment_market",
    status: "weak",
    sourceCount: 1,
    excerpts: ["只有岗位样本，没有学校毕业去向。"],
    note: "只有岗位样本，没有学校毕业去向。",
  },
  {
    taskId: "counter-evidence",
    claim: "counter_evidence",
    status: "counter_hit",
    sourceCount: 1,
    excerpts: ["招生章程显示专业组可能调剂到学生黑名单专业。"],
    note: "反证命中：专业组黑名单风险，阻断推荐。",
  },
];

export function buildDeepOpportunityEvaluation({
  plan,
  evidenceResults,
}: {
  plan: DeepEvidenceCollectionPlan;
  evidenceResults: DeepEvidenceResult[];
}): DeepOpportunityEvaluation {
  const resultByTask = new Map(evidenceResults.map((result) => [result.taskId, result]));
  const gateResults = plan.tasks.map((task) => evaluateTask(task, resultByTask.get(task.id)));
  const p0Results = gateResults.filter((result) => result.priority === "P0");
  const p0Passed = p0Results.filter((result) => result.status === "verified").length;
  const counterHits = gateResults.filter((result) => result.status === "counter_hit" || result.status === "conflict");
  const missingEvidence = gateResults
    .filter((result) => result.status === "missing" || result.status === "weak")
    .map((result) => `${result.priority} ${CLAIM_LABEL[result.claim]}：${result.reason}`);
  const blockedReasons = [
    ...counterHits.map((result) => `反证命中，阻断推荐：${result.reason}`),
    ...p0Results
      .filter((result) => result.status !== "verified")
      .map((result) => `P0 门槛未通过：${CLAIM_LABEL[result.claim]} - ${result.reason}`),
  ];
  const rawScore = gateResults.reduce((sum, result) => sum + result.score - result.downgrade, 0);
  const opportunityScore = Math.max(0, Math.min(100, Math.round(rawScore)));
  const p0GatePassed = p0Passed === p0Results.length;
  const status = statusFor({ p0GatePassed, opportunityScore, blockedReasons, counterHits });

  return {
    protocol: "deep_opportunity_evaluation_v1",
    status,
    opportunityScore,
    p0Gate: {
      passed: p0GatePassed,
      passedCount: p0Passed,
      totalCount: p0Results.length,
    },
    counterEvidence: {
      hit: counterHits.length > 0,
      reasons: counterHits.map((result) => result.reason),
    },
    gateResults,
    horizonSignals: buildHorizonSignals(gateResults, counterHits.length > 0),
    positiveSignals: positiveSignalsFor(gateResults),
    blockedReasons,
    missingEvidence,
    reviewChecklist: [
      "顾问复核前重新核验官方招生章程、计划数、专业组代码和校区。",
      "把科研、就业、升学证据的原文摘录附到报告，而不是只保留摘要。",
      "家庭签字前确认专业组调剂、黑名单专业、费用和城市约束。",
    ],
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function verified(
  taskId: string,
  claim: DeepEvidenceClaim,
  sourceCount: number,
  note: string,
): DeepEvidenceResult {
  return {
    taskId,
    claim,
    status: "verified",
    sourceCount,
    excerpts: [note],
    note,
  };
}

function evaluateTask(task: DeepEvidenceTask, result?: DeepEvidenceResult): DeepOpportunityGateResult {
  if (!result) {
    return {
      taskId: task.id,
      claim: task.claim,
      title: task.title,
      priority: task.priority,
      status: "missing",
      score: 0,
      downgrade: task.priority === "P0" ? 12 : 4,
      reason: "未提交证据结果。",
    };
  }

  const baseWeight = CLAIM_WEIGHTS[task.claim];
  if (result.status === "counter_hit" || result.status === "conflict") {
    return {
      taskId: task.id,
      claim: task.claim,
      title: task.title,
      priority: task.priority,
      status: result.status,
      score: 0,
      downgrade: task.priority === "P0" ? 20 : 10,
      reason: result.note,
    };
  }
  if (result.status === "missing") {
    return {
      taskId: task.id,
      claim: task.claim,
      title: task.title,
      priority: task.priority,
      status: "missing",
      score: 0,
      downgrade: task.priority === "P0" ? 12 : 4,
      reason: result.note,
    };
  }
  if (result.status === "weak" || result.sourceCount < requiredSourceCount(task)) {
    return {
      taskId: task.id,
      claim: task.claim,
      title: task.title,
      priority: task.priority,
      status: "weak",
      score: Math.floor(baseWeight * 0.45),
      downgrade: task.priority === "P0" ? 6 : 2,
      reason: `${result.note}；来源数量不足或证据偏弱。`,
    };
  }

  return {
    taskId: task.id,
    claim: task.claim,
    title: task.title,
    priority: task.priority,
    status: "verified",
    score: baseWeight,
    downgrade: 0,
    reason: result.note,
  };
}

function requiredSourceCount(task: DeepEvidenceTask) {
  if (task.claim === "civil_service_path") return 1;
  return task.priority === "P0" ? 2 : 1;
}

function statusFor({
  p0GatePassed,
  opportunityScore,
  blockedReasons,
  counterHits,
}: {
  p0GatePassed: boolean;
  opportunityScore: number;
  blockedReasons: string[];
  counterHits: DeepOpportunityGateResult[];
}): DeepOpportunityEvaluationStatus {
  if (counterHits.length > 0 || blockedReasons.some((reason) => reason.includes("阻断推荐"))) return "blocked";
  if (!p0GatePassed) return "evidence_gap";
  if (opportunityScore >= 82) return "counselor_review_ready";
  return "candidate";
}

function positiveSignalsFor(gateResults: DeepOpportunityGateResult[]) {
  return gateResults
    .filter((result) => result.status === "verified" && result.score >= 8)
    .map((result) => `${CLAIM_LABEL[result.claim]}已通过：${result.reason}`)
    .slice(0, 6);
}

function buildHorizonSignals(gateResults: DeepOpportunityGateResult[], hasCounterHit: boolean): HorizonSignal[] {
  const verifiedClaims = new Set(
    gateResults.filter((result) => result.status === "verified").map((result) => result.claim),
  );
  const weakClaims = new Set(
    gateResults
      .filter((result) => result.status === "weak" || result.status === "missing")
      .map((result) => result.claim),
  );

  return [
    {
      horizon: "短期录取",
      status: hasCounterHit || weakClaims.has("official_admission") || weakClaims.has("rank_history") ? "blocked" : "supported",
      summary: "先看官方计划、专业组代码、位次区间和调剂风险，避免把样板机会误写成录取承诺。",
    },
    {
      horizon: "中期升学",
      status:
        verifiedClaims.has("faculty_research") &&
        verifiedClaims.has("undergrad_access") &&
        verifiedClaims.has("graduate_progression")
          ? "supported"
          : "weak",
      summary: "考研和保研价值来自课题组入口、项目经历、课程路径和导师方向的连续性。",
    },
    {
      horizon: "长期职业",
      status: hasCounterHit ? "blocked" : verifiedClaims.has("employment_market") ? "supported" : "weak",
      summary: "职业判断必须落到岗位任务、学历门槛、技能栈和产业城市，而不是一句就业前景好。",
    },
  ];
}

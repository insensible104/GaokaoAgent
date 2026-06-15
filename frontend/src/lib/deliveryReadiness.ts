export type DeliveryGateStatus = "ready" | "needs_review" | "blocked";

export interface DeliveryReadinessGate {
  id: "data_boundary" | "plan_structure" | "evidence_pack" | "report_package" | "human_review";
  label: string;
  status: DeliveryGateStatus;
  signal: string;
  action: string;
}

export interface DeliveryReadinessSummary {
  status: DeliveryGateStatus;
  score: number;
  gates: DeliveryReadinessGate[];
  claimBoundary: string;
  nextAction: string;
}

export interface DeliveryReadinessGameMatrix {
  major_group_rows?: unknown[];
  rows?: unknown[];
  data_vintage?: {
    formal_recommendation_ready?: boolean;
    limitations?: string[];
  } | null;
  volunteer_plan?: {
    choices?: Array<{
      quant_evidence?: string[];
    }>;
    key_prefix_count?: number;
    shadowed_choice_count?: number;
    blacklist_violation_count?: number;
  } | null;
  plan_audit_summary?: {
    status?: string;
    coverage?: {
      coverage_sufficient?: boolean;
      deficits?: Record<string, number>;
    };
    data_boundary?: {
      formal_recommendation_ready?: boolean;
      limitations?: string[];
    };
    student_facing_items?: Array<{
      severity?: string;
      title?: string;
      detail?: string;
      type?: string;
    }>;
  } | null;
}

export interface DeliveryReadinessInput {
  gameMatrix?: DeliveryReadinessGameMatrix | null;
  deliveryProfile?: {
    score?: number;
    rank?: number;
    subject_group?: string;
  } | null;
  report?: string | null;
}

const CLAIM_BOUNDARY = "交付准备度是运营复核信号，不是录取承诺，也不是2026结果有效性的实验证据。";

const gateScore: Record<DeliveryGateStatus, number> = {
  ready: 1,
  needs_review: 0.55,
  blocked: 0,
};

function hasDeficit(deficits?: Record<string, number>) {
  return Object.values(deficits ?? {}).some((value) => Number(value || 0) > 0);
}

function summarizeOverall(gates: DeliveryReadinessGate[]): DeliveryGateStatus {
  if (gates.some((gate) => gate.status === "blocked")) return "blocked";
  if (gates.some((gate) => gate.status === "needs_review")) return "needs_review";
  return "ready";
}

export function buildDeliveryReadinessSummary(input: DeliveryReadinessInput): DeliveryReadinessSummary {
  const gameMatrix = input.gameMatrix;
  const audit = gameMatrix?.plan_audit_summary;
  const plan = gameMatrix?.volunteer_plan;
  const dataBoundary = audit?.data_boundary ?? gameMatrix?.data_vintage;
  const limitations = dataBoundary?.limitations ?? [];
  const formalReady = dataBoundary?.formal_recommendation_ready === true;
  const coverageSufficient = audit?.coverage?.coverage_sufficient !== false && !hasDeficit(audit?.coverage?.deficits);
  const hasPlanRows = Boolean((plan?.choices?.length ?? 0) || (gameMatrix?.major_group_rows?.length ?? 0) || (gameMatrix?.rows?.length ?? 0));
  const hasEvidence = Boolean(
    audit || plan?.choices?.some((choice) => (choice.quant_evidence?.length ?? 0) > 0),
  );
  const gates: DeliveryReadinessGate[] = [
    {
      id: "data_boundary",
      label: "数据年份",
      status: formalReady ? "ready" : "blocked",
      signal: formalReady ? "当前年份正式数据可用" : limitations[0] ?? "2026正式数据尚未完全就绪",
      action: formalReady ? "保留数据来源记录" : "正式交付前必须复核招生计划、位次表、章程和考试院公告",
    },
    {
      id: "plan_structure",
      label: "志愿结构",
      status:
        !hasPlanRows || (plan?.blacklist_violation_count ?? 0) > 0
          ? "blocked"
          : coverageSufficient && (plan?.key_prefix_count ?? 0) > 0
            ? "ready"
            : "needs_review",
      signal:
        (plan?.blacklist_violation_count ?? 0) > 0
          ? "存在硬边界或黑名单冲突"
          : coverageSufficient
            ? `关键前缀 ${plan?.key_prefix_count ?? 0} 行，遮蔽 ${plan?.shadowed_choice_count ?? 0} 行`
            : "冲稳保覆盖仍有缺口",
      action: coverageSufficient ? "检查关键前缀解释是否可读" : "补齐冲稳保结构或标注人工接受的缺口",
    },
    {
      id: "evidence_pack",
      label: "证据包",
      status: hasEvidence ? "ready" : "needs_review",
      signal: hasEvidence ? "已附带审计摘要或量化证据" : "缺少可追踪审计摘要",
      action: hasEvidence ? "保留证据账本和口径边界" : "补充结构审计摘要或量化证据",
    },
    {
      id: "report_package",
      label: "报告包",
      status: input.report || hasPlanRows ? "needs_review" : "blocked",
      signal: input.report ? "已生成报告正文，可进入交付预览" : "仅有结构化数据，报告正文待补",
      action: "打开报告预览，检查证据账本、风险账本和措辞边界",
    },
    {
      id: "human_review",
      label: "人工复核",
      status: "needs_review",
      signal: "正式交付前必须复核当前年份官方文件",
      action: "顾问确认章程、体检、单科、调剂和家庭风险接受记录",
    },
  ];
  const status = summarizeOverall(gates);
  const score = Math.round((gates.reduce((sum, gate) => sum + gateScore[gate.status], 0) / gates.length) * 100);
  const nextAction =
    gates.find((gate) => gate.status === "blocked")?.action ??
    gates.find((gate) => gate.status === "needs_review")?.action ??
    "交付 gate 已通过，保留审计证据后再发送。";
  return {
    status,
    score,
    gates,
    claimBoundary: CLAIM_BOUNDARY,
    nextAction,
  };
}

import type { EvidenceAutopilotSearchTask } from "./evidenceAutopilot";

export type EvidenceAutopilotProviderChannel =
  | "public_web"
  | "official_pdf"
  | "wechat_operator"
  | "job_market_operator"
  | "manual_review";

export interface EvidenceAutopilotProviderRequest {
  requestId: string;
  taskId: string;
  targetLabel: string;
  channel: EvidenceAutopilotProviderChannel;
  query: string;
  requiredFields: string[];
  maxResults: number;
}

export interface EvidenceAutopilotProviderResult {
  requestId: string;
  taskId: string;
  sourceTitle: string;
  sourceUrl: string;
  sourceType: "official" | "school" | "paper" | "job" | "wechat" | "discussion" | "other";
  excerpt: string;
  capturedAt: string;
  confidence: "high" | "medium" | "low";
}

export interface EvidenceAutopilotProvider {
  id: string;
  search(request: EvidenceAutopilotProviderRequest): Promise<EvidenceAutopilotProviderResult[]>;
}

export interface EvidenceAutopilotOperatorReviewTask {
  requestId: string;
  taskId: string;
  targetLabel: string;
  channel: EvidenceAutopilotProviderChannel;
  query: string;
  requiredFields: string[];
  reviewOnly: true;
  reason: string;
}

export function buildEvidenceAutopilotProviderRequest({
  requestId,
  targetLabel,
  task,
  maxResults = 5,
}: {
  requestId: string;
  targetLabel: string;
  task: EvidenceAutopilotSearchTask;
  maxResults?: number;
}): EvidenceAutopilotProviderRequest {
  return {
    requestId,
    taskId: task.taskId,
    targetLabel,
    channel: task.channel,
    query: task.query,
    requiredFields: task.requiredFields,
    maxResults,
  };
}

export function buildEvidenceAutopilotOperatorReviewTask(
  request: EvidenceAutopilotProviderRequest,
): EvidenceAutopilotOperatorReviewTask {
  return {
    requestId: request.requestId,
    taskId: request.taskId,
    targetLabel: request.targetLabel,
    channel: request.channel,
    query: request.query,
    requiredFields: request.requiredFields,
    reviewOnly: true,
    reason: "半封闭或人工复核渠道需要人工采集原文、链接或截图编号后，才能进入证据归一化。",
  };
}

export function isOperatorOnlyChannel(channel: EvidenceAutopilotProviderChannel): boolean {
  return channel === "wechat_operator" || channel === "job_market_operator" || channel === "manual_review";
}

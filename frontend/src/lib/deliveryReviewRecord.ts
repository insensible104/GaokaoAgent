import {
  buildCounselorDeliveryChecklist,
  type CounselorChecklistStatus,
  type CounselorDeliveryChecklistInput,
  type CounselorDeliveryChecklistItem,
} from "./counselorDeliveryChecklist";

export interface DeliveryReviewRecordSnapshot {
  protocol: "delivery_review_record_v1";
  kind: "review_record";
  versionStamp: string;
  status: CounselorChecklistStatus;
  leadAction: string;
  blockedItems: CounselorDeliveryChecklistItem[];
  reviewItems: CounselorDeliveryChecklistItem[];
  readyItems: CounselorDeliveryChecklistItem[];
  metrics: {
    blocked_items: number;
    review_items: number;
    ready_items: number;
  };
  copyText: string;
  claimBoundary: string;
}

export interface DeliveryReviewRecordInput extends CounselorDeliveryChecklistInput {
  generatedAt?: string | Date;
  operatorName?: string;
}

export const DELIVERY_REVIEW_RECORD_BOUNDARY =
  "交付复核记录只保存当前证据快照，不生成新的录取结论，不替代签字确认。";

export function buildDeliveryReviewRecord(input: DeliveryReviewRecordInput): DeliveryReviewRecordSnapshot {
  const checklist = buildCounselorDeliveryChecklist(input);
  const versionStamp = formatVersionStamp(input.generatedAt ?? new Date());
  const blockedItems = checklist.items.filter((item) => item.status === "blocked");
  const reviewItems = checklist.items.filter((item) => item.status === "needs_review");
  const readyItems = checklist.items.filter((item) => item.status === "ready");
  const copyText = buildCopyText({
    versionStamp,
    operatorName: input.operatorName,
    status: checklist.status,
    leadAction: checklist.leadAction,
    blockedItems,
    reviewItems,
    readyItems,
  });

  return {
    protocol: "delivery_review_record_v1",
    kind: "review_record",
    versionStamp,
    status: checklist.status,
    leadAction: checklist.leadAction,
    blockedItems,
    reviewItems,
    readyItems,
    metrics: {
      blocked_items: blockedItems.length,
      review_items: reviewItems.length,
      ready_items: readyItems.length,
    },
    copyText,
    claimBoundary: DELIVERY_REVIEW_RECORD_BOUNDARY,
  };
}

function buildCopyText({
  versionStamp,
  operatorName,
  status,
  leadAction,
  blockedItems,
  reviewItems,
  readyItems,
}: {
  versionStamp: string;
  operatorName?: string;
  status: CounselorChecklistStatus;
  leadAction: string;
  blockedItems: CounselorDeliveryChecklistItem[];
  reviewItems: CounselorDeliveryChecklistItem[];
  readyItems: CounselorDeliveryChecklistItem[];
}) {
  return [
    `# PathFinder 交付复核记录`,
    `版本快照：${versionStamp}`,
    `复核人：${operatorName?.trim() || "未填写"}`,
    `交付状态：${status}`,
    `下一步动作：${leadAction}`,
    "",
    renderRecordSection("阻断项", blockedItems),
    renderRecordSection("待复核项", reviewItems),
    renderRecordSection("已就绪项", readyItems),
    "",
    `证据边界：${DELIVERY_REVIEW_RECORD_BOUNDARY}`,
  ].join("\n");
}

function renderRecordSection(title: string, items: CounselorDeliveryChecklistItem[]) {
  if (items.length === 0) {
    return `## ${title}\n- 无`;
  }
  return [
    `## ${title}`,
    ...items.map((item) => `- ${item.label}｜负责人：${item.owner}｜证据：${item.evidence}｜动作：${item.action}`),
  ].join("\n");
}

function formatVersionStamp(value: string | Date) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "invalid-date";
  }
  const pad = (item: number) => item.toString().padStart(2, "0");
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
    "-",
    pad(date.getHours()),
    pad(date.getMinutes()),
  ].join("");
}

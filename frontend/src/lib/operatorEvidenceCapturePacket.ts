import type {
  OperatorEvidenceCaptureStatus,
  OperatorEvidenceCaptureWorkItem,
  OperatorEvidenceCaptureWorklist,
} from "./operatorEvidenceCaptureWorklist";
import type {
  OperatorReviewedEvidenceCaptureInput,
  ReviewedEvidenceAttachmentKind,
  ReviewedEvidenceReviewerIdentity,
  ReviewedEvidenceRedactionChecklist,
} from "./evidenceAutopilotApi";
import type { EvidenceAutopilotProviderResult } from "./evidenceAutopilotProvider";

export interface OperatorEvidenceCapturePacket {
  protocol: "operator_evidence_capture_packet_v1";
  caseId: string;
  targetLabel: string;
  status: "clear" | "ready_to_capture" | "blocked";
  workflowFunction: "captureAndSubmitOperatorReviewedEvidence";
  totalItems: number;
  blockingItemCount: number;
  operatorRules: string[];
  items: OperatorEvidenceCapturePacketItem[];
  claimBoundary: string;
}

export interface OperatorEvidenceCapturePacketItem {
  taskId: string;
  claim: string;
  title: string;
  priority: string;
  blocking: boolean;
  captureStatus: OperatorEvidenceCaptureStatus;
  sourceType: EvidenceAutopilotProviderResult["sourceType"];
  captureBrief: string;
  searchPrompts: string[];
  requiredOutputFields: string[];
  requiredAttachmentKinds: ReviewedEvidenceAttachmentKind[];
  redactionChecklist: string[];
  rejectionRules: string[];
  submissionTemplate: OperatorReviewedEvidenceCaptureInput;
}

export interface OperatorEvidenceCapturePacketFillInput {
  packet: OperatorEvidenceCapturePacket;
  item: OperatorEvidenceCapturePacketItem;
  reviewer: ReviewedEvidenceReviewerIdentity;
  sourceTitle: string;
  excerpt: string;
  capturedAt: string;
  contentType: string;
  contentBase64: string;
  originalFileName?: string;
  redactionChecklist: ReviewedEvidenceRedactionChecklist;
}

const WORKFLOW_FUNCTION = "captureAndSubmitOperatorReviewedEvidence";

const OPERATOR_RULES = [
  "Do not scrape or bypass login, paywall, anti-bot, or platform access limits.",
  "Use only evidence the reviewer can personally view and capture.",
  "Upload at least one screenshot, page capture, PDF, or image attachment for every operator-reviewed card.",
  "Complete the redaction checklist before submitting redacted evidence.",
  "Do not claim admission, graduate-school, employment, or civil-service outcomes from operator evidence alone.",
];

const REDACTION_CHECKLIST = [
  "Student personal information removed or absent.",
  "Private phone, email, WeChat, QQ, and address information removed or absent.",
  "Account identifiers and private profile handles removed or absent.",
  "Third-party personal information removed or absent.",
  "Reviewer confirms the final attachment matches the redaction status.",
];

export function buildOperatorEvidenceCapturePacket({
  worklist,
}: {
  worklist: OperatorEvidenceCaptureWorklist;
}): OperatorEvidenceCapturePacket {
  const items = worklist.items.map((item) => toPacketItem(worklist, item));
  return {
    protocol: "operator_evidence_capture_packet_v1",
    caseId: worklist.caseId,
    targetLabel: worklist.targetLabel,
    status: items.length === 0 ? "clear" : worklist.blockingItemCount > 0 ? "blocked" : "ready_to_capture",
    workflowFunction: WORKFLOW_FUNCTION,
    totalItems: worklist.totalItems,
    blockingItemCount: worklist.blockingItemCount,
    operatorRules: OPERATOR_RULES,
    items,
    claimBoundary:
      "Operator evidence capture packet only organizes human capture instructions and submission templates; it does not collect evidence, bypass platform limits, validate visual redaction, or prove admission/employment outcomes.",
  };
}

export function fillOperatorEvidenceCapturePacketItem({
  packet,
  item,
  reviewer,
  sourceTitle,
  excerpt,
  capturedAt,
  contentType,
  contentBase64,
  originalFileName,
  redactionChecklist,
}: OperatorEvidenceCapturePacketFillInput): OperatorReviewedEvidenceCaptureInput {
  assertNonEmpty(reviewer.reviewerId, "reviewerId");
  assertNonEmpty(reviewer.displayName, "reviewer displayName");
  assertNonEmpty(sourceTitle, "sourceTitle");
  assertNonEmpty(excerpt, "excerpt");
  assertNonEmpty(capturedAt, "capturedAt");
  assertNonEmpty(contentType, "contentType");
  assertNonEmpty(contentBase64, "contentBase64");
  assertCompleteRedactionChecklist(redactionChecklist);

  return {
    targetLabel: packet.targetLabel,
    caseId: packet.caseId,
    reviewer: reviewer.reviewerId,
    attachmentPayload: {
      ...item.submissionTemplate.attachmentPayload,
      reviewerId: reviewer.reviewerId,
      contentType: contentType.trim(),
      contentBase64: contentBase64.trim(),
      capturedAt: capturedAt.trim(),
      originalFileName,
      redactionStatus: "redacted",
      redactionChecklist,
    },
    card: {
      ...item.submissionTemplate.card,
      sourceTitle: sourceTitle.trim(),
      excerpt: excerpt.trim(),
      capturedAt: capturedAt.trim(),
      redactionStatus: "redacted",
      reviewerIdentity: reviewer,
    },
  };
}

function toPacketItem(
  worklist: OperatorEvidenceCaptureWorklist,
  item: OperatorEvidenceCaptureWorkItem,
): OperatorEvidenceCapturePacketItem {
  const sourceType = sourceTypeForClaim(item.claim);
  return {
    taskId: item.taskId,
    claim: item.claim,
    title: item.title,
    priority: item.priority,
    blocking: item.blocking,
    captureStatus: item.captureStatus,
    sourceType,
    captureBrief: captureBriefFor(item),
    searchPrompts: searchPromptsFor(worklist, item),
    requiredOutputFields: item.outputFields,
    requiredAttachmentKinds: item.requiredAttachmentKinds as ReviewedEvidenceAttachmentKind[],
    redactionChecklist: REDACTION_CHECKLIST,
    rejectionRules: rejectionRulesFor(item.claim),
    submissionTemplate: buildSubmissionTemplate(worklist, item, sourceType),
  };
}

function buildSubmissionTemplate(
  worklist: OperatorEvidenceCaptureWorklist,
  item: OperatorEvidenceCaptureWorkItem,
  sourceType: EvidenceAutopilotProviderResult["sourceType"],
): OperatorReviewedEvidenceCaptureInput {
  return {
    targetLabel: worklist.targetLabel,
    caseId: worklist.caseId,
    reviewer: "",
    attachmentPayload: {
      caseId: worklist.caseId,
      taskId: item.taskId,
      reviewerId: "",
      kind: "screenshot",
      contentType: "",
      contentBase64: "",
      capturedAt: "",
      redactionStatus: "redacted",
      redactionChecklist: emptyRedactionChecklist(),
    },
    card: {
      taskId: item.taskId,
      claim: item.claim,
      sourceTitle: "",
      sourceType,
      excerpt: "",
      capturedAt: "",
      confidence: "medium",
      reviewAction: item.reviewAction,
      redactionStatus: "redacted",
      reviewerIdentity: {
        reviewerId: "",
        displayName: "",
        role: "operator",
      },
    },
  };
}

function emptyRedactionChecklist(): ReviewedEvidenceRedactionChecklist {
  return {
    studentPersonalInfoRemoved: false,
    privateContactInfoRemoved: false,
    accountIdentifiersRemoved: false,
    thirdPartyPersonalInfoRemoved: false,
    reviewerConfirmed: false,
  };
}

function sourceTypeForClaim(claim: string): EvidenceAutopilotProviderResult["sourceType"] {
  if (claim === "employment_market") return "job";
  if (claim === "wechat_public_account") return "wechat";
  if (claim === "counter_evidence") return "discussion";
  return "other";
}

function captureBriefFor(item: OperatorEvidenceCaptureWorkItem): string {
  if (item.claim === "employment_market") {
    return "Capture a recent public job listing or public recruiting page that can support or weaken the employment-market claim.";
  }
  if (item.claim === "wechat_public_account") {
    return "Capture a public account article or public school/department post that the reviewer can open and cite.";
  }
  if (item.claim === "counter_evidence") {
    return "Capture public counter-evidence, complaint, policy conflict, or explicit evidence gap that could weaken the opportunity hypothesis.";
  }
  return `Capture reviewable public evidence for ${item.title}.`;
}

function searchPromptsFor(
  worklist: OperatorEvidenceCaptureWorklist,
  item: OperatorEvidenceCaptureWorkItem,
): string[] {
  const base = `${worklist.targetLabel} ${item.title}`;
  if (item.claim === "employment_market") {
    return [
      `${base} job listing skills city education requirement`,
      `${worklist.targetLabel} 智能制造 数据工程 招聘 岗位 技能`,
    ];
  }
  if (item.claim === "wechat_public_account") {
    return [
      `${base} public account article school department`,
      `${worklist.targetLabel} 公众号 文章 学院 专业 培养`,
    ];
  }
  if (item.claim === "counter_evidence") {
    return [
      `${base} complaint risk policy conflict`,
      `${worklist.targetLabel} 投诉 风险 调剂 争议 反证`,
    ];
  }
  return [base];
}

function rejectionRulesFor(claim: string): string[] {
  const shared = [
    "Reject evidence with no source title, no URL/review ID, or no excerpt.",
    "Reject screenshots containing private personal information unless redacted and checklist-confirmed.",
    "Reject content that the reviewer cannot personally reopen or explain.",
  ];
  if (claim === "employment_market") {
    return [
      ...shared,
      "Reject private chat, recruiter DM, or unverifiable private job-market claims.",
      "Reject stale job listings when capture time or current availability cannot be explained.",
    ];
  }
  if (claim === "wechat_public_account") {
    return [
      ...shared,
      "Reject login-only, friend-only, deleted, or non-public public-account material.",
      "Reject reposts that do not identify the original publisher or article date.",
    ];
  }
  if (claim === "counter_evidence") {
    return [
      ...shared,
      "Reject isolated sentiment with no concrete risk, policy conflict, complaint, or disconfirming fact.",
    ];
  }
  return shared;
}

function assertNonEmpty(value: string | undefined, field: string): void {
  if (!value?.trim()) {
    throw new Error(`operator evidence capture packet requires ${field}`);
  }
}

function assertCompleteRedactionChecklist(checklist: ReviewedEvidenceRedactionChecklist): void {
  for (const field of [
    "studentPersonalInfoRemoved",
    "privateContactInfoRemoved",
    "accountIdentifiersRemoved",
    "thirdPartyPersonalInfoRemoved",
    "reviewerConfirmed",
  ] as const) {
    if (checklist[field] !== true) {
      throw new Error(`operator evidence capture packet requires completed redaction checklist: ${field}`);
    }
  }
}

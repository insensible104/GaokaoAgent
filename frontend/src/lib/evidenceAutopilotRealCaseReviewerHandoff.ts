import type { DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { ReviewedEvidenceRecord } from "./evidenceAutopilotApi";
import type { EvidenceAutopilotRealCaseFixture } from "./evidenceAutopilotRealCaseProvider";
import {
  bootstrapRealCaseReviewedEvidenceLedger,
  type RealCaseReviewedEvidenceLedgerBootstrapResult,
} from "./evidenceAutopilotRealCaseLedgerBootstrap";
import {
  buildOperatorEvidenceCapturePacket,
  type OperatorEvidenceCapturePacket,
} from "./operatorEvidenceCapturePacket";
import {
  buildOperatorEvidenceCaptureWorklist,
} from "./operatorEvidenceCaptureWorklist";

type FetchLike = Parameters<typeof bootstrapRealCaseReviewedEvidenceLedger>[0]["fetchImpl"];

export interface RealCaseReviewerHandoff {
  protocol: "real_case_reviewer_handoff_v1";
  caseId: string;
  targetLabel: string;
  status: "clear" | "blocked_by_operator_capture";
  familyFacingAllowed: boolean;
  openTaskIds: string[];
  capturePacket: OperatorEvidenceCapturePacket;
  execution: {
    workflowFunction: "executeRealCaseOperatorClosureWorkflow";
    inputContract: "OperatorReviewedEvidenceCaptureInput";
    expectedStatusAfterValidCapture: "requires_counter_evidence_review" | "ready_for_counselor_review";
    notes: string[];
  };
  reviewerChecklist: string[];
  claimBoundary: string;
}

export interface RealCaseReviewerHandoffBriefSection {
  title: string;
  bullets: string[];
}

export interface RealCaseReviewerHandoffBrief {
  protocol: "real_case_reviewer_handoff_brief_v1";
  caseId: string;
  title: string;
  familyFacingAllowed: boolean;
  sections: RealCaseReviewerHandoffBriefSection[];
  markdown: string;
  claimBoundary: string;
}

export interface RealCaseReviewerHandoffBootstrapResult {
  protocol: "real_case_reviewer_handoff_bootstrap_v1";
  caseId: string;
  publicBootstrap: RealCaseReviewedEvidenceLedgerBootstrapResult;
  handoff: RealCaseReviewerHandoff;
  brief: RealCaseReviewerHandoffBrief;
  claimBoundary: string;
}

export async function bootstrapRealCaseReviewerHandoff({
  fixture,
  caseId,
  plan,
  fetchImpl,
}: {
  fixture: EvidenceAutopilotRealCaseFixture;
  caseId: string;
  plan: DeepEvidenceCollectionPlan;
  fetchImpl?: FetchLike;
}): Promise<RealCaseReviewerHandoffBootstrapResult> {
  if (fixture.caseId !== caseId) {
    throw new Error("real case reviewer handoff bootstrap requires matching caseId");
  }

  const publicBootstrap = await bootstrapRealCaseReviewedEvidenceLedger({
    fixture,
    caseId,
    plan,
    fetchImpl,
  });
  const handoff = buildRealCaseReviewerHandoff({
    fixture,
    caseId,
    plan,
    records: publicBootstrap.listing.records,
  });
  const brief = buildRealCaseReviewerHandoffBrief(handoff);

  return {
    protocol: "real_case_reviewer_handoff_bootstrap_v1",
    caseId,
    publicBootstrap,
    handoff,
    brief,
    claimBoundary:
      "Real Case reviewer handoff bootstrap submits reviewed public fixture evidence and prepares an internal reviewer work order; it does not prove admission probability, does not prove employment outcomes, and does not replace source freshness or counselor review.",
  };
}

export function buildRealCaseReviewerHandoff({
  fixture,
  caseId,
  plan,
  records,
}: {
  fixture: EvidenceAutopilotRealCaseFixture;
  caseId: string;
  plan: DeepEvidenceCollectionPlan;
  records: ReviewedEvidenceRecord[];
}): RealCaseReviewerHandoff {
  if (fixture.caseId !== caseId) {
    throw new Error("real case reviewer handoff requires matching caseId");
  }

  const worklist = buildOperatorEvidenceCaptureWorklist({
    caseId,
    plan,
    records,
  });
  const capturePacket = buildOperatorEvidenceCapturePacket({ worklist });
  const openTaskIds = capturePacket.items.map((item) => item.taskId);

  return {
    protocol: "real_case_reviewer_handoff_v1",
    caseId,
    targetLabel: plan.targetLabel,
    status: openTaskIds.length > 0 ? "blocked_by_operator_capture" : "clear",
    familyFacingAllowed: false,
    openTaskIds,
    capturePacket,
    execution: {
      workflowFunction: "executeRealCaseOperatorClosureWorkflow",
      inputContract: "OperatorReviewedEvidenceCaptureInput",
      expectedStatusAfterValidCapture: "requires_counter_evidence_review",
      notes: [
        "Fill one capture packet item into OperatorReviewedEvidenceCaptureInput before execution.",
        "After execution, ledger records are deduplicated by reviewId before readiness recomputation.",
        "A cleared operator capture gate still requires counselor review for counter-evidence and source freshness.",
      ],
    },
    reviewerChecklist: [
      "Capture only a source the reviewer can personally view and explain.",
      "Reject private chats, recruiter DMs, or unverifiable employment-market claims.",
      "Complete attachment upload and redaction checklist before ledger submission.",
      "Record source freshness and why the source supports or weakens the employment-market claim.",
      "Do not write family-facing opportunity language until the closure review and counselor review both allow it.",
    ],
    claimBoundary:
      "Real Case reviewer handoff organizes internal operator capture and closure workflow only; it does not prove admission probability, does not prove employment outcomes, does not prove source freshness, and is not a family-facing recommendation.",
  };
}

export function buildRealCaseReviewerHandoffBrief(
  handoff: RealCaseReviewerHandoff,
): RealCaseReviewerHandoffBrief {
  if (handoff.protocol !== "real_case_reviewer_handoff_v1") {
    throw new Error("real case reviewer handoff brief requires real_case_reviewer_handoff_v1");
  }

  const sections: RealCaseReviewerHandoffBriefSection[] = [
    {
      title: "待补证据",
      bullets: handoff.capturePacket.items.map((item) =>
        `${item.taskId}：${item.captureBrief}；必填字段：${item.requiredOutputFields.join(", ")}`,
      ),
    },
    {
      title: "执行合同",
      bullets: [
        `workflow：${handoff.execution.workflowFunction}`,
        `input：${handoff.execution.inputContract}`,
        `valid capture 后预期状态：${handoff.execution.expectedStatusAfterValidCapture}`,
        ...handoff.execution.notes,
      ],
    },
    {
      title: "拒收规则",
      bullets: unique(handoff.capturePacket.items.flatMap((item) => item.rejectionRules)),
    },
    {
      title: "复核清单",
      bullets: handoff.reviewerChecklist,
    },
    {
      title: "边界",
      bullets: [
        "不证明录取概率。",
        "不证明就业结果。",
        "不证明来源新鲜度或代表性。",
        "不是家庭端推荐结论。",
      ],
    },
  ];
  const title = `内部 reviewer handoff：${handoff.targetLabel}`;
  return {
    protocol: "real_case_reviewer_handoff_brief_v1",
    caseId: handoff.caseId,
    title,
    familyFacingAllowed: false,
    sections,
    markdown: toMarkdown(title, sections),
    claimBoundary:
      "Real Case reviewer handoff brief is an internal work order for evidence capture and closure execution only; it does not prove admission probability, does not prove employment outcomes, and is not a family-facing recommendation.",
  };
}

function toMarkdown(
  title: string,
  sections: RealCaseReviewerHandoffBriefSection[],
): string {
  return [
    `# ${title}`,
    "",
    ...sections.flatMap((section) => [
      `## ${section.title}`,
      ...section.bullets.map((bullet) => `- ${bullet}`),
      "",
    ]),
  ].join("\n").trim();
}

function unique(values: string[]): string[] {
  return [...new Set(values.filter((value) => value.trim()))];
}

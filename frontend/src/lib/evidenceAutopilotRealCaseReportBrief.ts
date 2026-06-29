import type {
  RealCaseOpportunityAuditPacket,
  RealCaseOpportunityAuditStatus,
} from "./evidenceAutopilotRealCaseAuditPacket";

export interface RealCaseOpportunityReportBriefSection {
  title: string;
  bullets: string[];
}

export interface RealCaseOpportunityReportBrief {
  protocol: "real_case_opportunity_report_brief_v1";
  caseId: string;
  targetLabel: string;
  status: RealCaseOpportunityAuditStatus;
  statusLabel: string;
  briefTitle: string;
  familyFacingAllowed: boolean;
  sections: RealCaseOpportunityReportBriefSection[];
  claimBoundary: string;
}

export function buildRealCaseOpportunityReportBrief(
  packet: RealCaseOpportunityAuditPacket,
): RealCaseOpportunityReportBrief {
  if (packet.protocol !== "real_case_opportunity_audit_packet_v1") {
    throw new Error("real case report brief requires a real_case_opportunity_audit_packet_v1 audit packet");
  }

  const familyFacingAllowed = packet.status === "ready_for_counselor_review";

  return {
    protocol: "real_case_opportunity_report_brief_v1",
    caseId: packet.caseId,
    targetLabel: packet.targetLabel,
    status: packet.status,
    statusLabel: statusLabelFor(packet.status),
    briefTitle: `内部审计 brief：${packet.targetLabel}`,
    familyFacingAllowed,
    sections: [
      {
        title: "已审证据",
        bullets: packet.supportedClaims.map((claim) =>
          `${claim.taskId}：${claim.title}；${claim.sourceCount} 条可追溯证据；来源：${claim.sourceTitles.join("、") || "未列出"}`,
        ),
      },
      {
        title: "阻塞缺口",
        bullets: packet.blockingGaps.length > 0
          ? packet.blockingGaps.map((gap) => `${gap.taskId}：${gap.reason}`)
          : ["暂无 P0 阻塞缺口；仍需人工复核来源新鲜度和口径。"],
      },
      {
        title: "反证复核",
        bullets: counterEvidenceBullets(packet),
      },
      {
        title: "下一步",
        bullets: packet.nextActions,
      },
    ],
    claimBoundary:
      "本 brief 只说明单案例、已审证据和缺口状态；不证明录取概率，不证明就业结果，不证明来源仍然最新，不证明学生适配度，也不替代高报顾问复核。",
  };
}

function statusLabelFor(status: RealCaseOpportunityAuditStatus): string {
  if (status === "blocked_by_p0_gaps") {
    return "暂不进入家庭版报告：仍有 P0 证据缺口";
  }
  if (status === "requires_counter_evidence_review") {
    return "暂不进入家庭版报告：反证需要顾问复核";
  }
  return "可进入顾问复核：仍需人工确认口径";
}

function counterEvidenceBullets(packet: RealCaseOpportunityAuditPacket): string[] {
  if (!packet.counterEvidence.requiresCounselorReview) {
    return ["暂无已审反证记录；仍需保留反证检索步骤。"];
  }
  return packet.counterEvidence.records.map((record) =>
    `${record.taskId}：${record.sourceTitle}；动作：${record.reviewAction}；摘录：${record.excerpt}`,
  );
}

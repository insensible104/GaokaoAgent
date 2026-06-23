import realCaseFixture from "../../../data/evidence_autopilot/real_case_v0.json";
import type { EvidenceAutopilotProviderResult } from "./evidenceAutopilotProvider";

export interface EvidenceAutopilotRealCaseFixture {
  caseId: string;
  candidate: {
    province: string;
    targetYear: number;
    score: number | null;
    rank: number | null;
    subjectTrack: string;
  };
  target: {
    schoolName: string;
    majorName: string;
  };
  opportunityHypothesis: string;
  claimBoundary: string;
  evidenceCards: EvidenceAutopilotRealCaseCard[];
}

export interface EvidenceAutopilotRealCaseCard {
  taskId: string;
  claim: string;
  status: "captured_candidate" | "requires_capture" | "operator_review";
  sourceTitle: string;
  sourceUrl: string;
  sourceType: EvidenceAutopilotProviderResult["sourceType"];
  excerpt: string;
  capturedAt: string;
  confidence: EvidenceAutopilotProviderResult["confidence"];
  reviewAction: string;
}

export function loadEvidenceAutopilotRealCaseFixture(): EvidenceAutopilotRealCaseFixture {
  return realCaseFixture as EvidenceAutopilotRealCaseFixture;
}

export function buildEvidenceAutopilotRealCaseProviderResults(
  fixture: EvidenceAutopilotRealCaseFixture = loadEvidenceAutopilotRealCaseFixture(),
): EvidenceAutopilotProviderResult[] {
  return fixture.evidenceCards
    .filter((card) => card.status === "captured_candidate" && card.sourceUrl.trim() && card.excerpt.trim())
    .map((card, index) => ({
      requestId: `real-case-v0-${index + 1}`,
      taskId: card.taskId,
      sourceTitle: card.sourceTitle,
      sourceUrl: card.sourceUrl,
      sourceType: card.sourceType,
      excerpt: card.excerpt,
      capturedAt: card.capturedAt,
      confidence: card.confidence,
    }));
}

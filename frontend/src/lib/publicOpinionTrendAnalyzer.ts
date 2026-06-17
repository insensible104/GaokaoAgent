import type { PublicOpinionTrendSignal, TrendSourceKind } from "./opportunityDiscoveryEngine";

export interface PublicOpinionObservation {
  id: string;
  sourceKind: TrendSourceKind;
  title: string;
  capturedAt: string;
  text: string;
}

export interface PublicOpinionTrendAnalyzerInput {
  targetYear: number;
  province: string;
  schoolCode?: string;
  schoolName: string;
  majorKeywords: string[];
  observations: PublicOpinionObservation[];
}

export interface PublicOpinionCounterEvidence {
  id: string;
  title: string;
  capturedAt: string;
  text: string;
}

export interface PublicOpinionTrendAnalysis {
  protocol: "public_opinion_trend_analyzer_v1";
  status: "signals_detected" | "no_signal";
  signals: PublicOpinionTrendSignal[];
  counterEvidence: PublicOpinionCounterEvidence[];
  trendProfile: PublicOpinionTrendProfile;
  trendLanguageGate: PublicOpinionTrendLanguageGate;
  blockedClaims: string[];
  nextAction: string;
  claimBoundary: string;
}

export type PublicOpinionOpportunitySignal =
  | "under_attention_candidate"
  | "crowded_or_hyped"
  | "conflicted"
  | "insufficient";

export interface PublicOpinionEvidenceBalance {
  lowAttentionSignals: number;
  avoidanceSignals: number;
  hypeSignals: number;
  counterEvidenceCount: number;
  distinctSourceKinds: number;
}

export interface PublicOpinionTrendProfile {
  protocol: "public_opinion_trend_profile_v1";
  opportunitySignal: PublicOpinionOpportunitySignal;
  confidence: "low" | "medium" | "high";
  evidenceBalance: PublicOpinionEvidenceBalance;
  familySafeSummary: string;
  requiredFollowUps: string[];
}

export type PublicOpinionTrendLanguageGateStatus =
  | "hypothesis_only"
  | "blocked_by_conflict"
  | "blocked_by_hype"
  | "insufficient_evidence";

export interface PublicOpinionTrendLanguageGate {
  protocol: "public_opinion_trend_language_gate_v1";
  status: PublicOpinionTrendLanguageGateStatus;
  score: number;
  canUseHiddenOpportunityLabel: boolean;
  familySafeWording: string;
  requiredEvidence: string[];
  forbiddenWording: string[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Public-opinion trend analysis produces hypothesis signals only. It cannot prove official plan changes, rank impact, competitor omission, or final recommendation readiness.";

const LANGUAGE_GATE_BOUNDARY =
  "Trend language gates decide wording only. They cannot prove demand, admission probability, or final recommendation readiness.";

export function analyzePublicOpinionTrends(input: PublicOpinionTrendAnalyzerInput): PublicOpinionTrendAnalysis {
  const counterEvidence = input.observations.filter((observation) => hasAny(observation.text, COUNTER_TERMS));
  const signalObservations = input.observations.filter((observation) => !counterEvidence.includes(observation));
  const avoidanceEvidence = signalObservations.filter((observation) => hasAny(observation.text, AVOIDANCE_TERMS));
  const lowAttentionEvidence = signalObservations.filter((observation) => hasAny(observation.text, LOW_ATTENTION_TERMS));
  const hypeEvidence = signalObservations.filter((observation) => hasAny(observation.text, HYPE_TERMS));
  const signals: PublicOpinionTrendSignal[] = [];

  if (avoidanceEvidence.length > 0 || lowAttentionEvidence.length > 0) {
    signals.push({
      id: `trend-${input.schoolCode ?? normalizeId(input.schoolName)}-low-attention-avoidance`,
      topic: `low attention or avoidance around ${input.schoolName} ${input.majorKeywords.join(" / ")}`,
      sourceKind: dominantSourceKind([...avoidanceEvidence, ...lowAttentionEvidence]),
      attention: "low",
      sentiment: "avoidance",
      schoolCode: input.schoolCode,
      majorKeywords: input.majorKeywords,
      evidence: buildEvidenceLine([...avoidanceEvidence, ...lowAttentionEvidence]),
    });
  }

  if (hypeEvidence.length > 0) {
    signals.push({
      id: `trend-${input.schoolCode ?? normalizeId(input.schoolName)}-hype`,
      topic: `hype around ${input.majorKeywords.join(" / ")}`,
      sourceKind: dominantSourceKind(hypeEvidence),
      attention: "high",
      sentiment: "hype",
      schoolCode: input.schoolCode,
      majorKeywords: input.majorKeywords,
      evidence: buildEvidenceLine(hypeEvidence),
    });
  }

  const trendProfile = buildTrendProfile({
    input,
    avoidanceEvidence,
    lowAttentionEvidence,
    hypeEvidence,
    counterEvidence,
    signals,
  });

  return {
    protocol: "public_opinion_trend_analyzer_v1",
    status: signals.length > 0 ? "signals_detected" : "no_signal",
    signals,
    counterEvidence: counterEvidence.map((observation) => ({
      id: observation.id,
      title: observation.title,
      capturedAt: observation.capturedAt,
      text: observation.text,
    })),
    trendProfile,
    trendLanguageGate: buildTrendLanguageGate({
      input,
      trendProfile,
    }),
    blockedClaims: [
      "Do not use public-opinion trend signals as official plan evidence.",
      "Do not infer final demand without official plan, rank history, and external-plan comparison.",
      "Do not promote a hidden opportunity when counter-evidence is stronger than the trend signal.",
    ],
    nextAction:
      signals.length > 0
        ? "Attach official plan diff, rank calibration, and external-plan comparison before using these signals in opportunity discovery."
        : "Collect more dated public-opinion observations before creating a trend hypothesis.",
    claimBoundary: CLAIM_BOUNDARY,
  };
}

const LOW_ATTENTION_TERMS = ["rarely mention", "not mention", "low attention", "miss the", "missed", "ignored", "under-attended"];
const AVOIDANCE_TERMS = ["avoid", "because of distance", "campus uncertainty", "adjustment concern", "fear of", "risk concern"];
const HYPE_TERMS = ["hot", "hype", "high salary", "everyone", "popular", "rush to apply"];
const COUNTER_TERMS = ["counter", "widely recognized", "not anecdotal", "mainstream", "broad attention"];

function hasAny(text: string, terms: string[]): boolean {
  const normalized = text.toLowerCase();
  return terms.some((term) => normalized.includes(term.toLowerCase()));
}

function dominantSourceKind(observations: PublicOpinionObservation[]): TrendSourceKind {
  return observations[0]?.sourceKind ?? "search_snippet";
}

function buildEvidenceLine(observations: PublicOpinionObservation[]): string {
  return observations
    .map((observation) => `${observation.id} (${observation.sourceKind}, ${observation.capturedAt}): ${observation.title}`)
    .join("; ");
}

function buildTrendProfile({
  input,
  avoidanceEvidence,
  lowAttentionEvidence,
  hypeEvidence,
  counterEvidence,
  signals,
}: {
  input: PublicOpinionTrendAnalyzerInput;
  avoidanceEvidence: PublicOpinionObservation[];
  lowAttentionEvidence: PublicOpinionObservation[];
  hypeEvidence: PublicOpinionObservation[];
  counterEvidence: PublicOpinionObservation[];
  signals: PublicOpinionTrendSignal[];
}): PublicOpinionTrendProfile {
  const evidenceBalance: PublicOpinionEvidenceBalance = {
    lowAttentionSignals: lowAttentionEvidence.length,
    avoidanceSignals: avoidanceEvidence.length,
    hypeSignals: hypeEvidence.length,
    counterEvidenceCount: counterEvidence.length,
    distinctSourceKinds: new Set(signals.map((signal) => signal.sourceKind)).size,
  };
  const opportunitySignal = resolveOpportunitySignal(evidenceBalance);
  return {
    protocol: "public_opinion_trend_profile_v1",
    opportunitySignal,
    confidence: resolveConfidence(opportunitySignal, evidenceBalance),
    evidenceBalance,
    familySafeSummary: buildFamilySafeSummary({ input, opportunitySignal, evidenceBalance }),
    requiredFollowUps: buildRequiredFollowUps(opportunitySignal),
  };
}

function resolveOpportunitySignal(balance: PublicOpinionEvidenceBalance): PublicOpinionOpportunitySignal {
  if (balance.counterEvidenceCount > 0 && (balance.lowAttentionSignals > 0 || balance.avoidanceSignals > 0 || balance.hypeSignals > 0)) {
    return "conflicted";
  }
  if (balance.lowAttentionSignals > 0 && balance.avoidanceSignals > 0) {
    return "under_attention_candidate";
  }
  if (balance.hypeSignals > 0) {
    return "crowded_or_hyped";
  }
  return "insufficient";
}

function resolveConfidence(
  opportunitySignal: PublicOpinionOpportunitySignal,
  balance: PublicOpinionEvidenceBalance,
): PublicOpinionTrendProfile["confidence"] {
  if (opportunitySignal === "conflicted" || opportunitySignal === "insufficient") {
    return "low";
  }
  if (balance.distinctSourceKinds >= 2 && balance.lowAttentionSignals + balance.avoidanceSignals + balance.hypeSignals >= 3) {
    return "high";
  }
  return "medium";
}

function buildFamilySafeSummary({
  input,
  opportunitySignal,
  evidenceBalance,
}: {
  input: PublicOpinionTrendAnalyzerInput;
  opportunitySignal: PublicOpinionOpportunitySignal;
  evidenceBalance: PublicOpinionEvidenceBalance;
}): string {
  const target = `${input.schoolName} ${input.majorKeywords.join(" / ")}`;
  if (opportunitySignal === "under_attention_candidate") {
    return `${target} has a possible under-attention hypothesis, but it still needs official plan, rank, and external-plan evidence before use.`;
  }
  if (opportunitySignal === "crowded_or_hyped") {
    return `${target} looks crowded or hyped in public discussion; treat it as demand pressure, not a hidden opportunity.`;
  }
  if (opportunitySignal === "conflicted") {
    return `${target} has public-opinion signal but also ${evidenceBalance.counterEvidenceCount} counter-evidence item(s); do not treat it as a hidden opportunity yet.`;
  }
  return `${target} has insufficient public-opinion evidence for a trend hypothesis.`;
}

function buildRequiredFollowUps(opportunitySignal: PublicOpinionOpportunitySignal): string[] {
  const followUps = [
    "Attach official plan diff before using public-opinion signals in opportunity discovery.",
    "Attach rank history and external-plan comparison before discussing hidden opportunity potential.",
  ];
  if (opportunitySignal === "conflicted") {
    followUps.push("Search for dated counter-evidence and resolve whether the trend is broad or anecdotal.");
    followUps.push("Do not present this as a hidden opportunity until counter-evidence is weaker than the trend signal.");
  }
  if (opportunitySignal === "crowded_or_hyped") {
    followUps.push("Treat hype as possible demand pressure and look for safer alternatives.");
  }
  if (opportunitySignal === "insufficient") {
    followUps.push("Collect more dated public-opinion observations from at least two source kinds.");
  }
  return followUps;
}

function buildTrendLanguageGate({
  input,
  trendProfile,
}: {
  input: PublicOpinionTrendAnalyzerInput;
  trendProfile: PublicOpinionTrendProfile;
}): PublicOpinionTrendLanguageGate {
  const status = resolveLanguageGateStatus(trendProfile.opportunitySignal);
  const score = scoreLanguageGate(trendProfile);
  return {
    protocol: "public_opinion_trend_language_gate_v1",
    status,
    score,
    canUseHiddenOpportunityLabel: status === "hypothesis_only",
    familySafeWording: buildLanguageGateFamilyWording({ input, trendProfile, status }),
    requiredEvidence: buildLanguageGateRequiredEvidence(status),
    forbiddenWording: [
      "Do not call this a hidden opportunity when counter-evidence, hype, or insufficient data is present.",
      "Do not say public opinion proves demand, admission probability, score movement, or guaranteed admission.",
      "Do not present trend wording without official plan diff, rank calibration, external-plan comparison, and counselor review.",
    ],
    claimBoundary: LANGUAGE_GATE_BOUNDARY,
  };
}

function resolveLanguageGateStatus(
  opportunitySignal: PublicOpinionOpportunitySignal,
): PublicOpinionTrendLanguageGateStatus {
  if (opportunitySignal === "under_attention_candidate") return "hypothesis_only";
  if (opportunitySignal === "conflicted") return "blocked_by_conflict";
  if (opportunitySignal === "crowded_or_hyped") return "blocked_by_hype";
  return "insufficient_evidence";
}

function scoreLanguageGate(trendProfile: PublicOpinionTrendProfile): number {
  const balance = trendProfile.evidenceBalance;
  if (trendProfile.opportunitySignal === "under_attention_candidate") {
    return clamp(
      60 +
        balance.lowAttentionSignals * 8 +
        balance.avoidanceSignals * 8 +
        Math.max(0, balance.distinctSourceKinds - 1) * 6 -
        balance.counterEvidenceCount * 20 -
        balance.hypeSignals * 12,
    );
  }
  if (trendProfile.opportunitySignal === "crowded_or_hyped") {
    return clamp(35 - balance.hypeSignals * 8);
  }
  if (trendProfile.opportunitySignal === "conflicted") {
    return clamp(45 - balance.counterEvidenceCount * 15 - balance.hypeSignals * 8);
  }
  return clamp(20 + balance.lowAttentionSignals * 5 + balance.avoidanceSignals * 5);
}

function buildLanguageGateFamilyWording({
  input,
  trendProfile,
  status,
}: {
  input: PublicOpinionTrendAnalyzerInput;
  trendProfile: PublicOpinionTrendProfile;
  status: PublicOpinionTrendLanguageGateStatus;
}): string {
  const target = `${input.schoolName} ${input.majorKeywords.join(" / ")}`;
  if (status === "hypothesis_only") {
    return `${target} can be described only as an under-attention candidate: public discussion looks quieter or avoidant, but this remains a hypothesis until official, rank, and external-plan evidence agree.`;
  }
  if (status === "blocked_by_conflict") {
    return `${target} has conflicted trend evidence; do not use hidden-opportunity wording until counter-evidence is resolved.`;
  }
  if (status === "blocked_by_hype") {
    return `${target} looks crowded or hyped; treat the trend as demand pressure, not as a hidden opportunity.`;
  }
  return `${target} has insufficient dated public-opinion evidence for opportunity wording; collect more independent sources first. ${trendProfile.familySafeSummary}`;
}

function buildLanguageGateRequiredEvidence(status: PublicOpinionTrendLanguageGateStatus): string[] {
  const common = [
    "Attach official plan diff before using trend language.",
    "Attach rank history and external-plan comparison before discussing hidden opportunity potential.",
  ];
  if (status === "blocked_by_conflict") {
    return [
      ...common,
      "Resolve dated counter-evidence and determine whether low attention is broad or anecdotal.",
    ];
  }
  if (status === "blocked_by_hype") {
    return [
      ...common,
      "Audit whether hype indicates demand pressure and search for less crowded alternatives.",
    ];
  }
  if (status === "insufficient_evidence") {
    return [
      ...common,
      "Collect public-opinion observations from at least two source kinds.",
    ];
  }
  return [
    ...common,
    "Keep wording as hypothesis-only until counselor review.",
  ];
}

function clamp(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function normalizeId(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

import type { PlanChangeDiff } from "./planChangeDiffEngine";

export type TrendSourceKind = "search_snippet" | "social_summary" | "article_summary" | "school_news" | "exam_authority_notice";
export type TrendAttention = "low" | "medium" | "high";
export type TrendSentiment = "avoidance" | "fear" | "hype" | "neutral";
export type OpportunityDiscoveryStatus = "research_ready" | "guarded" | "blocked";
export type StudentFitStatus = "fit" | "mixed" | "conflict";
export type FamilyConceptKey =
  | "professional_group"
  | "adjustment_tradeoff"
  | "safe_anchor_failure"
  | "interest_tradeoff"
  | "subject_requirement";

export interface PublicOpinionTrendSignal {
  id: string;
  topic: string;
  sourceKind: TrendSourceKind;
  attention: TrendAttention;
  sentiment: TrendSentiment;
  schoolCode?: string;
  majorKeywords?: string[];
  evidence: string;
}

export type PublicOpinionOpportunitySignal =
  | "under_attention_candidate"
  | "crowded_or_hyped"
  | "conflicted"
  | "insufficient";

export interface DiscoveryTrendProfile {
  schoolCode?: string;
  majorKeywords?: string[];
  opportunitySignal: PublicOpinionOpportunitySignal;
  confidence: "low" | "medium" | "high";
  familySafeSummary: string;
  requiredFollowUps: string[];
}

export interface OpportunityPublicOpinionGuard {
  status:
    | "supports_hypothesis"
    | "needs_counterevidence_review"
    | "hype_or_crowding_guard"
    | "insufficient_signal";
  opportunitySignal: PublicOpinionOpportunitySignal;
  confidence: "low" | "medium" | "high";
  summary: string;
  nextActions: string[];
}

export interface DiscoveryRankDeltaEstimate {
  direction: "easier" | "harder" | "uncertain";
  rankDelta?: number;
  confidence: "low" | "medium" | "high";
  explanation: string;
}

export interface DiscoveryStudentProfile {
  preferredMajorKeywords: string[];
  blacklistMajorKeywords: string[];
  riskTolerance: "conservative" | "balanced" | "aggressive";
  acceptableTradeoffs: string[];
}

export interface OpportunityDiscoveryInput {
  trendSignals: PublicOpinionTrendSignal[];
  trendProfiles?: DiscoveryTrendProfile[];
  planDiffs: PlanChangeDiff[];
  rankDeltaEstimates?: Record<string, DiscoveryRankDeltaEstimate>;
  studentProfile: DiscoveryStudentProfile;
}

export interface OpportunityDiscoveryInsight {
  id: string;
  opportunityKind: "under_attention_opportunity" | "overheated_attention_guard" | "official_change_guard";
  status: OpportunityDiscoveryStatus;
  officialEvidence: {
    auditKey: string;
    officialSource: string;
    diffType: PlanChangeDiff["diffType"];
    evidence: string;
  };
  trendHypotheses: Array<{
    id: string;
    role: "hypothesis_only";
    topic: string;
    evidence: string;
  }>;
  publicOpinionGuard: OpportunityPublicOpinionGuard;
  rankImpact: DiscoveryRankDeltaEstimate;
  studentFit: {
    status: StudentFitStatus;
    reasons: string[];
  };
  requiredConcepts: FamilyConceptKey[];
  parentExplanation: {
    summary: string;
    concepts: string[];
  };
}

export interface OpportunityDiscoveryLedger {
  protocol: "opportunity_discovery_engine_v1";
  status: "partial" | "blocked";
  insights: OpportunityDiscoveryInsight[];
  blockedClaims: string[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Public-opinion trends are hypotheses only. Official enrollment-plan diffs, rank impact, student constraints, and risk concepts must remain separate until counselor review.";

export function buildOpportunityDiscoveryLedger(input: OpportunityDiscoveryInput): OpportunityDiscoveryLedger {
  if (input.planDiffs.length === 0) {
    return {
      protocol: "opportunity_discovery_engine_v1",
      status: "blocked",
      insights: [],
      blockedClaims: [
        "Trend signals cannot become official opportunity evidence without an official enrollment-plan diff.",
        "Attach official 2025->2026 plan diffs before claiming any low-attention opportunity.",
      ],
      claimBoundary: CLAIM_BOUNDARY,
    };
  }

  const insights = input.planDiffs.map((diff) => buildInsight(diff, input)).filter(Boolean) as OpportunityDiscoveryInsight[];

  return {
    protocol: "opportunity_discovery_engine_v1",
    status: insights.length > 0 ? "partial" : "blocked",
    insights,
    blockedClaims:
      insights.length > 0
        ? ["Do not promote opportunity claims until external-plan omission and counselor risk guard are audited."]
        : ["Official diffs exist, but no student-fit or trend hypothesis can explain an opportunity yet."],
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildInsight(diff: PlanChangeDiff, input: OpportunityDiscoveryInput): OpportunityDiscoveryInsight | null {
  const matchingTrends = input.trendSignals.filter((signal) => trendMatchesDiff(signal, diff));
  const trendProfile = matchingTrendProfile(diff, input.trendProfiles);
  const publicOpinionGuard = buildPublicOpinionGuard({ trendProfile, matchingTrends });
  const rankImpact = input.rankDeltaEstimates?.[diff.auditKey] ?? defaultRankImpact(diff);
  const studentFit = evaluateStudentFit(diff, input.studentProfile);
  const requiredConcepts = buildRequiredConcepts(diff);

  if (diff.diffType === "subject_requirement_change") {
    return {
      id: `${diff.auditKey}-subject-guard`,
      opportunityKind: "official_change_guard",
      status: "guarded",
      officialEvidence: officialEvidence(diff),
      trendHypotheses: toTrendHypotheses(matchingTrends),
      publicOpinionGuard,
      rankImpact,
      studentFit,
      requiredConcepts,
      parentExplanation: buildParentExplanation(diff, "official_change_guard", rankImpact, studentFit, requiredConcepts),
    };
  }

  const hypeTrend = matchingTrends.find((signal) => signal.attention === "high" || signal.sentiment === "hype");
  if (hypeTrend || publicOpinionGuard.status === "hype_or_crowding_guard") {
    return {
      id: `${diff.auditKey}-hype-guard`,
      opportunityKind: "overheated_attention_guard",
      status: "guarded",
      officialEvidence: officialEvidence(diff),
      trendHypotheses: toTrendHypotheses(hypeTrend ? [hypeTrend] : matchingTrends),
      publicOpinionGuard,
      rankImpact,
      studentFit,
      requiredConcepts,
      parentExplanation: buildParentExplanation(diff, "overheated_attention_guard", rankImpact, studentFit, requiredConcepts),
    };
  }

  const lowAttentionTrend = matchingTrends.find((signal) => signal.attention === "low" || signal.sentiment === "avoidance");
  if (
    lowAttentionTrend &&
    diff.diffType === "quota_expansion" &&
    rankImpact.direction === "easier" &&
    studentFit.status !== "conflict" &&
    publicOpinionGuard.status === "supports_hypothesis"
  ) {
    return {
      id: `${diff.auditKey}-under-attention`,
      opportunityKind: "under_attention_opportunity",
      status: "research_ready",
      officialEvidence: officialEvidence(diff),
      trendHypotheses: toTrendHypotheses([lowAttentionTrend]),
      publicOpinionGuard,
      rankImpact,
      studentFit,
      requiredConcepts,
      parentExplanation: buildParentExplanation(diff, "under_attention_opportunity", rankImpact, studentFit, requiredConcepts),
    };
  }

  if (lowAttentionTrend && publicOpinionGuard.status !== "supports_hypothesis") {
    return {
      id: `${diff.auditKey}-public-opinion-guard`,
      opportunityKind: "official_change_guard",
      status: "guarded",
      officialEvidence: officialEvidence(diff),
      trendHypotheses: toTrendHypotheses([lowAttentionTrend]),
      publicOpinionGuard,
      rankImpact,
      studentFit,
      requiredConcepts,
      parentExplanation: buildParentExplanation(diff, "official_change_guard", rankImpact, studentFit, requiredConcepts),
    };
  }

  if (diff.diffType === "group_split" || diff.diffType === "group_merge") {
    return {
      id: `${diff.auditKey}-structure-guard`,
      opportunityKind: "official_change_guard",
      status: "guarded",
      officialEvidence: officialEvidence(diff),
      trendHypotheses: toTrendHypotheses(matchingTrends),
      publicOpinionGuard,
      rankImpact,
      studentFit,
      requiredConcepts,
      parentExplanation: buildParentExplanation(diff, "official_change_guard", rankImpact, studentFit, requiredConcepts),
    };
  }

  return null;
}

function trendMatchesDiff(signal: PublicOpinionTrendSignal, diff: PlanChangeDiff): boolean {
  const schoolMatches = !signal.schoolCode || signal.schoolCode === diff.row.schoolCode;
  const majorMatches =
    !signal.majorKeywords?.length ||
    signal.majorKeywords.some((keyword) => diff.row.majorName.toLowerCase().includes(keyword.toLowerCase()));
  return schoolMatches && majorMatches;
}

function matchingTrendProfile(diff: PlanChangeDiff, profiles?: DiscoveryTrendProfile[]): DiscoveryTrendProfile | undefined {
  return profiles?.find((profile) => {
    const schoolMatches = !profile.schoolCode || profile.schoolCode === diff.row.schoolCode;
    const majorMatches =
      !profile.majorKeywords?.length ||
      profile.majorKeywords.some((keyword) => diff.row.majorName.toLowerCase().includes(keyword.toLowerCase()));
    return schoolMatches && majorMatches;
  });
}

function buildPublicOpinionGuard({
  trendProfile,
  matchingTrends,
}: {
  trendProfile?: DiscoveryTrendProfile;
  matchingTrends: PublicOpinionTrendSignal[];
}): OpportunityPublicOpinionGuard {
  if (trendProfile) {
    if (trendProfile.opportunitySignal === "conflicted") {
      return {
        status: "needs_counterevidence_review",
        opportunitySignal: trendProfile.opportunitySignal,
        confidence: trendProfile.confidence,
        summary: trendProfile.familySafeSummary,
        nextActions:
          trendProfile.requiredFollowUps.length > 0
            ? trendProfile.requiredFollowUps
            : ["Resolve counter-evidence before presenting this as an opportunity."],
      };
    }

    if (trendProfile.opportunitySignal === "crowded_or_hyped") {
      return {
        status: "hype_or_crowding_guard",
        opportunitySignal: trendProfile.opportunitySignal,
        confidence: trendProfile.confidence,
        summary: trendProfile.familySafeSummary,
        nextActions:
          trendProfile.requiredFollowUps.length > 0
            ? trendProfile.requiredFollowUps
            : ["Separate popularity from actual admission-plan advantage."],
      };
    }

    if (trendProfile.opportunitySignal === "under_attention_candidate") {
      return {
        status: "supports_hypothesis",
        opportunitySignal: trendProfile.opportunitySignal,
        confidence: trendProfile.confidence,
        summary: trendProfile.familySafeSummary,
        nextActions:
          trendProfile.requiredFollowUps.length > 0
            ? trendProfile.requiredFollowUps
            : ["Verify the under-attention pattern with dated external-plan comparisons."],
      };
    }

    return {
      status: "insufficient_signal",
      opportunitySignal: trendProfile.opportunitySignal,
      confidence: trendProfile.confidence,
      summary: trendProfile.familySafeSummary,
      nextActions:
        trendProfile.requiredFollowUps.length > 0
          ? trendProfile.requiredFollowUps
          : ["Collect more independent public-opinion evidence before forming an opportunity hypothesis."],
    };
  }

  const hypeTrend = matchingTrends.find((signal) => signal.attention === "high" || signal.sentiment === "hype");
  if (hypeTrend) {
    return {
      status: "hype_or_crowding_guard",
      opportunitySignal: "crowded_or_hyped",
      confidence: "low",
      summary: "Matched public-opinion evidence points to hype or crowding, so it cannot support a hidden-opportunity claim.",
      nextActions: ["Separate popularity from official-plan advantage before presenting this to families."],
    };
  }

  const lowAttentionTrend = matchingTrends.find((signal) => signal.attention === "low" || signal.sentiment === "avoidance");
  if (lowAttentionTrend) {
    return {
      status: "supports_hypothesis",
      opportunitySignal: "under_attention_candidate",
      confidence: "low",
      summary: "Matched public-opinion evidence suggests low attention or avoidance, but this remains a hypothesis until cross-checked.",
      nextActions: ["Verify the low-attention pattern with dated search results and external-plan comparisons."],
    };
  }

  return {
    status: "insufficient_signal",
    opportunitySignal: "insufficient",
    confidence: "low",
    summary: "No matched public-opinion profile is strong enough to support an opportunity hypothesis.",
    nextActions: ["Collect public-opinion evidence before making a trend-based opportunity claim."],
  };
}

function defaultRankImpact(diff: PlanChangeDiff): DiscoveryRankDeltaEstimate {
  if (diff.diffType === "quota_expansion") {
    return {
      direction: "easier",
      confidence: "low",
      explanation: "Quota expansion can loosen rank pressure, but the magnitude is not calibrated yet.",
    };
  }
  if (diff.diffType === "quota_reduction") {
    return {
      direction: "harder",
      confidence: "low",
      explanation: "Quota reduction can tighten rank pressure, but the magnitude is not calibrated yet.",
    };
  }
  return {
    direction: "uncertain",
    confidence: "low",
    explanation: "This official change requires separate historical calibration before rank impact can be claimed.",
  };
}

function evaluateStudentFit(diff: PlanChangeDiff, profile: DiscoveryStudentProfile): OpportunityDiscoveryInsight["studentFit"] {
  const majorName = diff.row.majorName.toLowerCase();
  const blacklistHit = profile.blacklistMajorKeywords.some((keyword) => majorName.includes(keyword.toLowerCase()));
  const preferenceHit = profile.preferredMajorKeywords.some((keyword) => majorName.includes(keyword.toLowerCase()));

  if (blacklistHit) {
    return {
      status: "conflict",
      reasons: ["The changed major overlaps the student's stated blacklist."],
    };
  }
  if (preferenceHit) {
    return {
      status: "fit",
      reasons: ["The changed major matches the student's stated direction."],
    };
  }
  return {
    status: "mixed",
    reasons: ["The changed major is not blacklisted, but it is not an explicit interest match."],
  };
}

function buildRequiredConcepts(diff: PlanChangeDiff): FamilyConceptKey[] {
  const concepts: FamilyConceptKey[] = ["professional_group"];
  if (diff.diffType === "subject_requirement_change") concepts.push("subject_requirement");
  if (diff.diffType === "quota_expansion" || diff.diffType === "group_split" || diff.diffType === "group_merge") {
    concepts.push("adjustment_tradeoff", "safe_anchor_failure", "interest_tradeoff");
  }
  return [...new Set(concepts)];
}

function buildParentExplanation(
  diff: PlanChangeDiff,
  kind: OpportunityDiscoveryInsight["opportunityKind"],
  rankImpact: DiscoveryRankDeltaEstimate,
  studentFit: OpportunityDiscoveryInsight["studentFit"],
  concepts: FamilyConceptKey[],
): OpportunityDiscoveryInsight["parentExplanation"] {
  return {
    summary: buildSummary(diff, kind, rankImpact, studentFit),
    concepts: concepts.map((concept) => conceptText(concept)),
  };
}

function buildSummary(
  diff: PlanChangeDiff,
  kind: OpportunityDiscoveryInsight["opportunityKind"],
  rankImpact: DiscoveryRankDeltaEstimate,
  studentFit: OpportunityDiscoveryInsight["studentFit"],
): string {
  if (kind === "under_attention_opportunity") {
    return `${diff.row.schoolName} ${diff.row.majorName} 可能是机会：官方计划变化显示名额或结构更友好，舆论关注不足只能作为假设，还要用历史位次、外部方案遗漏和调剂风险复核。`;
  }
  if (kind === "overheated_attention_guard") {
    return `${diff.row.schoolName} ${diff.row.majorName} 的热度需要降温处理：即使有官方变化，也不能把热门叙事当成价值证明。`;
  }
  if (diff.diffType === "subject_requirement_change") {
    return `${diff.row.schoolName} ${diff.row.majorName} 的选科要求发生变化，先确认学生是否具备资格，再讨论机会。`;
  }
  return `${diff.row.schoolName} ${diff.row.majorName} 有官方计划变化，但当前只能作为复核项；位次影响为 ${rankImpact.direction}，学生匹配为 ${studentFit.status}。`;
}

function conceptText(concept: FamilyConceptKey): string {
  const copy: Record<FamilyConceptKey, string> = {
    professional_group: "专业组是投档单位，不等于一个单独专业；同一组里的专业和校区要一起看。",
    adjustment_tradeoff: "服从调剂保的是录取机会，不保证一定进入最想读的专业。",
    safe_anchor_failure: "保底不是只看能不能进组，还要看进组以后最差专业、校区和收费是否能接受。",
    interest_tradeoff: "兴趣不是一句喜欢热门专业；要说清楚愿意接受哪些课程、行业、城市和工作方式。",
    subject_requirement: "选科要求是硬门槛，不满足要求时，再好的位次和热度都不能填。",
  };
  return copy[concept];
}

function officialEvidence(diff: PlanChangeDiff): OpportunityDiscoveryInsight["officialEvidence"] {
  return {
    auditKey: diff.auditKey,
    officialSource: diff.officialSource,
    diffType: diff.diffType,
    evidence: diff.evidence,
  };
}

function toTrendHypotheses(signals: PublicOpinionTrendSignal[]): OpportunityDiscoveryInsight["trendHypotheses"] {
  return signals.map((signal) => ({
    id: signal.id,
    role: "hypothesis_only",
    topic: signal.topic,
    evidence: signal.evidence,
  }));
}

import type { OpportunityDiscoveryInsight, OpportunityDiscoveryLedger } from "./opportunityDiscoveryEngine";

export type WebEvidenceTaskType =
  | "official_plan_verification"
  | "school_rule_verification"
  | "rank_history_calibration"
  | "public_opinion_scan"
  | "external_plan_comparison"
  | "family_concept_clarification";

export type WebEvidenceSourceTier =
  | "official"
  | "historical_data"
  | "public_opinion"
  | "competitor_plan"
  | "concept";

export type EvidenceClaimSupport =
  | "official_diff"
  | "rank_delta"
  | "risk_guard"
  | "competitor_missed"
  | "hypothesis_only"
  | "parent_understanding"
  | "final_recommendation";

export interface WebEvidenceResearchPlanInput {
  discoveryLedger: OpportunityDiscoveryLedger;
  targetYear: number;
  province: string;
  externalPlanSources: string[];
}

export interface WebEvidenceResearchTask {
  id: string;
  insightId: string;
  taskType: WebEvidenceTaskType;
  sourceTier: WebEvidenceSourceTier;
  query: string;
  requiredEvidence: string[];
  canSupportClaims: EvidenceClaimSupport[];
  blocksRecommendationReadiness: boolean;
  claimBoundary: string;
}

export interface WebEvidenceResearchPlan {
  protocol: "web_evidence_research_plan_v1";
  status: "needs_research" | "blocked";
  tasks: WebEvidenceResearchTask[];
  interpretationChecklist: string[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Search tasks do not prove claims. They define what evidence must be collected before official diffs, trend hypotheses, rank estimates, and final recommendations can be connected.";

export function buildWebEvidenceResearchPlan(input: WebEvidenceResearchPlanInput): WebEvidenceResearchPlan {
  const insights = input.discoveryLedger.insights ?? [];
  const tasks = insights.flatMap((insight) => buildTasksForInsight(insight, input));

  return {
    protocol: "web_evidence_research_plan_v1",
    status: tasks.length > 0 ? "needs_research" : "blocked",
    tasks,
    interpretationChecklist: [
      "Do not call this a hidden opportunity until official plan, rank calibration, external omission, and risk guard evidence are all attached.",
      "Treat public-opinion search as a demand hypothesis, not as official evidence.",
      "Explain professional group, adjustment, safe-anchor failure, and interest tradeoff before showing final rows.",
      "Keep counselor review required whenever a task that blocks recommendation readiness is still unresolved.",
    ],
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildTasksForInsight(
  insight: OpportunityDiscoveryInsight,
  input: WebEvidenceResearchPlanInput,
): WebEvidenceResearchTask[] {
  return [
    officialPlanTask(insight, input),
    schoolRuleTask(insight, input),
    rankHistoryTask(insight, input),
    publicOpinionTask(insight, input),
    externalPlanTask(insight, input),
    familyConceptTask(insight),
  ];
}

function officialPlanTask(
  insight: OpportunityDiscoveryInsight,
  input: WebEvidenceResearchPlanInput,
): WebEvidenceResearchTask {
  const row = rowTerms(insight);
  return {
    id: `${insight.id}-official-plan`,
    insightId: insight.id,
    taskType: "official_plan_verification",
    sourceTier: "official",
    query: `${input.province} ${input.targetYear} official enrollment plan ${row.schoolCode} ${row.majorGroupCode} ${row.majorName} ${insight.officialEvidence.diffType}`,
    requiredEvidence: [
      "exam authority or school official plan URL",
      "row-level school code, major group code, major code, major name, quota, and subject requirements",
      "prior-year and current-year row comparison",
    ],
    canSupportClaims: ["official_diff"],
    blocksRecommendationReadiness: true,
    claimBoundary: "Only official plan sources can support the official diff claim.",
  };
}

function schoolRuleTask(
  insight: OpportunityDiscoveryInsight,
  input: WebEvidenceResearchPlanInput,
): WebEvidenceResearchTask {
  const row = rowTerms(insight);
  return {
    id: `${insight.id}-school-rule`,
    insightId: insight.id,
    taskType: "school_rule_verification",
    sourceTier: "official",
    query: `${row.schoolName} ${input.targetYear} admission charter adjustment transfer rules major group ${row.majorGroupCode}`,
    requiredEvidence: [
      "admission charter or school admissions office URL",
      "major assignment, adjustment, transfer, campus, tuition, and physical-exam restrictions",
      "risk guard checks that a counselor can verify before signoff",
    ],
    canSupportClaims: ["risk_guard"],
    blocksRecommendationReadiness: true,
    claimBoundary: "School rules can support risk guards, but not market demand or competitor omission.",
  };
}

function rankHistoryTask(
  insight: OpportunityDiscoveryInsight,
  input: WebEvidenceResearchPlanInput,
): WebEvidenceResearchTask {
  const row = rowTerms(insight);
  return {
    id: `${insight.id}-rank-history`,
    insightId: insight.id,
    taskType: "rank_history_calibration",
    sourceTier: "historical_data",
    query: `${input.province} 2025 2024 ${row.schoolName} ${row.majorGroupCode} ${row.majorName} minimum rank admission history`,
    requiredEvidence: [
      "2024 and 2025 admission rank or score lines for the same school and group",
      "quota and subject requirement context for each historical row",
      "explicit explanation of why the rank delta estimate is easier, harder, or uncertain",
    ],
    canSupportClaims: ["rank_delta"],
    blocksRecommendationReadiness: true,
    claimBoundary: "Historical ranks calibrate direction and magnitude; they do not prove this year's demand by themselves.",
  };
}

function publicOpinionTask(
  insight: OpportunityDiscoveryInsight,
  input: WebEvidenceResearchPlanInput,
): WebEvidenceResearchTask {
  const trendTerms = insight.trendHypotheses.map((hypothesis) => hypothesis.topic).join(" OR ");
  const row = rowTerms(insight);
  return {
    id: `${insight.id}-public-opinion`,
    insightId: insight.id,
    taskType: "public_opinion_scan",
    sourceTier: "public_opinion",
    query: `${input.province} ${row.schoolName} ${row.majorName} ${trendTerms || "public opinion admissions attention"}`,
    requiredEvidence: [
      "search snippets, mainstream articles, or discussion summaries with dates",
      "separate evidence for attention level, fear, hype, avoidance, or regional bias",
      "counter-evidence showing whether the trend is broad or anecdotal",
    ],
    canSupportClaims: ["hypothesis_only"],
    blocksRecommendationReadiness: false,
    claimBoundary: "Public-opinion evidence is a hypothesis signal only; it cannot support official_diff or final_recommendation claims.",
  };
}

function externalPlanTask(
  insight: OpportunityDiscoveryInsight,
  input: WebEvidenceResearchPlanInput,
): WebEvidenceResearchTask {
  const row = rowTerms(insight);
  const sources = input.externalPlanSources.join(" ");
  return {
    id: `${insight.id}-external-plan`,
    insightId: insight.id,
    taskType: "external_plan_comparison",
    sourceTier: "competitor_plan",
    query: `${sources} plan comparison ${row.schoolName} ${row.majorGroupCode} ${row.majorName} ${insight.officialEvidence.diffType}`,
    requiredEvidence: [
      "Qianwen, Tencent, teacher, or family plan row excerpts",
      "row-level comparison showing whether the official diff is absent, present, or contradicted",
      "checked source list and date",
    ],
    canSupportClaims: ["competitor_missed"],
    blocksRecommendationReadiness: true,
    claimBoundary: "External-plan comparison can support competitor omission only after row-level matching.",
  };
}

function familyConceptTask(insight: OpportunityDiscoveryInsight): WebEvidenceResearchTask {
  return {
    id: `${insight.id}-family-concepts`,
    insightId: insight.id,
    taskType: "family_concept_clarification",
    sourceTier: "concept",
    query: `professional group adjustment safe anchor interest tradeoff ${insight.requiredConcepts.join(" ")}`,
    requiredEvidence: [
      "student-facing explanation of professional group versus major",
      "adjustment and no-adjustment tradeoff in plain language",
      "safe-anchor failure and interest tradeoff questions the family can answer",
    ],
    canSupportClaims: ["parent_understanding"],
    blocksRecommendationReadiness: false,
    claimBoundary: "Concept clarification improves decision quality, but it does not prove admission probability.",
  };
}

function rowTerms(insight: OpportunityDiscoveryInsight): {
  schoolCode: string;
  schoolName: string;
  majorGroupCode: string;
  majorName: string;
} {
  const parts = insight.officialEvidence.auditKey.split("-");
  const evidence = insight.officialEvidence.evidence;
  const majorGroupCode = parts[1] ?? "";
  const readable = majorGroupCode
    ? evidence.match(new RegExp(`for (.+) ${escapeRegExp(majorGroupCode)} (.+)\\.$`))
    : null;
  return {
    schoolCode: parts[0] ?? "",
    majorGroupCode,
    schoolName: readable?.[1] ?? parts[0] ?? "",
    majorName: readable?.[2] ?? parts[2] ?? "",
  };
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

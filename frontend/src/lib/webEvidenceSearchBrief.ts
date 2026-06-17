import type {
  EvidenceClaimSupport,
  WebEvidenceResearchPlan,
  WebEvidenceResearchTask,
  WebEvidenceSourceTier,
  WebEvidenceTaskType,
} from "./webEvidencePlanner";

export interface WebEvidenceSearchBriefInput {
  evidencePlan: WebEvidenceResearchPlan;
  locale?: "zh-CN" | "en-US";
}

export interface WebEvidenceResultTemplate {
  taskId: string;
  sourceTier: WebEvidenceSourceTier;
  claimedSupports: EvidenceClaimSupport[];
  excerptsRequired: boolean;
}

export interface WebEvidenceTaskSearchBrief {
  taskId: string;
  insightId: string;
  taskType: WebEvidenceTaskType;
  priority: "blocking" | "context";
  searchQueries: string[];
  preferredDomains: string[];
  acceptanceCriteria: string[];
  mustReject: string[];
  evidenceResultTemplate: WebEvidenceResultTemplate;
  claimBoundary: string;
}

export interface WebEvidenceSearchBrief {
  protocol: "web_evidence_search_brief_v1";
  status: "ready_to_search" | "blocked";
  taskBriefs: WebEvidenceTaskSearchBrief[];
  claimBoundary: string;
}

const CLAIM_BOUNDARY =
  "Search briefs prepare evidence collection. They do not support any claim until captured sources pass evidence intake.";

export function buildWebEvidenceSearchBrief(input: WebEvidenceSearchBriefInput): WebEvidenceSearchBrief {
  const taskBriefs = input.evidencePlan.tasks.map((task) => buildTaskBrief(task, input.locale ?? "zh-CN"));

  return {
    protocol: "web_evidence_search_brief_v1",
    status: taskBriefs.length > 0 ? "ready_to_search" : "blocked",
    taskBriefs,
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildTaskBrief(
  task: WebEvidenceResearchTask,
  locale: NonNullable<WebEvidenceSearchBriefInput["locale"]>,
): WebEvidenceTaskSearchBrief {
  return {
    taskId: task.id,
    insightId: task.insightId,
    taskType: task.taskType,
    priority: task.blocksRecommendationReadiness ? "blocking" : "context",
    searchQueries: buildSearchQueries(task, locale),
    preferredDomains: preferredDomains(task),
    acceptanceCriteria: [
      ...task.requiredEvidence,
      "captured source URL, title, date, and at least one excerpt",
      "row-level matching when the claim depends on school, group, major, quota, rank, or external-plan comparison",
    ],
    mustReject: rejectionRules(task),
    evidenceResultTemplate: {
      taskId: task.id,
      sourceTier: task.sourceTier,
      claimedSupports: task.canSupportClaims,
      excerptsRequired: true,
    },
    claimBoundary: task.claimBoundary,
  };
}

function buildSearchQueries(
  task: WebEvidenceResearchTask,
  locale: NonNullable<WebEvidenceSearchBriefInput["locale"]>,
): string[] {
  const localized = locale === "zh-CN" ? localizedSearchTerms(task) : task.query;
  const domains = preferredDomains(task).slice(0, 2);
  const siteQueries = domains.map((domain) => `site:${domain} ${localized}`);
  return Array.from(new Set([task.query, localized, ...siteQueries]));
}

function localizedSearchTerms(task: WebEvidenceResearchTask): string {
  const query = task.query;
  if (task.taskType === "official_plan_verification") {
    return `${query} Guangdong 2026 official enrollment catalog quota major group`;
  }
  if (task.taskType === "school_rule_verification") {
    return `${query} admission charter adjustment transfer physical exam restriction`;
  }
  if (task.taskType === "rank_history_calibration") {
    return `${query} Guangdong 2025 2024 admission line minimum rank history`;
  }
  if (task.taskType === "public_opinion_scan") {
    return `${query} low attention avoidance parent discussion overlooked opportunity`;
  }
  if (task.taskType === "external_plan_comparison") {
    return `${query} volunteer plan comparison omitted quota expansion major group`;
  }
  return `${query} major group adjustment safe anchor interest tradeoff`;
}

function preferredDomains(task: WebEvidenceResearchTask): string[] {
  if (task.sourceTier === "official" && task.taskType === "official_plan_verification") {
    return ["eea.gd.gov.cn", "gd.gov.cn", "edu.cn"];
  }
  if (task.sourceTier === "official") {
    return ["edu.cn", "school-admissions-office", "gd.gov.cn"];
  }
  if (task.sourceTier === "historical_data") {
    return ["eea.gd.gov.cn", "gaokao.chsi.com.cn", "data-admission-history"];
  }
  if (task.sourceTier === "public_opinion") {
    return ["zhihu.com", "xiaohongshu.com", "weibo.com", "baidu.com"];
  }
  if (task.sourceTier === "competitor_plan") {
    return ["qianwen", "tencent", "teacher-plan", "family-plan"];
  }
  return ["internal-concept-brief"];
}

function rejectionRules(task: WebEvidenceResearchTask): string[] {
  const rules = [
    "Reject any result that claims final recommendation readiness.",
    `Reject sources that are not ${task.sourceTier} tier for this task.`,
    "Reject captures without excerpts, dates, or source URLs.",
  ];
  if (task.taskType === "official_plan_verification") {
    rules.push("Reject public-opinion or reposted plan tables as support for official_diff.");
  }
  if (task.taskType === "external_plan_comparison") {
    rules.push("Reject competitor omission claims without row-level matching.");
  }
  if (task.taskType === "public_opinion_scan") {
    rules.push("Reject public-opinion evidence as proof of official plan changes or admission probability.");
  }
  return rules;
}

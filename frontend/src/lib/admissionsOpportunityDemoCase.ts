import {
  buildAdmissionsOpportunityWorkflow,
  type AdmissionsOpportunityWorkflow,
  type AdmissionsOpportunityWorkflowInput,
} from "./admissionsOpportunityWorkflow";
import {
  buildEvidenceCollectionWorkspace,
  type EvidenceCollectionWorkspace,
} from "./evidenceCollectionWorkspace";
import {
  buildWebEvidenceCaptureWorksheet,
  normalizeWebEvidenceCaptureSubmissions,
  type WebEvidenceCaptureNormalizationResult,
  type WebEvidenceCaptureSubmission,
  type WebEvidenceCaptureWorksheet,
} from "./webEvidenceCaptureWorksheet";
import type { WebEvidenceSearchResult } from "./webEvidenceIntake";
import {
  buildWebEvidenceSearchRun,
  type WebEvidenceSearchRun,
} from "./webEvidenceSearchRun";
import {
  rerunEvidenceGapSearch,
  type EvidenceGapSearchRerun,
} from "./evidenceGapSearchRerun";
import {
  buildCounselorReviewDossier,
  type CounselorReviewDossier,
} from "./counselorReviewDossier";
import {
  buildDetailedVolunteerPlanInterpretation,
  type DetailedVolunteerPlanInterpretation,
} from "./detailedVolunteerPlanInterpretation";
import {
  buildWebEvidenceResearchStrategy,
  type WebEvidenceResearchStrategy,
} from "./webEvidenceResearchStrategy";
import {
  buildFamilyDecisionClarityRoadmap,
  type FamilyDecisionClarityRoadmap,
} from "./familyDecisionClarityRoadmap";
import {
  buildHiddenOpportunityAudit,
  type HiddenOpportunityAudit,
} from "./hiddenOpportunityAudit";
import {
  buildPlanChangeOpportunityLedger,
  type PlanChangeOpportunityLedger,
} from "./planChangeOpportunityLedger";
import {
  buildVolunteerPlanNarrativePackage,
  type VolunteerPlanNarrativePackage,
} from "./volunteerPlanNarrativePackage";

export interface AdmissionsOpportunityDemoCase {
  protocol: "admissions_opportunity_demo_case_v1";
  studentName: string;
  workflow: AdmissionsOpportunityWorkflow;
  partialEvidenceResults: WebEvidenceSearchResult[];
  partialWorkspace: EvidenceCollectionWorkspace;
  captureWorksheet: WebEvidenceCaptureWorksheet;
  operatorSearchRun: WebEvidenceSearchRun;
  operatorCaptureNormalization: WebEvidenceCaptureNormalizationResult;
  readyWorkspace: EvidenceCollectionWorkspace;
  gapSearchRerun: EvidenceGapSearchRerun;
  counselorReviewDossier: CounselorReviewDossier;
  detailedInterpretation: DetailedVolunteerPlanInterpretation;
  researchStrategy: WebEvidenceResearchStrategy;
  familyClarityRoadmap: FamilyDecisionClarityRoadmap;
  hiddenOpportunityAudit: HiddenOpportunityAudit;
  planChangeOpportunityLedger: PlanChangeOpportunityLedger;
  volunteerPlanNarrativePackage: VolunteerPlanNarrativePackage;
  operatorRunbook: string[];
  familyExplanationPreview: string;
  claimBoundary: string;
}

const STUDENT_NAME = "Student A";
const CAPTURED_AT = "2026-06-16";
const CLAIM_BOUNDARY =
  "This demo case is not a final recommendation. It demonstrates the auditable workflow from official diff, public-opinion hypothesis, capture worksheet, evidence intake, and counselor-review package.";

export function buildAdmissionsOpportunityDemoCase(): AdmissionsOpportunityDemoCase {
  const workflow = buildAdmissionsOpportunityWorkflow(demoWorkflowInput());
  const partialEvidenceResults = [
    resultForTask(workflow, "official_plan_verification"),
  ];
  const partialWorkspace = buildEvidenceCollectionWorkspace({
    workflow,
    evidenceResults: partialEvidenceResults,
    studentName: STUDENT_NAME,
  });
  const captureWorksheet = buildWebEvidenceCaptureWorksheet({ workspace: partialWorkspace });
  const operatorSearchRun = buildWebEvidenceSearchRun({
    workspace: partialWorkspace,
    responses: buildOperatorSearchResponses(captureWorksheet),
    capturedAt: CAPTURED_AT,
  });
  const operatorCaptureNormalization = normalizeWebEvidenceCaptureSubmissions({
    workspace: partialWorkspace,
    submissions: buildOperatorSubmissions(captureWorksheet),
    capturedAt: CAPTURED_AT,
  });
  const readyWorkspace = buildEvidenceCollectionWorkspace({
    workflow,
    evidenceResults: [...partialEvidenceResults, ...operatorSearchRun.acceptedEvidenceResults],
    studentName: STUDENT_NAME,
  });
  const gapSearchRerun = rerunEvidenceGapSearch({
    workflow,
    workspace: readyWorkspace,
    currentEvidenceResults: [...partialEvidenceResults, ...operatorSearchRun.acceptedEvidenceResults],
    responses: buildGapSearchResponses(readyWorkspace),
    capturedAt: CAPTURED_AT,
    studentName: STUDENT_NAME,
  });
  const counselorReviewDossier = buildCounselorReviewDossier({
    workflow,
    workspace: gapSearchRerun.refreshedWorkspace,
    studentName: STUDENT_NAME,
    searchRuns: [operatorSearchRun, gapSearchRerun.searchRun],
  });
  const detailedInterpretation = buildDetailedVolunteerPlanInterpretation(counselorReviewDossier);
  const researchStrategy = buildWebEvidenceResearchStrategy({
    dossier: counselorReviewDossier,
    detailedInterpretation,
  });
  const familyDecisionBrief = counselorReviewDossier.decisionBrief;
  if (!familyDecisionBrief) {
    throw new Error("Demo case requires a family decision brief for clarity roadmap.");
  }
  const familyClarityRoadmap = buildFamilyDecisionClarityRoadmap({
    decisionBrief: familyDecisionBrief,
    detailedInterpretation,
  });
  const hiddenOpportunityAudit = buildHiddenOpportunityAudit({
    dossier: counselorReviewDossier,
    detailedInterpretation,
    researchStrategy,
    familyClarityRoadmap,
  });
  const planChangeOpportunityLedger = buildPlanChangeOpportunityLedger({
    gameMatrix: buildDemoPlanChangeLedgerGameMatrix(workflow),
    externalPlanAuditSummary: {
      parsedCount: 2,
    },
    hiddenOpportunityAudit,
  });
  const volunteerPlanNarrativePackage = buildVolunteerPlanNarrativePackage({
    detailedInterpretation,
    researchStrategy,
    familyClarityRoadmap,
    hiddenOpportunityAudit,
    planChangeOpportunityLedger,
  });

  return {
    protocol: "admissions_opportunity_demo_case_v1",
    studentName: STUDENT_NAME,
    workflow,
    partialEvidenceResults,
    partialWorkspace,
    captureWorksheet,
    operatorSearchRun,
    operatorCaptureNormalization,
    readyWorkspace,
    gapSearchRerun,
    counselorReviewDossier,
    detailedInterpretation,
    researchStrategy,
    familyClarityRoadmap,
    hiddenOpportunityAudit,
    planChangeOpportunityLedger,
    volunteerPlanNarrativePackage,
    operatorRunbook: [
      "Search official plan rows and confirm school code, group code, major code, quota, and subject requirements.",
      "Search public-opinion trend signals and keep them hypothesis-only.",
      "Paste excerpts into capture submissions using the worksheet templates.",
      "Run evidence gap follow-up searches when triangulation asks for second independent sources.",
      "Run evidence intake; do not move to counselor review until blocking official, rank, risk, and external-plan evidence pass.",
      "Use the interpretation package to explain professional group, adjustment, safe anchor, and interest tradeoff to the family.",
    ],
    familyExplanationPreview: gapSearchRerun.refreshedWorkspace.completion.interpretationPackage?.opportunityCards[0]?.familyReadableExplanation ?? "",
    claimBoundary: CLAIM_BOUNDARY,
  };
}

function buildDemoPlanChangeLedgerGameMatrix(workflow: AdmissionsOpportunityWorkflow) {
  const currentRow = workflow.inputEcho.currentRows[0];
  const officialChanges = workflow.planDiffResult.diffs.map((diff) => ({
    change_type: diff.diffType,
    before: diff.before,
    after: diff.after,
    evidence: diff.evidence,
    official_source: diff.officialSource,
    source_tier: "official",
    applied_to_ranking: true,
    rank_delta_estimate: {
      direction: "easier",
      rank_delta: 1800,
      explanation: "Quota expands from 20 to 36 seats; demand calibration is still required.",
    },
    external_plan_coverage: {
      competitor_missed: true,
      checked_sources: ["qianwen", "teacher"],
      evidence: "External plan kept last year's rank anchor and did not mention quota expansion.",
    },
    recommendation_action: "promote",
    risk_guard: {
      level: "medium",
      checks: ["do not use as safety anchor", "verify group code before final signoff"],
    },
  }));

  return {
    major_group_rows: currentRow
      ? [
          {
            school_name: currentRow.schoolName,
            school_code: currentRow.schoolCode,
            major_group_code: currentRow.majorGroupCode,
            choice_index: 1,
            strategy_tag: "target",
            major_list: [currentRow.majorName],
            plan_change_explanation: {
              status: "official_diff",
              ranking_impact: "official_diff_applied",
              official_changes: officialChanges,
            },
          },
        ]
      : [],
    data_vintage: {
      target_year: workflow.planDiffResult.currentYear,
      formal_recommendation_ready: true,
      limitations: [],
    },
  };
}

function demoWorkflowInput(): AdmissionsOpportunityWorkflowInput {
  return {
    priorYear: 2025,
    currentYear: 2026,
    province: "Guangdong",
    officialSource: "Guangdong Education Exam Authority 2026 enrollment plan",
    priorRows: [
      row({
        year: 2025,
        schoolCode: "10561",
        schoolName: "South China Tech",
        groupCode: "201",
        majorCode: "080901",
        majorName: "Computer Science",
        quota: 20,
      }),
    ],
    currentRows: [
      row({
        year: 2026,
        schoolCode: "10561",
        schoolName: "South China Tech",
        groupCode: "201",
        majorCode: "080901",
        majorName: "Computer Science",
        quota: 36,
      }),
    ],
    publicOpinionObservations: [
      {
        id: "search-1",
        sourceKind: "search_snippet",
        title: "Parents focus on local schools",
        capturedAt: CAPTURED_AT,
        text: "Discussion snippets mostly mention local brands and rarely mention South China Tech Computer Science.",
      },
      {
        id: "social-1",
        sourceKind: "social_summary",
        title: "Distance concern thread",
        capturedAt: CAPTURED_AT,
        text: "Families avoid non-local engineering options because of distance and adjustment concern.",
      },
    ],
    studentProfile: {
      preferredMajors: ["Computer Science", "Software Engineering"],
      blacklistMajors: ["Civil Engineering", "Materials"],
      riskTolerance: "balanced",
      acceptableTradeoffs: ["can_accept_medium_adjustment_risk"],
      conceptAnswers: {
        professionalGroup: "understands_group_unit",
        adjustment: "accepts_worst_case_major",
        safeAnchor: "checks_worst_case",
        interestTradeoff: "course_industry_city_workstyle",
      },
      careerAssessment: {
        mode: "quick",
        answers: { I1: 5, I2: 5, R1: 4, R2: 4, A1: 2, A2: 2, S1: 2, S2: 2, E1: 3, E2: 3, C1: 3, C2: 3 },
        career_values: ["growth"],
      },
    },
    rankDeltaEstimates: {
      "10561-201-080901-quota_expansion": {
        direction: "easier",
        rankDelta: 1800,
        confidence: "medium",
        explanation: "Quota expands from 20 to 36 seats; demand calibration is still required.",
      },
    },
    externalPlanSources: ["qianwen", "tencent", "teacher", "family"],
  };
}

function buildOperatorSearchResponses(worksheet: WebEvidenceCaptureWorksheet) {
  return worksheet.pendingRows.map((captureRow) => ({
    taskId: captureRow.taskId,
    provider: "demo-search-provider",
    results: [
      {
        title: sourceTitleFor(captureRow.taskType),
        url: sourceUrlFor(captureRow.taskType),
        snippet: excerptsFor(captureRow.taskType)[0] ?? "",
        sourceTier: captureRow.resultTemplate.sourceTier,
        excerpts: excerptsFor(captureRow.taskType),
        claimedSupports: captureRow.resultTemplate.claimedSupports,
      },
    ],
  }));
}

function buildOperatorSubmissions(worksheet: WebEvidenceCaptureWorksheet): WebEvidenceCaptureSubmission[] {
  return worksheet.pendingRows.map((captureRow) => ({
    ...captureRow.copyableSubmission,
    sourceTitle: sourceTitleFor(captureRow.taskType),
    sourceUrl: sourceUrlFor(captureRow.taskType),
    excerpts: excerptsFor(captureRow.taskType),
  }));
}

function buildGapSearchResponses(workspace: EvidenceCollectionWorkspace) {
  return workspace.evidenceGapSearchPlan.followUps.map((followUp) => ({
    taskId: followUp.taskId ?? followUp.id,
    provider: "demo-gap-search-provider",
    results: [
      {
        title: gapSourceTitleFor(followUp.claim),
        url: gapSourceUrlFor(followUp.claim),
        snippet: gapExcerptFor(followUp.claim),
        sourceTier: followUp.sourceTier,
        excerpts: [gapExcerptFor(followUp.claim)],
        claimedSupports: [followUp.claim],
      },
    ],
  }));
}

function resultForTask(
  workflow: AdmissionsOpportunityWorkflow,
  taskType:
    | "official_plan_verification"
    | "school_rule_verification"
    | "rank_history_calibration"
    | "public_opinion_scan"
    | "external_plan_comparison"
    | "family_concept_clarification",
): WebEvidenceSearchResult {
  const task = workflow.evidencePlan.tasks.find((candidate) => candidate.taskType === taskType);
  if (!task) {
    throw new Error(`Missing demo task: ${taskType}`);
  }

  if (taskType === "official_plan_verification") {
    return {
      taskId: task.id,
      sourceTitle: "Guangdong official 2026 enrollment plan",
      sourceUrl: "https://eea.gd.gov.cn/2026-plan",
      sourceTier: "official",
      capturedAt: CAPTURED_AT,
      excerpts: ["10561 major group 201 Computer Science quota 36; subject requirements physics and chemistry."],
      claimedSupports: ["official_diff"],
    };
  }

  if (taskType === "public_opinion_scan") {
    return {
      taskId: task.id,
      sourceTitle: "Search summary for non-local engineering attention",
      sourceUrl: "https://search.example/non-local-engineering",
      sourceTier: "public_opinion",
      capturedAt: CAPTURED_AT,
      excerpts: ["Search snippets emphasize local schools and rarely mention the quota expansion."],
      claimedSupports: ["hypothesis_only"],
    };
  }

  throw new Error(`Use capture worksheet for demo task: ${taskType}`);
}

function gapSourceTitleFor(claim: string): string {
  if (claim === "rank_delta") return "CHSI rank history second source";
  if (claim === "competitor_missed") return "Teacher plan comparison second source";
  return "Evidence gap second source";
}

function gapSourceUrlFor(claim: string): string {
  if (claim === "rank_delta") return "https://gaokao.chsi.com.cn/rank-history-second-source";
  if (claim === "competitor_missed") return "https://teacher-plan.example/review-second-source";
  return "https://example.com/evidence-gap-second-source";
}

function gapExcerptFor(claim: string): string {
  if (claim === "rank_delta") {
    return "The same school group has 2025 rank 42000 and 2024 rank 43800 with quota context.";
  }
  if (claim === "competitor_missed") {
    return "A second external plan still keeps the 2025 quota assumption and omits the 2026 expansion.";
  }
  return "Second independent source excerpt for evidence gap follow-up.";
}

function sourceTitleFor(taskType: WebEvidenceCaptureWorksheet["pendingRows"][number]["taskType"]): string {
  if (taskType === "school_rule_verification") return "South China Tech 2026 admission charter";
  if (taskType === "rank_history_calibration") return "Guangdong historical admission rank table";
  if (taskType === "external_plan_comparison") return "Qianwen and teacher plan comparison";
  if (taskType === "family_concept_clarification") return "Family concept checklist";
  if (taskType === "public_opinion_scan") return "Search summary for non-local engineering attention";
  return "Operator captured evidence";
}

function sourceUrlFor(taskType: WebEvidenceCaptureWorksheet["pendingRows"][number]["taskType"]): string {
  if (taskType === "school_rule_verification") return "https://admission.example/charter-2026";
  if (taskType === "rank_history_calibration") return "https://data.example/rank-history";
  if (taskType === "external_plan_comparison") return "https://example.com/external-plan-review";
  if (taskType === "family_concept_clarification") return "internal://concept-brief";
  if (taskType === "public_opinion_scan") return "https://search.example/non-local-engineering";
  return "https://example.com/captured-evidence";
}

function excerptsFor(taskType: WebEvidenceCaptureWorksheet["pendingRows"][number]["taskType"]): string[] {
  if (taskType === "school_rule_verification") {
    return ["Adjustment stays inside eligible majors in the same group; physical-exam restrictions must be checked."];
  }
  if (taskType === "rank_history_calibration") {
    return ["2025 rank 42000; 2024 rank 43800 for the same school group with quota context retained."];
  }
  if (taskType === "external_plan_comparison") {
    return ["External plans keep the 2025 quota assumption and omit the 2026 expansion."];
  }
  if (taskType === "family_concept_clarification") {
    return ["Professional group, adjustment, safe anchor, and interest tradeoff explained before final rows."];
  }
  if (taskType === "public_opinion_scan") {
    return ["Search snippets emphasize local schools and rarely mention the quota expansion."];
  }
  return ["Captured evidence excerpt."];
}

function row({
  year,
  schoolCode,
  schoolName,
  groupCode,
  majorCode,
  majorName,
  quota,
}: {
  year: number;
  schoolCode: string;
  schoolName: string;
  groupCode: string;
  majorCode: string;
  majorName: string;
  quota: number;
}) {
  return {
    year,
    officialSource: "Guangdong Education Exam Authority 2026 enrollment plan",
    province: "Guangdong",
    batch: "undergraduate",
    schoolCode,
    schoolName,
    majorGroupCode: groupCode,
    majorCode,
    majorName,
    quota,
    subjectRequirements: ["physics", "chemistry"],
  };
}

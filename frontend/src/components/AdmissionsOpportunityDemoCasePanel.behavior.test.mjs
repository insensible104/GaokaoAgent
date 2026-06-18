import assert from "node:assert/strict";
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const require = createRequire(import.meta.url);
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const here = path.dirname(fileURLToPath(import.meta.url));
const libDir = path.join(here, "..", "lib");

function loadTsModule(filePath, mocks = {}, jsx = ts.JsxEmit.React) {
  const source = fs.readFileSync(filePath, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      jsx,
      esModuleInterop: true,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (mocks[specifier]) return mocks[specifier];
    if (specifier === "react") return React;
    throw new Error(`Unexpected require: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const demoCase = {
  protocol: "admissions_opportunity_demo_case_v1",
  studentName: "Student A",
  workflow: {
    status: "needs_evidence_research",
    discoveryLedger: {
      insights: [
        {
          id: "insight-1",
          opportunityKind: "under_attention_opportunity",
          publicOpinionGuard: {
            status: "supports_hypothesis",
            opportunitySignal: "under_attention_candidate",
            confidence: "medium",
            summary: "Low-attention pattern is plausible after counter-evidence screening.",
            nextActions: ["Verify with dated search results."],
          },
        },
      ],
    },
    trendAnalysis: {
      trendLanguageGate: {
        protocol: "public_opinion_trend_language_gate_v1",
        status: "hypothesis_only",
        score: 76,
        canUseHiddenOpportunityLabel: true,
        familySafeWording:
          "South China Tech Computer Science can be described only as an under-attention candidate.",
        requiredEvidence: [
          "Attach official plan diff before using trend language.",
          "Keep wording as hypothesis-only until counselor review.",
        ],
        forbiddenWording: [
          "Do not say public opinion proves demand.",
          "Do not say guaranteed admission.",
        ],
        claimBoundary: "Trend language gates decide wording only.",
      },
    },
    evidencePlan: { tasks: [{ id: "task-1" }] },
  },
  partialEvidenceResults: [{ taskId: "official-plan" }, { taskId: "public-opinion" }],
  partialWorkspace: {
    status: "collecting_evidence",
    coverageSummary: {
      totalTasks: 6,
      blockingTasks: 4,
      completedBlockingTasks: 1,
      acceptedEvidenceCount: 2,
      rejectedEvidenceCount: 0,
      missingClaims: ["rank_delta", "risk_guard", "competitor_missed", "final_recommendation"],
    },
  },
  captureWorksheet: {
    status: "ready_to_capture",
    pendingRows: [
      { taskType: "rank_history_calibration" },
      { taskType: "school_rule_verification" },
      { taskType: "external_plan_comparison" },
      { taskType: "family_concept_clarification" },
    ],
  },
  operatorCaptureNormalization: {
    evidenceResults: [{}, {}, {}, {}],
    rejectedSubmissions: [],
  },
  operatorSearchRun: {
    protocol: "web_evidence_search_run_v1",
    status: "completed",
    providerResponseCount: 4,
    acceptedEvidenceResults: [{}, {}, {}, {}],
    rejectedAdapterResults: [],
    rejectedCaptureSubmissions: [],
    unreturnedTaskIds: [],
    nextActions: ["Attach 4 normalized evidence results to evidence intake."],
    claimBoundary:
      "Search runs collect candidate evidence and normalize it for intake. They do not support claims or make final recommendations by themselves.",
  },
  gapSearchRerun: {
    protocol: "evidence_gap_search_rerun_v1",
    searchRun: {
      status: "completed",
      acceptedEvidenceResults: [{}, {}],
    },
    mergedEvidenceResults: [{}, {}, {}, {}, {}, {}],
    refreshedWorkspace: {
      status: "ready_for_counselor_review",
      evidenceGapSearchPlan: {
        status: "no_gaps",
      },
    },
    nextActions: ["Counselor review can start with the attached evidence-backed interpretation package."],
    claimBoundary:
      "Evidence gap search reruns merge follow-up search evidence and refresh triangulation. They do not make final recommendations.",
  },
  counselorReviewDossier: {
    protocol: "counselor_review_dossier_v1",
    status: "ready_for_counselor_review",
    caseSummary: {
      studentName: "Student A",
      summary: "This case is review-ready: blocking evidence passed intake and counselor signoff is still required.",
    },
    opportunityThesis:
      "quota_expansion: 10561-201-080901-quota_expansion. Public opinion remains a hypothesis, not demand proof.",
    evidenceTrail: [
      {
        claim: "official_diff",
        sourceTitle: "Guangdong official 2026 enrollment plan",
        sourceTier: "official",
      },
      {
        claim: "rank_delta",
        sourceTitle: "CHSI rank history second source",
        sourceTier: "historical_data",
      },
    ],
    publicOpinionPosition: {
      guardStatus: "supports_hypothesis",
      opportunitySignal: "under_attention_candidate",
      confidence: "medium",
      evidenceRole: "hypothesis_only",
      familySafeSummary: "Low-attention pattern is still a hypothesis.",
      requiredFollowUps: ["Verify with dated search results."],
      wordingGateStatus: "hypothesis_only",
      wordingGateScore: 76,
      canUseHiddenOpportunityLabel: true,
      familySafeWording:
        "South China Tech Computer Science can be described only as an under-attention candidate.",
      requiredEvidence: [
        "Attach official plan diff before using trend language.",
        "Keep wording as hypothesis-only until counselor review.",
      ],
      forbiddenWording: [
        "Do not say public opinion proves demand.",
        "Do not say guaranteed admission.",
      ],
    },
    gapPosition: {
      status: "no_gaps",
      triangulationStatus: "triangulated",
      followUpCount: 0,
      unresolvedClaims: [],
    },
    searchProvenance: {
      protocol: "counselor_search_provenance_v1",
      runCount: 2,
      providerIds: ["demo-search-provider", "demo-gap-search-provider"],
      summary: {
        acceptedRows: 6,
        rejectedRows: 0,
        unreturnedRows: 0,
      },
      queryRows: [
        {
          taskId: "rank-history",
          taskType: "rank_history_calibration",
          query: "Guangdong rank history query",
          sourceTier: "historical_data",
          allowedClaims: ["rank_delta"],
        },
        {
          taskId: "rank-history",
          taskType: "rank_history_calibration",
          query: "Guangdong rank history query second independent source",
          sourceTier: "historical_data",
          allowedClaims: ["rank_delta"],
        },
        {
          taskId: "public-opinion",
          taskType: "public_opinion_scan",
          query: "South China Tech Computer Science counter-evidence widely discussed mainstream attention popular",
          sourceTier: "public_opinion",
          allowedClaims: ["hypothesis_only"],
          searchIntent: "counter_evidence",
          evidenceQuestion: "What evidence would disprove the low-attention hypothesis or show broad recognition?",
          rejectsAsProof: ["official plan", "admission probability", "final recommendation"],
        },
        {
          taskId: "public-opinion",
          taskType: "public_opinion_scan",
          query: "South China Tech Computer Science hype pressure hot major high salary everyone applying",
          sourceTier: "public_opinion",
          allowedClaims: ["hypothesis_only"],
          searchIntent: "hype_pressure",
          evidenceQuestion: "Is the topic crowded or hyped enough to block hidden-opportunity wording?",
          rejectsAsProof: ["official plan", "admission probability", "final recommendation"],
        },
      ],
      resultRows: [
        {
          taskId: "rank-history",
          taskType: "rank_history_calibration",
          query: "Guangdong rank history query second independent source",
          provider: "demo-gap-search-provider",
          outcome: "accepted",
          sourceTitle: "CHSI rank history second source",
          rejectionReason: null,
        },
      ],
      claimBoundary: "Search provenance is provider provenance only, not claim support.",
    },
    evidenceQuality: {
      protocol: "counselor_evidence_quality_v1",
      status: "review_ready",
      assessedAt: "2026-06-16",
      summary: {
        authoritativeSources: 2,
        currentCycleSources: 6,
        staleSources: 0,
        conflictedClaims: 0,
        rejectedSearchRows: 0,
        unreturnedSearchRows: 0,
      },
      sourceRows: [
        {
          taskId: "official-plan",
          claim: "official_diff",
          sourceTitle: "Guangdong official 2026 enrollment plan",
          sourceTier: "official",
          capturedAt: "2026-06-16",
          authorityLevel: "authoritative",
          freshness: "current_cycle",
          riskFlags: [],
        },
      ],
      blockingConcerns: [],
      familyPresentationGate:
        "This dossier can be shown as a counselor-review explanation, with final filing still gated by counselor signoff.",
      claimBoundary: "Evidence quality scores source authority, freshness, conflicts, and search gaps.",
    },
    whatWeCanSay: [
      "Official quota expansion evidence is attached.",
      "Rank impact can be discussed directionally.",
      "Public-opinion wording may say under-attention candidate only as hypothesis-only.",
    ],
    whatWeCannotSay: [
      "This is not a final recommendation.",
      "This is not an admission guarantee.",
      "Public-opinion evidence cannot prove demand.",
    ],
    counselorReviewChecklist: [
      "Verify the official source row.",
      "Confirm the family accepts the worst-case adjusted major.",
    ],
    familyQuestions: ["Would you still accept the group if the final major is not Computer Science?"],
    claimBoundary:
      "This dossier is not a final filing recommendation. It organizes auditable evidence, claim limits, and counselor-review questions.",
  },
  detailedInterpretation: {
    protocol: "detailed_volunteer_plan_interpretation_v1",
    status: "ready_for_family_review",
    headline: "Student A: evidence-backed plan interpretation ready for family review",
    summary:
      "quota_expansion: 10561-201-080901-quota_expansion. Public opinion remains a hypothesis, not demand proof.",
    claimRows: [
      {
        claim: "official_diff",
        stance: "can_explain",
        familyWording: "The official plan change is attached and can be used as the factual starting point.",
        evidenceBasis: ["10561 group 201 Computer Science quota 36."],
        sourceRefs: ["Guangdong official 2026 enrollment plan (official)"],
        counterChecks: ["Recheck school code, group code, major code, quota, subject requirements, and official URL before filing."],
        claimBoundary: "Official diff supports that the plan row changed; it does not by itself prove admission probability.",
      },
      {
        claim: "trend_wording",
        stance: "hypothesis_only",
        familyWording:
          "South China Tech Computer Science can be described only as an under-attention candidate.",
        evidenceBasis: ["Trend language gate: hypothesis_only; score 76."],
        sourceRefs: ["Search summary for non-local engineering attention (public_opinion)"],
        counterChecks: [
          "counter_evidence: What evidence would disprove the low-attention hypothesis?; rejects as proof: official plan, admission probability, final recommendation",
          "hype_pressure: Is the topic crowded enough to block hidden-opportunity wording?; rejects as proof: official plan, admission probability, final recommendation",
        ],
        claimBoundary:
          "Public-opinion evidence can frame a low-attention hypothesis only. It cannot prove demand, score movement, admission probability, or final recommendation quality.",
      },
      {
        claim: "concept_readiness",
        stance: "can_explain",
        familyWording: "Concept readiness supports row-level discussion.",
        evidenceBasis: ["professional_group: understood; Family accepts group-level uncertainty."],
        sourceRefs: ["Family concept checklist (concept)"],
        counterChecks: [],
        claimBoundary: "Concept readiness is a communication gate.",
      },
    ],
    familyDecisionPath: {
      conceptReadinessProtocol: "family_concept_readiness_v1",
      conceptReadinessStatus: "ready",
      requiredQuestions: ["Would you still accept the group if the final major is not Computer Science?"],
      hardStops: ["Do not recommend majors matching blacklist: Civil Engineering."],
    },
    planPosition: {
      rowUse: "candidate_for_counselor_review",
      notARecommendationReasons: [
        "This is not a final recommendation.",
        "This is not an admission guarantee.",
      ],
      counselorSignoffChecklist: [
        "Verify the official source row.",
        "Confirm the family accepts the worst-case adjusted major.",
      ],
    },
    nextActions: [
      "Use this as a family-review explanation only after counselor signoff.",
      "Keep public-opinion wording hypothesis-only and preserve counter-evidence checks.",
    ],
    claimBoundary:
      "This detailed interpretation is not a final filing recommendation. It translates the counselor dossier into family-readable reasoning.",
  },
  researchStrategy: {
    protocol: "web_evidence_research_strategy_v1",
    status: "ready_to_run",
    researchPillars: [
      {
        pillar: "official_plan",
        status: "covered",
        evidenceCount: 1,
        nextCheck: "Verify official school code, group code, major code, quota, subject requirements, and source URL.",
      },
      {
        pillar: "public_opinion_trend",
        status: "needs_counter_check",
        evidenceCount: 1,
        nextCheck:
          "Run low-attention, counter-evidence, hype-pressure, regional-preference, and source-diversity searches.",
      },
    ],
    priorityQueries: [
      {
        id: "public-opinion-counter",
        status: "ready",
        priority: "critical",
        taskType: "public_opinion_scan",
        searchIntent: "counter_evidence",
        query: "South China Tech Computer Science counter-evidence widely discussed mainstream attention popular",
        sourceTier: "public_opinion",
        evidenceQuestion: "What evidence would disprove the low-attention hypothesis?",
        allowedClaims: ["hypothesis_only"],
        rejectsAsProof: ["official plan", "admission probability", "final recommendation"],
        escalationRule:
          "If broad recognition appears, block low-attention or hidden-opportunity wording and keep the claim as hypothesis-only.",
      },
      {
        id: "public-opinion-hype",
        status: "ready",
        priority: "high",
        taskType: "public_opinion_scan",
        searchIntent: "hype_pressure",
        query: "South China Tech Computer Science hype pressure hot major high salary everyone applying",
        sourceTier: "public_opinion",
        evidenceQuestion: "Is the topic crowded enough to block hidden-opportunity wording?",
        allowedClaims: ["hypothesis_only"],
        rejectsAsProof: ["official plan", "admission probability", "final recommendation"],
        escalationRule:
          "If hype pressure appears, block hidden-opportunity wording and require counselor review before family presentation.",
      },
    ],
    contradictionTests: [
      "Search for broad recognition, hype pressure, or mainstream attention before using under-attention wording.",
    ],
    minimumEvidenceRules: [
      "Official plan diff must be attached before opportunity language is used.",
      "Public-opinion trend language requires low-attention evidence, counter-evidence search, hype-pressure search, and source diversity; it remains hypothesis-only.",
      "Final recommendation remains forbidden until counselor signoff.",
    ],
    presentationGate:
      "Use as a family-review explanation only after counselor signoff; keep public-opinion wording hypothesis-only.",
    operatorBrief: [
      "Run counter-evidence and hype-pressure searches before using trend wording.",
      "Keep public-opinion evidence as hypothesis-only; never use it as admission probability or final recommendation proof.",
    ],
    claimBoundary:
      "This research strategy does not support claims or make recommendations.",
  },
  familyClarityRoadmap: {
    protocol: "family_decision_clarity_roadmap_v1",
    status: "ready_for_row_discussion",
    conceptCards: [
      {
        concept: "professional_group",
        status: "understood",
        plainMeaning: "The filing unit is a school major group, not one favorite major.",
        familyQuestion: "Can the family explain that filing is by school major group?",
        evidenceNeeded: "Family accepts group-level uncertainty.",
        decisionImpact: "Blocks row discussion when the family treats one group as one single major.",
        repairAction: "Keep this concept visible during row discussion.",
      },
      {
        concept: "interest_tradeoff",
        status: "understood",
        plainMeaning: "Interest should be explained through courses, industry path, city, work style, and regret tolerance.",
        familyQuestion: "Can the student describe interest beyond the major label?",
        evidenceNeeded: "Student gives interest reasons beyond a hot major label.",
        decisionImpact: "Determines whether the student is choosing a real direction or reacting to a crowded label.",
        repairAction: "Keep this concept visible during row discussion.",
      },
    ],
    interestAxes: [
      {
        axis: "course_content",
        prompt: "Which courses would the student willingly study for four years?",
        whyItMatters: "Course content turns a major label into a daily learning commitment.",
        evidenceToCollect: "Primary interest direction: Computer Science.",
      },
      {
        axis: "regret_boundary",
        prompt: "Which outcome would make the family regret accepting this row even if admission succeeds?",
        whyItMatters: "Regret boundaries define the real blacklist and safe-anchor floor.",
        evidenceToCollect: "Do not recommend majors matching blacklist: Civil Engineering.",
      },
    ],
    parentStudentAlignment: {
      questions: ["Which matters more for this row: school platform, major certainty, city, tuition, or low regret risk?"],
      hardStops: ["This is not a final recommendation."],
    },
    rowDiscussionGate: {
      canDiscussRows: true,
      nextAction: "Concept readiness supports row-level discussion; use the interest axes before final counselor signoff.",
      blockedReasons: [],
    },
    claimBoundary:
      "This roadmap is for communication and decision-clarity only.",
  },
  hiddenOpportunityAudit: {
    protocol: "hidden_opportunity_audit_v1",
    status: "candidate_for_counselor_review",
    labelPermission: "under_attention_candidate_only",
    score: 100,
    scoreBands: [
      {
        factor: "official_change",
        points: 15,
        maxPoints: 15,
        rationale: "Official plan diff is attached and can be explained.",
      },
      {
        factor: "counter_evidence_clearance",
        points: 10,
        maxPoints: 10,
        rationale: "Counter-evidence search has been run without rejected or unreturned rows.",
      },
      {
        factor: "hype_pressure_clearance",
        points: 10,
        maxPoints: 10,
        rationale: "Hype-pressure search has been run without rejected or unreturned rows.",
      },
      {
        factor: "family_readiness",
        points: 10,
        maxPoints: 10,
        rationale: "Family concept readiness allows row-level discussion.",
      },
    ],
    positiveSignals: ["Official quota expansion evidence is attached."],
    negativeSignals: [],
    requiredBeforeFamilyWording: [],
    forbiddenClaims: [
      "Do not claim admission guarantee.",
      "Do not claim final recommendation.",
      "Do not claim public opinion proves demand.",
    ],
    reviewGate: {
      canEnterLedger: true,
      canUseHiddenOpportunityLabel: true,
      mustStayHypothesisOnly: true,
      counselorSignoffRequired: true,
      reasons: ["Public-opinion signals remain hypothesis-only even when the row enters the opportunity ledger."],
    },
    claimBoundary:
      "Hidden opportunity audit is a counselor-review gate only. Public-opinion evidence must stay hypothesis-only.",
  },
  planChangeOpportunityLedger: {
    protocol: "plan_change_opportunity_ledger_v1",
    targetYear: 2026,
    score: 100,
    status: "ready",
    hiddenOpportunityGate: {
      status: "candidate_cleared",
      canEnterLedger: true,
      labelPermission: "under_attention_candidate_only",
      score: 100,
      reasons: ["Public-opinion signals remain hypothesis-only even when the row enters the opportunity ledger."],
      claimBoundary: "Hidden opportunity audit is a counselor-review gate only.",
    },
    opportunities: [
      {
        id: "10561-201-quota_expansion-0",
        officialSource: "Guangdong Education Exam Authority 2026 enrollment plan",
        diffType: "quota_expansion",
        affectedRows: [
          {
            choiceIndex: 1,
            schoolName: "South China Tech",
            schoolCode: "10561",
            majorGroupCode: "201",
            strategyTag: "target",
          },
        ],
        rankDeltaEstimate: {
          direction: "easier",
          rankDelta: 1800,
          explanation: "Quota expands from 20 to 36 seats.",
        },
        competitorMissed: {
          status: "missed",
          checkedSources: ["qianwen", "teacher"],
          evidence: "External plan kept last year's rank anchor and did not mention quota expansion.",
        },
        recommendationAction: "promote",
        riskGuard: {
          level: "medium",
          checks: ["do not use as safety anchor", "verify group code before final signoff"],
        },
        hiddenOpportunityAudit: {
          protocol: "hidden_opportunity_audit_v1",
          status: "candidate_for_counselor_review",
          labelPermission: "under_attention_candidate_only",
          score: 100,
          canEnterLedger: true,
          mustStayHypothesisOnly: true,
          claimBoundary: "Hidden opportunity audit is a counselor-review gate only.",
        },
        auditScore: 100,
        status: "ready",
        evidence: "Guangdong 2026 official plan row",
        auditTrail: ["hidden_opportunity_audit=can_enter_ledger:candidate_for_counselor_review"],
      },
    ],
    blockedClaims: [],
    summary: "1 official plan-change opportunity object(s), top audit score 100.",
    nextAction: "Promote the top audited opportunity into counselor review, while keeping the risk guard attached.",
    claimBoundary: "Plan change opportunity ledger is an audit object for official enrollment-plan differences.",
  },
  volunteerPlanNarrativePackage: {
    protocol: "volunteer_plan_narrative_package_v1",
    status: "ready_for_family_delivery",
    headline: "Student A: evidence-backed family narrative",
    planRows: [
      {
        id: "10561-201-quota_expansion-0",
        displayName: "South China Tech / 201",
        position: "audited_opportunity_candidate",
        labelPermission: "under_attention_candidate_only",
        mustStayHypothesisOnly: true,
        familyWording:
          "Official quota expansion and external omission can be discussed as an under-attention candidate, not a final recommendation.",
        evidencePillars: [
          {
            claim: "plan_change_ledger",
            stance: "ledger_ready",
            familyWording: "quota_expansion is in the plan-change ledger with audit score 100.",
            evidenceBasis: ["Guangdong 2026 official plan row", "Quota expands from 20 to 36 seats."],
            sourceRefs: ["Guangdong Education Exam Authority 2026 enrollment plan"],
            counterChecks: ["do not use as safety anchor"],
            claimBoundary: "Plan change opportunity ledger is an audit object.",
          },
          {
            claim: "trend_wording",
            stance: "hypothesis_only",
            familyWording: "Public-opinion language stays hypothesis-only.",
            evidenceBasis: ["Low-attention snippets exist."],
            sourceRefs: ["search-run"],
            counterChecks: ["counter_evidence", "hype_pressure"],
            claimBoundary: "Public opinion stays hypothesis-only.",
          },
        ],
        searchFollowUps: [
          "counter-evidence: What evidence would disprove the low-attention hypothesis?",
          "Search for broad recognition, hype pressure, or mainstream attention.",
        ],
        conceptPrompts: ["Can the family explain that filing is by school major group?"],
        interestPrompts: ["Which courses would the student willingly study for four years?"],
        riskGuard: ["do not use as safety anchor", "verify group code before final signoff"],
      },
    ],
    conversationFlow: [
      "Start with the official plan change, then show what is verified and what is still bounded.",
      "Use the interest axes to test whether the student wants the course content.",
    ],
    deliveryGate: {
      canShowToFamily: true,
      counselorSignoffRequired: true,
      blockedReasons: [],
    },
    forbiddenClaims: ["Do not claim admission guarantee.", "Final recommendation remains forbidden."],
    nextActions: ["Use this as family-review explanation after counselor signoff."],
    claimBoundary:
      "Volunteer plan narrative package organizes evidence, search follow-ups, and family discussion prompts.",
  },
  readyWorkspace: {
    protocol: "evidence_collection_workspace_v1",
    status: "ready_for_counselor_review",
    searchBrief: { protocol: "web_evidence_search_brief_v1", status: "ready_to_search", taskBriefs: [], claimBoundary: "" },
    completion: {
      protocol: "admissions_opportunity_workflow_completion_v1",
      status: "interpretation_ready",
      blockedReasons: [],
      nextAction: "Counselor review can start with the attached evidence-backed interpretation package.",
      claimBoundary: "Workflow completion can produce a counselor-review package, not a final recommendation.",
      interpretationPackage: {
        status: "counselor_review_ready",
        opportunityCards: [
          {
            familyReadableExplanation:
              "Professional group: the application unit is the school major group, not a single major. Adjustment: accepting adjustment protects admission chance but may change the final major.",
            familyDecisionBrief: {
              protocol: "family_decision_brief_v1",
              status: "ready_for_family_discussion",
              interestFitSummary: "Primary interest direction: Computer Science. Student fit is fit.",
              riskPosture: "Interest brief is ready_for_plan_discussion; risk tolerance is balanced.",
              hardBoundaries: ["Do not recommend majors matching blacklist: Civil Engineering."],
              conceptCheckpoints: [
                "Professional group: the unit of filing is a school major group, not a single favorite major.",
                "Adjustment: accepting adjustment protects admission chance, but the final major may change.",
              ],
              conceptReadiness: {
                protocol: "family_concept_readiness_v1",
                status: "ready",
                checkpoints: [
                  {
                    concept: "professional_group",
                    status: "understood",
                    familyQuestion: "Can the family explain that filing is by school major group?",
                    evidenceNeeded: "Family accepts group-level uncertainty.",
                  },
                  {
                    concept: "safe_anchor",
                    status: "understood",
                    familyQuestion: "Can the family define safe by worst acceptable outcome?",
                    evidenceNeeded: "Family checks worst-case major, campus, fee, and city.",
                  },
                ],
                nextAction: "Concept readiness supports row-level discussion.",
                claimBoundary: "Concept readiness is a communication gate.",
              },
              decisionQuestions: ["Would you still accept the group if the final major is not Computer Science?"],
              cannotClaim: ["This is not a final recommendation."],
            },
          },
        ],
      },
      intakeResult: {
        protocol: "web_evidence_intake_v1",
        status: "review_ready",
        acceptedEvidence: [],
        rejectedEvidence: [],
        blockedTasks: [],
        claimSupport: {},
        claimBoundary: "",
      },
    },
    coverageSummary: {
      totalTasks: 6,
      blockingTasks: 4,
      completedBlockingTasks: 4,
      acceptedEvidenceCount: 6,
      rejectedEvidenceCount: 0,
      missingClaims: ["final_recommendation"],
    },
    taskRows: [],
    nextSearchActions: ["Counselor review can start with the attached evidence-backed interpretation package."],
    familyConceptReadiness: {
      status: "explained",
      nextAction: "Family concepts have supporting explanation evidence attached.",
    },
    claimBoundary:
      "Evidence collection workspace coordinates collection and readiness. It does not make final recommendations or replace counselor review.",
  },
  operatorRunbook: [
    "Search official plan rows and confirm school code, group code, major code, quota, and subject requirements.",
    "Paste excerpts into capture submissions using the worksheet templates.",
  ],
  familyExplanationPreview:
    "Professional group: the application unit is the school major group, not a single major. Adjustment: accepting adjustment protects admission chance but may change the final major.",
  claimBoundary: "This demo case is not a final recommendation.",
};

const panel = loadTsModule(path.join(here, "AdmissionsOpportunityDemoCasePanel.tsx"), {
  "../lib/admissionsOpportunityDemoCase": {
    buildAdmissionsOpportunityDemoCase: () => demoCase,
  },
  "./EvidenceCollectionWorkspacePanel": {
    EvidenceCollectionWorkspacePanel: ({ workspace }) =>
      React.createElement("section", { "data-protocol": workspace.protocol }, workspace.status),
  },
});

const markup = renderToStaticMarkup(React.createElement(panel.AdmissionsOpportunityDemoCasePanel));

assert.match(markup, /data-protocol="admissions_opportunity_demo_case_v1"/);
assert.match(markup, /趋势机会研究演示案例/);
assert.match(markup, /Student A/);
assert.match(markup, /collecting_evidence/);
assert.match(markup, /ready_for_counselor_review/);
assert.match(markup, /1 \/ 4/);
assert.match(markup, /4 \/ 4/);
assert.match(markup, /ready_to_capture/);
assert.match(markup, /舆情线索门禁/);
assert.match(markup, /supports_hypothesis/);
assert.match(markup, /under_attention_candidate/);
assert.match(markup, /Verify with dated search results/);
assert.match(markup, /趋势措辞门禁/);
assert.match(markup, /public_opinion_trend_language_gate_v1/);
assert.match(markup, /hypothesis_only/);
assert.match(markup, /评分：76/);
assert.match(markup, /under-attention candidate/);
assert.match(markup, /Do not say public opinion proves demand/);
assert.match(markup, /rank_history_calibration/);
assert.match(markup, /搜索执行记录/);
assert.match(markup, /web_evidence_search_run_v1/);
assert.match(markup, /completed/);
assert.match(markup, /缺口补采复跑/);
assert.match(markup, /evidence_gap_search_rerun_v1/);
assert.match(markup, /no_gaps/);
assert.match(markup, /已合并 6 条证据结果/);
assert.match(markup, /4 条归一化证据结果/);
assert.match(markup, /人工采集归一化/);
assert.match(markup, /Search official plan rows/);
assert.match(markup, /Paste excerpts into capture submissions/);
assert.match(markup, /Professional group/);
assert.match(markup, /Adjustment/);
assert.match(markup, /决策简报/);
assert.match(markup, /family_decision_brief_v1/);
assert.match(markup, /risk tolerance is balanced/);
assert.match(markup, /family_concept_readiness_v1/);
assert.match(markup, /概念理解准备度/);
assert.match(markup, /professional_group/);
assert.match(markup, /Concept readiness supports row-level discussion/);
assert.match(markup, /Would you still accept/);
assert.match(markup, /Counselor review dossier/);
assert.match(markup, /counselor_review_dossier_v1/);
assert.match(markup, /quota_expansion/);
assert.match(markup, /Trend wording boundary/);
assert.match(markup, /hidden label: allowed/);
assert.match(markup, /South China Tech Computer Science can be described only as an under-attention candidate/);
assert.match(markup, /Search provenance/);
assert.match(markup, /counselor_search_provenance_v1/);
assert.match(markup, /demo-gap-search-provider/);
assert.match(markup, /second independent source/);
assert.match(markup, /counter_evidence/);
assert.match(markup, /hype_pressure/);
assert.match(markup, /What evidence would disprove/);
assert.match(markup, /admission probability/);
assert.match(markup, /accepted: 6/);
assert.match(markup, /Evidence quality/);
assert.match(markup, /counselor_evidence_quality_v1/);
assert.match(markup, /review_ready/);
assert.match(markup, /authoritative: 2/);
assert.match(markup, /current cycle: 6/);
assert.match(markup, /can be shown as a counselor-review explanation/);
assert.match(markup, /Detailed interpretation/);
assert.match(markup, /detailed_volunteer_plan_interpretation_v1/);
assert.match(markup, /ready_for_family_review/);
assert.match(markup, /candidate_for_counselor_review/);
assert.match(markup, /trend_wording/);
assert.match(markup, /concept_readiness/);
assert.match(markup, /counter_evidence/);
assert.match(markup, /hype_pressure/);
assert.match(markup, /family_concept_readiness_v1/);
assert.match(markup, /Web research strategy/);
assert.match(markup, /web_evidence_research_strategy_v1/);
assert.match(markup, /ready_to_run/);
assert.match(markup, /public_opinion_trend/);
assert.match(markup, /needs_counter_check/);
assert.match(markup, /critical/);
assert.match(markup, /Run counter-evidence and hype-pressure searches/);
assert.match(markup, /Final recommendation remains forbidden/);
assert.match(markup, /Family clarity roadmap/);
assert.match(markup, /family_decision_clarity_roadmap_v1/);
assert.match(markup, /ready_for_row_discussion/);
assert.match(markup, /professional_group/);
assert.match(markup, /interest_tradeoff/);
assert.match(markup, /course_content/);
assert.match(markup, /regret_boundary/);
assert.match(markup, /row-level discussion/);
assert.match(markup, /Hidden opportunity audit/);
assert.match(markup, /hidden_opportunity_audit_v1/);
assert.match(markup, /candidate_for_counselor_review/);
assert.match(markup, /under_attention_candidate_only/);
assert.match(markup, /counter_evidence_clearance/);
assert.match(markup, /hype_pressure_clearance/);
assert.match(markup, /family_readiness/);
assert.match(markup, /can enter ledger: yes/);
assert.match(markup, /must stay hypothesis-only: yes/);
assert.match(markup, /Plan change ledger handoff/);
assert.match(markup, /plan_change_opportunity_ledger_v1/);
assert.match(markup, /candidate_cleared/);
assert.match(markup, /quota_expansion/);
assert.match(markup, /hidden_opportunity_audit=can_enter_ledger/);
assert.match(markup, /Evidence-backed plan narrative/);
assert.match(markup, /volunteer_plan_narrative_package_v1/);
assert.match(markup, /ready_for_family_delivery/);
assert.match(markup, /audited_opportunity_candidate/);
assert.match(markup, /plan_change_ledger/);
assert.match(markup, /trend_wording/);
assert.match(markup, /counter-evidence/);
assert.match(markup, /Which courses would the student willingly study/);
assert.match(markup, /Official quota expansion evidence is attached/);
assert.match(markup, /admission guarantee/);
assert.match(markup, /Verify the official source row/);
assert.match(markup, /not a final recommendation/);
assert.match(markup, /not a final recommendation/);
assert.match(markup, /data-protocol="evidence_collection_workspace_v1"/);

console.log("Admissions opportunity demo case panel behavior test passed");

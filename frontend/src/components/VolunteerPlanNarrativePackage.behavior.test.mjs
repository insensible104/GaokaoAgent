import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const libDir = path.join(here, "..", "lib");

function loadTsModule(filePath, mocks = {}) {
  const source = fs.readFileSync(filePath, "utf8");
  const output = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      esModuleInterop: true,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (mocks[specifier]) return mocks[specifier];
    throw new Error(`Unexpected require: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const narrative = loadTsModule(path.join(libDir, "volunteerPlanNarrativePackage.ts"));

const detailedInterpretation = {
  protocol: "detailed_volunteer_plan_interpretation_v1",
  status: "ready_for_family_review",
  headline: "Student A: evidence-backed plan interpretation ready for family review",
  summary: "Official quota expansion, rank history, external omission, and public-opinion hypothesis are ready for family review.",
  claimRows: [
    {
      claim: "official_diff",
      stance: "can_explain",
      familyWording: "The 2026 official plan expands quota for this group.",
      evidenceBasis: ["Guangdong official plan row confirms quota expansion."],
      sourceRefs: ["official-plan"],
      counterChecks: [],
      claimBoundary: "Official diff does not prove admission probability.",
    },
    {
      claim: "rank_delta",
      stance: "can_explain",
      familyWording: "Rank direction can be discussed as easier after calibration.",
      evidenceBasis: ["Rank delta estimate: easier 1800."],
      sourceRefs: ["rank-history"],
      counterChecks: ["Check second rank-history source."],
      claimBoundary: "Rank delta is directional.",
    },
    {
      claim: "trend_wording",
      stance: "hypothesis_only",
      familyWording: "Public discussion supports only under-attention candidate wording.",
      evidenceBasis: ["Low-attention snippets exist."],
      sourceRefs: ["search-run"],
      counterChecks: ["counter_evidence", "hype_pressure"],
      claimBoundary: "Public opinion stays hypothesis-only.",
    },
  ],
  familyDecisionPath: {
    conceptReadinessProtocol: "family_concept_readiness_v1",
    conceptReadinessStatus: "ready",
    requiredQuestions: ["Would you still accept the group if adjusted away from Computer Science?"],
    hardStops: ["This is not a final recommendation."],
  },
  planPosition: {
    rowUse: "candidate_for_counselor_review",
    notARecommendationReasons: ["Final recommendation remains forbidden."],
    counselorSignoffChecklist: ["Verify group code before final signoff."],
  },
  nextActions: ["Use this as family-review explanation after counselor signoff."],
  claimBoundary: "Detailed interpretation is not a final filing recommendation.",
};

const researchStrategy = {
  protocol: "web_evidence_research_strategy_v1",
  status: "ready_to_run",
  researchPillars: [
    {
      pillar: "official_plan",
      status: "covered",
      evidenceCount: 1,
      nextCheck: "Verify official school code, group code, major code, quota, and source URL.",
    },
    {
      pillar: "public_opinion_trend",
      status: "needs_counter_check",
      evidenceCount: 1,
      nextCheck: "Run low-attention, counter-evidence, hype-pressure, regional-preference, and source-diversity searches.",
    },
  ],
  priorityQueries: [
    {
      id: "counter",
      status: "ready",
      priority: "critical",
      taskType: "public_opinion_scan",
      searchIntent: "counter_evidence",
      query: "South China Tech Computer Science counter-evidence mainstream attention",
      sourceTier: "public_opinion",
      evidenceQuestion: "What evidence would disprove the low-attention hypothesis?",
      allowedClaims: ["hypothesis_only"],
      rejectsAsProof: ["admission probability", "final recommendation"],
      escalationRule: "If broad recognition appears, block hidden-opportunity wording.",
    },
  ],
  contradictionTests: ["Search for broad recognition, hype pressure, or mainstream attention."],
  minimumEvidenceRules: ["Final recommendation remains forbidden.", "Public opinion remains hypothesis-only."],
  presentationGate: "Use after counselor signoff.",
  operatorBrief: ["Run counter-evidence and hype-pressure searches before using trend wording."],
  claimBoundary: "Research strategy does not support claims by itself.",
};

const familyClarityRoadmap = {
  protocol: "family_decision_clarity_roadmap_v1",
  status: "ready_for_row_discussion",
  conceptCards: [
    {
      concept: "professional_group",
      status: "understood",
      plainMeaning: "The filing unit is a school major group, not one favorite major.",
      familyQuestion: "Can the family explain that filing is by school major group?",
      evidenceNeeded: "Family accepts group-level uncertainty.",
      decisionImpact: "Blocks row discussion when the family treats one group as one major.",
      repairAction: "Keep this concept visible.",
    },
  ],
  interestAxes: [
    {
      axis: "course_content",
      prompt: "Which courses would the student willingly study for four years?",
      whyItMatters: "Course content turns a major label into daily learning commitment.",
      evidenceToCollect: "Primary interest direction: Computer Science.",
    },
    {
      axis: "regret_boundary",
      prompt: "Which outcome would make the family regret this row even if admitted?",
      whyItMatters: "Regret boundaries define the real blacklist and safe-anchor floor.",
      evidenceToCollect: "Blacklist: Civil Engineering.",
    },
  ],
  parentStudentAlignment: {
    questions: ["Which matters more: school platform, major certainty, city, tuition, or low regret risk?"],
    hardStops: ["This is not a final recommendation."],
  },
  rowDiscussionGate: {
    canDiscussRows: true,
    nextAction: "Use interest axes before final counselor signoff.",
    blockedReasons: [],
  },
  claimBoundary: "Roadmap is for communication and decision clarity only.",
};

const hiddenOpportunityAudit = {
  protocol: "hidden_opportunity_audit_v1",
  status: "candidate_for_counselor_review",
  labelPermission: "under_attention_candidate_only",
  score: 100,
  scoreBands: [],
  positiveSignals: ["Official quota expansion evidence is attached."],
  negativeSignals: [],
  requiredBeforeFamilyWording: [],
  forbiddenClaims: ["Do not claim admission guarantee.", "Do not claim final recommendation."],
  reviewGate: {
    canEnterLedger: true,
    canUseHiddenOpportunityLabel: true,
    mustStayHypothesisOnly: true,
    counselorSignoffRequired: true,
    reasons: ["Public-opinion signals remain hypothesis-only even when the row enters the opportunity ledger."],
  },
  claimBoundary: "Hidden opportunity audit is a counselor-review gate only.",
};

const planChangeOpportunityLedger = {
  protocol: "plan_change_opportunity_ledger_v1",
  status: "ready",
  score: 100,
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
  nextAction: "Promote the top audited opportunity into counselor review.",
  claimBoundary: "Plan change opportunity ledger is an audit object.",
};

const pack = narrative.buildVolunteerPlanNarrativePackage({
  detailedInterpretation,
  researchStrategy,
  familyClarityRoadmap,
  hiddenOpportunityAudit,
  planChangeOpportunityLedger,
});

assert.equal(pack.protocol, "volunteer_plan_narrative_package_v1");
assert.equal(pack.status, "ready_for_family_delivery");
assert.match(pack.headline, /evidence-backed/i);
assert.equal(pack.planRows.length, 1);
assert.equal(pack.planRows[0].position, "audited_opportunity_candidate");
assert.equal(pack.planRows[0].labelPermission, "under_attention_candidate_only");
assert.equal(pack.planRows[0].mustStayHypothesisOnly, true);
assert.match(pack.planRows[0].familyWording, /not a final recommendation/i);
assert.equal(pack.planRows[0].evidencePillars.some((pillar) => pillar.claim === "official_diff"), true);
assert.equal(pack.planRows[0].evidencePillars.some((pillar) => pillar.claim === "trend_wording" && pillar.stance === "hypothesis_only"), true);
assert.equal(pack.planRows[0].searchFollowUps.some((item) => /counter-evidence/i.test(item)), true);
assert.equal(pack.planRows[0].conceptPrompts.some((item) => /school major group/i.test(item)), true);
assert.equal(pack.planRows[0].interestPrompts.some((item) => /courses/i.test(item)), true);
assert.match(pack.conversationFlow[0], /official plan change/i);
assert.match(pack.conversationFlow.join("\n"), /interest axes/i);
assert.match(pack.forbiddenClaims.join("\n"), /admission guarantee/i);
assert.match(pack.forbiddenClaims.join("\n"), /Final recommendation remains forbidden/i);
assert.match(pack.claimBoundary, /does not make final filing recommendations/i);

const blockedPack = narrative.buildVolunteerPlanNarrativePackage({
  detailedInterpretation: { ...detailedInterpretation, status: "blocked" },
  researchStrategy: { ...researchStrategy, status: "blocked_by_evidence_quality" },
  familyClarityRoadmap: {
    ...familyClarityRoadmap,
    status: "blocked",
    rowDiscussionGate: {
      canDiscussRows: false,
      nextAction: "Resolve blockers.",
      blockedReasons: ["Family concept readiness blocked."],
    },
  },
  hiddenOpportunityAudit: {
    ...hiddenOpportunityAudit,
    status: "blocked",
    labelPermission: "do_not_use_hidden_opportunity",
    reviewGate: {
      ...hiddenOpportunityAudit.reviewGate,
      canEnterLedger: false,
      canUseHiddenOpportunityLabel: false,
      reasons: ["counter_evidence search has rejected or unreturned rows."],
    },
  },
  planChangeOpportunityLedger: {
    ...planChangeOpportunityLedger,
    status: "blocked",
    opportunities: [],
    blockedClaims: ["Hidden opportunity audit blocked ledger entry."],
    hiddenOpportunityGate: {
      ...planChangeOpportunityLedger.hiddenOpportunityGate,
      status: "blocked",
      canEnterLedger: false,
      labelPermission: "do_not_use_hidden_opportunity",
    },
  },
});

assert.equal(blockedPack.status, "blocked");
assert.equal(blockedPack.planRows.length, 0);
assert.match(blockedPack.deliveryGate.blockedReasons.join("\n"), /Hidden opportunity audit blocked/i);
assert.match(blockedPack.nextActions.join("\n"), /Resolve blockers/i);

console.log("Volunteer plan narrative package behavior test passed");

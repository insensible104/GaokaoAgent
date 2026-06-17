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

const auditModule = loadTsModule(path.join(libDir, "hiddenOpportunityAudit.ts"));

function buildReadyDossier(overrides = {}) {
  return {
    protocol: "counselor_review_dossier_v1",
    status: "ready_for_counselor_review",
    opportunityThesis:
      "Official quota expansion, rank direction, and external-plan omission support a counselor-review opportunity hypothesis.",
    evidenceTrail: [
      trail("official_diff", "official"),
      trail("rank_delta", "official"),
      trail("competitor_missed", "context"),
      trail("hypothesis_only", "public_opinion"),
    ],
    publicOpinionPosition: {
      guardStatus: "supports_hypothesis",
      opportunitySignal: "under_attention_candidate",
      confidence: "medium",
      evidenceRole: "hypothesis_only",
      familySafeSummary: "Low-attention evidence supports only a hypothesis.",
      requiredFollowUps: ["Keep checking dated counter-evidence."],
      wordingGateStatus: "hypothesis_only",
      wordingGateScore: 76,
      canUseHiddenOpportunityLabel: true,
      familySafeWording: "Use under-attention candidate wording only.",
      requiredEvidence: ["Counter-evidence search", "Hype-pressure search"],
      forbiddenWording: ["Do not say public opinion proves demand."],
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
        query("low_attention_signal"),
        query("counter_evidence"),
        query("hype_pressure"),
        query("source_diversity"),
        query("regional_preference"),
      ],
      resultRows: [
        result("low_attention_signal", "accepted"),
        result("counter_evidence", "accepted"),
        result("hype_pressure", "accepted"),
        result("source_diversity", "accepted"),
      ],
      claimBoundary: "Search provenance is not proof.",
    },
    evidenceQuality: {
      protocol: "counselor_evidence_quality_v1",
      status: "review_ready",
      summary: {
        authoritativeSources: 2,
        currentCycleSources: 6,
        staleSources: 0,
        conflictedClaims: 0,
        rejectedSearchRows: 0,
        unreturnedSearchRows: 0,
      },
      blockingConcerns: [],
      familyPresentationGate: "This can be shown as a counselor-review explanation.",
      claimBoundary: "Evidence quality gates presentation only.",
    },
    whatWeCanSay: ["Official quota expansion evidence is attached."],
    whatWeCannotSay: ["This does not prove admission guarantee or final recommendation."],
    claimBoundary: "Dossier is not a final filing recommendation.",
    ...overrides,
  };
}

function buildReadyInterpretation(overrides = {}) {
  return {
    protocol: "detailed_volunteer_plan_interpretation_v1",
    status: "ready_for_family_review",
    planPosition: {
      rowUse: "candidate_for_counselor_review",
      notARecommendationReasons: ["Final recommendation remains forbidden."],
    },
    claimRows: [
      {
        claim: "official_diff",
        stance: "can_explain",
        evidenceBasis: ["Official plan diff attached."],
      },
      {
        claim: "rank_delta",
        stance: "can_explain",
        evidenceBasis: ["Rank history attached."],
      },
      {
        claim: "competitor_missed",
        stance: "can_explain",
        evidenceBasis: ["External plan comparison attached."],
      },
      {
        claim: "trend_wording",
        stance: "hypothesis_only",
        counterChecks: ["counter_evidence", "hype_pressure"],
      },
    ],
    ...overrides,
  };
}

function buildReadyResearchStrategy(overrides = {}) {
  return {
    protocol: "web_evidence_research_strategy_v1",
    status: "ready_to_run",
    priorityQueries: [
      { searchIntent: "counter_evidence", priority: "critical", status: "ready_to_run" },
      { searchIntent: "hype_pressure", priority: "high", status: "ready_to_run" },
      { searchIntent: "source_diversity", priority: "medium", status: "ready_to_run" },
    ],
    minimumEvidenceRules: [
      "Final recommendation remains forbidden.",
      "Public opinion remains hypothesis-only.",
    ],
    ...overrides,
  };
}

function buildReadyRoadmap(overrides = {}) {
  return {
    protocol: "family_decision_clarity_roadmap_v1",
    status: "ready_for_row_discussion",
    rowDiscussionGate: {
      canDiscussRows: true,
      nextAction: "Discuss rows after counselor review.",
      blockedReasons: [],
    },
    ...overrides,
  };
}

function trail(claim, sourceTier) {
  return {
    taskId: `${claim}-task`,
    claim,
    sourceTitle: `${claim} source`,
    sourceUrl: `https://example.test/${claim}`,
    sourceTier,
    capturedAt: "2026-06-16",
    excerpts: [`${claim} excerpt`],
  };
}

function query(searchIntent) {
  return {
    requestId: `${searchIntent}-request`,
    taskId: `${searchIntent}-task`,
    taskType: "public_opinion_scan",
    query: `${searchIntent} query`,
    sourceTier: "public_opinion",
    allowedClaims: ["hypothesis_only"],
    searchIntent,
    evidenceQuestion: `Check ${searchIntent}`,
    rejectsAsProof: ["admission probability", "final recommendation"],
  };
}

function result(searchIntent, outcome, rejectionReason = null) {
  return {
    requestId: `${searchIntent}-request`,
    taskId: `${searchIntent}-task`,
    taskType: "public_opinion_scan",
    query: `${searchIntent} query`,
    domains: [],
    searchIntent,
    evidenceQuestion: `Check ${searchIntent}`,
    rejectsAsProof: ["admission probability", "final recommendation"],
    provider: "demo-search-provider",
    outcome,
    sourceTitle: `${searchIntent} source`,
    sourceUrl: `https://example.test/${searchIntent}`,
    sourceTier: "public_opinion",
    claimedSupports: ["hypothesis_only"],
    rejectionReason,
  };
}

const readyAudit = auditModule.buildHiddenOpportunityAudit({
  dossier: buildReadyDossier(),
  detailedInterpretation: buildReadyInterpretation(),
  researchStrategy: buildReadyResearchStrategy(),
  familyClarityRoadmap: buildReadyRoadmap(),
});

assert.equal(readyAudit.protocol, "hidden_opportunity_audit_v1");
assert.equal(readyAudit.status, "candidate_for_counselor_review");
assert.equal(readyAudit.labelPermission, "under_attention_candidate_only");
assert.equal(readyAudit.reviewGate.canEnterLedger, true);
assert.equal(readyAudit.reviewGate.canUseHiddenOpportunityLabel, true);
assert.equal(readyAudit.reviewGate.mustStayHypothesisOnly, true);
assert.equal(readyAudit.reviewGate.counselorSignoffRequired, true);
assert.equal(readyAudit.score >= 75, true);
assert.equal(readyAudit.scoreBands.some((band) => band.factor === "counter_evidence_clearance" && band.points > 0), true);
assert.equal(readyAudit.scoreBands.some((band) => band.factor === "hype_pressure_clearance" && band.points > 0), true);
assert.equal(readyAudit.scoreBands.some((band) => band.factor === "family_readiness" && band.points > 0), true);
assert.match(readyAudit.forbiddenClaims.join("\n"), /admission guarantee/i);
assert.match(readyAudit.forbiddenClaims.join("\n"), /final recommendation/i);
assert.match(readyAudit.claimBoundary, /hypothesis-only/i);

const blockedAudit = auditModule.buildHiddenOpportunityAudit({
  dossier: buildReadyDossier({
    evidenceQuality: {
      ...buildReadyDossier().evidenceQuality,
      status: "blocked",
      blockingConcerns: ["Counter-evidence search returned conflict."],
    },
    searchProvenance: {
      ...buildReadyDossier().searchProvenance,
      summary: { acceptedRows: 5, rejectedRows: 1, unreturnedRows: 1 },
      resultRows: [
        result("counter_evidence", "rejected", "Counter-evidence conflict found."),
        result("hype_pressure", "unreturned"),
      ],
    },
    publicOpinionPosition: {
      ...buildReadyDossier().publicOpinionPosition,
      wordingGateStatus: "blocked_by_conflict",
      canUseHiddenOpportunityLabel: false,
      forbiddenWording: ["Do not use hidden-opportunity wording while conflict is unresolved."],
    },
  }),
  detailedInterpretation: buildReadyInterpretation({ status: "blocked" }),
  researchStrategy: buildReadyResearchStrategy({ status: "blocked" }),
  familyClarityRoadmap: buildReadyRoadmap({
    status: "blocked",
    rowDiscussionGate: {
      canDiscussRows: false,
      nextAction: "Resolve evidence blockers.",
      blockedReasons: ["Evidence conflict"],
    },
  }),
});

assert.equal(blockedAudit.status, "blocked");
assert.equal(blockedAudit.labelPermission, "do_not_use_hidden_opportunity");
assert.equal(blockedAudit.reviewGate.canEnterLedger, false);
assert.equal(blockedAudit.reviewGate.canUseHiddenOpportunityLabel, false);
assert.equal(blockedAudit.reviewGate.mustStayHypothesisOnly, true);
assert.match(blockedAudit.negativeSignals.join("\n"), /Counter-evidence search returned conflict/i);
assert.match(blockedAudit.requiredBeforeFamilyWording.join("\n"), /Resolve/i);

const hypothesisAudit = auditModule.buildHiddenOpportunityAudit({
  dossier: buildReadyDossier({
    evidenceTrail: [trail("official_diff", "official"), trail("rank_delta", "official")],
    searchProvenance: {
      ...buildReadyDossier().searchProvenance,
      queryRows: [query("low_attention_signal"), query("source_diversity")],
      resultRows: [result("low_attention_signal", "accepted")],
    },
  }),
  detailedInterpretation: buildReadyInterpretation({
    claimRows: [
      { claim: "official_diff", stance: "can_explain", evidenceBasis: ["Official diff attached."] },
      { claim: "trend_wording", stance: "hypothesis_only", counterChecks: [] },
    ],
  }),
  researchStrategy: buildReadyResearchStrategy({ status: "needs_more_search" }),
  familyClarityRoadmap: buildReadyRoadmap(),
});

assert.equal(hypothesisAudit.status, "hypothesis_only");
assert.equal(hypothesisAudit.reviewGate.canEnterLedger, false);
assert.equal(hypothesisAudit.reviewGate.canUseHiddenOpportunityLabel, false);
assert.match(hypothesisAudit.requiredBeforeFamilyWording.join("\n"), /counter-evidence/i);
assert.match(hypothesisAudit.requiredBeforeFamilyWording.join("\n"), /hype-pressure/i);

console.log("Hidden opportunity audit behavior test passed");

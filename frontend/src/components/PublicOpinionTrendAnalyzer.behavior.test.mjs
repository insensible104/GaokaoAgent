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

const analyzer = loadTsModule(path.join(libDir, "publicOpinionTrendAnalyzer.ts"));

const analysis = analyzer.analyzePublicOpinionTrends({
  targetYear: 2026,
  province: "Guangdong",
  schoolCode: "10561",
  schoolName: "South China Tech",
  majorKeywords: ["Computer Science", "Data Science"],
  observations: [
    {
      id: "search-1",
      sourceKind: "search_snippet",
      title: "Parents focus on local schools",
      capturedAt: "2026-06-16",
      text: "Discussion snippets mostly mention local brands and rarely mention South China Tech Computer Science.",
    },
    {
      id: "social-1",
      sourceKind: "social_summary",
      title: "Distance concern thread",
      capturedAt: "2026-06-16",
      text: "Families avoid non-local engineering options because of distance, campus uncertainty, and adjustment concern.",
    },
    {
      id: "article-1",
      sourceKind: "article_summary",
      title: "Data science salary hype",
      capturedAt: "2026-06-16",
      text: "Several articles describe Data Science as a hot high salary major and encourage everyone to apply.",
    },
    {
      id: "counter-1",
      sourceKind: "article_summary",
      title: "Counter evidence",
      capturedAt: "2026-06-16",
      text: "A mainstream article says South China Tech engineering remains widely recognized, so low attention may be anecdotal.",
    },
  ],
});

assert.equal(analysis.protocol, "public_opinion_trend_analyzer_v1");
assert.equal(analysis.status, "signals_detected");
assert.match(analysis.claimBoundary, /hypothesis/);
assert.equal(analysis.signals.length >= 2, true);
assert.equal(analysis.trendProfile.protocol, "public_opinion_trend_profile_v1");
assert.equal(analysis.trendProfile.opportunitySignal, "conflicted");
assert.equal(analysis.trendProfile.confidence, "low");
assert.equal(analysis.trendLanguageGate.protocol, "public_opinion_trend_language_gate_v1");
assert.equal(analysis.trendLanguageGate.status, "blocked_by_conflict");
assert.equal(analysis.trendLanguageGate.canUseHiddenOpportunityLabel, false);
assert.equal(analysis.trendLanguageGate.score < 50, true);
assert.match(analysis.trendLanguageGate.familySafeWording, /conflicted/i);
assert.match(analysis.trendLanguageGate.forbiddenWording.join("\n"), /hidden opportunity/i);
assert.match(analysis.trendLanguageGate.requiredEvidence.join("\n"), /counter-evidence/i);
assert.equal(analysis.trendProfile.evidenceBalance.lowAttentionSignals, 1);
assert.equal(analysis.trendProfile.evidenceBalance.avoidanceSignals, 1);
assert.equal(analysis.trendProfile.evidenceBalance.hypeSignals, 1);
assert.equal(analysis.trendProfile.evidenceBalance.counterEvidenceCount, 1);
assert.match(analysis.trendProfile.familySafeSummary, /counter-evidence/i);
assert.match(analysis.trendProfile.requiredFollowUps.join("\n"), /Search for dated counter-evidence/);
assert.match(analysis.trendProfile.requiredFollowUps.join("\n"), /Do not present this as a hidden opportunity/);

const underAttention = analysis.signals.find((signal) => signal.attention === "low" && signal.sentiment === "avoidance");
assert.ok(underAttention);
assert.equal(underAttention.schoolCode, "10561");
assert.deepEqual(underAttention.majorKeywords, ["Computer Science", "Data Science"]);
assert.match(underAttention.topic, /low attention/i);
assert.match(underAttention.evidence, /search-1/);
assert.match(underAttention.evidence, /social-1/);
assert.doesNotMatch(underAttention.evidence, /official enrollment-plan/);

const hype = analysis.signals.find((signal) => signal.attention === "high" && signal.sentiment === "hype");
assert.ok(hype);
assert.match(hype.topic, /hype/i);
assert.match(hype.evidence, /article-1/);

assert.equal(analysis.counterEvidence.length, 1);
assert.match(analysis.counterEvidence[0].text, /widely recognized/);
assert.match(analysis.blockedClaims.join("\n"), /Do not use public-opinion trend signals as official plan evidence/);
assert.match(analysis.blockedClaims.join("\n"), /Do not infer final demand without official plan, rank history, and external-plan comparison/);

const emptyAnalysis = analyzer.analyzePublicOpinionTrends({
  targetYear: 2026,
  province: "Guangdong",
  schoolCode: "11845",
  schoolName: "Pearl River Normal",
  majorKeywords: ["English"],
  observations: [
    {
      id: "neutral-1",
      sourceKind: "search_snippet",
      title: "Neutral school page",
      capturedAt: "2026-06-16",
      text: "Official school page lists general admissions contact information.",
    },
  ],
});

assert.equal(emptyAnalysis.status, "no_signal");
assert.equal(emptyAnalysis.signals.length, 0);
assert.equal(emptyAnalysis.trendProfile.opportunitySignal, "insufficient");
assert.equal(emptyAnalysis.trendProfile.confidence, "low");
assert.equal(emptyAnalysis.trendLanguageGate.status, "insufficient_evidence");
assert.equal(emptyAnalysis.trendLanguageGate.canUseHiddenOpportunityLabel, false);
assert.match(emptyAnalysis.nextAction, /Collect more dated public-opinion observations/);

const cleanUnderAttention = analyzer.analyzePublicOpinionTrends({
  targetYear: 2026,
  province: "Guangdong",
  schoolCode: "10561",
  schoolName: "South China Tech",
  majorKeywords: ["Computer Science"],
  observations: [
    {
      id: "search-low",
      sourceKind: "search_snippet",
      title: "Search snippets rarely mention the group",
      capturedAt: "2026-06-16",
      text: "Families rarely mention this Computer Science major group and miss the quota expansion.",
    },
    {
      id: "social-avoid",
      sourceKind: "social_summary",
      title: "Distance avoidance",
      capturedAt: "2026-06-16",
      text: "Parents avoid non-local options because of distance and adjustment concern.",
    },
  ],
});

assert.equal(cleanUnderAttention.trendProfile.opportunitySignal, "under_attention_candidate");
assert.equal(cleanUnderAttention.trendProfile.confidence, "medium");
assert.equal(cleanUnderAttention.trendLanguageGate.status, "hypothesis_only");
assert.equal(cleanUnderAttention.trendLanguageGate.canUseHiddenOpportunityLabel, true);
assert.equal(cleanUnderAttention.trendLanguageGate.score >= 70, true);
assert.match(cleanUnderAttention.trendLanguageGate.familySafeWording, /under-attention candidate/i);
assert.match(cleanUnderAttention.trendLanguageGate.forbiddenWording.join("\n"), /guaranteed/i);
assert.match(cleanUnderAttention.trendProfile.familySafeSummary, /possible under-attention hypothesis/i);
assert.match(cleanUnderAttention.trendProfile.requiredFollowUps.join("\n"), /official plan diff/);

const crowdedTrend = analyzer.analyzePublicOpinionTrends({
  targetYear: 2026,
  province: "Guangdong",
  schoolCode: "10001",
  schoolName: "Popular Finance University",
  majorKeywords: ["Finance"],
  observations: [
    {
      id: "hype-1",
      sourceKind: "article_summary",
      title: "Finance rush",
      capturedAt: "2026-06-16",
      text: "Finance is a hot high salary major and everyone plans to rush to apply.",
    },
  ],
});

assert.equal(crowdedTrend.trendLanguageGate.status, "blocked_by_hype");
assert.equal(crowdedTrend.trendLanguageGate.canUseHiddenOpportunityLabel, false);
assert.match(crowdedTrend.trendLanguageGate.familySafeWording, /crowded/i);

console.log("Public opinion trend analyzer behavior test passed");

# Real Case v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one auditable Real Case v0 path where captured public evidence cards flow through Evidence Autopilot, Opportunity Radar, Deep Opportunity Card, and the Chinese report.

**Architecture:** Use a fixture-backed real case before building live retrieval. The fixture is intentionally different from the snapshot provider: snapshot preserves demo stability, while Real Case v0 stores reviewed `captured_candidate` evidence with URL, excerpt, capture time, confidence, and review action. Existing normalizer, API adapter, and report logic must be reused rather than creating a parallel opportunity system.

**Tech Stack:** React + Vite + TypeScript behavior tests, Node `.mjs` smoke tests, FastAPI backend smoke tests, JSON fixture under `data/evidence_autopilot`, existing Evidence Autopilot frontend modules.

---

## 0. Scope Guard

This plan implements the next slice from `docs/superpowers/specs/2026-06-24-real-case-v0-design.md`.

Do not implement:

- new public UI redesign
- live WeChat/Boss scraping
- generalized case-management platform
- admission, graduate-school, employment, or 2026 outcome improvement claims
- visible multi-agent debate

Every evidence claim must remain an auditable opportunity hypothesis unless validated by outcome data that directly covers the claim.

## 1. File Structure

Create:

- `data/evidence_autopilot/real_case_v0.json`
  Stores one concrete case and reviewed captured public evidence cards.

- `docs/evidence_autopilot/real_case_v0_source_log.md`
  Human-readable source log recording URLs, capture date, why each source was accepted, and what remains unverified.

- `frontend/src/lib/evidenceAutopilotRealCaseProvider.ts`
  Converts the fixture into typed `EvidenceAutopilotProviderResult[]` and exposes case metadata.

- `frontend/src/components/EvidenceAutopilotRealCaseProvider.test.mjs`
  Tests fixture schema, no active placeholders, minimum evidence count, status gating, and provider output.

Modify:

- `frontend/src/lib/evidenceAutopilotApi.ts`
  Add a `real_case_fixture` API state and helper that packages real fixture evidence without pretending it came from the live backend.

- `frontend/src/components/EvidenceAutopilotApi.test.mjs`
  Cover `real_case_fixture` state and ensure placeholders still fall back.

- `frontend/src/components/DeepOpportunityEvaluationPanel.tsx`
  Prefer the real case fixture only for the demo case it matches; keep backend and snapshot fallback behavior.

- `frontend/src/components/PathFinderReportTemplate.tsx`
  Use real case fixture provider results for the deep opportunity report example when available.

- `frontend/src/components/PathFinderDeepOpportunityReport.test.mjs`
  Assert report text distinguishes real fixture evidence from demo snapshot evidence and renders source excerpts.

## 2. Evidence Fixture Contract

Use this exact TypeScript shape in `frontend/src/lib/evidenceAutopilotRealCaseProvider.ts`:

```ts
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
  sourceType: "official" | "school" | "paper" | "job" | "wechat" | "discussion" | "other";
  excerpt: string;
  capturedAt: string;
  confidence: "high" | "medium" | "low";
  reviewAction: string;
}
```

The fixture may contain `requires_capture` and `operator_review` cards, but only `captured_candidate` cards with URL and excerpt can become provider results.

## 3. Task 1: Freeze the Real Case Source Log

**Files:**

- Create: `docs/evidence_autopilot/real_case_v0_source_log.md`
- Create later in Task 2: `data/evidence_autopilot/real_case_v0.json`

- [ ] **Step 1: Select one concrete case**

Use a case that can be supported mostly by public official/school sources. Recommended default unless stronger current sources are found:

```text
Province: Guangdong
Subject track: physics
Target year: 2026
Target school: South China University of Technology
Target major/theme: intelligent manufacturing / data engineering opportunity path
Opportunity hypothesis: a manufacturing-data direction may be under-explained by generic computer-science-oriented counseling and needs evidence across admissions, training, faculty, graduate progression, and career path.
```

Do not write this as a recommendation. It is only the opportunity hypothesis to investigate.

- [ ] **Step 2: Collect public sources**

Use browser/search or official site navigation to collect at least five public sources. Prefer these categories:

```text
official admissions rule or enrollment plan
historical admission rank or score evidence
school/faculty/major training evidence
graduate progression, employment, civil-service, or career-path evidence
counter-evidence or explicit evidence gap
```

For each source, record:

```text
Source title:
URL:
Captured at:
Source type:
Claim task id:
Accepted excerpt:
Confidence:
Review action:
What this does not prove:
```

- [ ] **Step 3: Write the source log**

Create `docs/evidence_autopilot/real_case_v0_source_log.md` with this structure:

```markdown
# Evidence Autopilot Real Case v0 Source Log

Date: 2026-06-24

## Case

- Province: Guangdong
- Subject track: physics
- Target year: 2026
- Candidate score/rank band: not used as admission proof in v0
- Target school: South China University of Technology
- Target major/theme: intelligent manufacturing / data engineering opportunity path

## Claim Boundary

This source log supports an auditable opportunity hypothesis only. It does not prove admission probability, graduate-school results, employment outcomes, or improved 2026 admission performance.

## Sources

### 1. Official admissions rule or enrollment plan

- Source title:
- URL:
- Captured at:
- Source type:
- Claim task id: official-plan-charter
- Accepted excerpt:
- Confidence:
- Review action:
- What this does not prove:

### 2. Historical admission rank or score evidence

- Source title:
- URL:
- Captured at:
- Source type:
- Claim task id: rank-history-band
- Accepted excerpt:
- Confidence:
- Review action:
- What this does not prove:

### 3. School/faculty/major training evidence

- Source title:
- URL:
- Captured at:
- Source type:
- Claim task id: faculty-research-direction
- Accepted excerpt:
- Confidence:
- Review action:
- What this does not prove:

### 4. Progression or career-path evidence

- Source title:
- URL:
- Captured at:
- Source type:
- Claim task id: graduate-progression
- Accepted excerpt:
- Confidence:
- Review action:
- What this does not prove:

### 5. Counter-evidence or evidence gap

- Source title:
- URL:
- Captured at:
- Source type:
- Claim task id: counter-evidence
- Accepted excerpt:
- Confidence:
- Review action:
- What this does not prove:
```

- [ ] **Step 4: Self-audit source log before coding**

Run:

```powershell
rg -n "Source title:$|URL:$|Accepted excerpt:$|Confidence:$|What this does not prove:$" docs/evidence_autopilot/real_case_v0_source_log.md
```

Expected:

```text
No output.
```

If there is output, the source log still has blank active evidence fields and must not feed `captured_candidate`.

- [ ] **Step 5: Commit the source log**

Run:

```powershell
git add docs/evidence_autopilot/real_case_v0_source_log.md
git commit -m "docs: add real case v0 source log"
```

## 4. Task 2: Add Real Case Fixture and Failing Provider Test

**Files:**

- Create: `data/evidence_autopilot/real_case_v0.json`
- Create: `frontend/src/components/EvidenceAutopilotRealCaseProvider.test.mjs`
- Later create: `frontend/src/lib/evidenceAutopilotRealCaseProvider.ts`

- [ ] **Step 1: Create fixture from audited source log**

Create `data/evidence_autopilot/real_case_v0.json` using only the completed source log. Include at least five `captured_candidate` cards.

Use this exact JSON structure:

```json
{
  "caseId": "scut-intelligent-manufacturing-real-case-v0",
  "candidate": {
    "province": "Guangdong",
    "targetYear": 2026,
    "score": null,
    "rank": null,
    "subjectTrack": "physics"
  },
  "target": {
    "schoolName": "South China University of Technology",
    "majorName": "intelligent manufacturing / data engineering opportunity path"
  },
  "opportunityHypothesis": "Manufacturing-data and intelligent-manufacturing evidence may reveal a differentiated opportunity path that generic computer-science-oriented counseling can miss.",
  "claimBoundary": "This fixture supports an auditable opportunity hypothesis only. It does not prove admission probability, graduate-school results, employment outcomes, or improved 2026 admission performance.",
  "evidenceCards": []
}
```

Then fill `evidenceCards` from the completed source log. Do not leave `evidenceCards` empty.

- [ ] **Step 2: Write failing provider test**

Create `frontend/src/components/EvidenceAutopilotRealCaseProvider.test.mjs`:

```js
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..", "..", "..");
const fixturePath = path.join(root, "data", "evidence_autopilot", "real_case_v0.json");
const providerPath = path.join(here, "..", "lib", "evidenceAutopilotRealCaseProvider.ts");

assert.equal(fs.existsSync(fixturePath), true, "Real Case v0 fixture should exist");
assert.equal(fs.existsSync(providerPath), true, "Real Case provider should exist");

function loadTsModule(source, requireMap = {}) {
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      module: ts.ModuleKind.CommonJS,
      resolveJsonModule: true,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (requireMap[specifier]) return requireMap[specifier];
    throw new Error(`Unexpected require: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const providerModule = loadTsModule(fs.readFileSync(providerPath, "utf8"), {
  "../../../data/evidence_autopilot/real_case_v0.json": JSON.parse(fs.readFileSync(fixturePath, "utf8")),
});

assert.equal(typeof providerModule.loadEvidenceAutopilotRealCaseFixture, "function");
assert.equal(typeof providerModule.buildEvidenceAutopilotRealCaseProviderResults, "function");

const fixture = providerModule.loadEvidenceAutopilotRealCaseFixture();
assert.equal(fixture.caseId, "scut-intelligent-manufacturing-real-case-v0");
assert.match(fixture.claimBoundary, /auditable opportunity hypothesis/i);
assert.doesNotMatch(fixture.claimBoundary, /prove admission probability/i);
assert(fixture.evidenceCards.length >= 5);

const captured = fixture.evidenceCards.filter((card) => card.status === "captured_candidate");
assert(captured.length >= 5);
assert(captured.some((card) => card.taskId === "counter-evidence"));

for (const card of captured) {
  assert(card.sourceTitle.trim().length > 0, `${card.taskId} has source title`);
  assert.match(card.sourceUrl, /^https?:\/\//, `${card.taskId} has public URL`);
  assert(card.excerpt.trim().length >= 20, `${card.taskId} has useful excerpt`);
  assert.match(card.capturedAt, /^\d{4}-\d{2}-\d{2}/, `${card.taskId} has capture date`);
  assert(["official", "school", "paper", "job", "wechat", "discussion", "other"].includes(card.sourceType));
  assert(["high", "medium", "low"].includes(card.confidence));
  assert(card.reviewAction.trim().length > 0, `${card.taskId} has review action`);
}

const providerResults = providerModule.buildEvidenceAutopilotRealCaseProviderResults();
assert(providerResults.length >= 5);
assert.equal(providerResults.every((result) => result.requestId.startsWith("real-case-v0-")), true);
assert.equal(providerResults.some((result) => result.taskId === "counter-evidence"), true);

console.log("Evidence Autopilot real case provider test passed");
```

- [ ] **Step 3: Run failing test**

Run:

```powershell
node frontend/src/components/EvidenceAutopilotRealCaseProvider.test.mjs
```

Expected:

```text
AssertionError: Real Case provider should exist
```

The fixture should already exist. The provider should not exist yet.

## 5. Task 3: Implement Real Case Provider

**Files:**

- Create: `frontend/src/lib/evidenceAutopilotRealCaseProvider.ts`

- [ ] **Step 1: Implement provider**

Create `frontend/src/lib/evidenceAutopilotRealCaseProvider.ts`:

```ts
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
```

- [ ] **Step 2: Run provider test**

Run:

```powershell
node frontend/src/components/EvidenceAutopilotRealCaseProvider.test.mjs
```

Expected:

```text
Evidence Autopilot real case provider test passed
```

- [ ] **Step 3: Commit provider and fixture**

Run:

```powershell
git add data/evidence_autopilot/real_case_v0.json frontend/src/lib/evidenceAutopilotRealCaseProvider.ts frontend/src/components/EvidenceAutopilotRealCaseProvider.test.mjs
git commit -m "feat: add evidence autopilot real case fixture provider"
```

## 6. Task 4: Add Real Case API State

**Files:**

- Modify: `frontend/src/lib/evidenceAutopilotApi.ts`
- Modify: `frontend/src/components/EvidenceAutopilotApi.test.mjs`

- [ ] **Step 1: Write failing API state test**

Append this to `frontend/src/components/EvidenceAutopilotApi.test.mjs` after the existing fallback assertions:

```js
const realCaseState = api.buildEvidenceAutopilotRealCaseState({
  providerResults: [
    {
      requestId: "real-case-v0-1",
      taskId: "official-plan-charter",
      sourceTitle: "Official source",
      sourceUrl: "https://example.edu/official",
      sourceType: "official",
      excerpt: "Official public source excerpt for audited real case.",
      capturedAt: "2026-06-24",
      confidence: "high",
    },
  ],
  claimBoundary: "Real Case v0 fixture supports an auditable opportunity hypothesis only.",
});
assert.equal(realCaseState.status, "real_case_fixture");
assert.equal(realCaseState.providerResults.length, 1);
assert.match(realCaseState.claimBoundary, /auditable opportunity hypothesis/i);
```

- [ ] **Step 2: Run failing API test**

Run:

```powershell
node frontend/src/components/EvidenceAutopilotApi.test.mjs
```

Expected:

```text
TypeError: api.buildEvidenceAutopilotRealCaseState is not a function
```

- [ ] **Step 3: Implement real case state**

Modify `frontend/src/lib/evidenceAutopilotApi.ts`:

```ts
export type EvidenceAutopilotBackendStatus =
  | "demo_snapshot"
  | "backend_connected"
  | "backend_failed_snapshot_fallback"
  | "real_case_fixture";
```

Add:

```ts
export function buildEvidenceAutopilotRealCaseState({
  providerResults,
  claimBoundary,
}: {
  providerResults: EvidenceAutopilotProviderResult[];
  claimBoundary: string;
}): EvidenceAutopilotApiState {
  return {
    status: "real_case_fixture",
    providerResults,
    claimBoundary,
  };
}
```

- [ ] **Step 4: Run API test**

Run:

```powershell
node frontend/src/components/EvidenceAutopilotApi.test.mjs
```

Expected:

```text
Evidence Autopilot API adapter test passed
```

- [ ] **Step 5: Commit API state**

Run:

```powershell
git add frontend/src/lib/evidenceAutopilotApi.ts frontend/src/components/EvidenceAutopilotApi.test.mjs
git commit -m "feat: add evidence autopilot real case api state"
```

## 7. Task 5: Route Real Case Through Opportunity Radar

**Files:**

- Modify: `frontend/src/components/DeepOpportunityEvaluationPanel.tsx`
- Modify: `frontend/src/components/DeepOpportunityEvaluator.test.mjs` or create `frontend/src/components/DeepOpportunityRealCase.test.mjs`

- [ ] **Step 1: Write failing real case evaluation test**

Create `frontend/src/components/DeepOpportunityRealCase.test.mjs`:

```js
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const lib = path.join(here, "..", "lib");
const root = path.join(here, "..", "..", "..");

function loadTsModule(source, requireMap = {}) {
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      module: ts.ModuleKind.CommonJS,
      resolveJsonModule: true,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (requireMap[specifier]) return requireMap[specifier];
    throw new Error(`Unexpected require: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const fixture = JSON.parse(fs.readFileSync(path.join(root, "data", "evidence_autopilot", "real_case_v0.json"), "utf8"));
const realCase = loadTsModule(fs.readFileSync(path.join(lib, "evidenceAutopilotRealCaseProvider.ts"), "utf8"), {
  "../../../data/evidence_autopilot/real_case_v0.json": fixture,
});
const planModule = loadTsModule(fs.readFileSync(path.join(lib, "deepEvidenceCollectionPlan.ts"), "utf8"));
const evaluator = loadTsModule(fs.readFileSync(path.join(lib, "deepOpportunityEvaluator.ts"), "utf8"));
const normalizer = loadTsModule(fs.readFileSync(path.join(lib, "evidenceAutopilotResultNormalizer.ts"), "utf8"));
const autopilot = loadTsModule(fs.readFileSync(path.join(lib, "evidenceAutopilot.ts"), "utf8"), {
  "./deepEvidenceCollectionPlan": planModule,
  "./deepOpportunityEvaluator": evaluator,
  "./evidenceAutopilotResultNormalizer": normalizer,
});

const plan = planModule.buildDeepEvidenceCollectionPlan({
  province: fixture.candidate.province,
  targetYear: fixture.candidate.targetYear,
  schoolName: fixture.target.schoolName,
  majorName: fixture.target.majorName,
});
const providerResults = realCase.buildEvidenceAutopilotRealCaseProviderResults(fixture);
const run = autopilot.buildEvidenceAutopilotRun({ plan, providerResults });

assert(run.evidenceResults.filter((result) => result.status === "verified").length >= 3);
assert(run.evidenceResults.some((result) => result.taskId === "counter-evidence"));
assert(run.evaluation.horizonSignals.shortTermAdmission.length > 0);
assert(run.evaluation.horizonSignals.midTermProgression.length > 0);
assert(run.evaluation.horizonSignals.longTermCareer.length > 0);
assert.match(run.evaluation.claimBoundary, /不承诺录取|不会承诺录取|hypothesis/i);

console.log("Deep opportunity real case test passed");
```

- [ ] **Step 2: Run failing or passing evaluation test**

Run:

```powershell
node frontend/src/components/DeepOpportunityRealCase.test.mjs
```

Expected before provider exists:

```text
Unexpected require or file not found for evidenceAutopilotRealCaseProvider.ts
```

Expected after Task 3:

```text
Deep opportunity real case test passed
```

- [ ] **Step 3: Wire panel real case state**

Modify `frontend/src/components/DeepOpportunityEvaluationPanel.tsx`:

```ts
import {
  buildEvidenceAutopilotRealCaseProviderResults,
  loadEvidenceAutopilotRealCaseFixture,
} from "@/lib/evidenceAutopilotRealCaseProvider";
import { buildEvidenceAutopilotRealCaseState } from "@/lib/evidenceAutopilotApi";
```

Extend `backendStatusLabel`:

```ts
const backendStatusLabel: Record<EvidenceAutopilotBackendStatus, string> = {
  demo_snapshot: "Demo snapshot",
  backend_connected: "Backend connected",
  backend_failed_snapshot_fallback: "Demo fallback",
  real_case_fixture: "Real case fixture",
};
```

Inside the `baseRun` memo, keep the existing `exampleCollectionContext` and include it in the returned object:

```ts
return {
  context: exampleCollectionContext,
  plan,
  searchTasks: draftRun.searchTasks,
  targetLabel: plan.targetLabel,
  initialApiState: {
    status: "demo_snapshot" as const,
    providerResults,
    claimBoundary: "Demo snapshot uses deterministic public evidence samples until backend returns captured source excerpts.",
  },
};
```

Inside the initial effect path, build real case state when the example context matches the fixture target:

```ts
const realCaseFixture = loadEvidenceAutopilotRealCaseFixture();
const realCaseProviderResults = buildEvidenceAutopilotRealCaseProviderResults(realCaseFixture);
if (
  realCaseProviderResults.length > 0 &&
  realCaseFixture.target.schoolName === baseRun.context.schoolName &&
  realCaseFixture.target.majorName === baseRun.context.majorName
) {
  const realCaseApiState = buildEvidenceAutopilotRealCaseState({
    providerResults: realCaseProviderResults,
    claimBoundary: realCaseFixture.claimBoundary,
  });
  setApiState(realCaseApiState);
  setRun(buildEvidenceAutopilotRun({ plan, providerResults: realCaseApiState.providerResults }));
  return;
}
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
node frontend/src/components/DeepOpportunityRealCase.test.mjs
node frontend/src/components/DeepOpportunityEvaluator.test.mjs
```

Expected:

```text
Deep opportunity real case test passed
Deep opportunity evaluator test passed
```

- [ ] **Step 5: Commit real case evaluation route**

Run:

```powershell
git add frontend/src/components/DeepOpportunityEvaluationPanel.tsx frontend/src/components/DeepOpportunityRealCase.test.mjs
git commit -m "feat: route real case evidence through opportunity radar"
```

## 8. Task 6: Add Real Case Report Evidence

**Files:**

- Modify: `frontend/src/components/PathFinderReportTemplate.tsx`
- Modify: `frontend/src/components/PathFinderDeepOpportunityReport.test.mjs`

- [ ] **Step 1: Write failing report assertion**

Add assertions to `frontend/src/components/PathFinderDeepOpportunityReport.test.mjs`:

```js
assert.match(source, /buildEvidenceAutopilotRealCaseProviderResults/);
assert.match(source, /real_case_fixture|Real Case v0/);
assert.match(source, /auditable opportunity hypothesis/);
assert.match(source, /sourceExcerpt/);
```

- [ ] **Step 2: Run failing report test**

Run:

```powershell
node frontend/src/components/PathFinderDeepOpportunityReport.test.mjs
```

Expected:

```text
AssertionError
```

- [ ] **Step 3: Use real case provider in report**

Modify `frontend/src/components/PathFinderReportTemplate.tsx` near the existing deep opportunity report setup:

```ts
import {
  buildEvidenceAutopilotRealCaseProviderResults,
  loadEvidenceAutopilotRealCaseFixture,
} from "@/lib/evidenceAutopilotRealCaseProvider";
```

Then replace the report's deep opportunity provider result source:

```ts
const realCaseFixture = loadEvidenceAutopilotRealCaseFixture();
const realCaseProviderResults = buildEvidenceAutopilotRealCaseProviderResults(realCaseFixture);
const providerResults =
  realCaseProviderResults.length > 0
    ? realCaseProviderResults
    : buildEvidenceAutopilotSnapshotProviderResults({
        plan,
        searchTasks: draftRun.searchTasks,
        targetLabel: plan.targetLabel,
      });
```

Add a small text boundary inside the Evidence Autopilot report section:

```tsx
<p>
  Real Case v0 fixture: {realCaseFixture.claimBoundary}
</p>
```

Do not change the report layout beyond adding the boundary sentence.

- [ ] **Step 4: Run report tests**

Run:

```powershell
node frontend/src/components/PathFinderDeepOpportunityReport.test.mjs
node frontend/src/components/PathFinderReportTemplate.behavior.test.mjs
```

Expected:

```text
PathFinder deep opportunity report smoke test passed
PathFinder report template behavior test passed
```

- [ ] **Step 5: Commit report integration**

Run:

```powershell
git add frontend/src/components/PathFinderReportTemplate.tsx frontend/src/components/PathFinderDeepOpportunityReport.test.mjs
git commit -m "feat: show real case evidence in pathfinder report"
```

## 9. Task 7: Final Verification and Handoff Analysis

**Files:**

- Modify: `docs/2026-06-24-top-gaokao-opportunity-system-analysis.md`
- Create or modify: `docs/evidence_autopilot/real_case_v0_handoff.md`

- [ ] **Step 1: Write handoff document**

Create `docs/evidence_autopilot/real_case_v0_handoff.md`:

```markdown
# Evidence Autopilot Real Case v0 Handoff

Date: 2026-06-24

## What Changed

- Added one Real Case v0 source log.
- Added one captured evidence fixture.
- Added a fixture-backed provider that emits provider results only from `captured_candidate` cards.
- Routed captured evidence through Evidence Autopilot, Opportunity Radar, and report output.

## What This Proves

The system can carry one reviewed public evidence fixture through the opportunity-research loop.

## What This Does Not Prove

- It does not prove admission probability.
- It does not prove graduate-school or employment outcomes.
- It does not prove improved 2026 admission results.
- It does not validate live web/PDF retrieval.
- It does not validate WeChat/Boss operator evidence.

## Verification Commands

```powershell
node frontend/src/components/EvidenceAutopilotRealCaseProvider.test.mjs
node frontend/src/components/EvidenceAutopilotApi.test.mjs
node frontend/src/components/EvidenceAutopilotResultNormalizer.test.mjs
node frontend/src/components/DeepOpportunityRealCase.test.mjs
node frontend/src/components/PathFinderDeepOpportunityReport.test.mjs
node frontend/src/PublicLaunchReadiness.test.mjs
Set-Location frontend
npm run lint
npm run build
Set-Location ..
Set-Location backend
.\.venv\Scripts\python.exe -m pytest src/test_evidence_autopilot_api_smoke.py src/test_backend_api_status_smoke.py -q
Set-Location ..
git diff --check
```

## Remaining Work

- Replace fixture-only public evidence with a live official-source provider.
- Add durable operator capture workflow for semi-closed sources.
- Connect quant positioning and 2025 backtest signals to case selection.
- Run outcome validation before making any effectiveness claim.
```

- [ ] **Step 2: Run final verification**

Run:

```powershell
node frontend/src/components/EvidenceAutopilotRealCaseProvider.test.mjs
node frontend/src/components/EvidenceAutopilotApi.test.mjs
node frontend/src/components/EvidenceAutopilotResultNormalizer.test.mjs
node frontend/src/components/DeepOpportunityRealCase.test.mjs
node frontend/src/components/PathFinderDeepOpportunityReport.test.mjs
node frontend/src/PublicLaunchReadiness.test.mjs
```

Run:

```powershell
Set-Location frontend
npm run lint
npm run build
Set-Location ..
```

Run:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest src/test_evidence_autopilot_api_smoke.py src/test_backend_api_status_smoke.py -q
Set-Location ..
git diff --check
```

Expected:

```text
All Node smoke tests pass.
Frontend lint has 0 errors; existing Fast Refresh warnings may remain.
Frontend build succeeds.
Backend smoke tests pass.
git diff --check has no whitespace errors.
```

- [ ] **Step 3: Commit handoff**

Run:

```powershell
git add docs/evidence_autopilot/real_case_v0_handoff.md docs/2026-06-24-top-gaokao-opportunity-system-analysis.md
git commit -m "docs: hand off evidence autopilot real case v0"
```

## 10. Plan Self-Review

Spec coverage:

- The plan implements one concrete case fixture.
- It requires at least five captured public evidence cards.
- It keeps placeholder/operator cards out of Opportunity Radar.
- It routes captured evidence through existing normalizer and report logic.
- It preserves claim boundaries and avoids outcome-improvement claims.
- It does not add UI redesign, live semi-closed scraping, or multi-agent spectacle.

Placeholder scan:

- The plan includes source-log blanks only in Task 1 before evidence is accepted.
- The plan explicitly blocks coding `captured_candidate` until those blanks are filled.
- No active implementation step permits empty URL, empty excerpt, or empty confidence.

Type consistency:

- `captured_candidate`, `requires_capture`, and `operator_review` match the existing API adapter contract.
- Provider results use `EvidenceAutopilotProviderResult`.
- Report and panel reuse existing `buildEvidenceAutopilotRun` and normalizer behavior.

Plan complete and saved to `docs/superpowers/plans/2026-06-24-real-case-v0-implementation.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - execute tasks in this session using checkpoints.

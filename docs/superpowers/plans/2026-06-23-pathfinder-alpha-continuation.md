# PathFinder Alpha Continuation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the full PathFinder / GaokaoAgent iteration record and continue toward a top-tier Gaokao opportunity research system built around evidence, quant signals, and auditable delivery.

**Architecture:** The product should converge on one main loop: `candidate profile -> Evidence Autopilot -> Opportunity Radar -> Deep Opportunity Card -> deliverable Chinese report`. Existing quant/backtest, evidence workflow, delivery review, report template, and public demo modules should be reused instead of starting a parallel product line.

**Tech Stack:** React + Vite frontend, TypeScript behavior tests, FastAPI backend, DeepSeek LLM provider, existing deep research agent/subgraph, GitHub Pages public demo, Docker Compose local deployment.

---

## 0. Problem Anchor

PathFinder / GaokaoAgent is not trying to be a generic admissions chatbot. The internal standard is to produce a top-tier Gaokao volunteer planning research system: use data, rules, evidence and deep research to find opportunities that ordinary parents, ordinary AI tools, and ordinary counselors often miss, then explain each opportunity in a way that is auditable, reviewable, and deliverable.

The durable product loop is:

```text
quant positioning
  -> evidence autopilot
  -> opportunity radar
  -> short/mid/long horizon judgment
  -> counselor-reviewable report
```

Non-goals for the next iteration:

- Do not rename the product to "one in ten thousand" or any similar slogan.
- Do not open another UI-only redesign branch before the evidence loop works.
- Do not build uncontrolled scraping for WeChat or Boss. Generate compliant operator tasks and process user-visible evidence only.
- Do not build random multi-agent social simulation before the evidence and opportunity model can provide real inputs.
- Do not claim admission certainty or employment certainty.

Success condition:

- A user can enter a candidate profile and target school/major.
- The system generates evidence tasks automatically.
- Public/open sources are retrieved through a provider interface.
- WeChat/Boss/semi-closed sources become compliant operator tasks.
- Evidence is normalized into cards with source, excerpt, date/provenance, confidence, counter-evidence, and review action.
- Opportunity Radar turns evidence into short-term admission, mid-term graduate progression, and long-term career judgments.
- The public demo and report template show the same product logic in Chinese.

---

## 1. Full Iteration Record

This section corrects the common mistake of treating the 2026-05-06 git initial commit as the real project start. It is only the start of the current git history. Local archived reports show the project was already active by 2026-01-01, with a clear FastAPI route by 2026-02-10.

### 2026-01-01: Running Prototype Evidence

Evidence:

- `archive/logs/backend_new.log`
- `archive/logs/backend_final.log`
- `archive/logs/frontend.log`
- `archive/logs/backend_2025.log`
- `archive/logs/backend_final_test.log`

What happened:

- Backend and frontend were already being run and debugged.
- There were multiple backend restart/fix/test logs on the same evening.
- This indicates the project existed before the current git history.

Why it matters:

- The project is not a June public-demo sprint. It has a much longer technical lineage.

### 2026-01-02: Project Structure Documentation

Evidence:

- `docs/reports_archive/260102_PROJECT_STRUCTURE.md`
- `00_REPORTS_INDEX.md`

What happened:

- The project structure was documented.
- Directory and file responsibilities were already being organized.

Why it matters:

- The system had enough code and complexity to require a project-structure report.

### 2026-01-07: Prompt RL and Test-Time Scaling

Evidence:

- `docs/reports_archive/260107_PROMPT_RL_IMPLEMENTATION_REPORT.md`
- `docs/reports_archive/260107_PROMPT_RL_TRAINING_RESULTS.md`
- `docs/reports_archive/260107_TTS_IMPLEMENTATION_REPORT.md`
- `docs/reports_archive/260107_FINAL_SESSION_SUMMARY.md`

What happened:

- Prompt RL was implemented and evaluated.
- Test-Time Scaling / Best-of-N style inference was explored.
- A final session summary documented the then-current state.

Why it matters:

- The early project was already thinking about policy improvement and inference-time quality, not just static recommendation rules.

### 2026-01-08: Review, Fixes, and School-Major Integration

Evidence:

- `docs/reports_archive/260108_LOGIC_FIXES_REPORT.md`
- `docs/reports_archive/260108_SCHOOL_MAJOR_INTEGRATION_PLAN.md`
- `docs/reports_archive/260108_INTEGRATION_COMPLETION_REPORT.md`
- `docs/reports_archive/260108_MEDIUM_ISSUES_LIST.md`
- `docs/reports_archive/260108_ALL_ISSUES_REPORT.md`
- `docs/reports_archive/260108_PROJECT_CLEANUP_REPORT.md`

What happened:

- Multiple rounds of code review and issue fixing were completed.
- School-major integration became an explicit workstream.
- Project cleanup and archive hygiene were started.

Why it matters:

- The "school + major group + major assignment" problem was already visible very early.

### 2026-01-09: Critical Recovery, Two-Stage Recommendation, GRPO Data

Evidence:

- `docs/reports_archive/260109_PROJECT_FINAL_REPORT.md`
- `docs/reports_archive/260109_CRITICAL_FIXES_REPORT.md`
- `docs/reports_archive/260109_TWO_STAGE_RECOMMENDATION_REPORT.md`
- `docs/reports_archive/260109_REALISTIC_DATA_GENERATOR_REPORT.md`
- `docs/reports_archive/260109_REALISTIC_DATA_IMPLEMENTATION_SUMMARY.md`
- `docs/reports_archive/260109_RESUME_VERIFICATION.md`

What happened:

- Critical errors were fixed and the project was recovered to a runnable state.
- A two-stage recommendation architecture was documented:
  - stage 1: school/major-group candidate selection
  - stage 2: major assignment and final combination
- GRPO-oriented realistic data generation was built around real rank sampling, candidate pools, and Monte Carlo probability.
- Resume/project claims were verified against code.

Why it matters:

- The project's original strength was not UI. It was the combination of quant engines, major assignment reasoning, recommendation policy, and auditability.

### 2026-01-10: Code Reading, Verification, and File Organization

Evidence:

- `docs/reports_archive/260110_CODE_READING_GUIDE.md`
- `docs/reports_archive/260110_CODE_WALKTHROUGH_EXAMPLES.md`
- `docs/reports_archive/260110_MODULE_DEPENDENCY_DIAGRAM.md`
- `docs/reports_archive/260110_RESUME_VERIFICATION_REPORT.md`
- `docs/reports_archive/260110_FILE_ORGANIZATION_REPORT.md`

What happened:

- The architecture and execution path were documented in detail.
- Example flows explained candidate generation, Monte Carlo simulation, and GRPO training.
- File naming and archive conventions were established.

Why it matters:

- There was already enough implementation depth to require onboarding docs and module dependency diagrams.

### 2026-01-13: Safe School Fixes

Evidence:

- `docs/260113_SAFE_SCHOOLS_FIX_REPORT.md`

What happened:

- The safe-school / lower-risk recommendation surface was corrected.

Why it matters:

- The project was already dealing with admission risk calibration and not only "best school" ranking.

### 2026-02-10: FastAPI Route A

Evidence:

- `docs/ROUTE_A_FASTAPI.md`

What happened:

- A FastAPI-based route was documented.

Why it matters:

- February work was about service/API productization, not a fresh start.

### 2026-03-23: Current Project Status Overview

Evidence:

- `docs/current_project_status_overview.md`

What happened:

- The project was described as a runnable research prototype.
- The main architecture included:
  - supervisor graph
  - routing and policy
  - profiling/game/deep research/report/critic agents
  - deliberation roles
  - rollout/pairwise/reward/GRPO alignment layer

Why it matters:

- The system had already moved beyond a simple Q&A app.

### 2026-03-31: Resume Project Reference

Evidence:

- `docs/resume_project_reference.md`

What happened:

- The project was converted into a coherent technical narrative for external communication.

Why it matters:

- A major workstream was explaining the project credibly.

### 2026-04-26: Interview Memory Cards

Evidence:

- `docs/interview_answer_memory_cards.md`
- `00_REPORTS_INDEX.md`

What happened:

- Interview materials and project claims were consolidated into one main reference.

Why it matters:

- The project had a mature enough technical narrative to be packaged for external evaluation.

### 2026-05-06: Current Git History Begins

Evidence:

- git commit `ac266af Initial GaokaoAgent project`

What happened:

- The current git line was initialized with a large import of backend, frontend, data, docs, and tests.

Why it matters:

- This is not the real project start. It is the start of the currently visible git lineage.

### 2026-05-20: 2025 Outcomes, Backtest, and Opportunity Radar Notes

Evidence:

- git commits `f508eee`, `d343325`, `8859fc5`, `a2c323d`
- `docs/2025_data_inventory.md`
- `docs/2025_actual_outcome_inventory.md`
- `docs/2025_real_backtest_results.md`
- `docs/opportunity_radar_modeling_notes.md`

What happened:

- 2025 outcome labels and ablation workflow were added.
- Frozen 2025 backtest flow was documented.
- Outcome-key coverage was improved.
- Opportunity Radar modeling was documented.

Why it matters:

- This was the transition from "recommendation system" to "validated opportunity research".

### 2026-05-26 to 2026-05-28: Quant Arbitrage and Plan Change Signals

Evidence:

- git commits `5a9cd65`, `e15197d`, `81110e8`
- `docs/quant_arbitrage_model_upgrade.md`
- `docs/arbitrage_strategy_casebook_zh.md`
- `docs/market_evidence_modeling_backtest.md`
- `docs/2025_enrollment_diff_report.md`

What happened:

- Quant arbitrage evidence loop was added.
- Market evidence, segment simulation, prefix optimizer, and arbitrage adapter were implemented.
- 2025 enrollment diff and major normalization were added.
- Plan change opportunity signals were added.

Why it matters:

- This is the strongest "top quant project" lineage in the repo.

### 2026-06-03: DeepSeek, Calibration, Delivery Gates

Evidence:

- 18 git commits on 2026-06-03.

What happened:

- DeepSeek provider support was added.
- Local analyze flow with DeepSeek was fixed.
- Candidate scoring and report evidence were optimized.
- Deterministic quant scorecards and calibration reports were added.
- Self-improvement, offline tuning, holdout validation, delivery bundle workflows, plan-quality gates, and portfolio audits were added.

Why it matters:

- The system began to look like an internal research and delivery platform.

### 2026-06-04: QuantLab and Research Evidence Integration

Evidence:

- 23 git commits on 2026-06-04.

What happened:

- Parallel-world stress testing was added.
- Deep research evidence was converted into quant signals and game scoring.
- Evidence refresh, failure mining, improvement actions, replay queue, experiment leaderboard, benchmark coverage, claim readiness, and research evidence audit were added.

Why it matters:

- This is the core of the project's "research lab" identity.

### 2026-06-05 to 2026-06-12: Delivery Preview and Client/Internal Separation

Evidence:

- git commits from 2026-06-05, 2026-06-07, 2026-06-11, 2026-06-12.
- `docs/iteration_log.md`

What happened:

- Volunteer plans were fed into delivery preview.
- Delivery preview bundle export was added.
- Client and internal delivery exports were split.
- Client package export was gated.
- Student career profile design was documented.

Why it matters:

- The project was being shaped into something a counselor could actually deliver.

### 2026-06-14 to 2026-06-15: Trusted Recommendation and Delivery System

Evidence:

- git commits from 2026-06-14 and 2026-06-15.
- `docs/superpowers/plans/2026-06-15-*.md`

What happened:

- Trusted recommendation baseline was closed.
- Plan audit workbench, printable report preview, delivery readiness console, external plan comparator, counselor checklist, delivery review record, evidence-bound report package, delivery case status, event store, competitive differentiation, paid value score, and plan change opportunity ledger were added.

Why it matters:

- This is when the project became a structured counselor-delivery system.

### 2026-06-17: Merge, Public Launch, GitHub Pages

Evidence:

- PR merge commit `a937117`.
- GitHub Pages workflow commits.
- public launch demo commits.

What happened:

- Admissions evidence workflow was added.
- Public launch demos and deploy scripts were added.
- GitHub Pages deployment config and SPA fallback were added.
- PR branch was merged into main.

Why it matters:

- The project moved from internal workflow to public demo and deployable product.

### 2026-06-18 to 2026-06-20: Public Demo, Report Design, Career/Job Evidence

Evidence:

- git commits from 2026-06-18, 2026-06-19, 2026-06-20.

What happened:

- Public demos and report were redesigned.
- Chinese public presentation was polished.
- Blue-white visual system was introduced.
- Report content was deepened and made more PDF-like.
- Career choice simulator was added.
- Domestic job market anchors and job evidence workbench were added.

Why it matters:

- The product became more presentable, but also risked drifting into UI/report polishing.

### 2026-06-22: Deep Opportunity Card and Evidence Ledger

Evidence:

- git commits `9a340b7`, `8bbffb2`, `76e2c6c`, `4b10817`.

What happened:

- Public demo surface text was localized.
- Deep opportunity card demo was added.
- Deep opportunity page was added to the report.
- Deep evidence collection ledger was added.

Why it matters:

- The project started returning to its strongest product thesis: discover deep, overlooked opportunities with evidence.

### 2026-06-23: Current Uncommitted Evidence Autopilot Work

Evidence:

- Dirty worktree as of 2026-06-23.
- New files:
  - `frontend/src/lib/evidenceAutopilot.ts`
  - `frontend/src/lib/deepOpportunityEvaluator.ts`
  - `frontend/src/components/DeepOpportunityEvaluationPanel.tsx`
  - `frontend/src/components/DeepOpportunityEvaluator.test.mjs`
- Modified files:
  - `frontend/src/lib/deepEvidenceCollectionPlan.ts`
  - `frontend/src/lib/deepOpportunityCard.ts`
  - `frontend/src/components/DeepEvidenceCollectionPlan.tsx`
  - `frontend/src/components/DeepOpportunityCard.tsx`
  - related tests

What happened:

- Mojibake in the deep opportunity path was cleaned up.
- Evidence Autopilot demo was added.
- Deep evidence plan, opportunity evaluation, and deep opportunity card were connected.
- The public page shows automatic evidence tasks, Boss/WeChat compliant operator tasks, and short/mid/long horizon evaluation.
- Verification already run:
  - `node frontend/src/components/DeepEvidenceCollectionPlan.test.mjs`
  - `node frontend/src/components/DeepOpportunityCard.test.mjs`
  - `node frontend/src/components/DeepOpportunityEvaluator.test.mjs`
  - `node frontend/src/PublicLaunchReadiness.test.mjs`
  - `npm run lint` in `frontend` with 0 errors and 3 existing Fast Refresh warnings
  - `npm run build` in `frontend`
  - Playwright check on `http://127.0.0.1:5180/app/deep-opportunity-card`

Why it matters:

- This is the current best continuation point. It starts connecting the previous evidence workflow to the public product experience.

---

## 2. Current State

### What Is Strong

- The project has a long technical lineage: RL, TTS, GRPO, quant scoring, Monte Carlo, Pareto, backtest, DeepSeek, research evidence, delivery review, and report generation.
- The strongest differentiation is not chat. It is evidence-backed opportunity discovery.
- The repo already has many pieces needed for the final system:
  - backend deep research agent/subgraph
  - frontend web evidence provider abstraction
  - evidence collection workspace
  - evidence intake and triangulation
  - opportunity radar / deep opportunity card
  - report template
  - GitHub Pages deployment
  - Docker deploy scripts

### What Is Weak

- The latest `Evidence Autopilot` is still demo-driven; it does not yet execute real provider searches end to end.
- The backend deep research path is not connected to the frontend Opportunity Radar.
- Semi-closed evidence sources such as WeChat and Boss are only represented as tasks, not normalized into a mature operator workflow.
- Some older files still contain mojibake or English claim boundaries.
- The project has accumulated many subsystems; without a single Alpha loop, it feels scattered.

### Main Product Risk

The biggest risk is continuing to add visible features without proving that the system can turn real evidence into a better recommendation. The next iteration should not prioritize another page redesign. It should prioritize a single credible evidence-to-opportunity loop.

---

## 3. Next Core Goal

Do not use "one in ten thousand" as a product name. Use it only as an internal quality bar.

Public product name:

```text
PathFinder / GaokaoAgent 高考志愿研究台
```

Internal quality bar:

```text
做出极少数顶尖高报顾问才有的判断质量：
能发现被低估机会，解释为什么，给出证据，指出反证，并落到录取、升学、就业、考公和家庭约束上。
```

Next concrete target:

```text
Evidence Autopilot v0: one real auditable opportunity case
```

The v0 product should complete this loop:

```text
candidate profile + target school/major
  -> generate evidence tasks
  -> execute public/open search provider
  -> create compliant operator tasks for WeChat/Boss
  -> normalize evidence into DeepEvidenceResult
  -> run Opportunity Radar gates
  -> render DeepOpportunityCard
  -> include result in PathFinderReportTemplate
```

---

## 4. Implementation Plan

### Task 1: Freeze and Verify the Current Evidence Autopilot Work

**Files:**

- Modify: `frontend/src/lib/evidenceAutopilot.ts`
- Modify: `frontend/src/lib/deepOpportunityEvaluator.ts`
- Modify: `frontend/src/lib/deepEvidenceCollectionPlan.ts`
- Modify: `frontend/src/lib/deepOpportunityCard.ts`
- Modify: `frontend/src/components/DeepOpportunityEvaluationPanel.tsx`
- Modify: `frontend/src/components/DeepOpportunityEvaluator.test.mjs`

- [ ] **Step 1: Check dirty worktree**

Run:

```powershell
git status -sb
git diff --stat
```

Expected:

- Uncommitted frontend deep opportunity / evidence autopilot changes are visible.
- No unrelated destructive reset or checkout is performed.

- [ ] **Step 2: Run focused tests**

Run:

```powershell
node frontend/src/components/DeepEvidenceCollectionPlan.test.mjs
node frontend/src/components/DeepOpportunityCard.test.mjs
node frontend/src/components/DeepOpportunityEvaluator.test.mjs
node frontend/src/PublicLaunchReadiness.test.mjs
```

Expected:

- All tests pass.

- [ ] **Step 3: Run frontend quality checks**

Run:

```powershell
Set-Location frontend
npm run lint
npm run build
Set-Location ..
```

Expected:

- `npm run lint` has 0 errors. Existing Fast Refresh warnings may remain.
- `npm run build` succeeds.

- [ ] **Step 4: Browser smoke test**

Use Playwright or the existing local server to check:

```text
http://127.0.0.1:5180/app/deep-opportunity-card
```

Expected visible tokens:

- `深度机会卡`
- `Evidence Autopilot`
- `机会雷达`
- `自动证据任务`
- `Boss直聘`
- `微信公众号`
- `短期录取`
- `中期升学`
- `长期职业`

- [ ] **Step 5: Commit the stable baseline**

Run only after all checks pass:

```powershell
git add frontend/src/lib/evidenceAutopilot.ts frontend/src/lib/deepOpportunityEvaluator.ts frontend/src/lib/deepEvidenceCollectionPlan.ts frontend/src/lib/deepOpportunityCard.ts frontend/src/components/DeepOpportunityEvaluationPanel.tsx frontend/src/components/DeepOpportunityEvaluator.test.mjs frontend/src/components/DeepEvidenceCollectionPlan.tsx frontend/src/components/DeepEvidenceCollectionPlan.test.mjs frontend/src/components/DeepOpportunityCard.tsx frontend/src/components/DeepOpportunityCard.test.mjs frontend/src/lib/jobEvidence.ts
git commit -m "feat: add evidence autopilot opportunity loop"
```

Expected:

- A clean commit preserving the current Alpha loop.

### Task 2: Add a Typed Evidence Autopilot Provider Contract

**Files:**

- Create: `frontend/src/lib/evidenceAutopilotProvider.ts`
- Create: `frontend/src/components/EvidenceAutopilotProvider.test.mjs`
- Modify: `frontend/src/lib/evidenceAutopilot.ts`

- [ ] **Step 1: Write the failing provider test**

Create `frontend/src/components/EvidenceAutopilotProvider.test.mjs` with assertions for:

- provider input contains `targetLabel`, task id, query, channel, required fields.
- public provider result becomes a candidate evidence capture.
- operator-only channels return review tasks, not fake verified evidence.

Expected failure:

- `Cannot find module '../lib/evidenceAutopilotProvider.ts'`.

- [ ] **Step 2: Run the failing test**

Run:

```powershell
node frontend/src/components/EvidenceAutopilotProvider.test.mjs
```

Expected:

- FAIL because the provider contract does not exist.

- [ ] **Step 3: Implement minimal provider contract**

Create a TypeScript module with:

```ts
export type EvidenceAutopilotProviderChannel =
  | "public_web"
  | "official_pdf"
  | "wechat_operator"
  | "job_market_operator"
  | "manual_review";

export interface EvidenceAutopilotProviderRequest {
  requestId: string;
  taskId: string;
  targetLabel: string;
  channel: EvidenceAutopilotProviderChannel;
  query: string;
  requiredFields: string[];
  maxResults: number;
}

export interface EvidenceAutopilotProviderResult {
  requestId: string;
  taskId: string;
  sourceTitle: string;
  sourceUrl: string;
  sourceType: "official" | "school" | "paper" | "job" | "wechat" | "discussion" | "other";
  excerpt: string;
  capturedAt: string;
  confidence: "high" | "medium" | "low";
}

export interface EvidenceAutopilotProvider {
  id: string;
  search(request: EvidenceAutopilotProviderRequest): Promise<EvidenceAutopilotProviderResult[]>;
}
```

- [ ] **Step 4: Keep operator channels blocked from fake verification**

Add a helper:

```ts
export function isOperatorOnlyChannel(channel: EvidenceAutopilotProviderChannel): boolean {
  return channel === "wechat_operator" || channel === "job_market_operator" || channel === "manual_review";
}
```

Expected:

- Operator-only channels can generate tasks, but cannot be silently promoted to verified evidence without captured excerpts.

- [ ] **Step 5: Run test again**

Run:

```powershell
node frontend/src/components/EvidenceAutopilotProvider.test.mjs
```

Expected:

- PASS.

### Task 3: Convert Provider Results into DeepEvidenceResult

**Files:**

- Create: `frontend/src/lib/evidenceAutopilotResultNormalizer.ts`
- Create: `frontend/src/components/EvidenceAutopilotResultNormalizer.test.mjs`
- Modify: `frontend/src/lib/evidenceAutopilot.ts`

- [ ] **Step 1: Write failing normalizer test**

Test these behaviors:

- two official/public results for a P0 task become `verified`.
- one result for a P0 task becomes `weak`.
- zero results become `missing`.
- counter-evidence result containing blocking keywords becomes `counter_hit`.
- operator-only task with no captured result remains `missing` or `weak`.

Expected:

- FAIL because normalizer does not exist.

- [ ] **Step 2: Implement normalizer**

Create:

```ts
export function normalizeEvidenceAutopilotResults({
  plan,
  providerResults,
}: {
  plan: DeepEvidenceCollectionPlan;
  providerResults: EvidenceAutopilotProviderResult[];
}): DeepEvidenceResult[] {
  // group by taskId
  // compare source count with task priority
  // create verified / weak / missing / counter_hit statuses
}
```

Rules:

- `P0` normally requires at least 2 sources.
- `civil_service_path` may pass with 1 source.
- `counter_evidence` with blocking terms such as `黑名单`, `校区冲突`, `调剂风险`, `断档`, `投诉` becomes `counter_hit`.
- Evidence notes must include source title and excerpt.

- [ ] **Step 3: Connect into `buildEvidenceAutopilotRun`**

Allow:

```ts
buildEvidenceAutopilotRun({
  plan,
  providerResults,
})
```

Expected:

- If `providerResults` is supplied, use normalized real results.
- If not supplied, keep the existing demo evidence path for public demo stability.

- [ ] **Step 4: Run tests**

Run:

```powershell
node frontend/src/components/EvidenceAutopilotResultNormalizer.test.mjs
node frontend/src/components/DeepOpportunityEvaluator.test.mjs
```

Expected:

- Both pass.

### Task 4: Add a Snapshot Public Provider for Demo Stability

**Files:**

- Create: `frontend/src/lib/evidenceAutopilotSnapshotProvider.ts`
- Create: `frontend/src/components/EvidenceAutopilotSnapshotProvider.test.mjs`
- Modify: `frontend/src/components/DeepOpportunityEvaluationPanel.tsx`

- [ ] **Step 1: Write failing snapshot provider test**

Test that the provider:

- returns official admissions evidence for `official_admission`.
- returns school/faculty evidence for `faculty_research`.
- returns job evidence for `employment_market`.
- returns no fake full evidence for `wechat_operator` unless explicit snapshot data exists.

- [ ] **Step 2: Implement snapshot provider**

Create a deterministic local provider that returns stable public-demo evidence shaped like `EvidenceAutopilotProviderResult`.

Expected:

- Public demo remains deterministic.
- The data shape is the same as a future real provider.

- [ ] **Step 3: Use snapshot provider in the demo panel**

The panel should call the same normalizer path used by real provider results.

Expected:

- Public page still renders the same visible product narrative.
- The code path is closer to production.

### Task 5: Backend Deep Research Bridge

**Files:**

- Modify: `backend/src/agents/deep_research_agent.py`
- Modify: `backend/src/subgraphs/deep_research.py`
- Create or modify: `backend/src/evidence_autopilot_api.py`
- Create: `backend/src/test_evidence_autopilot_api_smoke.py`
- Modify: `backend/src/main.py`

- [ ] **Step 1: Write backend smoke test**

Test an endpoint or callable function that accepts:

```json
{
  "province": "广东",
  "schoolName": "华南理工示例校",
  "majorName": "智能制造与数据工程",
  "targetYear": 2026
}
```

Expected output:

- task list
- search queries
- evidence cards
- claim boundary

- [ ] **Step 2: Fix mojibake in deep research prompts**

Read:

- `backend/src/subgraphs/deep_research.py`
- `backend/src/agents/deep_research_agent.py`

Replace mojibake public strings with Chinese or English consistently.

Expected:

- Backend source no longer leaks broken Chinese prompts into outputs.

- [ ] **Step 3: Add candidate-specific research topic builder**

Add a helper that builds research questions for:

- official admissions
- historical rank
- faculty research
- undergraduate access
- employment market
- graduate progression
- civil service path
- counter-evidence

Expected:

- Backend no longer treats every research request as a generic topic.

- [ ] **Step 4: Wire endpoint into FastAPI**

Expose a minimal endpoint:

```text
POST /api/evidence-autopilot/research
```

Expected:

- Local dev can call it with candidate/target payload.

### Task 6: Frontend API Adapter

**Files:**

- Create: `frontend/src/lib/evidenceAutopilotApi.ts`
- Create: `frontend/src/components/EvidenceAutopilotApi.test.mjs`
- Modify: `frontend/src/components/DeepOpportunityEvaluationPanel.tsx`

- [ ] **Step 1: Write failing frontend API test**

Test that:

- request payload maps province/school/major/year correctly.
- backend evidence cards map into provider results.
- API failure falls back to snapshot provider with an explicit "demo fallback" boundary.

- [ ] **Step 2: Implement API adapter**

Use existing frontend API patterns from:

- `frontend/src/lib/api.ts`

Expected:

- The adapter respects same-origin API config and GitHub Pages public demo constraints.

- [ ] **Step 3: Render backend-backed state when available**

Panel states:

- `demo_snapshot`
- `backend_connected`
- `backend_failed_snapshot_fallback`

Expected:

- Users can see whether evidence is live or demo snapshot.

### Task 7: Report Integration

**Files:**

- Modify: `frontend/src/components/PathFinderReportTemplate.tsx`
- Modify: `frontend/src/components/PathFinderReportTemplate.behavior.test.mjs`
- Modify: `frontend/src/components/PathFinderDeepOpportunityReport.test.mjs`

- [ ] **Step 1: Write failing report test**

Assert that report includes:

- Evidence Autopilot status
- Opportunity Radar score
- P0 gate status
- counter-evidence status
- short/mid/long horizon sections
- source excerpts or evidence placeholders

- [ ] **Step 2: Reuse deep opportunity model in report**

Do not duplicate separate report-only logic unless necessary.

Expected:

- Public demo page and report page tell the same product story.

- [ ] **Step 3: Build and visually inspect**

Run:

```powershell
Set-Location frontend
npm run build
Set-Location ..
```

Expected:

- Build passes.
- Report remains Chinese and readable.

### Task 8: Launch Readiness and Public Demo

**Files:**

- Modify: `frontend/src/PublicLaunchReadiness.test.mjs`
- Modify: `README.md`
- Modify: `.github/workflows/deploy-pages.yml` only if needed

- [ ] **Step 1: Update launch readiness smoke**

Assert public demo routes include:

- `/app/deep-opportunity-card`
- report preview route
- GitHub Pages fallback
- DeepSeek env documentation

- [ ] **Step 2: Update README**

Add one concise section:

```md
## PathFinder Alpha Loop

PathFinder uses quant positioning, evidence autopilot, opportunity radar, and a Chinese deliverable report to find auditable Gaokao volunteer opportunities.
```

- [ ] **Step 3: Run final checks**

Run:

```powershell
node frontend/src/PublicLaunchReadiness.test.mjs
Set-Location frontend
npm run lint
npm run build
Set-Location ..
git diff --check
```

Expected:

- 0 lint errors.
- Build passes.
- No whitespace errors.

---

## 5. Execution Order

Recommended order:

1. Commit the current Evidence Autopilot baseline.
2. Add typed provider contract.
3. Add result normalizer.
4. Add snapshot provider.
5. Add backend research bridge.
6. Add frontend API adapter.
7. Connect report.
8. Verify launch readiness.

Do not start backend bridge before the provider contract and normalizer are stable. The frontend contract defines what the backend must supply.

---

## 6. Quality Bar

Each future opportunity claim must answer:

- What is the claim?
- Which source supports it?
- What excerpt supports it?
- What is the source type?
- What is the confidence?
- What would disprove it?
- Which horizon does it affect: admission, graduate progression, career, civil-service path?
- Is this ready for counselor review or blocked?

If a claim cannot answer these questions, it should be shown as an evidence gap, not as a recommendation.

---

## 7. Self-Review

Spec coverage:

- Full history from January through current uncommitted June work is recorded.
- The product name is preserved as PathFinder / GaokaoAgent.
- The internal "top-tier" bar is separated from branding.
- The next implementation path focuses on Evidence Autopilot v0 rather than UI drift.
- Backend, frontend, report, tests, and deployment readiness are included.

Placeholder scan:

- No `TBD` or `TODO` placeholders are used.
- Every task has files, commands, and expected outcomes.

Type consistency:

- Provider types are named consistently as `EvidenceAutopilotProvider*`.
- Normalized evidence output uses existing `DeepEvidenceResult`.
- Opportunity scoring continues to use `buildDeepOpportunityEvaluation`.

---

Plan complete and saved to `docs/superpowers/plans/2026-06-23-pathfinder-alpha-continuation.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task and review between tasks.
2. **Inline Execution** - execute tasks in this session using checkpoints.

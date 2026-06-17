# PathFinder Product Iteration Handoff - 2026-06-15

## 1. Why This Handoff Exists

The next conversation should continue product iteration without reopening the
whole history. The founder's current objective is not "make another Gaokao
chatbot." The objective is to build a paid product that can do three things
better than broad free AI tools:

1. Accurately mine public-opinion and admissions-market trends, then turn them
   into real low-attention opportunity analysis.
2. Use enough data, web search, and evidence-based reasoning to produce a
   detailed plan that can be defended row by row.
3. Help students and parents understand the concepts, tradeoffs, and interests
   they should actually care about before choosing schools and majors.

## 2. Current Repo State At Handoff

- Repository: `C:\PathFinder`
- Branch: `codex/trusted-recommendation-baseline`
- Latest pushed commit: `415214e fix: require audited plan change evidence`
- Remote tracking state: local branch is synced with origin at the time this
  note was created.
- Current worktree is not clean because another thread appears to be editing:
  - `frontend/src/components/PathFinderReportTemplate.tsx`
  - `frontend/src/components/PathFinderReportTemplate.test.mjs`
- Do not reset, checkout, rebase, pull blindly, or discard those template
  changes. Inspect them before any staging operation.

Recent product-iteration commits:

- `415214e fix: require audited plan change evidence`
- `60d50c7 feat: add plan change opportunity ledger`
- `835df2e feat: add paid value scoring`
- `ab80570 feat: add competitive differentiation score`
- `58aad97 feat: add delivery case event persistence adapter`
- `793056b feat: add delivery case event store`
- `ed7d6aa feat: surface delivery case status panel`
- `74298bf feat: add delivery case status contract`

## 3. Current Product Thesis

Large free AI products have strong conversation and distribution. PathFinder
should not charge for "also can answer." The paid reason must be evidence work:

- Find official enrollment-plan changes that others missed.
- Detect adjustment, withdrawal, blacklist, and safety-anchor failure risks.
- Audit Qianwen, Tencent, teacher, and family plans instead of ignoring them.
- Produce an executable volunteer draft, not a loose recommendation list.
- Require counselor signoff and make claim boundaries explicit.

The product standard should be:

> Do not claim opportunity unless the chain can be audited.

## 4. What Is Implemented Now

### Competitive differentiation score

File: `frontend/src/lib/competitiveDifferentiationScore.ts`

Protocol: `competitive_differentiation_score_v1`

It scores whether a case is differentiated from generic AI/report workflows
using evidence coverage, external plan challenge, delivery trace, preference
fidelity, official data boundary, and plan-change alpha.

### Paid value score

File: `frontend/src/lib/paidValueScore.ts`

Protocol: `paid_value_score_v1`

It scores the concrete reasons a family could reasonably pay:

- plan-change opportunity
- adjustment and withdrawal risk avoidance
- external-plan audit
- executable volunteer draft
- counselor signoff boundary

### Plan Change Opportunity Ledger

File: `frontend/src/lib/planChangeOpportunityLedger.ts`

Protocol: `plan_change_opportunity_ledger_v1`

Each opportunity must preserve:

`official_source -> diff_type -> affected_rows -> rank_delta_estimate -> competitor_missed -> recommendation_action -> risk_guard`

Important scoring boundary:

- `competitor_missed=unknown` does not add score.
- missing explicit `risk_guard.checks` does not add score.
- an official diff with rank delta and action, but without competitor-miss
  proof and risk guard, cannot become `ready`.

Panel:

- `frontend/src/components/PlanChangeOpportunityLedgerPanel.tsx`
- Integrated into `frontend/src/components/GameMatrixView.tsx`

Tests:

- `frontend/src/components/PlanChangeOpportunityLedger.behavior.test.mjs`
- `frontend/src/components/PlanChangeOpportunityLedgerPanel.behavior.test.mjs`

## 5. Verification Evidence From Latest Iteration

These commands passed in the latest implementation pass:

```powershell
cd C:\PathFinder\frontend
node src\components\PlanChangeOpportunityLedger.behavior.test.mjs
node src\components\PlanChangeOpportunityLedgerPanel.behavior.test.mjs
node src\components\PaidValueScore.behavior.test.mjs
node src\components\PaidValuePanel.behavior.test.mjs
node src\components\CompetitiveDifferentiationPanel.behavior.test.mjs
node src\components\DeliveryWorkflowBehavior.test.mjs
npm run lint
npm run build
```

`npm run lint` still reports two existing Fast Refresh warnings in:

- `frontend/src/components/ui/badge.tsx`
- `frontend/src/components/ui/button.tsx`

No lint errors and production build passed.

Subagent review:

- Ledger initial review: 82/100. Main criticism was that unknown competitor
  coverage and default risk guard could still allow a weak opportunity to look
  ready.
- After tightening scoring: 88/100. The issue was confirmed fixed.

These scores are product and engineering judgments, not automated truth.

## 6. What Still Is Not Solved

The current ledger is an audit container, not yet the discovery engine.

Hard remaining gaps:

1. 2026 official enrollment plan ingestion is still missing.
2. 2025 to 2026 row-level diff engine is still missing.
3. rank-impact calibration for quota changes, new majors, discontinued majors,
   group splits, group merges, and subject requirement changes is still
   missing.
4. competitor omission proof is not automatic. We need to compare PathFinder's
   ledger against Qianwen, Tencent, teacher, and family plans row by row.
5. public-opinion trend mining is not yet connected to opportunity scoring.
6. the product still needs a better student/parent concept layer: families need
   to understand what a professional group is, why adjustment risk matters, why
   "safe" can fail, and what kind of interest or career preference should change
   the plan.

## 7. The Three Next Product Tracks

### Track A: Trend and opportunity discovery

Goal: turn social attention, narratives, and plan changes into opportunity
signals.

Build:

- public-opinion signal schema: heat, fear, policy attention, brand
  overreaction, regional avoidance, new-major hype, tuition sensitivity
- source capture: official plan, school charter, school news, exam-authority
  notices, mainstream articles, search snippets, social discussion summaries
- opportunity model: whether the public narrative is likely overpricing or
  underpricing a school/group/major
- guardrail: no trend signal can override official plan data or hard student
  constraints

Minimum useful output:

- "This group may be under-attended because X narrative is dominating, but
  official plan and historical rank evidence show Y."

### Track B: Data and web-backed detailed plan

Goal: produce a detailed, defensible volunteer draft, not a chat answer.

Build:

- official 2026 plan ingestion
- 2025 to 2026 diff ledger
- row-level evidence cards
- external-plan comparator for Qianwen/Tencent/teacher/family plans
- rank-impact estimates with confidence and failure interpretation
- final volunteer draft with counselor review state

Minimum useful output:

- each row explains why it is selected, what could go wrong, what changed from
  last year, whether competitors missed it, and what to verify before signoff

### Track C: Student and parent concept clarity

Goal: help families know what they should care about.

Build:

- concept map for Guangdong professional-group admissions
- interest clarification flow that does not overuse MBTI
- RIASEC/career values as soft major-fit context, not admission logic
- parent-facing explanations for adjustment, withdrawal, safe-anchor failure,
  tail-major risk, and group-bundle risk
- comparison mode: "what you think you are choosing" versus "what the
  professional group actually contains"

Minimum useful output:

- families can explain their own constraints, blacklist, acceptable tradeoffs,
  and interest direction before looking at final rows

## 8. Recommended Next Iteration

Start with the discovery engine, because it is closest to paid differentiation.

Suggested implementation order:

1. Add a `planChangeDiffEngine` contract that accepts prior-year and
   current-year plan rows and emits normalized diffs.
2. Add behavior tests for quota expansion, quota reduction, new major,
   discontinued major, group split, group merge, and subject requirement change.
3. Convert diffs into `PlanChangeOpportunityLedger` inputs.
4. Add rank-impact placeholders with explicit confidence and claim boundary.
5. Add a public-opinion trend signal object, but keep it separate from official
   plan evidence until calibrated.

Do not start by making the UI prettier. The bottleneck is evidence generation.

## 9. Suggested New-Chat Opening Prompt

Use this prompt in the next chat:

```text
请继续 C:\PathFinder 项目。先阅读：

- docs/handoffs/2026-06-15-product-iteration-handoff.md
- docs/superpowers/plans/2026-06-15-plan-change-opportunity-ledger.md

当前分支是 codex/trusted-recommendation-baseline。先运行 git status -sb，不要 reset、checkout、rebase、pull，也不要覆盖另一个聊天在 PathFinderReportTemplate.tsx 和 PathFinderReportTemplate.test.mjs 上的改动。

我的核心目标是：
1. 准确挖掘社会舆论趋势，并真正分析捡漏机会；
2. 有足够多的数据、联网搜索和证据推理能力，给出一套有理有据的详细志愿解读方案；
3. 作为产品，支撑学生和家长理清楚概念，知道自己到底应该对什么感兴趣、应该接受哪些取舍。

请每次使用科研相关 skill 校准 claim/evidence/boundary。下一步优先做 planChangeDiffEngine，把 2025->2026 官方招生计划变化转成可审计 diff，再接入 Plan Change Opportunity Ledger。不要把舆论趋势当成官方证据，趋势只能作为 opportunity hypothesis。
```

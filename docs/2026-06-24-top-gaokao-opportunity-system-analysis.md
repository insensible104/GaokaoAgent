# PathFinder Top Gaokao Opportunity System Analysis

Date: 2026-06-24

## Thesis

The core product is now fixed:

```text
quant positioning
  -> Evidence Autopilot
  -> Opportunity Radar
  -> Deep Opportunity Card
  -> deliverable Chinese report
```

The project should be judged by whether this loop can produce a better auditable opportunity judgment than a generic AI chat answer. More pages, more agents, and more report styling are secondary unless they make this loop more true.

## What Is Already Useful

### January to April agent and recommendation work

The early agent work is not wasted. It should be treated as a research-planning and critique engine, not as the front-stage product.

Useful parts:

- candidate profiling and routing
- two-stage school/major-group/major assignment thinking
- Monte Carlo and risk calibration concepts
- Prompt RL, TTS, and GRPO as future policy-improvement infrastructure
- deep research and critic agents as evidence-task and counter-evidence planners
- FastAPI route/productization groundwork

Current role:

```text
agents generate better questions and checks
evidence decides what can be claimed
```

The agent layer should not make unsupported conclusions visible to families or counselors.

### May quant and outcome work

The May work is one of the strongest assets because it moved the project from recommendation generation toward validation:

- 2025 outcome inventory
- backtest reports
- opportunity radar notes
- enrollment diff analysis
- quant arbitrage and plan-change signals

This should become the quant-positioning layer that decides where Evidence Autopilot should spend attention.

### June delivery and evidence work

The June work made the system presentable and closer to delivery:

- DeepSeek provider support
- QuantLab and evidence-to-quant concepts
- delivery readiness and report package workflows
- public demos and GitHub Pages
- career/job evidence surfaces
- Deep Opportunity Card
- Evidence Autopilot provider contract, normalizer, snapshot provider, backend bridge, API adapter, and report integration

This is enough infrastructure to stop broad expansion and start one real case.

## Current Implementation Maturity

### Implemented

- Evidence Autopilot can generate tasks.
- Provider result shape is typed.
- Operator-only channels are separated from verified evidence.
- Normalizer can mark verified, weak, missing, and counter-hit evidence.
- Frontend API adapter rejects malformed backend evidence cards.
- Only `captured_candidate` cards can become provider results.
- Backend can generate candidate-specific research tasks and placeholders.
- Backend now returns an `evidenceCoverage` gate summary with captured task IDs, missing P0 task IDs, operator/manual-review tasks, review blockers, and counselor-review readiness.
- Frontend API state now preserves and validates backend `evidenceCoverage`, so a malformed or incomplete backend response falls back to the demo boundary instead of appearing connected.
- Backend accepts request-scoped `reviewedEvidenceCards` so compliant human-captured operator evidence can enter the same coverage gate without pretending that an uncollected task is verified.
- Report template can show Evidence Autopilot / Opportunity Radar content.

### Partially implemented

- Backend-to-frontend bridge exists, but backend does not execute public web/PDF retrieval.
- Snapshot provider stabilizes demo output, but it is not live evidence.
- Report integration exists, but it still needs one real captured case to become credible as a product artifact.
- Agent research logic exists historically, but it is not yet fully reused as a disciplined evidence planner.

### Not implemented yet

- Real provider retrieval for official public sources.
- Durable captured-evidence storage for one real case.
- Operator workflow for semi-closed evidence capture with screenshots or review IDs.
- A verified real opportunity case that flows into card and report.
- Outcome validation proving improved 2026 admission results.

## Main Risk

The main risk is not technical inability. It is scope drift.

The project has enough components to keep expanding forever:

- more agent roles
- more report sections
- more public demos
- more career simulations
- more delivery gates
- more quantitative experiments

Most of those are useful later. Right now they are harmful if they delay the first real evidence-to-opportunity case.

## Research Taste Calibration

A top-tier opportunity system should be conservative about claims and aggressive about evidence.

Good taste:

- show the exact source and excerpt
- separate opportunity hypothesis from recommendation
- look for disconfirming evidence
- expose evidence gaps instead of hiding them
- distinguish demo/snapshot from captured evidence
- connect short-term admission, mid-term progression, and long-term career logic

Bad taste:

- claiming certainty from a polished report
- treating agent consensus as proof
- treating synthetic or snapshot evidence as real evidence
- adding dashboards before one real case works
- optimizing prompts before ground truth and evaluation scope are clear

## Next Iteration Slice

The next slice should be Real Case v0:

1. Select one concrete province, rank/score band, school, and major.
2. Capture at least five public evidence cards with URL, excerpt, time, source type, confidence, and review action.
3. Add a fixture-backed provider or backend response path that emits `captured_candidate`.
4. Run the existing normalizer and Opportunity Radar.
5. Render the case in Deep Opportunity Card and the Chinese report.
6. Keep WeChat/Boss as operator tasks unless manually captured evidence is provided.

This is the first milestone where PathFinder can credibly say:

```text
Here is one opportunity hypothesis, here is the evidence, here is what would disprove it, and here is the counselor-review boundary.
```

## Decision

Continue with Real Case v0 before any new UI redesign, multi-case platform, live semi-closed scraping, or additional agent spectacle.

The agent work remains a backend research capability. The product value is the auditable opportunity judgment.

## 2026-06-24 Real Case v0 Status Update

Real Case v0 is now implemented as a fixture-backed, auditable slice:

- Source log: `docs/evidence_autopilot/real_case_v0_source_log.md`
- Fixture: `data/evidence_autopilot/real_case_v0.json`
- Provider: `frontend/src/lib/evidenceAutopilotRealCaseProvider.ts`
- API state: `real_case_fixture`
- Opportunity Radar smoke test: `frontend/src/components/DeepOpportunityRealCase.test.mjs`
- Report integration: `PathFinderReportTemplate.tsx`
- Handoff: `docs/evidence_autopilot/real_case_v0_handoff.md`

This changes the maturity assessment: the system now has one real reviewed public-evidence case flowing through Evidence Autopilot, Opportunity Radar, and the report. It is still fixture-backed, so the next bottleneck is live official-source retrieval and durable capture provenance, not another UI layer.

### 2026-06-24 Live Official-Source Provider Slice

The first narrow live provider now exists on the backend:

- Module: `backend/src/official_source_provider.py`
- Test: `backend/src/test_official_source_provider_smoke.py`
- API contract: `enableOfficialSourceProvider` opt-in on `EvidenceAutopilotResearchRequest`
- Captured cards: `official-plan-charter`, `rank-history-band`, `faculty-research-direction`, `undergrad-access`, `graduate-progression`
- Current scope: SCUT 2026 admissions-plan/charter boundary, the 2025 Guangdong physics ordinary-batch historical score row for `工科试验班(智能装备与先进制造)`, and WUSIE school pages for curriculum/faculty, undergraduate platform access, and school-described progression paths

This is intentionally not a general crawler. It proves that official SCUT and school pages can be parsed into `captured_candidate` cards with URL, excerpt, capture time, confidence, and review action. It also establishes a provider registry that can merge cards and warnings without letting a failed provider fabricate evidence or break task generation. It still does not prove 2026 admission probability, final Guangdong professional-group placement, graduate-school outcomes, employment outcomes, or generalized source coverage.

### 2026-06-24 Evidence Coverage Gate

The backend API now exposes `evidenceCoverage` on every Evidence Autopilot response:

- `capturedTaskIds`: tasks backed by a captured card with URL and excerpt
- `missingP0TaskIds`: P0 evidence gates that still block counselor review
- `operatorTaskIds`: WeChat, job-market, and manual-review tasks that require compliant human capture
- `readyForCounselorReview`: false until P0 gaps are closed
- `reviewBlockers`: machine-readable reasons the case is not yet deliverable

This is a product-control improvement, not an outcome claim. It helps PathFinder stop expanding the case when the immediate blocker is simply missing P0 evidence.

The frontend adapter now carries this summary through `EvidenceAutopilotApiState`. No new UI surface was added in this slice; the point is to stabilize the contract first.

### 2026-06-24 Reviewed Evidence Injection

The backend request contract now accepts `reviewedEvidenceCards` for human-captured evidence from semi-closed or manual-review channels. A reviewed card only closes a task when it matches an existing task and includes a source URL or review ID, excerpt, capture date, confidence, and review action. Incomplete notes are rejected and keep the P0 gate blocked.

This gives the system a compliant path for Boss, WeChat, and counter-evidence work without scraping or fabricating evidence. It is still stateless and request-scoped; durable storage, reviewer identity, screenshots, and audit IDs remain future work.

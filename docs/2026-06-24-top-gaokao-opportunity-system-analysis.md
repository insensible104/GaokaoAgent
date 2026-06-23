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

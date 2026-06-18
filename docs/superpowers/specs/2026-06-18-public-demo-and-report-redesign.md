# Public Demo And Report Redesign

## Context

PathFinder is now public on GitHub Pages, but the visible experience does not yet match the product claim. The repository positions the system as evidence-first Gaokao planning: structured recommendation, quantitative risk control, deep research, external-plan audit, and counselor-review boundaries. The current UI exposes these capabilities, but the visual language still reads like a generic AI dashboard and the generated report does not yet feel like a trusted research deliverable.

The redesign will use the Garden skills workflow as the design operating system:

- `web-design-engineer` for the app shell, public landing surface, and demo workstations.
- `beautiful-article` for the generated report as a formal `full-report` style artifact.
- `web-video-presentation` later for launch/传播 videos, after the report and demos can stand on their own.

## Goal

Rewrite the public-facing app, both public demos, and the generated report template as one coherent evidence product.

The first impression should be: this is not another chat wrapper. It is a quant-and-research workbench that turns a volunteer plan into a reviewable decision package.

## Design Direction

Use one unified design language: **Evidence Workbench + Research Report**.

The visual anchors are:

- Tufte data-ink for charts, evidence notes, and report pages.
- Bloomberg-style information density for operator/demo workspaces.
- Stripe Press-style editorial warmth for the family-facing report.

This is not a decorative remix. The hierarchy is:

1. Report readability and trust come first.
2. Data density is used only where the user is comparing evidence, risks, and opportunities.
3. Editorial warmth is used to make the final deliverable feel worth saving, sharing, and printing.

## Design System

- Palette:
  - Paper: `#FBFAF6`
  - Bone: `#F1ECDE`
  - Ink: `#1B1B1A`
  - Slate: `#3E4A5C`
  - Evidence green: `#0D8A5A`
  - Risk red: `#A6300E`
  - Warning amber: `#B86B16`
  - Rule line: `#D8D2C2`
- Typography:
  - Report titles use a Chinese-friendly serif stack when available, falling back cleanly.
  - App controls and dense tables use compact sans/mono stacks with tabular numbers.
  - Avoid generic oversized AI headlines. Compact panels get compact headings.
- Layout:
  - Public home becomes a product surface, not a marketing hero page.
  - Demos become three-zone workbenches: case input, evidence ledger, decision output.
  - Report becomes a multi-section printable document with cover, contents, executive summary, opportunity radar, risk ledger, evidence ledger, trend analysis, and final action checklist.
- Radius and shadows:
  - Small radius only, usually 0-6px.
  - Hairline borders instead of floating card shadows.
- Motion:
  - Restrained hover/focus states.
  - No gradient-orb backgrounds, no decorative blobs, no emoji-as-icons.

## Scope

### App Shell And Public Entry

Rewrite the first screen in `frontend/src/App.tsx` so it immediately shows:

- PathFinder's concrete claim: 志愿表体检、趋势机会、证据账本、交付边界.
- Two public demos as primary routes:
  - `/app/external-plan-audit-demo`
  - `/app/admissions-opportunity-demo`
- A report-preview entry that shows the final artifact quality.
- Clear API/backend status boundary without making the page feel broken when the API is not available.

### Public Demo Workstations

Rewrite `AdmissionsOpportunityDemoCasePanel.tsx` and `ExternalPlanAuditDemoPanel.tsx` around the same grammar:

- Left: student/context and compared plan.
- Center: evidence, gaps, trend signals, source confidence.
- Right: decision output, blocked claims, next actions, counselor signoff.

Each demo must expose the difference from Qwen-style generation:

- It audits an answer instead of trusting fluent text.
- It shows which claims are allowed, blocked, or hypothesis-only.
- It separates official-data facts, trend hypotheses, and family-facing wording.

### Generated Report

Rewrite `PathFinderReportTemplate.tsx` as a formal report package rather than a dashboard printout.

Required sections:

1. Cover and report boundary.
2. Executive decision summary.
3. Volunteer slate overview.
4. Hidden opportunity radar.
5. Trend analysis with confidence labels.
6. Risk ledger.
7. Evidence ledger.
8. Counselor review and family action checklist.

The report must be printable, screenshot-worthy, and readable on the published Pages route. It must not include sample-only claims when rendering a real payload.

## Implementation Boundaries

- Do not change the recommendation algorithm in this redesign.
- Do not invent new admissions facts or fake evidence.
- Do not add a new design library unless the current stack makes a control impossible.
- Do not use AI-cliche decoration: purple-blue gradients, orb backgrounds, emoji icon substitutes, fake stats, or card spam.
- Keep public demos working without an API key.

## Testing And Verification

Add or update focused checks for:

- No mojibake in public-facing report/demo strings.
- Report template still renders `EvidenceLedger`, `RiskLedger`, delivery boundaries, and real-payload safeguards.
- Static demo routes still build and deep-link under GitHub Pages.
- Desktop and mobile screenshots show no overlap, cropped buttons, or unreadable dense panels.

Run at minimum:

- frontend static/report tests
- frontend build
- browser verification for:
  - `/app`
  - `/app/admissions-opportunity-demo`
  - `/app/external-plan-audit-demo`
  - `/app/report-template-preview`

## Success Criteria

- A first-time visitor can understand PathFinder's difference within 10 seconds.
- The public demos show evidence and trend analysis before generic AI prose.
- The generated report feels like a serious paid deliverable, not a debug page.
- The design reinforces the product thesis: comprehensive, accurate, trend-aware, and evidence-bound.
- The project remains deployable through the existing GitHub Pages workflow and backend API configuration.

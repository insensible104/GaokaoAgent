# Delivery Readiness Console Design

## Problem Anchor

PathFinder needs to feel like a flagship decision product, not another broad Gaokao chatbot. The next visible step is to answer whether the current recommendation is ready for client handoff, what blocks it, and what evidence must be reviewed before a family treats it as a deliverable.

## Scope

This iteration adds a student/advisor-facing delivery readiness console to the result page and mirrors its summary into the printable A4 report preview. It does not add external plan ingestion, batch agency operations, or new backend endpoints.

## Product Behavior

The result page will show `交付准备度` before the recommendation matrix. It will summarize five gates:

- `data_boundary`: current-year data readiness and 2026 disclosure.
- `plan_structure`: key-prefix, coverage, blacklist, and shadowing diagnostics.
- `evidence_pack`: whether plan audit and quantitative evidence exist.
- `report_package`: whether the report and printable package are available.
- `human_review`: official plan/rule/manual review before final filing.

Statuses are deliberately conservative:

- `ready`: no blocker is visible for this gate.
- `needs_review`: usable for discussion, but a human review action remains.
- `blocked`: do not treat as deliverable until repaired or refreshed.

The overall status is `blocked` if any gate blocks, `needs_review` if any gate needs review, otherwise `ready`.

## Architecture

Create a pure frontend helper in `frontend/src/lib/deliveryReadiness.ts`. The helper consumes the existing `game_matrix`, `deliveryProfile`, and report text and returns a structured summary. `DeliveryReadinessConsole.tsx` renders that summary and owns only presentation. `PathFinderReportTemplate.tsx` imports the same helper and prints a compact readiness section, using `payload.deliveryReadiness` when App has already computed it.

## Claim Boundary

Delivery readiness is an operational QA signal. It is not evidence of admission quality, acceptance probability, paid-delivery success rate, or 2026 outcome validity. The UI and report must state that final filing still requires official current-year documents and human review.

## Test Strategy

Use static frontend smoke tests to guard product contract strings, shared helper wiring, report propagation, and mojibake regression. Then verify with TypeScript build, lint, and browser render checks.

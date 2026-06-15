# Plan Change Opportunity Ledger

Date: 2026-06-15

## Claim

PathFinder should not charge for generic AI answers. It can charge when an official enrollment-plan change becomes an auditable opportunity with a clear action and risk boundary.

## Protocol

Each opportunity must preserve this chain:

`official_source -> diff_type -> affected_rows -> rank_delta_estimate -> competitor_missed -> recommendation_action -> risk_guard`

## Implementation

- Added `frontend/src/lib/planChangeOpportunityLedger.ts`.
- Added `frontend/src/components/PlanChangeOpportunityLedgerPanel.tsx`.
- Integrated the panel into `GameMatrixView` before the paid-value score.
- Added behavior tests for weak and strong evidence cases.

## Current Boundary

This is a protocol and UI layer. It does not yet discover true 2026 opportunities from a full official plan file because that source has not been provided in this workspace.

## Next Iteration

When the official 2026 plan arrives, build an ingestion path that creates row-level diffs:

- 2025 to 2026 quota expansion or reduction.
- new or discontinued major.
- professional group split or merge.
- subject requirement change.
- major-bundle structure change.
- competitor or teacher plan omission.

Then populate `rank_delta_estimate`, `external_plan_coverage`, `recommendation_action`, and `risk_guard` for each diff before counselor review.

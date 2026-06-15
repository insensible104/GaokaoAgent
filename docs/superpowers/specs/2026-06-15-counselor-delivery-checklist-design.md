# Counselor Delivery Checklist Design

Date: 2026-06-15

## Goal

Move PathFinder closer to a flagship startup product by turning scattered recommendation evidence into a counselor-facing delivery checklist.

The product claim is narrow: a counselor should be able to decide in about one minute whether a plan can be delivered, what blocks delivery, and what action comes next.

## Product Position

General assistants can generate plausible volunteer-plan text. PathFinder should own the delivery workflow:

- Gather existing plan evidence.
- Surface blocking risks before a family sees the plan.
- Assign review actions to counselor, family, or data update.
- Keep official-data limitations visible.
- Treat Qianwen or teacher plans as audit inputs, not as threats.

## Evidence Boundary

This iteration does not refresh official data and does not create new admission conclusions. The checklist only organizes existing signals:

- `data_vintage`
- `plan_audit_summary`
- `volunteer_plan`
- major-group evidence
- explicit profile facts
- report readiness
- external comparison readiness

The feature must state that it does not replace manual review.

## Interface

Add `buildCounselorDeliveryChecklist` as a pure frontend helper. It returns:

- protocol version
- overall status
- ready/review/blocked counts
- lead action
- checklist items
- claim boundary

Add `CounselorDeliveryChecklist` to `GameMatrixView` after the internal plan audit workbench and before external plan comparison.

## Checklist Items

- Data boundary
- Profile completeness
- Plan structure
- Evidence integrity
- External comparison
- Report package

Each item includes status, owner, evidence, and action.

## Non-Goals

- No official-data ingestion.
- No report-template layout work.
- No persistent workflow state.
- No automatic external-plan merge.
- No admissions guarantee or correctness claim.

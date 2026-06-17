# Paid Value Score

Date: 2026-06-15

## Claim

PathFinder cannot charge for being another fluent AI answer. A family should only pay when the case contains evidence that generic free tools are unlikely to deliver: plan-change opportunity, risk avoidance, external-plan audit, executable volunteer draft, and counselor signoff boundary.

## Evidence Added

- `frontend/src/lib/paidValueScore.ts` defines `paid_value_score_v1`.
- The score uses five paid-value dimensions:
  - official plan-change opportunity: 25
  - adjustment and withdrawal risk avoidance: 25
  - external Qianwen/teacher/family plan audit: 15
  - executable volunteer draft: 20
  - counselor signoff boundary: 15
- `frontend/src/components/PaidValuePanel.tsx` renders the paid-value score in the result workflow.
- `frontend/src/components/PaidValueScore.behavior.test.mjs` proves generic AI-like recommendations stay low-value and cannot claim paid plan-change opportunity or final delivery.
- `frontend/src/components/PaidValuePanel.behavior.test.mjs` proves the panel exposes all five paid-value dimensions and blocked revenue claims.

## Product Boundary

The score does not create admission certainty. It only decides whether the current case has enough evidence to justify a paid counselor delivery. Without official 2026 plan-change evidence, the plan-change paid claim stays blocked.

## Next Iteration

After official 2026 plan data arrives, replace the placeholder plan-change dimension with a real `planChangeOpportunityLedger`: quota delta, group split/merge, selection requirement change, comparable-history reliability, opportunity score, and trap risk.

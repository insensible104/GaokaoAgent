# Delivery Case Status Panel And History

Date: 2026-06-15

## Claim

The delivery desk should expose case status as an operator workflow, not a hidden helper. Counselors need a visible status panel plus a version/event contract before this can become a flagship delivery product.

## Evidence Added

- `frontend/src/components/DeliveryCaseStatusPanel.tsx` renders `delivery_case_status_v1` in the active recommendation workflow.
- `frontend/src/lib/deliveryCaseHistory.ts` defines `delivery_case_history_v1` with event IDs, actor, version stamp, workflow stage, lock readiness, and missing-before-lock reasons.
- `frontend/src/components/GameMatrixView.tsx` now passes `externalPlanAuditSummary` from the external plan comparator into the visible case status panel.
- `frontend/src/components/DeliveryCaseStatusPanel.behavior.test.mjs` renders the panel and verifies forced `locked/confirmed` requests are downgraded when data boundary blocks formal delivery.
- `frontend/src/components/DeliveryCaseHistory.behavior.test.mjs` proves a ready case can move from counselor review into a lockable event history only after external audit, report readiness, family confirmation, and signoff are complete.

## Product Boundary

This is still frontend state and contract-level history. It does not claim backend persistence, auth, or immutable audit logs yet. It does make those backend tables and API events straightforward to implement next.

## Next Iteration

Add real interaction coverage for paste external plan -> audit state -> case status panel -> review record/report package sync. After that, add backend persistence or a local case-store adapter.

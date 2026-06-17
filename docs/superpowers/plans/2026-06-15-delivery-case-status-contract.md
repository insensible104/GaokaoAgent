# Delivery Case Status Contract

Date: 2026-06-15

## Claim

PathFinder should behave like a counselor delivery desk, not only a recommendation renderer. A case must expose one persistable status snapshot that operators can review, sign off, and hand to a family without losing the evidence boundary.

## Evidence Added

- `frontend/src/lib/deliveryCaseStatus.ts` defines `delivery_case_status_v1`.
- The status snapshot combines checklist status, blocked/review/ready items, external-plan audit metrics, review-record payload, reviewer identity, signoff state, parent confirmation state, next action, and a claim boundary.
- Blocked cases cannot be forced into `locked` or `confirmed`; the contract downgrades them to `not_started` and `requested`.
- `frontend/src/components/DeliveryCaseStatus.behavior.test.mjs` proves the external audit summary, blocked data boundary, review items, signoff downgrade, parent confirmation downgrade, and review record linkage.

## Product Boundary

This is still a frontend contract, not backend persistence. It makes the persistence shape explicit so the next iteration can add case history, reviewer actions, and React interaction coverage without inventing a new object model.

## Next Iteration

Add an operator-facing case status panel or interaction test that proves paste external plan -> audit state -> delivery case status -> review/report entry stay synchronized.

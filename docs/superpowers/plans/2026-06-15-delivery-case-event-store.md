# Delivery Case Event Store

Date: 2026-06-15

## Claim

PathFinder's delivery desk should not stop at a visible case snapshot. It needs a minimal event-store contract so counselor actions, signoff state, parent confirmation, and lock readiness can be serialized and replayed before backend persistence exists.

## Evidence Added

- `frontend/src/lib/deliveryCaseEventStore.ts` defines `delivery_case_event_store_v1`.
- The store records ordered events with `sequence`, `actor`, `createdAt`, `eventType`, payload counts, signoff state, parent confirmation state, review-record version, and deterministic checksum.
- The store rejects cross-case writes, serializes to JSON, parses back with protocol checks, and replays into `delivery_case_event_replay_v1`.
- `frontend/src/components/DeliveryCaseEventStore.behavior.test.mjs` proves blocked-to-locked progression, event ordering, checksum shape, replay, and case mismatch protection.
- `frontend/src/components/DeliveryCaseStatusPanel.tsx` now surfaces event replay metadata beside the visible case status and history contract.

## Product Boundary

This is a client-side event-store contract, not backend persistence or permissions. It is intentionally narrow: enough to make the next backend table/API shape obvious while avoiding a premature storage layer.

## Next Iteration

Add either a local storage adapter for operator sessions or a backend case-event API with reviewer identity, immutable append semantics, and permission checks.

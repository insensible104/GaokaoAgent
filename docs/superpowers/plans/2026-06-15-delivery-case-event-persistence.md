# Delivery Case Event Persistence Adapter

Date: 2026-06-15

## Claim

The event store becomes operationally useful only when it has a persistence boundary. PathFinder should expose a narrow adapter interface now, so the same event contract can back memory, browser storage, or a future backend API without rewriting delivery logic.

## Evidence Added

- `frontend/src/lib/deliveryCaseEventPersistence.ts` defines `delivery_case_event_persistence_adapter_v1`.
- The adapter supports `load`, `save`, `appendStatusEvent`, `listCaseIds`, and `clear`.
- `createMemoryDeliveryCaseEventPersistence` supports deterministic tests and future non-browser runtimes.
- `createBrowserStorageDeliveryCaseEventPersistence` persists serialized `delivery_case_event_store_v1` payloads behind a namespace key.
- `frontend/src/components/DeliveryCaseEventPersistence.behavior.test.mjs` proves save/load, append, clear, list, protocol validation, storage namespace isolation, and case mismatch protection.

## Product Boundary

This is a persistence adapter contract, not a backend system. It deliberately avoids auth, immutable server logs, and reviewer permissions. Those should be added behind the same adapter shape.

## Next Iteration

Add a small operator action UI for counselor signoff, family confirmation, and lock attempt. The UI should write through the adapter and replay events back into the status panel.

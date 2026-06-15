import {
  createDeliveryCaseEventStore,
  parseDeliveryCaseEventStore,
  recordDeliveryCaseStatusEvent,
  serializeDeliveryCaseEventStore,
  type DeliveryCaseEventStoreSnapshot,
} from "./deliveryCaseEventStore";
import type { DeliveryCaseStatus } from "./deliveryCaseStatus";

export interface DeliveryCaseEventPersistenceAdapter {
  protocol: "delivery_case_event_persistence_adapter_v1";
  kind: "memory" | "browser_storage";
  load(caseId: string): Promise<DeliveryCaseEventStoreSnapshot | null>;
  save(store: DeliveryCaseEventStoreSnapshot): Promise<DeliveryCaseEventStoreSnapshot>;
  appendStatusEvent(input: {
    caseId: string;
    status: DeliveryCaseStatus;
    actor?: string;
    createdAt?: string | Date;
  }): Promise<DeliveryCaseEventStoreSnapshot>;
  listCaseIds(): Promise<string[]>;
  clear(caseId: string): Promise<void>;
}

export interface BrowserStorageLike {
  readonly length: number;
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
  key(index: number): string | null;
}

export function createMemoryDeliveryCaseEventPersistence(
  initialStores: DeliveryCaseEventStoreSnapshot[] = [],
): DeliveryCaseEventPersistenceAdapter {
  const stores = new Map<string, DeliveryCaseEventStoreSnapshot>();
  for (const store of initialStores) {
    stores.set(store.caseId, store);
  }

  return {
    protocol: "delivery_case_event_persistence_adapter_v1",
    kind: "memory",
    async load(caseId) {
      return stores.get(caseId) ?? null;
    },
    async save(store) {
      stores.set(store.caseId, store);
      return store;
    },
    async appendStatusEvent({ caseId, status, actor, createdAt }) {
      const store = stores.get(caseId) ?? createDeliveryCaseEventStore(caseId);
      const nextStore = recordDeliveryCaseStatusEvent({ store, status, actor, createdAt });
      stores.set(caseId, nextStore);
      return nextStore;
    },
    async listCaseIds() {
      return Array.from(stores.keys()).sort();
    },
    async clear(caseId) {
      stores.delete(caseId);
    },
  };
}

export function createBrowserStorageDeliveryCaseEventPersistence({
  storage,
  namespace = "pathfinder.delivery.case_events",
}: {
  storage: BrowserStorageLike;
  namespace?: string;
}): DeliveryCaseEventPersistenceAdapter {
  const keyFor = (caseId: string) => `${namespace}:${caseId}`;
  const caseIdFromKey = (key: string) => key.slice(namespace.length + 1);

  return {
    protocol: "delivery_case_event_persistence_adapter_v1",
    kind: "browser_storage",
    async load(caseId) {
      const raw = storage.getItem(keyFor(caseId));
      return raw ? parseDeliveryCaseEventStore(raw) : null;
    },
    async save(store) {
      storage.setItem(keyFor(store.caseId), serializeDeliveryCaseEventStore(store));
      return store;
    },
    async appendStatusEvent({ caseId, status, actor, createdAt }) {
      const existing = await this.load(caseId);
      const store = existing ?? createDeliveryCaseEventStore(caseId);
      const nextStore = recordDeliveryCaseStatusEvent({ store, status, actor, createdAt });
      await this.save(nextStore);
      return nextStore;
    },
    async listCaseIds() {
      const ids: string[] = [];
      for (let index = 0; index < storage.length; index += 1) {
        const key = storage.key(index);
        if (key?.startsWith(`${namespace}:`)) {
          ids.push(caseIdFromKey(key));
        }
      }
      return ids.sort();
    },
    async clear(caseId) {
      storage.removeItem(keyFor(caseId));
    },
  };
}

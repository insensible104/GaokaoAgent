import React, { useMemo } from "react";
import {
  createDeliveryCaseEventStore,
  recordDeliveryCaseStatusEvent,
  replayDeliveryCaseEventStore,
} from "../lib/deliveryCaseEventStore";
import { buildDeliveryCaseHistory } from "../lib/deliveryCaseHistory";
import {
  buildDeliveryCaseStatus,
  type DeliveryCaseStatus,
  type DeliverySignoffState,
  type ParentConfirmationState,
} from "../lib/deliveryCaseStatus";
import type { ExternalPlanAuditSummary } from "../lib/externalPlanAudit";
import type { GameMatrix, RecommendationProfileSummary } from "./GameMatrixView";

interface DeliveryCaseStatusPanelProps {
  gameMatrix: GameMatrix;
  userProfile?: RecommendationProfileSummary | null;
  externalPlanCompared?: boolean;
  externalPlanAuditSummary?: ExternalPlanAuditSummary | null;
  reportReady?: boolean;
  caseId?: string;
  reviewer?: string;
  signoffState?: DeliverySignoffState;
  parentConfirmationState?: ParentConfirmationState;
  generatedAt?: string | Date;
  updatedAt?: string | Date;
  previousStatuses?: DeliveryCaseStatus[];
}

const statusLabels: Record<DeliveryCaseStatus["status"], string> = {
  ready: "Ready",
  needs_review: "Needs review",
  blocked: "Blocked",
};

const stageLabels: Record<DeliveryCaseStatus["workflowStage"], string> = {
  intake: "Intake",
  counselor_review: "Counselor review",
  family_confirmation: "Family confirmation",
  ready_to_lock: "Ready to lock",
  locked: "Locked",
};

const statusStyles: Record<DeliveryCaseStatus["status"], string> = {
  ready: "border-emerald-200 bg-emerald-50 text-emerald-900",
  needs_review: "border-amber-200 bg-amber-50 text-amber-900",
  blocked: "border-red-200 bg-red-50 text-red-900",
};

export const DeliveryCaseStatusPanel: React.FC<DeliveryCaseStatusPanelProps> = ({
  gameMatrix,
  userProfile,
  externalPlanCompared = false,
  externalPlanAuditSummary = null,
  reportReady = false,
  caseId,
  reviewer = "Lead counselor",
  signoffState = "counselor_reviewed",
  parentConfirmationState = "not_requested",
  generatedAt,
  updatedAt,
  previousStatuses = [],
}) => {
  const status = useMemo(
    () =>
      buildDeliveryCaseStatus({
        caseId: caseId ?? buildCaseId(gameMatrix),
        gameMatrix,
        userProfile,
        reportReady,
        externalPlanCompared,
        externalPlanAuditSummary,
        generatedAt,
        updatedAt,
        operatorName: reviewer,
        reviewer,
        signoffState,
        parentConfirmationState,
      }),
    [
      caseId,
      externalPlanAuditSummary,
      externalPlanCompared,
      gameMatrix,
      generatedAt,
      parentConfirmationState,
      reportReady,
      reviewer,
      signoffState,
      updatedAt,
      userProfile,
    ],
  );
  const history = useMemo(
    () => buildDeliveryCaseHistory({ current: status, previous: previousStatuses, actor: reviewer }),
    [previousStatuses, reviewer, status],
  );
  const eventReplay = useMemo(() => {
    const initialStore = createDeliveryCaseEventStore(status.caseId);
    const store = recordDeliveryCaseStatusEvent({
      store: initialStore,
      status,
      actor: reviewer,
      createdAt: status.updatedAt,
    });
    return replayDeliveryCaseEventStore(store);
  }, [reviewer, status]);

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-md" data-protocol={status.protocol}>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900">Delivery case status</h3>
          <p className="mt-1 text-sm leading-6 text-gray-600">
            One operator-facing snapshot for review state, signoff, family confirmation, external audit, and version
            history.
          </p>
        </div>
        <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusStyles[status.status]}`}>
          {statusLabels[status.status]}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric label="Case" value={status.caseId} />
        <Metric label="Stage" value={stageLabels[status.workflowStage]} />
        <Metric label="Signoff" value={status.signoffState} />
        <Metric label="Family" value={status.parentConfirmationState} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="rounded-md bg-gray-50 p-4">
          <div className="text-sm font-semibold text-gray-900">Next action</div>
          <p className="mt-2 text-sm leading-6 text-gray-700">{status.nextAction}</p>
          <div className="mt-4 grid grid-cols-3 gap-2 text-center">
            <CountTile label="Blocked" value={status.blockedItems.length} tone="text-red-700" />
            <CountTile label="Review" value={status.reviewItems.length} tone="text-amber-700" />
            <CountTile label="Ready" value={status.readyItems.length} tone="text-emerald-700" />
          </div>
          <div className="mt-4 rounded border border-gray-200 bg-white px-3 py-2 text-xs leading-5 text-gray-600">
            Review record metrics: blocked {status.reviewRecord.metrics.blocked_items}, review{" "}
            {status.reviewRecord.metrics.review_items}, ready {status.reviewRecord.metrics.ready_items}
          </div>
        </div>

        <div className="space-y-3">
          <StatusList title="Blocked items" items={status.blockedItems.map((item) => item.label)} empty="None" />
          <StatusList title="Review items" items={status.reviewItems.map((item) => item.label)} empty="None" />
          <StatusList
            title="External audit"
            items={
              status.externalAuditSummary
                ? [
                    `parsed ${status.externalAuditSummary.parsedCount}`,
                    `unmatched ${status.externalAuditSummary.unmatchedCount}`,
                    `duplicates ${status.externalAuditSummary.duplicateCount}`,
                    `needs review ${String(status.externalAuditSummary.needsReview)}`,
                  ]
                : ["not compared"]
            }
            empty="not compared"
          />
        </div>
      </div>

      <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-slate-900">Case history</div>
            <p className="mt-1 text-xs leading-5 text-slate-600">
              {history.protocol} / version {history.currentVersion} / events {history.eventCount}
            </p>
          </div>
          <span
            className={`rounded-full border px-3 py-1 text-xs font-semibold ${
              history.lockReady
                ? "border-emerald-200 bg-emerald-50 text-emerald-900"
                : "border-amber-200 bg-amber-50 text-amber-900"
            }`}
          >
            {history.lockReady ? "Lock ready" : "Lock blocked"}
          </span>
        </div>
        {history.missingBeforeLock.length > 0 && (
          <ul className="mt-3 list-disc space-y-1 pl-4 text-xs leading-5 text-slate-700">
            {history.missingBeforeLock.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-4 rounded-md border border-cyan-100 bg-cyan-50 px-4 py-3 text-xs leading-5 text-cyan-950">
        Event store: {eventReplay.protocol} / events {eventReplay.eventCount} / stage {eventReplay.currentStage}
      </div>

      <p className="mt-4 text-xs leading-5 text-gray-500">Claim boundary: {status.claimBoundary}</p>
    </section>
  );
};

interface MetricProps {
  label: string;
  value: string;
}

const Metric: React.FC<MetricProps> = ({ label, value }) => (
  <div className="min-w-0 rounded-md bg-gray-50 px-3 py-3">
    <div className="text-xs font-semibold text-gray-500">{label}</div>
    <div className="mt-1 break-words text-sm font-bold text-gray-900">{value}</div>
  </div>
);

const CountTile: React.FC<{ label: string; value: number; tone: string }> = ({ label, value, tone }) => (
  <div className="rounded bg-white px-2 py-2">
    <div className="text-xs text-gray-500">{label}</div>
    <div className={`mt-1 text-xl font-bold ${tone}`}>{value}</div>
  </div>
);

const StatusList: React.FC<{ title: string; items: string[]; empty: string }> = ({ title, items, empty }) => (
  <div className="rounded-md border border-gray-200 px-3 py-3">
    <div className="text-sm font-semibold text-gray-900">{title}</div>
    <ul className="mt-2 space-y-1 text-xs leading-5 text-gray-600">
      {(items.length > 0 ? items : [empty]).map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  </div>
);

function buildCaseId(gameMatrix: GameMatrix): string {
  const rowCount = gameMatrix.major_group_rows?.length ?? gameMatrix.rows?.length ?? 0;
  const status = gameMatrix.plan_audit_summary?.status ?? "draft";
  return `pf-${status}-${rowCount}`;
}

import React, { useMemo } from "react";
import { buildPaidValueScore } from "../lib/paidValueScore";
import { createDeliveryCaseEventStore, recordDeliveryCaseStatusEvent, replayDeliveryCaseEventStore } from "../lib/deliveryCaseEventStore";
import { buildDeliveryCaseStatus } from "../lib/deliveryCaseStatus";
import type { ExternalPlanAuditSummary } from "../lib/externalPlanAudit";
import type { GameMatrix, RecommendationProfileSummary } from "./GameMatrixView";

interface PaidValuePanelProps {
  gameMatrix: GameMatrix;
  userProfile?: RecommendationProfileSummary | null;
  externalPlanAuditSummary?: ExternalPlanAuditSummary | null;
}

const bandStyles = {
  premium: "border-emerald-200 bg-emerald-50 text-emerald-950",
  credible_paid: "border-cyan-200 bg-cyan-50 text-cyan-950",
  advisory_only: "border-amber-200 bg-amber-50 text-amber-950",
  free_tier: "border-red-200 bg-red-50 text-red-950",
};

export const PaidValuePanel: React.FC<PaidValuePanelProps> = ({
  gameMatrix,
  userProfile,
  externalPlanAuditSummary,
}) => {
  const paidValue = useMemo(() => {
    const status = buildDeliveryCaseStatus({
      caseId: buildCaseId(gameMatrix),
      gameMatrix,
      userProfile,
      externalPlanCompared: Boolean(externalPlanAuditSummary),
      externalPlanAuditSummary,
      reportReady: false,
      reviewer: "Lead counselor",
    });
    const store = recordDeliveryCaseStatusEvent({
      store: createDeliveryCaseEventStore(status.caseId),
      status,
      actor: "Lead counselor",
      createdAt: status.updatedAt,
    });
    return buildPaidValueScore({
      gameMatrix,
      externalPlanAuditSummary,
      eventReplay: replayDeliveryCaseEventStore(store),
    });
  }, [externalPlanAuditSummary, gameMatrix, userProfile]);
  const dimensions = Object.values(paidValue.dimensions);

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-md" data-protocol={paidValue.protocol}>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900">Paid value score</h3>
          <p className="mt-1 text-sm leading-6 text-gray-600">
            Measures whether this case has evidence a family could reasonably pay for, not just a fluent AI answer.
          </p>
        </div>
        <div className={`rounded-md border px-4 py-2 text-right ${bandStyles[paidValue.band]}`}>
          <div className="text-xs font-semibold uppercase">{paidValue.band}</div>
          <div className="text-2xl font-bold">{paidValue.score}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
        {dimensions.map((dimension) => (
          <div key={dimension.key} className="rounded-md border border-gray-200 px-3 py-3">
            <div className="text-sm font-semibold text-gray-900">{dimension.label}</div>
            <div className="mt-1 text-lg font-bold text-gray-900">
              {dimension.score}/{dimension.maxScore}
            </div>
            <div className="text-xs font-semibold text-gray-500">{dimension.status}</div>
            <p className="mt-2 text-xs leading-5 text-gray-600">{dimension.evidence}</p>
          </div>
        ))}
      </div>

      {paidValue.payReasons.length > 0 && (
        <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3">
          <div className="text-sm font-semibold text-emerald-950">Reasons a family might pay</div>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5 text-emerald-900">
            {paidValue.payReasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </div>
      )}

      {paidValue.blockedRevenueClaims.length > 0 && (
        <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-3">
          <div className="text-sm font-semibold text-amber-950">Revenue claims blocked</div>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5 text-amber-900">
            {paidValue.blockedRevenueClaims.map((claim) => (
              <li key={claim}>{claim}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
};

function buildCaseId(gameMatrix: GameMatrix): string {
  const rowCount = gameMatrix.major_group_rows?.length ?? gameMatrix.rows?.length ?? 0;
  const status = gameMatrix.plan_audit_summary?.status ?? "draft";
  return `pf-paid-${status}-${rowCount}`;
}

import React, { useMemo } from "react";
import { buildCompetitiveDifferentiationScore } from "../lib/competitiveDifferentiationScore";
import { createDeliveryCaseEventStore, recordDeliveryCaseStatusEvent, replayDeliveryCaseEventStore } from "../lib/deliveryCaseEventStore";
import { buildDeliveryCaseStatus } from "../lib/deliveryCaseStatus";
import type { ExternalPlanAuditSummary } from "../lib/externalPlanAudit";
import type { GameMatrix, RecommendationProfileSummary } from "./GameMatrixView";

interface CompetitiveDifferentiationPanelProps {
  gameMatrix: GameMatrix;
  userProfile?: RecommendationProfileSummary | null;
  externalPlanAuditSummary?: ExternalPlanAuditSummary | null;
}

const bandStyles = {
  flagship: "border-emerald-200 bg-emerald-50 text-emerald-950",
  credible: "border-sky-200 bg-sky-50 text-sky-950",
  thin: "border-amber-200 bg-amber-50 text-amber-950",
  blocked: "border-red-200 bg-red-50 text-red-950",
};

export const CompetitiveDifferentiationPanel: React.FC<CompetitiveDifferentiationPanelProps> = ({
  gameMatrix,
  userProfile,
  externalPlanAuditSummary,
}) => {
  const benchmark = useMemo(() => {
    const status = buildDeliveryCaseStatus({
      caseId: buildCaseId(gameMatrix),
      gameMatrix,
      userProfile,
      externalPlanCompared: Boolean(externalPlanAuditSummary),
      externalPlanAuditSummary,
      reportReady: false,
      reviewer: "Lead counselor",
    });
    const eventStore = recordDeliveryCaseStatusEvent({
      store: createDeliveryCaseEventStore(status.caseId),
      status,
      actor: "Lead counselor",
      createdAt: status.updatedAt,
    });
    return buildCompetitiveDifferentiationScore({
      gameMatrix,
      userProfile,
      externalPlanAuditSummary,
      eventReplay: replayDeliveryCaseEventStore(eventStore),
    });
  }, [externalPlanAuditSummary, gameMatrix, userProfile]);

  const dimensions = Object.values(benchmark.dimensions);

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-md" data-protocol={benchmark.protocol}>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900">Competitive benchmark</h3>
          <p className="mt-1 text-sm leading-6 text-gray-600">
            Quantifies where PathFinder can beat generic AI/report workflows, and where it still cannot claim advantage.
          </p>
        </div>
        <div className={`rounded-md border px-4 py-2 text-right ${bandStyles[benchmark.band]}`}>
          <div className="text-xs font-semibold uppercase">{benchmark.band}</div>
          <div className="text-2xl font-bold">{benchmark.score}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {dimensions.map((dimension) => (
          <div key={dimension.key} className="rounded-md border border-gray-200 px-3 py-3">
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-semibold text-gray-900">{dimension.label}</div>
              <div className="text-sm font-bold text-gray-900">
                {dimension.score}/{dimension.maxScore}
              </div>
            </div>
            <div className="mt-1 text-xs font-semibold text-gray-500">{dimension.status}</div>
            <p className="mt-2 text-xs leading-5 text-gray-600">{dimension.evidence}</p>
          </div>
        ))}
      </div>

      {benchmark.blockedClaims.length > 0 && (
        <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-3">
          <div className="text-sm font-semibold text-amber-950">Claims not allowed yet</div>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5 text-amber-900">
            {benchmark.blockedClaims.map((claim) => (
              <li key={claim}>{claim}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
        <Positioning title="Qianwen gap" value={benchmark.benchmarkPositioning.qianwenGap} />
        <Positioning title="Tencent gap" value={benchmark.benchmarkPositioning.tencentGap} />
      </div>
    </section>
  );
};

const Positioning: React.FC<{ title: string; value: string }> = ({ title, value }) => (
  <div className="rounded-md bg-slate-50 px-4 py-3">
    <div className="text-xs font-semibold text-slate-500">{title}</div>
    <p className="mt-1 text-xs leading-5 text-slate-700">{value}</p>
  </div>
);

function buildCaseId(gameMatrix: GameMatrix): string {
  const rowCount = gameMatrix.major_group_rows?.length ?? gameMatrix.rows?.length ?? 0;
  const status = gameMatrix.plan_audit_summary?.status ?? "draft";
  return `pf-benchmark-${status}-${rowCount}`;
}

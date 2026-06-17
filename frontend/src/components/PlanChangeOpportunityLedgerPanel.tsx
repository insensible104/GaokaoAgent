import React, { useMemo } from "react";
import { buildPlanChangeOpportunityLedger } from "../lib/planChangeOpportunityLedger";
import type { ExternalPlanAuditSummary } from "../lib/externalPlanAudit";
import type { HiddenOpportunityAudit } from "../lib/hiddenOpportunityAudit";
import type { GameMatrix } from "./GameMatrixView";

interface PlanChangeOpportunityLedgerPanelProps {
  gameMatrix: GameMatrix;
  externalPlanAuditSummary?: ExternalPlanAuditSummary | null;
  hiddenOpportunityAudit?: HiddenOpportunityAudit | null;
}

const statusStyles = {
  ready: "border-emerald-200 bg-emerald-50 text-emerald-950",
  partial: "border-amber-200 bg-amber-50 text-amber-950",
  blocked: "border-red-200 bg-red-50 text-red-950",
};

export const PlanChangeOpportunityLedgerPanel: React.FC<PlanChangeOpportunityLedgerPanelProps> = ({
  gameMatrix,
  externalPlanAuditSummary,
  hiddenOpportunityAudit,
}) => {
  const ledger = useMemo(
    () => buildPlanChangeOpportunityLedger({ gameMatrix, externalPlanAuditSummary, hiddenOpportunityAudit }),
    [externalPlanAuditSummary, gameMatrix, hiddenOpportunityAudit],
  );

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-md" data-protocol={ledger.protocol}>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900">Plan change opportunity ledger</h3>
          <p className="mt-1 text-sm leading-6 text-gray-600">
            Turns each official enrollment-plan diff into an auditable opportunity object before it can become paid advice.
          </p>
        </div>
        <div className={`rounded-md border px-4 py-2 text-right ${statusStyles[ledger.status]}`}>
          <div className="text-xs font-semibold uppercase">{ledger.status}</div>
          <div className="text-2xl font-bold">{ledger.score}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 text-sm md:grid-cols-7">
        {[
          "official source",
          "diff type",
          "affected rows",
          "rank delta",
          "competitor missed",
          "recommendation action",
          "risk guard",
        ].map((label) => (
          <div key={label} className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 font-semibold text-gray-700">
            {label}
          </div>
        ))}
      </div>

      <div className="mt-3 space-y-3">
        {ledger.opportunities.length === 0 ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
            {ledger.summary}
          </div>
        ) : (
          ledger.opportunities.map((opportunity) => (
            <article key={opportunity.id} className="rounded-md border border-gray-200 px-4 py-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-gray-900">
                    {opportunity.affectedRows[0]?.schoolName ?? "Unknown school"} /
                    {opportunity.affectedRows[0]?.majorGroupCode ?? "unknown group"}
                  </div>
                  <div className="mt-1 text-xs text-gray-500">audit score {opportunity.auditScore}</div>
                </div>
                <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${statusStyles[opportunity.status]}`}>
                  {opportunity.status}
                </span>
              </div>

              <dl className="mt-4 grid grid-cols-1 gap-3 text-xs leading-5 md:grid-cols-2 lg:grid-cols-3">
                <LedgerField label="official source" value={opportunity.officialSource} />
                <LedgerField label="diff type" value={opportunity.diffType} />
                <LedgerField
                  label="affected rows"
                  value={opportunity.affectedRows
                    .map((row) => `#${row.choiceIndex ?? "-"} ${row.schoolName ?? "-"} ${row.majorGroupCode ?? "-"}`)
                    .join("; ")}
                />
                <LedgerField
                  label="rank delta"
                  value={`${opportunity.rankDeltaEstimate.direction} ${
                    opportunity.rankDeltaEstimate.rankDelta ?? "unknown"
                  }`}
                />
                <LedgerField
                  label="competitor missed"
                  value={`${opportunity.competitorMissed.status}: ${opportunity.competitorMissed.evidence}`}
                />
                <LedgerField label="recommendation action" value={opportunity.recommendationAction} />
                <LedgerField
                  label="risk guard"
                  value={`${opportunity.riskGuard.level}: ${opportunity.riskGuard.checks.join("; ")}`}
                />
                {opportunity.hiddenOpportunityAudit ? (
                  <LedgerField
                    label="hidden opportunity audit"
                    value={`${opportunity.hiddenOpportunityAudit.status}; ${opportunity.hiddenOpportunityAudit.labelPermission}; must stay hypothesis-only: ${
                      opportunity.hiddenOpportunityAudit.mustStayHypothesisOnly ? "yes" : "no"
                    }`}
                  />
                ) : null}
              </dl>
            </article>
          ))
        )}
      </div>

      {ledger.hiddenOpportunityGate.status !== "not_supplied" && (
        <div className="mt-4 rounded-md border border-orange-200 bg-orange-50 px-4 py-3 text-sm text-orange-950">
          <div className="font-semibold">Hidden opportunity gate</div>
          <div className="mt-2 grid grid-cols-1 gap-2 text-xs leading-5 md:grid-cols-2">
            <LedgerField label="protocol" value={hiddenOpportunityAudit?.protocol ?? "hidden_opportunity_audit_v1"} />
            <LedgerField label="status" value={ledger.hiddenOpportunityGate.status} />
            <LedgerField label="label permission" value={ledger.hiddenOpportunityGate.labelPermission} />
            <LedgerField
              label="can enter ledger"
              value={`can enter ledger: ${ledger.hiddenOpportunityGate.canEnterLedger ? "yes" : "no"}`}
            />
            <LedgerField
              label="hypothesis boundary"
              value={`must stay hypothesis-only: ${
                hiddenOpportunityAudit?.reviewGate.mustStayHypothesisOnly ? "yes" : "no"
              }`}
            />
            <LedgerField label="score" value={ledger.hiddenOpportunityGate.score ?? "not supplied"} />
          </div>
          {ledger.hiddenOpportunityGate.reasons.length > 0 && (
            <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5">
              {ledger.hiddenOpportunityGate.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {ledger.blockedClaims.length > 0 && (
        <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-4 py-3">
          <div className="text-sm font-semibold text-red-950">Claims blocked</div>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5 text-red-900">
            {ledger.blockedClaims.map((claim) => (
              <li key={claim}>{claim}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
};

function LedgerField({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="min-w-0 rounded-md bg-gray-50 px-3 py-2">
      <dt className="font-semibold text-gray-500">{label}</dt>
      <dd className="mt-1 break-words text-gray-900">{value}</dd>
    </div>
  );
}

import {
  buildReviewedEvidenceCaseBrowser,
} from "../lib/reviewedEvidenceCaseBrowser";
import type { DeepEvidenceCollectionPlan } from "../lib/deepEvidenceCollectionPlan";
import type { ReviewedEvidenceRecord } from "../lib/evidenceAutopilotApi";
import {
  buildReviewedEvidenceCaseBrowserPanelSummary,
  type ReviewerPanelTone,
} from "../lib/reviewedEvidenceCaseBrowserPanelSummary";

export interface ReviewedEvidenceCaseBrowserPanelProps {
  caseId: string;
  records: ReviewedEvidenceRecord[];
  plan?: DeepEvidenceCollectionPlan;
}

export function ReviewedEvidenceCaseBrowserPanel({
  caseId,
  records,
  plan,
}: ReviewedEvidenceCaseBrowserPanelProps) {
  const view = buildReviewedEvidenceCaseBrowser({ caseId, records, plan });
  const summary = buildReviewedEvidenceCaseBrowserPanelSummary(view);
  const visibleGroups = view.taskGroups
    .filter((group) => group.status !== "missing" || group.priority === "P0")
    .slice(0, 6);

  return (
    <section
      aria-label="case-scoped reviewed evidence"
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      data-tone={summary.tone}
    >
      <div className="flex flex-col gap-2 border-b border-slate-100 pb-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Reviewed evidence case browser
          </p>
          <h3 className="mt-1 text-base font-semibold text-slate-950">Case {summary.caseId}</h3>
          <p className="mt-1 max-w-3xl text-sm text-slate-600">{summary.primaryAction}</p>
        </div>
        <span className={statusBadgeClass(summary.tone)}>
          {summary.tone === "ready" ? "ready_for_report" : summary.tone}
        </span>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric label="captured" value={summary.metrics.captured} />
        <Metric label="ready_for_report" value={summary.metrics.readyForReport} />
        <Metric label="needs_capture" value={summary.metrics.pending} />
        <Metric label="missing P0" value={summary.metrics.missingP0} />
      </dl>

      {view.missingP0TaskIds.length > 0 ? (
        <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          <p className="font-medium">missingP0TaskIds</p>
          <p className="mt-1 break-words">{view.missingP0TaskIds.join(", ")}</p>
        </div>
      ) : null}

      {view.counterEvidenceHit ? (
        <div className="mt-3 rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900">
          counterEvidenceHit: review counter-evidence before counselor signoff.
        </div>
      ) : null}

      <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-100">
        {visibleGroups.map((group) => (
          <div key={group.taskId} className="flex items-start justify-between gap-3 p-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-950">{group.title}</p>
              <p className="mt-1 text-xs text-slate-500">
                {group.taskId} - {group.priority} - {group.records.length} record(s)
              </p>
            </div>
            <span className="shrink-0 rounded border border-slate-200 px-2 py-1 text-xs text-slate-600">
              {group.status}
            </span>
          </div>
        ))}
      </div>

      <p className="mt-3 text-xs text-slate-500">{summary.claimBoundary}</p>
    </section>
  );
}

function statusBadgeClass(tone: ReviewerPanelTone): string {
  const base = "inline-flex rounded border px-2 py-1 text-xs font-medium";
  if (tone === "blocked") return `${base} border-rose-200 bg-rose-50 text-rose-800`;
  if (tone === "needs_review") return `${base} border-amber-200 bg-amber-50 text-amber-800`;
  return `${base} border-emerald-200 bg-emerald-50 text-emerald-800`;
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-slate-100 bg-slate-50 p-3">
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="mt-1 text-lg font-semibold text-slate-950">{value}</dd>
    </div>
  );
}

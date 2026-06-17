import React from "react";
import type { EvidenceCollectionWorkspace, EvidenceCollectionTaskRow } from "../lib/evidenceCollectionWorkspace";
import { buildWebEvidenceCaptureWorksheet, type WebEvidenceCaptureRow } from "../lib/webEvidenceCaptureWorksheet";
import {
  buildWebEvidenceSearchRequests,
  type WebEvidenceSearchAdapterRequest,
} from "../lib/webEvidenceSearchAdapter";
import type { EvidenceTriangulationClaim } from "../lib/evidenceTriangulationReport";

interface EvidenceCollectionWorkspacePanelProps {
  workspace: EvidenceCollectionWorkspace;
}

const workspaceStatusStyles: Record<EvidenceCollectionWorkspace["status"], string> = {
  ready_for_counselor_review: "border-emerald-200 bg-emerald-50 text-emerald-950",
  collecting_evidence: "border-amber-200 bg-amber-50 text-amber-950",
  upstream_blocked: "border-red-200 bg-red-50 text-red-950",
};

const taskStatusStyles: Record<EvidenceCollectionTaskRow["status"], string> = {
  accepted: "border-emerald-200 bg-emerald-50 text-emerald-950",
  needs_capture: "border-amber-200 bg-amber-50 text-amber-950",
  rejected_only: "border-red-200 bg-red-50 text-red-950",
};

export function EvidenceCollectionWorkspacePanel({ workspace }: EvidenceCollectionWorkspacePanelProps) {
  const coverage = workspace.coverageSummary;
  const searchRequestBatch = buildWebEvidenceSearchRequests({ workspace });
  const captureWorksheet = buildWebEvidenceCaptureWorksheet({ workspace });

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-md" data-protocol={workspace.protocol}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-xl font-bold text-gray-900">Evidence collection workspace</h3>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-gray-600">
            Operator queue for official diffs, rank calibration, public-opinion hypotheses, external-plan comparison,
            and family concept evidence before counselor review.
          </p>
        </div>
        <div className={`rounded-md border px-4 py-2 text-right ${workspaceStatusStyles[workspace.status]}`}>
          <div className="text-xs font-semibold uppercase">{workspace.status}</div>
          <div className="text-2xl font-bold">
            {coverage.completedBlockingTasks} / {coverage.blockingTasks}
          </div>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-3 text-sm md:grid-cols-4">
        <Metric label="tasks" value={coverage.totalTasks} />
        <Metric label="accepted evidence" value={coverage.acceptedEvidenceCount} />
        <Metric label="rejected evidence" value={coverage.rejectedEvidenceCount} />
        <Metric label="family concepts" value={workspace.familyConceptReadiness.status} />
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-3">
          {workspace.taskRows.map((task) => (
            <TaskRow key={task.taskId} task={task} />
          ))}
        </div>

        <aside className="space-y-4">
          <PanelBlock title="Missing claims">
            {coverage.missingClaims.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {coverage.missingClaims.map((claim) => (
                  <span key={claim} className="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-950">
                    {claim}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-600">No missing claim support before counselor review.</p>
            )}
          </PanelBlock>

          <PanelBlock title="Next search actions">
            <ol className="space-y-2 text-sm leading-6 text-gray-700">
              {workspace.nextSearchActions.map((action) => (
                <li key={action} className="rounded-md bg-gray-50 px-3 py-2">
                  {action}
                </li>
              ))}
            </ol>
          </PanelBlock>

          <PanelBlock title="Search request batch">
            <div className="mb-3 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-xs leading-5 text-gray-600">
              <div className="font-semibold text-gray-900">{searchRequestBatch.protocol}</div>
              <div>{searchRequestBatch.claimBoundary}</div>
            </div>
            <div className="space-y-3">
              {searchRequestBatch.requests.length > 0 ? (
                searchRequestBatch.requests.map((request) => (
                  <SearchRequestTemplate key={request.requestId} request={request} />
                ))
              ) : (
                <p className="text-sm text-gray-600">No pending search requests.</p>
              )}
            </div>
          </PanelBlock>

          <PanelBlock title="Evidence triangulation">
            <div className="mb-3 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-xs leading-5 text-gray-600">
              <div className="font-semibold text-gray-900">{workspace.triangulationReport.protocol}</div>
              <div className="mt-1 font-semibold text-gray-900">{workspace.triangulationReport.status}</div>
              <div className="mt-1">{workspace.triangulationReport.claimBoundary}</div>
            </div>
            <div className="mb-3 grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
              <SmallStat label="accepted" value={workspace.triangulationReport.summary.totalAcceptedEvidence} />
              <SmallStat label="needs evidence" value={workspace.triangulationReport.summary.claimsNeedingMoreEvidence} />
              <SmallStat label="conflicts" value={workspace.triangulationReport.summary.conflictedClaims} />
              <SmallStat label="triangulated" value={workspace.triangulationReport.summary.triangulatedClaims} />
            </div>
            <div className="space-y-3">
              {workspace.triangulationReport.claims.map((claim) => (
                <TriangulationClaimRow key={claim.claim} claim={claim} />
              ))}
            </div>
          </PanelBlock>

          <PanelBlock title="Evidence gap follow-up">
            <div className="mb-3 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-xs leading-5 text-gray-600">
              <div className="font-semibold text-gray-900">{workspace.evidenceGapSearchPlan.protocol}</div>
              <div className="mt-1 font-semibold text-gray-900">{workspace.evidenceGapSearchPlan.status}</div>
              <div className="mt-1">{workspace.evidenceGapSearchPlan.claimBoundary}</div>
            </div>
            <div className="space-y-3">
              {workspace.evidenceGapSearchPlan.followUps.length > 0 ? (
                workspace.evidenceGapSearchPlan.followUps.map((followUp) => (
                  <article key={followUp.id} className="rounded-md border border-cyan-200 bg-cyan-50 px-3 py-3 text-xs leading-5 text-cyan-950">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <div className="font-bold">{followUp.claim}</div>
                        <div className="mt-1">{followUp.reason}</div>
                      </div>
                      <span className="rounded-md border border-cyan-200 bg-white px-2 py-1 font-semibold">
                        {followUp.gapStatus}
                      </span>
                    </div>
                    <dl className="mt-3 grid grid-cols-1 gap-2">
                      <Field label="query" value={followUp.query} />
                      <Field label="domains" value={followUp.domains.join(", ")} />
                      <Field label="source tier" value={followUp.sourceTier} />
                      <Field label="existing hosts" value={followUp.existingSourceHosts.join(", ") || "none"} />
                    </dl>
                  </article>
                ))
              ) : (
                <p className="text-sm text-gray-600">No triangulation gaps need follow-up search.</p>
              )}
            </div>
          </PanelBlock>

          <PanelBlock title="Capture worksheet">
            <div className="mb-3 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-xs leading-5 text-gray-600">
              <div className="font-semibold text-gray-900">{captureWorksheet.protocol}</div>
              <div>{captureWorksheet.status}</div>
            </div>
            <div className="space-y-3">
              {captureWorksheet.pendingRows.length > 0 ? (
                captureWorksheet.pendingRows.map((row) => <CaptureTemplate key={row.taskId} row={row} />)
              ) : (
                <p className="text-sm text-gray-600">All capture templates are complete.</p>
              )}
            </div>
          </PanelBlock>

          <PanelBlock title="Family concept readiness">
            <div className={`rounded-md border px-3 py-2 text-sm ${workspace.familyConceptReadiness.status === "explained" ? taskStatusStyles.accepted : taskStatusStyles.needs_capture}`}>
              <div className="font-semibold">{workspace.familyConceptReadiness.status}</div>
              <p className="mt-1 leading-6">{workspace.familyConceptReadiness.nextAction}</p>
            </div>
          </PanelBlock>

          {workspace.completion.blockedReasons.length > 0 && (
            <PanelBlock title="Blocked reasons">
              <ul className="space-y-2 text-xs leading-5 text-red-900">
                {workspace.completion.blockedReasons.map((reason) => (
                  <li key={reason} className="rounded-md border border-red-100 bg-red-50 px-3 py-2">
                    {reason}
                  </li>
                ))}
              </ul>
            </PanelBlock>
          )}
        </aside>
      </div>

      <div className="mt-5 rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-xs leading-5 text-gray-600">
        {workspace.claimBoundary}
      </div>
    </section>
  );
}

function SmallStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="min-w-0">
      <div className="font-semibold uppercase text-gray-500">{label}</div>
      <div className="mt-0.5 break-words font-bold text-gray-900">{value}</div>
    </div>
  );
}

function TriangulationClaimRow({ claim }: { claim: EvidenceTriangulationClaim }) {
  return (
    <article className="rounded-md border border-gray-200 bg-gray-50 px-3 py-3 text-xs leading-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="font-bold text-gray-900">{claim.claim}</div>
          <div className="mt-1 text-gray-600">{claim.acceptedEvidenceCount} evidence, {claim.distinctSourceHosts} hosts</div>
        </div>
        <span className="rounded-md border border-gray-200 bg-white px-2 py-1 font-semibold text-gray-700">
          {claim.status}
        </span>
      </div>
      {claim.sourceHosts.length > 0 && (
        <div className="mt-2 break-words text-gray-700">{claim.sourceHosts.join(", ")}</div>
      )}
      {claim.issues.length > 0 && (
        <ul className="mt-2 list-disc space-y-1 pl-4 text-red-900">
          {claim.issues.map((issue) => (
            <li key={issue}>{issue}</li>
          ))}
        </ul>
      )}
      {claim.nextActions.length > 0 && (
        <ul className="mt-2 list-disc space-y-1 pl-4 text-gray-700">
          {claim.nextActions.map((action) => (
            <li key={action}>{action}</li>
          ))}
        </ul>
      )}
    </article>
  );
}

function SearchRequestTemplate({ request }: { request: WebEvidenceSearchAdapterRequest }) {
  return (
    <article className="rounded-md border border-gray-200 bg-gray-50 px-3 py-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="text-xs font-bold text-gray-900">{request.taskType}</div>
          <div className="mt-1 text-xs text-gray-500">{request.requestId}</div>
        </div>
        <span className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs font-semibold text-gray-700">
          {request.sourceTier}
        </span>
      </div>
      <dl className="mt-3 grid grid-cols-1 gap-2 text-xs leading-5">
        {request.searchIntent && <Field label="intent" value={request.searchIntent} />}
        {request.evidenceQuestion && <Field label="evidence question" value={request.evidenceQuestion} />}
        <Field label="query" value={request.query} />
        <Field label="domains" value={request.domains.join(", ")} />
        <Field label="claims" value={request.allowedClaims.join(", ")} />
        <Field label="max results" value={request.maxResults} />
        {request.rejectsAsProof && request.rejectsAsProof.length > 0 && (
          <Field label="rejects as proof" value={request.rejectsAsProof.join(", ")} />
        )}
      </dl>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
      <div className="text-xs font-semibold uppercase text-gray-500">{label}</div>
      <div className="mt-1 break-words text-lg font-bold text-gray-900">{value}</div>
    </div>
  );
}

function TaskRow({ task }: { task: EvidenceCollectionTaskRow }) {
  return (
    <article className="rounded-md border border-gray-200 px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-bold text-gray-900">{task.taskType}</div>
          <div className="mt-1 text-xs text-gray-500">{task.taskId}</div>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-md border border-gray-200 bg-gray-50 px-2 py-1 text-xs font-semibold text-gray-700">
            {task.priority}
          </span>
          <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${taskStatusStyles[task.status]}`}>
            {task.status}
          </span>
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-1 gap-3 text-xs leading-5 md:grid-cols-2">
        <Field label="accepted" value={task.acceptedEvidenceCount} />
        <Field label="rejected" value={task.rejectedEvidenceCount} />
        <Field label="source tier" value={task.resultTemplate.sourceTier} />
        <Field label="claims" value={task.resultTemplate.claimedSupports.join(", ")} />
      </dl>

      <div className="mt-3 rounded-md bg-gray-50 px-3 py-2 text-xs leading-5 text-gray-700">
        <div className="font-semibold text-gray-900">Primary query</div>
        <div className="mt-1 break-words">{task.primaryQuery}</div>
      </div>

      <div className="mt-3 grid grid-cols-1 gap-3 text-xs leading-5 md:grid-cols-2">
        <ListBlock title="Operator checklist" items={task.operatorChecklist} />
        <ListBlock title="Must reject" items={task.mustReject} />
      </div>
    </article>
  );
}

function Field({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="min-w-0 rounded-md bg-gray-50 px-3 py-2">
      <dt className="font-semibold text-gray-500">{label}</dt>
      <dd className="mt-1 break-words text-gray-900">{value}</dd>
    </div>
  );
}

function PanelBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-md border border-gray-200 bg-white px-4 py-4">
      <h4 className="text-sm font-bold text-gray-900">{title}</h4>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md bg-gray-50 px-3 py-2">
      <div className="font-semibold text-gray-900">{title}</div>
      <ul className="mt-1 list-disc space-y-1 pl-4 text-gray-700">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function CaptureTemplate({ row }: { row: WebEvidenceCaptureRow }) {
  return (
    <article className="rounded-md border border-gray-200 bg-gray-50 px-3 py-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="text-xs font-bold text-gray-900">{row.taskType}</div>
          <div className="mt-1 text-xs text-gray-500">{row.taskId}</div>
        </div>
        <span className={`rounded-md border px-2 py-1 text-xs font-semibold ${taskStatusStyles[row.currentStatus]}`}>
          {row.currentStatus}
        </span>
      </div>
      <div className="mt-3 text-xs font-semibold text-gray-900">Copyable submission</div>
      <pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap break-words rounded-md bg-white p-3 text-xs leading-5 text-gray-800">
        {JSON.stringify(row.copyableSubmission, null, 2)}
      </pre>
    </article>
  );
}

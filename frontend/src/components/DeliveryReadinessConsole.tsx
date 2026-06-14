import { AlertTriangle, CheckCircle2, ClipboardCheck, FileText, ShieldCheck } from "lucide-react";
import { buildDeliveryReadinessSummary, type DeliveryReadinessInput, type DeliveryGateStatus } from "@/lib/deliveryReadiness";

interface DeliveryReadinessConsoleProps extends DeliveryReadinessInput {
  onOpenReportPreview: () => void;
}

const statusCopy: Record<DeliveryGateStatus, { label: string; className: string }> = {
  ready: {
    label: "Ready",
    className: "border-emerald-200 bg-emerald-50 text-emerald-900",
  },
  needs_review: {
    label: "Review",
    className: "border-amber-200 bg-amber-50 text-amber-900",
  },
  blocked: {
    label: "Blocked",
    className: "border-red-200 bg-red-50 text-red-900",
  },
};

const gateIcons = {
  data_boundary: ShieldCheck,
  plan_structure: ClipboardCheck,
  evidence_pack: FileText,
  report_package: FileText,
  human_review: AlertTriangle,
};

export function DeliveryReadinessConsole({
  gameMatrix,
  deliveryProfile,
  report,
  onOpenReportPreview,
}: DeliveryReadinessConsoleProps) {
  const readiness = buildDeliveryReadinessSummary({ gameMatrix, deliveryProfile, report });
  const overall = statusCopy[readiness.status];
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Delivery Readiness</p>
          <h2 className="mt-1 text-xl font-bold text-slate-950">交付准备度</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">
            这里检查当前方案是否能进入家庭沟通和顾问复核；每个交付 gate 都是操作检查，它不是录取承诺，正式交付前必须复核官方数据。
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className={`rounded-md border px-3 py-2 text-right ${overall.className}`}>
            <div className="text-xs font-semibold">{overall.label}</div>
            <div className="text-2xl font-black">{readiness.score}</div>
          </div>
          <button
            type="button"
            onClick={onOpenReportPreview}
            className="rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700"
          >
            打开 A4 报告预览
          </button>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-5">
        {readiness.gates.map((gate) => {
          const Icon = gateIcons[gate.id] ?? CheckCircle2;
          const copy = statusCopy[gate.status];
          return (
            <article key={gate.id} className={`rounded-md border p-3 ${copy.className}`}>
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  <h3 className="text-sm font-bold">{gate.label}</h3>
                </div>
                <span className="text-xs font-black">{copy.label}</span>
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-700">{gate.signal}</p>
              <p className="mt-2 text-xs font-semibold leading-5 text-slate-900">{gate.action}</p>
            </article>
          );
        })}
      </div>

      <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 px-4 py-3">
        <div className="text-sm font-bold text-slate-900">下一步：{readiness.nextAction}</div>
        <p className="mt-1 text-xs leading-5 text-slate-600">{readiness.claimBoundary}</p>
      </div>
    </section>
  );
}

import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import { AlertTriangle, CheckCircle2, ClipboardCheck, FileText, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface DeliveryProfile {
  score: number;
  rank?: number;
  subject_group: string;
  preferred_cities?: string[];
  excluded_cities?: string[];
  preferred_majors?: string[];
  blacklist_majors?: string[];
  risk_tolerance?: string;
  school_major_preference?: string;
  stated_misconceptions?: string[];
  emotional_concerns?: string[];
  family_pressure_points?: string[];
  preference_assumptions?: string[];
  preference_confidence?: number;
  major_cognition_risk?: number;
  regret_sensitivity?: number;
  medical_restrictions?: Record<string, boolean>;
  subject_scores?: Record<string, number>;
}

interface DeliveryManifest {
  status: string;
  intake_status?: string;
  intake_readiness_score?: number;
  plan_quality_status?: string;
  plan_quality_score?: number;
  expectation_status?: string;
  report_quality_status?: string;
  report_quality_score?: number;
  delivery_gates?: Array<{
    gate: string;
    status: string;
    requirement: string;
  }>;
  next_actions?: string[];
}

interface DeliveryPreview {
  success: boolean;
  message: string;
  case_id: string;
  output_dir: string;
  manifest: DeliveryManifest;
  artifacts: Record<string, string>;
}

interface InternalDeliveryReviewProps {
  profile: DeliveryProfile | null;
  report: string | null;
}

const statusLabel: Record<string, string> = {
  ready_to_deliver: "可交付",
  pending_signoff: "待确认",
  needs_revision: "需修订",
  blocked: "阻塞",
  blocked_missing_core: "阻塞",
  ready_for_recommendation: "已就绪",
  needs_clarification: "待澄清",
  not_provided: "未提供",
  pass: "通过",
};

function statusTone(status: string | undefined) {
  if (!status) return "border-slate-300 bg-slate-50 text-slate-700";
  if (["ready_to_deliver", "ready_for_recommendation", "pass"].includes(status)) {
    return "border-emerald-300 bg-emerald-50 text-emerald-700";
  }
  if (["pending_signoff", "needs_clarification", "not_provided"].includes(status)) {
    return "border-amber-300 bg-amber-50 text-amber-700";
  }
  return "border-red-300 bg-red-50 text-red-700";
}

function percent(value: number | undefined) {
  if (value === undefined || Number.isNaN(value)) return "--";
  return `${Math.round(value * 100)}%`;
}

function artifactTitle(id: string) {
  const labels: Record<string, string> = {
    delivery_bundle: "交付包索引",
    intake_audit: "问诊审计",
    expectation_packet: "预期确认单",
    plan_quality_audit: "志愿表质检",
    report_quality_audit: "报告质检",
    final_report: "最终报告",
  };
  return labels[id] || id;
}

export function InternalDeliveryReview({ profile, report }: InternalDeliveryReviewProps) {
  const [preview, setPreview] = useState<DeliveryPreview | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canRun = Boolean(profile?.score && profile?.subject_group && report);
  const orderedArtifacts = useMemo(() => {
    if (!preview) return [];
    const preferredOrder = [
      "delivery_bundle",
      "intake_audit",
      "expectation_packet",
      "plan_quality_audit",
      "report_quality_audit",
      "final_report",
    ];
    return Object.entries(preview.artifacts).sort(
      ([left], [right]) => preferredOrder.indexOf(left) - preferredOrder.indexOf(right)
    );
  }, [preview]);

  async function runReview() {
    if (!profile || !report) return;
    setIsLoading(true);
    setError(null);

    try {
      const apiUrl = import.meta.env.DEV
        ? "http://localhost:8000"
        : import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/delivery/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile,
          report,
          case_id: `web-${profile.subject_group}-${profile.rank || profile.score}`,
        }),
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(body || `交付预检失败 (${response.status})`);
      }

      setPreview(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "交付预检失败");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="rounded-xl border border-slate-300 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2 text-slate-900">
            <ClipboardCheck className="size-5 text-cyan-700" aria-hidden="true" />
            <h2 className="text-xl font-semibold">内部交付预检</h2>
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            生成客户交付前的问诊、预期确认、风险解释、推荐依据和免责边界质检。
          </p>
        </div>
        <Button
          type="button"
          onClick={runReview}
          disabled={!canRun || isLoading}
          className="bg-cyan-700 text-white hover:bg-cyan-800"
        >
          {isLoading ? "预检中..." : "生成交付预检"}
        </Button>
      </div>

      {!canRun && (
        <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800">
          需要先生成报告，并保留分数、选科等画像信息，才能进行内部交付预检。
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {preview && (
        <div className="mt-6 space-y-5">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
            {[
              ["总状态", preview.manifest.status, undefined],
              ["问诊", preview.manifest.intake_status, preview.manifest.intake_readiness_score],
              ["志愿表", preview.manifest.plan_quality_status, preview.manifest.plan_quality_score],
              ["报告", preview.manifest.report_quality_status, preview.manifest.report_quality_score],
            ].map(([label, status, score]) => (
              <div key={String(label)} className="rounded-lg border border-slate-200 p-4">
                <div className="text-xs text-slate-500">{label}</div>
                <div className="mt-2 flex items-center justify-between gap-2">
                  <Badge className={statusTone(String(status))} variant="outline">
                    {statusLabel[String(status)] || String(status || "unknown")}
                  </Badge>
                  {typeof score === "number" && (
                    <span className="text-sm font-semibold text-slate-700">{percent(score)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-lg border border-slate-200 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
              <ShieldAlert className="size-4 text-slate-600" aria-hidden="true" />
              交付门槛
            </div>
            <div className="space-y-3">
              {(preview.manifest.delivery_gates || []).map((gate) => (
                <div key={gate.gate} className="grid gap-2 text-sm md:grid-cols-[160px_110px_1fr]">
                  <span className="font-medium text-slate-700">{gate.gate}</span>
                  <Badge className={statusTone(gate.status)} variant="outline">
                    {statusLabel[gate.status] || gate.status}
                  </Badge>
                  <span className="text-slate-600">{gate.requirement}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
              {preview.manifest.status === "ready_to_deliver" ? (
                <CheckCircle2 className="size-4 text-emerald-600" aria-hidden="true" />
              ) : (
                <AlertTriangle className="size-4 text-amber-600" aria-hidden="true" />
              )}
              下一步动作
            </div>
            <ol className="list-decimal space-y-2 pl-5 text-sm leading-6 text-slate-700">
              {(preview.manifest.next_actions || []).map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ol>
          </div>

          {orderedArtifacts.length > 0 && (
            <Tabs defaultValue={orderedArtifacts[0][0]} className="rounded-lg border border-slate-200 p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
                <FileText className="size-4 text-slate-600" aria-hidden="true" />
                交付材料预览
              </div>
              <TabsList className="flex h-auto w-full flex-wrap justify-start gap-2 bg-slate-100">
                {orderedArtifacts.map(([id]) => (
                  <TabsTrigger key={id} value={id} className="min-h-8 flex-none">
                    {artifactTitle(id)}
                  </TabsTrigger>
                ))}
              </TabsList>
              {orderedArtifacts.map(([id, content]) => (
                <TabsContent key={id} value={id} className="mt-4">
                  <div className="max-h-[520px] overflow-auto rounded-md bg-slate-950 p-5">
                    <ReactMarkdown
                      components={{
                        h1: ({ children }) => (
                          <h1 className="mb-4 text-2xl font-semibold text-cyan-100">{children}</h1>
                        ),
                        h2: ({ children }) => (
                          <h2 className="mb-3 mt-6 text-lg font-semibold text-cyan-200">{children}</h2>
                        ),
                        p: ({ children }) => (
                          <p className="mb-3 text-sm leading-6 text-slate-200">{children}</p>
                        ),
                        li: ({ children }) => (
                          <li className="mb-1 text-sm leading-6 text-slate-200">{children}</li>
                        ),
                        table: ({ children }) => (
                          <table className="mb-4 w-full border-collapse text-sm text-slate-200">
                            {children}
                          </table>
                        ),
                        th: ({ children }) => (
                          <th className="border border-slate-700 px-2 py-1 text-left">{children}</th>
                        ),
                        td: ({ children }) => (
                          <td className="border border-slate-700 px-2 py-1 align-top">{children}</td>
                        ),
                      }}
                    >
                      {content}
                    </ReactMarkdown>
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          )}
        </div>
      )}
    </section>
  );
}

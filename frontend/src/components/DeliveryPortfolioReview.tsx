import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import { BarChart3, FileSearch, RefreshCw, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

type DeliveryManifestLike = object & {
  case_id?: unknown;
  status?: unknown;
};

interface DeliveryPortfolioReviewProps {
  sessionManifests: DeliveryManifestLike[];
}

interface DeliveryPortfolioAudit {
  status: string;
  case_count: number;
  ready_to_deliver_rate?: number;
  blocked_rate?: number;
  client_delivery_allowed_rate?: number;
  client_delivery_blocked_rate?: number;
  status_counts?: Record<string, number>;
  client_delivery_status_counts?: Record<string, number>;
  top_failed_gates?: Array<{ gate: string; failed_count: number; failed_rate: number }>;
  top_client_delivery_blocked_reasons?: Array<{ reason: string; count: number; rate: number }>;
  worst_cases?: Array<{
    case_id: string;
    status: string;
    portfolio_score: number;
    failed_gates?: Array<{ gate: string; status: string }>;
  }>;
}

interface DeliveryPortfolioResponse {
  success: boolean;
  message: string;
  audit: DeliveryPortfolioAudit;
  markdown: string;
}

const statusLabel: Record<string, string> = {
  on_track: "可规模化",
  needs_targeted_iteration: "需定向迭代",
  needs_operational_iteration: "需流程迭代",
  blocked_for_scale: "规模化阻塞",
  no_cases: "无案例",
};

function percent(value: number | undefined) {
  if (value === undefined || Number.isNaN(value)) return "--";
  return `${Math.round(value * 100)}%`;
}

function parsePastedManifests(raw: string): DeliveryManifestLike[] {
  const text = raw.trim();
  if (!text) return [];
  try {
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) return parsed.filter((item) => item && typeof item === "object");
    if (parsed && typeof parsed === "object") return [parsed as DeliveryManifestLike];
  } catch {
    return text
      .split(/\n+/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .filter((item) => item && typeof item === "object");
  }
  return [];
}

function compactManifestKey(manifest: DeliveryManifestLike, index: number) {
  return String(manifest.case_id || `${manifest.status || "case"}-${index}`);
}

export function DeliveryPortfolioReview({ sessionManifests }: DeliveryPortfolioReviewProps) {
  const [rawInput, setRawInput] = useState("");
  const [auditResult, setAuditResult] = useState<DeliveryPortfolioResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const parsedManifests = useMemo(() => {
    try {
      return parsePastedManifests(rawInput);
    } catch {
      return [];
    }
  }, [rawInput]);

  const manifests = useMemo(() => {
    const merged = [...sessionManifests, ...parsedManifests];
    const seen = new Set<string>();
    return merged.filter((manifest, index) => {
      const key = compactManifestKey(manifest, index);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [parsedManifests, sessionManifests]);

  async function runPortfolioAudit() {
    if (manifests.length === 0) return;
    setIsLoading(true);
    setError(null);
    try {
      const apiUrl = import.meta.env.DEV
        ? "http://localhost:8000"
        : import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/delivery/portfolio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ manifests }),
      });
      if (!response.ok) {
        const body = await response.text();
        throw new Error(body || `批量交付复盘失败 (${response.status})`);
      }
      setAuditResult(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量交付复盘失败");
    } finally {
      setIsLoading(false);
    }
  }

  const audit = auditResult?.audit;

  return (
    <section className="rounded-xl border border-slate-300 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2 text-slate-900">
            <BarChart3 className="size-5 text-cyan-700" aria-hidden="true" />
            <h2 className="text-xl font-semibold">批量交付复盘</h2>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant="outline" className="border-slate-300 bg-slate-50 text-slate-700">
              当前会话 {sessionManifests.length} 例
            </Badge>
            <Badge variant="outline" className="border-slate-300 bg-slate-50 text-slate-700">
              待审计 {manifests.length} 例
            </Badge>
          </div>
        </div>
        <Button
          type="button"
          onClick={runPortfolioAudit}
          disabled={manifests.length === 0 || isLoading}
          className="bg-cyan-700 text-white hover:bg-cyan-800"
        >
          <RefreshCw className="size-4" aria-hidden="true" />
          {isLoading ? "复盘中..." : "运行批量复盘"}
        </Button>
      </div>

      <div className="mt-4">
        <Textarea
          value={rawInput}
          onChange={(event) => setRawInput(event.target.value)}
          className="min-h-28 border-slate-300 text-sm"
          placeholder='[{"case_id":"case-001","status":"ready_to_deliver","client_delivery":{"allowed":true,"status":"allowed"}}]'
        />
      </div>

      {rawInput.trim() && parsedManifests.length === 0 && (
        <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
          粘贴内容暂未解析为 delivery_bundle JSON 数组或 JSONL。
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {audit && (
        <div className="mt-6 space-y-5">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
            {[
              ["状态", statusLabel[audit.status] || audit.status],
              ["案例数", String(audit.case_count)],
              ["可交付", percent(audit.ready_to_deliver_rate)],
              ["客户包可发", percent(audit.client_delivery_allowed_rate)],
              ["客户包阻断", percent(audit.client_delivery_blocked_rate)],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg border border-slate-200 p-4">
                <div className="text-xs text-slate-500">{label}</div>
                <div className="mt-2 text-lg font-semibold text-slate-900">{value}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div className="rounded-lg border border-slate-200 p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
                <ShieldAlert className="size-4 text-slate-600" aria-hidden="true" />
                客户包阻断原因
              </div>
              <div className="space-y-3">
                {(audit.top_client_delivery_blocked_reasons || []).length > 0 ? (
                  (audit.top_client_delivery_blocked_reasons || []).map((item) => (
                    <div key={item.reason} className="grid gap-2 text-sm md:grid-cols-[80px_70px_1fr]">
                      <span className="font-semibold text-slate-900">{percent(item.rate)}</span>
                      <span className="text-slate-600">{item.count} 例</span>
                      <span className="text-slate-700">{item.reason}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-slate-600">暂无重复阻断原因。</div>
                )}
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
                <FileSearch className="size-4 text-slate-600" aria-hidden="true" />
                高频失败 Gate
              </div>
              <div className="space-y-3">
                {(audit.top_failed_gates || []).length > 0 ? (
                  (audit.top_failed_gates || []).slice(0, 5).map((item) => (
                    <div key={item.gate} className="grid gap-2 text-sm md:grid-cols-[1fr_80px_80px]">
                      <span className="font-medium text-slate-800">{item.gate}</span>
                      <span className="text-slate-600">{item.failed_count} 次</span>
                      <span className="font-semibold text-slate-900">{percent(item.failed_rate)}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-slate-600">暂无失败 gate。</div>
                )}
              </div>
            </div>
          </div>

          {(audit.worst_cases || []).length > 0 && (
            <div className="rounded-lg border border-slate-200 p-4">
              <div className="mb-3 text-sm font-semibold text-slate-800">优先复盘案例</div>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-slate-500">
                      <th className="py-2 pr-3 font-medium">Case</th>
                      <th className="py-2 pr-3 font-medium">Status</th>
                      <th className="py-2 pr-3 font-medium">Score</th>
                      <th className="py-2 pr-3 font-medium">Failed Gates</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(audit.worst_cases || []).slice(0, 6).map((item) => (
                      <tr key={item.case_id} className="border-b border-slate-100">
                        <td className="py-2 pr-3 font-medium text-slate-800">{item.case_id}</td>
                        <td className="py-2 pr-3 text-slate-700">{item.status}</td>
                        <td className="py-2 pr-3 text-slate-700">{percent(item.portfolio_score)}</td>
                        <td className="py-2 pr-3 text-slate-600">
                          {(item.failed_gates || []).map((gate) => `${gate.gate}=${gate.status}`).join("；")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {auditResult?.markdown && (
            <details className="rounded-lg border border-slate-200 p-4">
              <summary className="cursor-pointer text-sm font-semibold text-slate-800">Markdown 复盘报告</summary>
              <div className="mt-4 max-h-96 overflow-auto rounded-md bg-slate-950 p-5">
                <ReactMarkdown
                  components={{
                    h1: ({ children }) => <h1 className="mb-4 text-xl font-semibold text-cyan-100">{children}</h1>,
                    h2: ({ children }) => <h2 className="mb-3 mt-5 text-base font-semibold text-cyan-200">{children}</h2>,
                    h3: ({ children }) => <h3 className="mb-2 mt-4 text-sm font-semibold text-cyan-200">{children}</h3>,
                    p: ({ children }) => <p className="mb-3 text-sm leading-6 text-slate-200">{children}</p>,
                    li: ({ children }) => <li className="mb-1 text-sm leading-6 text-slate-200">{children}</li>,
                    table: ({ children }) => (
                      <table className="mb-4 w-full border-collapse text-sm text-slate-200">{children}</table>
                    ),
                    th: ({ children }) => <th className="border border-slate-700 px-2 py-1 text-left">{children}</th>,
                    td: ({ children }) => <td className="border border-slate-700 px-2 py-1 align-top">{children}</td>,
                  }}
                >
                  {auditResult.markdown}
                </ReactMarkdown>
              </div>
            </details>
          )}
        </div>
      )}
    </section>
  );
}

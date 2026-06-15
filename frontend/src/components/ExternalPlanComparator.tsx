import React, { useEffect, useMemo, useState } from "react";
import { auditExternalPlan } from "../lib/externalPlanAudit";
import type { ExternalPlanAuditSummary, ExternalPlanFinding, ExternalPlanStrategy } from "../lib/externalPlanAudit";
import type { GameMatrix } from "./GameMatrixView";

interface ExternalPlanComparatorProps {
  gameMatrix: GameMatrix;
  onAuditChange?: (summary: ExternalPlanAuditSummary | null) => void;
}

const examplePlan = [
  "冲 华南理工大学 专业组 202",
  "稳 广东工业大学 专业组 205",
  "保 佛山科学技术学院 专业组 204",
].join("\n");

const strategyLabels: Record<ExternalPlanStrategy, string> = {
  rush: "冲",
  target: "稳",
  safe: "保",
  unknown: "未标注",
};

const severityStyles: Record<ExternalPlanFinding["severity"], string> = {
  info: "border-slate-200 bg-slate-50 text-slate-800",
  review: "border-amber-200 bg-amber-50 text-amber-900",
  blocker: "border-red-200 bg-red-50 text-red-900",
};

const formatPercent = (value: number) => `${(value * 100).toFixed(0)}%`;

export const ExternalPlanComparator: React.FC<ExternalPlanComparatorProps> = ({ gameMatrix, onAuditChange }) => {
  const [externalPlanText, setExternalPlanText] = useState("");
  const summary = useMemo(
    () => auditExternalPlan({ text: externalPlanText, gameMatrix }),
    [externalPlanText, gameMatrix],
  );
  const hasInput = externalPlanText.trim().length > 0;
  const unmatchedPreview = summary.unmatchedEntries.slice(0, 6);

  useEffect(() => {
    onAuditChange?.(hasInput ? summary : null);
  }, [hasInput, onAuditChange, summary]);

  return (
    <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-md">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900">外部方案审计</h3>
          <p className="mt-1 text-sm text-gray-600">
            粘贴千问/家长/人工方案，按 PathFinder 审计口径检查结构重合、未匹配条目和复核动作。
          </p>
        </div>
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-800">
          external_plan_audit
        </span>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(320px,0.8fr)]">
        <div className="min-w-0">
          <label htmlFor="external-plan-input" className="text-sm font-semibold text-gray-800">
            粘贴千问/家长/人工方案
          </label>
          <textarea
            id="external-plan-input"
            value={externalPlanText}
            onChange={(event) => setExternalPlanText(event.target.value)}
            placeholder={examplePlan}
            className="mt-2 min-h-44 w-full resize-y rounded-md border border-gray-300 px-3 py-2 text-sm leading-6 text-gray-900 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
          />
          <p className="mt-2 text-xs leading-5 text-gray-500">{summary.claimBoundary}</p>
        </div>

        <div className="min-w-0">
          <div className="grid grid-cols-3 gap-3">
            <Metric label="解析行数" value={summary.parsedCount.toString()} />
            <Metric label="重合院校专业组" value={`${summary.matchedCount}/${summary.parsedCount || 0}`} />
            <Metric label="重合率" value={hasInput ? formatPercent(summary.overlapRate) : "-"} />
          </div>

          <div className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4">
            <div className="text-sm font-semibold text-gray-900">策略结构</div>
            <div className="mt-3 grid grid-cols-4 gap-2 text-center">
              {(Object.keys(strategyLabels) as ExternalPlanStrategy[]).map((strategy) => (
                <div key={strategy} className="rounded bg-white px-2 py-2">
                  <div className="text-xs text-gray-500">{strategyLabels[strategy]}</div>
                  <div className="mt-1 text-base font-bold text-gray-900">{summary.strategyMix[strategy]}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="min-w-0 border-t border-gray-200 pt-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h4 className="font-semibold text-gray-900">未匹配条目</h4>
            <span className="text-xs font-semibold text-gray-500">{summary.unmatchedEntries.length} 行</span>
          </div>
          {unmatchedPreview.length > 0 ? (
            <div className="space-y-2">
              {unmatchedPreview.map((entry) => (
                <div key={`${entry.index}-${entry.normalizedKey}`} className="rounded-md bg-gray-50 px-3 py-2">
                  <div className="text-sm font-semibold text-gray-900">
                    {entry.schoolName}
                    {entry.majorGroupCode ? ` / ${entry.majorGroupCode}` : " / 未提供专业组"}
                  </div>
                  <div className="mt-1 break-words text-xs text-gray-600">{entry.rawLine}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="rounded-md bg-gray-50 px-3 py-3 text-sm text-gray-600">
              {hasInput ? "当前没有未匹配条目。" : "粘贴外部方案后显示未匹配条目。"}
            </p>
          )}
        </div>

        <div className="min-w-0 border-t border-gray-200 pt-4">
          <h4 className="mb-3 font-semibold text-gray-900">复核动作</h4>
          <div className="space-y-2">
            {summary.findings.map((finding) => (
              <div
                key={`${finding.type}-${finding.title}`}
                className={`rounded-md border px-3 py-3 ${severityStyles[finding.severity]}`}
              >
                <div className="text-sm font-semibold">{finding.title}</div>
                <p className="mt-1 text-xs leading-5">{finding.detail}</p>
                <p className="mt-2 text-xs font-semibold">动作：{finding.action}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

interface MetricProps {
  label: string;
  value: string;
}

const Metric: React.FC<MetricProps> = ({ label, value }) => (
  <div className="rounded-md bg-gray-50 px-3 py-3">
    <div className="text-xs font-semibold text-gray-500">{label}</div>
    <div className="mt-1 text-lg font-bold text-gray-900">{value}</div>
  </div>
);

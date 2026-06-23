import { useMemo } from "react";
import { buildDeepEvidenceCollectionPlan, exampleCollectionContext } from "../lib/deepEvidenceCollectionPlan";
import { buildEvidenceAutopilotRun } from "../lib/evidenceAutopilot";
import { buildEvidenceAutopilotSnapshotProviderResults } from "../lib/evidenceAutopilotSnapshotProvider";
import type { DeepOpportunityEvaluationStatus } from "../lib/deepOpportunityEvaluator";

const statusLabel: Record<DeepOpportunityEvaluationStatus, string> = {
  counselor_review_ready: "顾问复核就绪",
  candidate: "候选机会",
  evidence_gap: "证据缺口",
  blocked: "阻断推荐",
};

const statusTone: Record<DeepOpportunityEvaluationStatus, string> = {
  counselor_review_ready: "border-[#0F766E] bg-[#E7F7F2] text-[#0F3F3B]",
  candidate: "border-[#1F5E99] bg-[#EAF3FF] text-[#123E68]",
  evidence_gap: "border-[#B7791F] bg-[#FFF7E8] text-[#69420F]",
  blocked: "border-[#C14E2A] bg-[#FFF0E7] text-[#8F3218]",
};

export function DeepOpportunityEvaluationPanel() {
  const autopilotRun = useMemo(() => {
    const plan = buildDeepEvidenceCollectionPlan(exampleCollectionContext);
    const draftRun = buildEvidenceAutopilotRun({ plan });
    const providerResults = buildEvidenceAutopilotSnapshotProviderResults({
      plan,
      searchTasks: draftRun.searchTasks,
      targetLabel: plan.targetLabel,
    });
    return buildEvidenceAutopilotRun({ plan, providerResults });
  }, []);
  const evaluation = autopilotRun.evaluation;
  const p0Failures = evaluation.gateResults.filter((item) => item.priority === "P0" && item.status !== "verified");

  return (
    <section className="deep-opportunity-evaluation-panel border border-[#C8D8EA] bg-white p-5">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div>
          <p className="text-xs font-semibold tracking-[0.16em] text-[#1F5E99]">机会雷达 · Alpha Board</p>
          <h2 className="mt-2 text-2xl font-semibold">把高维证据转成“能不能进入顾问复核”</h2>
          <p className="mt-2 text-xs font-semibold text-[#64748B]">短期录取 / 中期升学 / 长期职业</p>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-[#35506B]">
            Evidence Autopilot 先自动生成官方招生、科研方向、真实就业、考研保研、考公路径、公众号材料和反证降权任务。
            P0 门槛不过就留下证据缺口，反证命中就阻断推荐，全部通过才进入顾问复核。
          </p>
        </div>
        <aside className={`border p-4 ${statusTone[evaluation.status]}`}>
          <span className="text-xs font-semibold">当前状态</span>
          <div className="mt-2 flex items-end justify-between gap-3">
            <b className="text-3xl">{evaluation.opportunityScore}</b>
            <strong>{statusLabel[evaluation.status]}</strong>
          </div>
          <p className="mt-3 text-xs leading-5">综合机会分 / 100。{evaluation.claimBoundary}</p>
        </aside>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <Metric label="P0 门槛" value={`${evaluation.p0Gate.passedCount}/${evaluation.p0Gate.totalCount}`} />
        <Metric label="反证命中" value={evaluation.counterEvidence.hit ? "有" : "无"} />
        <Metric label="证据缺口" value={String(evaluation.missingEvidence.length + p0Failures.length)} />
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {evaluation.horizonSignals.map((signal) => (
          <section key={signal.horizon} className="border border-[#C8D8EA] bg-[#F8FBFF] p-4">
            <p className="text-xs font-semibold text-[#64748B]">{signal.horizon}</p>
            <b className="mt-2 block text-lg text-[#102033]">
              {signal.status === "supported" ? "已支持" : signal.status === "weak" ? "待补证" : "阻断"}
            </b>
            <p className="mt-2 text-sm leading-6 text-[#35506B]">{signal.summary}</p>
          </section>
        ))}
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <section className="border border-[#C8D8EA] bg-[#F8FBFF] p-4">
          <p className="text-xs font-semibold tracking-[0.16em] text-[#0F766E]">自动证据任务</p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-[#35506B]">
            {autopilotRun.searchTasks.slice(0, 4).map((task) => (
              <li key={task.taskId} className="border-t border-[#C8D8EA] pt-2">
                <b>{task.title}</b>：{task.query}
              </li>
            ))}
          </ul>
        </section>
        <section className="border border-[#C8D8EA] bg-[#F8FBFF] p-4">
          <p className="text-xs font-semibold tracking-[0.16em] text-[#C14E2A]">阻断与复核</p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-[#35506B]">
            {(evaluation.blockedReasons.length ? evaluation.blockedReasons : evaluation.reviewChecklist).slice(0, 4).map((item) => (
              <li key={item} className="border-t border-[#C8D8EA] pt-2">{item}</li>
            ))}
          </ul>
        </section>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-[#C8D8EA] bg-[#F8FBFF] p-4">
      <span className="text-xs font-semibold text-[#64748B]">{label}</span>
      <b className="mt-2 block text-2xl text-[#1F5E99]">{value}</b>
    </div>
  );
}

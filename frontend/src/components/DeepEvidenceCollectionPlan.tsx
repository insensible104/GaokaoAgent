import { useMemo } from "react";
import {
  buildDeepEvidenceCollectionPlan,
  exampleCollectionContext,
  type DeepEvidenceTask,
} from "../lib/deepEvidenceCollectionPlan";

const priorityTone = {
  P0: "border-[#C14E2A] bg-[#FFF0E7] text-[#8F3218]",
  P1: "border-[#1F5E99] bg-[#EAF3FF] text-[#123E68]",
  P2: "border-[#0F766E] bg-[#E7F7F2] text-[#0F3F3B]",
};

export function DeepEvidenceCollectionPlan() {
  const plan = useMemo(() => buildDeepEvidenceCollectionPlan(exampleCollectionContext), []);
  const p0Tasks = plan.tasks.filter((task) => task.priority === "P0");
  const otherTasks = plan.tasks.filter((task) => task.priority !== "P0");

  return (
    <section className="deep-evidence-collection-plan border border-[#C8D8EA] bg-white p-5">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div>
          <p className="text-xs font-semibold tracking-[0.16em] text-[#1F5E99]">高维证据采集台账</p>
          <h2 className="mt-2 text-2xl font-semibold">先把要查的证据定义清楚，再谈自动化。</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-[#35506B]">
            这一层把官方招生、科研方向、师资与论文、本科生可获得性、真实就业、升学/保研、考公、微信公众号和反证降权拆成可执行任务。
            就业侧以 Boss直聘/国聘/校招官网 的岗位样本为锚点；它不会承诺自动抓取半封闭平台，而是规定每一类证据的字段、通过规则和降权规则。
          </p>
        </div>
        <aside className="border border-[#C8D8EA] bg-[#F8FBFF] p-4">
          <p className="text-xs font-semibold text-[#64748B]">目标样例</p>
          <p className="mt-2 text-sm font-semibold leading-6 text-[#102033]">{plan.targetLabel}</p>
          <p className="mt-3 text-xs leading-5 text-[#64748B]">{plan.claimBoundary}</p>
        </aside>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {p0Tasks.map((task) => (
          <TaskCard key={task.id} task={task} />
        ))}
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {otherTasks.map((task) => (
          <TaskCard key={task.id} task={task} compact />
        ))}
      </div>

      <div className="mt-5 border border-[#C8D8EA] bg-[#EAF3FF] p-4">
        <p className="text-xs font-semibold tracking-[0.16em] text-[#1F5E99]">复核门槛</p>
        <ul className="mt-3 grid gap-2 text-sm leading-6 text-[#35506B] lg:grid-cols-2">
          {plan.reviewGates.map((gate) => (
            <li key={gate} className="border-l-2 border-[#1F5E99] pl-3">{gate}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function TaskCard({ task, compact = false }: { task: DeepEvidenceTask; compact?: boolean }) {
  return (
    <article className="border border-[#C8D8EA] bg-[#F8FBFF] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-[#102033]">{task.title}</h3>
          <p className="mt-1 text-xs leading-5 text-[#64748B]">{task.sourceFamily}</p>
        </div>
        <span className={`border px-2 py-1 text-xs font-semibold ${priorityTone[task.priority]}`}>
          {task.priority}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-[#35506B]">{task.accessMethod}</p>
      {!compact && (
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div>
            <span className="text-xs font-semibold text-[#64748B]">输出字段</span>
            <p className="mt-1 text-xs leading-5 text-[#35506B]">{task.outputFields.join(" / ")}</p>
          </div>
          <div>
            <span className="text-xs font-semibold text-[#64748B]">反证降权</span>
            <p className="mt-1 text-xs leading-5 text-[#35506B]">{task.failRule}</p>
          </div>
        </div>
      )}
    </article>
  );
}

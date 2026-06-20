import { useMemo, useState } from "react";
import {
  buildCareerSimulations,
  type CareerSimulationMajorRow,
  type CareerSimulationProfile,
} from "../lib/careerSimulation";

interface CareerChoiceSimulatorProps {
  profile?: CareerSimulationProfile | null;
  rows?: CareerSimulationMajorRow[];
  compact?: boolean;
}

const fitTone = {
  high: "border-[#0F766E] bg-[#E7F7F2] text-[#0F3F3B]",
  medium: "border-[#1F5E99] bg-[#EAF3FF] text-[#123E68]",
  low: "border-[#B7791F] bg-[#FFF7E8] text-[#69420F]",
};

const routeTone: Record<string, string> = {
  employment: "就业",
  graduate: "考研/保研",
  civil_service: "考公/选调",
  research: "科研",
};

export function CareerChoiceSimulator({ profile, rows = [], compact = false }: CareerChoiceSimulatorProps) {
  const simulations = useMemo(
    () => buildCareerSimulations({ profile, rows, limit: compact ? 2 : 3 }),
    [compact, profile, rows],
  );
  const [activeId, setActiveId] = useState(simulations[0]?.id ?? "");
  const activeSimulation = simulations.find((item) => item.id === activeId) ?? simulations[0];

  if (!activeSimulation) return null;

  return (
    <section className="career-simulator border border-[#C8D8EA] bg-[#F8FBFF] p-5">
      <div className="grid gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border border-[#C8D8EA] bg-white p-4">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-[#0F766E]">
            生涯选择模拟
          </p>
          <h3 className="mt-3 text-xl font-semibold leading-snug text-[#102033]">
            先看这个职业每天到底在做什么
          </h3>
          <p className="mt-3 text-sm leading-6 text-[#35506B]">
            这里不改变录取概率，只把专业选择翻译成工作日常、技能要求、读研保研和考公现实，用来校准家庭对专业的想象。
          </p>
          <div className="mt-4 grid gap-2">
            {simulations.map((simulation) => (
              <button
                key={simulation.id}
                className={`border px-3 py-3 text-left transition ${
                  simulation.id === activeSimulation.id
                    ? "border-[#102033] bg-[#102033] text-white"
                    : "border-[#C8D8EA] bg-[#F8FBFF] text-[#102033] hover:bg-[#EAF3FF]"
                }`}
                onClick={() => setActiveId(simulation.id)}
                type="button"
              >
                <span className="block text-sm font-semibold">{simulation.title}</span>
                <span className="mt-1 block text-xs opacity-80">适配度 {simulation.fitScore} / 100</span>
              </button>
            ))}
          </div>
        </aside>

        <main className="min-w-0 border border-[#C8D8EA] bg-white">
          <div className="grid gap-4 border-b border-[#C8D8EA] p-5 lg:grid-cols-[minmax(0,1fr)_150px]">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-2xl font-semibold text-[#102033]">{activeSimulation.title}</h3>
                <span className={`border px-2 py-1 text-xs font-semibold ${fitTone[activeSimulation.fitLevel]}`}>
                  适配度 {activeSimulation.fitScore}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-[#35506B]">{activeSimulation.workScene}</p>
            </div>
            <div className="border border-[#C8D8EA] bg-[#EAF3FF] px-3 py-2 text-sm text-[#102033]">
              <span className="block text-xs font-semibold text-[#64748B]">证据边界</span>
              <b>职业模拟，不替代访谈</b>
            </div>
          </div>

          <div className="grid gap-0 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
            <section className="border-b border-[#C8D8EA] p-5 lg:border-b-0 lg:border-r">
              <h4 className="font-semibold text-[#102033]">一天工作切片</h4>
              <div className="mt-4 grid gap-3">
                {activeSimulation.dayParts.map((part) => (
                  <div key={`${part.time}-${part.task}`} className="grid grid-cols-[56px_minmax(0,1fr)] gap-3">
                    <span className="border-t-2 border-[#1F5E99] pt-2 text-sm font-semibold text-[#1F5E99]">
                      {part.time}
                    </span>
                    <div className="border-t border-[#C8D8EA] pt-2">
                      <p className="text-sm font-semibold text-[#102033]">{part.task}</p>
                      <p className="mt-1 text-xs leading-5 text-[#64748B]">产出：{part.output}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="p-5">
              <h4 className="font-semibold text-[#102033]">为什么推荐先看它</h4>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-[#35506B]">
                {activeSimulation.matchReasons.map((reason) => (
                  <li key={reason} className="border-l-2 border-[#1F5E99] pl-3">
                    {reason}
                  </li>
                ))}
              </ul>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <SkillList title="核心技能" items={activeSimulation.coreSkills} />
                <SkillList title="适配信号" items={activeSimulation.skillSignals} />
              </div>

              <div className="mt-4 border border-[#F1C27D] bg-[#FFF7E8] p-3">
                <h5 className="text-sm font-semibold text-[#69420F]">不适配提醒</h5>
                <ul className="mt-2 space-y-1 text-xs leading-5 text-[#69420F]">
                  {activeSimulation.mismatchSignals.map((signal) => (
                    <li key={signal}>- {signal}</li>
                  ))}
                </ul>
              </div>
            </section>
          </div>

          {!compact && (
            <section className="border-t border-[#C8D8EA] p-5">
              <h4 className="font-semibold text-[#102033]">国内真实岗位锚点</h4>
              <p className="mt-2 text-xs leading-5 text-[#64748B]">
                先把职业想象落到招聘市场会出现的岗位名、用工场景和 JD 关键词，再回头判断专业选择是否值得。
              </p>
              <div className="mt-4 grid gap-3 lg:grid-cols-2">
                {activeSimulation.domesticJobAnchors.map((anchor) => (
                  <div key={anchor.title} className="border border-[#C8D8EA] bg-[#F8FBFF] p-3">
                    <h5 className="font-semibold text-[#102033]">{anchor.title}</h5>
                    <p className="mt-2 text-xs leading-5 text-[#35506B]">{anchor.marketReality}</p>
                    <div className="mt-3 grid gap-2 md:grid-cols-2">
                      <div>
                        <span className="text-xs font-semibold text-[#64748B]">招聘场景</span>
                        <p className="mt-1 text-xs leading-5 text-[#35506B]">{anchor.hiringScenes.join("、")}</p>
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-[#64748B]">JD 关键词</span>
                        <p className="mt-1 text-xs leading-5 text-[#35506B]">{anchor.jdKeywords.join("、")}</p>
                      </div>
                    </div>
                    <p className="mt-3 border-t border-[#C8D8EA] pt-2 text-xs leading-5 text-[#64748B]">
                      岗位证据：{anchor.evidenceToCollect}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {!compact && (
            <section className="border-t border-[#C8D8EA] p-5">
              <h4 className="font-semibold text-[#102033]">升学、就业、考公的真实路径</h4>
              <div className="mt-4 grid gap-3 lg:grid-cols-3">
                {activeSimulation.routesDetail.map((route) => (
                  <div key={route.label} className="border border-[#C8D8EA] bg-[#F8FBFF] p-3">
                    <span className="text-xs font-semibold text-[#64748B]">{routeTone[route.route]}</span>
                    <h5 className="mt-1 font-semibold text-[#102033]">{route.label}</h5>
                    <p className="mt-2 text-xs leading-5 text-[#35506B]">{route.reality}</p>
                    <p className="mt-2 border-t border-[#C8D8EA] pt-2 text-xs leading-5 text-[#64748B]">
                      需要补证：{route.evidenceToCollect}
                    </p>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-xs leading-5 text-[#64748B]">
                结构参考 O*NET 职业任务/技能框架和 Lightcast Open Skills 分类；当前为本地化种子库，后续可扩展到完整职业图谱。
              </p>
            </section>
          )}
        </main>
      </div>
    </section>
  );
}

function SkillList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="border border-[#C8D8EA] bg-[#F8FBFF] p-3">
      <h5 className="text-sm font-semibold text-[#102033]">{title}</h5>
      <ul className="mt-2 space-y-1 text-xs leading-5 text-[#35506B]">
        {items.map((item) => (
          <li key={item}>- {item}</li>
        ))}
      </ul>
    </div>
  );
}

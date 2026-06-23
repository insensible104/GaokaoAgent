import { useMemo } from "react";
import { buildDeepOpportunityCard, exampleDeepOpportunityInput } from "../lib/deepOpportunityCard";
import { DeepEvidenceCollectionPlan } from "./DeepEvidenceCollectionPlan";
import { DeepOpportunityEvaluationPanel } from "./DeepOpportunityEvaluationPanel";

const statusTone = {
  strong: "border-[#0F766E] bg-[#E7F7F2] text-[#0F3F3B]",
  medium: "border-[#1F5E99] bg-[#EAF3FF] text-[#123E68]",
  needs_check: "border-[#B7791F] bg-[#FFF7E8] text-[#69420F]",
};

const statusLabel = {
  strong: "证据较强",
  medium: "需要复核",
  needs_check: "反证优先",
};

export function DeepOpportunityCard() {
  const card = useMemo(() => buildDeepOpportunityCard(exampleDeepOpportunityInput), []);
  const topPillars = card.evidencePillars.slice(0, 3);
  const detailPillars = card.evidencePillars.slice(3);

  return (
    <article className="deep-opportunity-card mx-auto max-w-[1360px] text-[#102033]">
      <section className="grid gap-0 overflow-hidden border border-[#C8D8EA] bg-white lg:grid-cols-[minmax(0,1.08fr)_380px]">
        <div className="bg-[#F8FBFF] p-6 sm:p-8 lg:p-10">
          <p className="text-xs font-semibold tracking-[0.16em] text-[#1F5E99]">PathFinder Alpha Lab · 公开演示</p>
          <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight tracking-normal sm:text-5xl">
            深度机会卡：先判断这是不是机会，再判断能不能推荐
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-7 text-[#35506B]">
            这张样板卡把量化定位、科研方向、师资与论文、本科生机会、真实就业、考研保研、考公路径和反证降权放进同一套证据协议。
            它的目标不是生成一句“可以冲”，而是说明机会来自哪里、代价是什么、谁能承受、下一步该查什么。
          </p>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            {topPillars.map((pillar) => (
              <section key={pillar.label} className="border border-[#C8D8EA] bg-white p-4">
                <span className="text-xs font-semibold text-[#64748B]">{pillar.label}</span>
                <div className="mt-3 flex items-end justify-between gap-3">
                  <b className="text-3xl text-[#1F5E99]">{pillar.score}</b>
                  <span className={`border px-2 py-1 text-xs font-semibold ${statusTone[pillar.status]}`}>
                    {statusLabel[pillar.status]}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-6 text-[#35506B]">{pillar.interpretation}</p>
              </section>
            ))}
          </div>
        </div>

        <aside className="border-t border-[#C8D8EA] bg-[#1F5E99] p-6 text-white lg:border-l lg:border-t-0 lg:p-8">
          <p className="text-xs font-semibold tracking-[0.16em] text-[#DCEBFA]">机会类型</p>
          <h2 className="mt-3 text-2xl font-semibold leading-snug">{card.opportunityType}</h2>
          <div className="mt-8 border border-[#78A7D8] bg-[#EAF3FF] p-5 text-[#102033]">
            <span className="text-xs font-semibold text-[#52708F]">综合证据分</span>
            <div className="mt-2 flex items-end justify-between">
              <b className="text-5xl text-[#1F5E99]">{card.totalScore}</b>
              <span className="mb-1 text-sm font-semibold">置信度：{card.confidence}</span>
            </div>
            <p className="mt-4 text-sm leading-6 text-[#35506B]">{card.targetLabel}</p>
          </div>
          <p className="mt-6 border-l-2 border-[#DCEBFA] pl-4 text-sm leading-6 text-[#EAF3FF]">
            {card.claimBoundary}
          </p>
        </aside>
      </section>

      <section className="mt-6 border border-[#C8D8EA] bg-white p-5">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-semibold tracking-[0.16em] text-[#1F5E99]">Alpha Board</p>
            <h2 className="mt-2 text-2xl font-semibold">像量化项目一样拆机会因子</h2>
          </div>
          <span className="border border-[#C8D8EA] bg-[#F8FBFF] px-3 py-2 text-sm text-[#35506B]">
            正向因子必须配反证风险
          </span>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {card.alphaBoard.map((row) => (
            <section key={row.factor} className="border border-[#C8D8EA] bg-[#F8FBFF] p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold">{row.factor}</h3>
                  <p className="mt-2 text-sm leading-6 text-[#35506B]">{row.evidence}</p>
                </div>
                <b className={row.exposure === "负向" ? "text-2xl text-[#C14E2A]" : "text-2xl text-[#1F5E99]"}>
                  {row.score}
                </b>
              </div>
              <span className="mt-3 inline-block border border-[#C8D8EA] bg-white px-2 py-1 text-xs text-[#64748B]">
                暴露：{row.exposure}
              </span>
            </section>
          ))}
        </div>
      </section>

      <section className="mt-6 grid gap-5 lg:grid-cols-[minmax(0,1fr)_380px]">
        <main className="space-y-5">
          <section className="border border-[#C8D8EA] bg-white p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold tracking-[0.16em] text-[#1F5E99]">证据栈</p>
                <h2 className="mt-2 text-2xl font-semibold">从“分数够不够”扩展到“机会真不真”</h2>
              </div>
              <span className="border border-[#C8D8EA] bg-[#F8FBFF] px-3 py-2 text-sm text-[#35506B]">
                量化定位只是入口
              </span>
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              {detailPillars.map((pillar) => (
                <section key={pillar.label} className="border border-[#C8D8EA] bg-[#F8FBFF] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold">{pillar.label}</h3>
                      <p className="mt-2 text-sm leading-6 text-[#35506B]">{pillar.interpretation}</p>
                    </div>
                    <b className="text-2xl text-[#1F5E99]">{pillar.score}</b>
                  </div>
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-[#35506B]">
                    {pillar.evidence.map((item) => (
                      <li key={item} className="border-t border-[#C8D8EA] pt-2">{item}</li>
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          </section>

          <section className="grid gap-5 lg:grid-cols-2">
            <SignalPanel title="科研方向" eyebrow="科研视角" items={card.researchSignals} />
            <SignalPanel title="师资与论文" eyebrow="导师证据" items={card.researchSignals.slice(1)} />
            <SignalPanel title="本科生可获得性" eyebrow="机会是否落到本科" items={card.undergradAccessSignals} />
            <SignalPanel title="真实就业" eyebrow="国内岗位锚点" items={card.employmentSignals} />
            <SignalPanel title="升学路径" eyebrow="考研 / 保研 / 交叉方向" items={card.graduateSignals} />
            <SignalPanel title="反证与降权" eyebrow="先找反例" items={card.counterEvidenceChecks} tone="warning" />
          </section>
        </main>

        <aside className="space-y-5">
          <section className="border border-[#C8D8EA] bg-[#F8FBFF] p-5">
            <p className="text-xs font-semibold tracking-[0.16em] text-[#0F766E]">适合谁</p>
            <ul className="mt-4 space-y-2 text-sm leading-6 text-[#35506B]">
              {card.fitFor.map((item) => <li key={item}>- {item}</li>)}
            </ul>
          </section>
          <section className="border border-[#F1C27D] bg-[#FFF7E8] p-5">
            <p className="text-xs font-semibold tracking-[0.16em] text-[#B7791F]">不适合谁</p>
            <ul className="mt-4 space-y-2 text-sm leading-6 text-[#69420F]">
              {card.notFitFor.map((item) => <li key={item}>- {item}</li>)}
            </ul>
          </section>
          <section className="border border-[#C8D8EA] bg-white p-5">
            <p className="text-xs font-semibold tracking-[0.16em] text-[#C14E2A]">证据缺口</p>
            <h2 className="mt-2 text-xl font-semibold">上线演示也要让用户看见“不知道”</h2>
            <ul className="mt-4 space-y-3 text-sm leading-6 text-[#35506B]">
              {card.evidenceGaps.map((gap) => (
                <li key={gap} className="border-l-2 border-[#C14E2A] pl-3">{gap}</li>
              ))}
            </ul>
          </section>
          <section className="border border-[#C8D8EA] bg-[#EAF3FF] p-5">
            <p className="text-xs font-semibold tracking-[0.16em] text-[#1F5E99]">下一步采集</p>
            <ol className="mt-4 space-y-3 text-sm leading-6 text-[#35506B]">
              {card.nextActions.map((action, index) => (
                <li key={action} className="grid grid-cols-[28px_minmax(0,1fr)] gap-3">
                  <b className="text-[#1F5E99]">{index + 1}</b>
                  <span>{action}</span>
                </li>
              ))}
            </ol>
          </section>
        </aside>
      </section>

      <section className="mt-6">
        <DeepOpportunityEvaluationPanel />
      </section>

      <section className="mt-6">
        <DeepEvidenceCollectionPlan />
      </section>
    </article>
  );
}

function SignalPanel({
  eyebrow,
  title,
  items,
  tone = "default",
}: {
  eyebrow: string;
  title: string;
  items: string[];
  tone?: "default" | "warning";
}) {
  const borderColor = tone === "warning" ? "border-[#F1C27D]" : "border-[#C8D8EA]";
  const eyebrowColor = tone === "warning" ? "text-[#B7791F]" : "text-[#1F5E99]";

  return (
    <section className={`border ${borderColor} bg-white p-5`}>
      <p className={`text-xs font-semibold tracking-[0.16em] ${eyebrowColor}`}>{eyebrow}</p>
      <h2 className="mt-2 text-xl font-semibold">{title}</h2>
      <ul className="mt-4 space-y-3 text-sm leading-6 text-[#35506B]">
        {items.map((item) => (
          <li key={item} className="border-t border-[#C8D8EA] pt-3">{item}</li>
        ))}
      </ul>
    </section>
  );
}

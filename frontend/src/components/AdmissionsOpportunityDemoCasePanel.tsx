import React from "react";
import { buildAdmissionsOpportunityDemoCase } from "../lib/admissionsOpportunityDemoCase";
import { CareerChoiceSimulator } from "./CareerChoiceSimulator";
import { EvidenceCollectionWorkspacePanel } from "./EvidenceCollectionWorkspacePanel";

export function AdmissionsOpportunityDemoCasePanel() {
  const demo = buildAdmissionsOpportunityDemoCase();
  const partialCoverage = demo.partialWorkspace.coverageSummary;
  const readyCoverage = demo.readyWorkspace.coverageSummary;
  const decisionBrief =
    demo.gapSearchRerun.refreshedWorkspace.completion?.interpretationPackage?.opportunityCards[0]?.familyDecisionBrief ??
    demo.readyWorkspace.completion.interpretationPackage?.opportunityCards[0]?.familyDecisionBrief;
  const publicOpinionGuards = demo.workflow.discoveryLedger.insights
    .map((insight) => ({
      id: insight.id,
      opportunityKind: insight.opportunityKind,
      guard: insight.publicOpinionGuard,
    }))
    .filter((item) => item.guard);
  const trendLanguageGate = demo.workflow.trendAnalysis?.trendLanguageGate;
  const demoCareerProfile = {
    preferred_majors: ["计算机科学", "软件工程"],
    blacklist_majors: ["土木工程", "材料"],
    riasec_top_codes: ["I", "R"],
    career_values: ["growth"],
    risk_tolerance: "balanced",
  };
  const demoCareerRows = [
    {
      school_name: "South China Tech",
      major_group_code: "201",
      major_list: ["计算机科学", "软件工程", "人工智能"],
      suggested_major_choices: [{ major_name: "计算机科学" }, { major_name: "软件工程" }],
    },
  ];

  return (
    <section className="space-y-5" data-protocol={demo.protocol}>
      <header className="border border-[#C8D8EA] bg-[#EAF3FF] p-5">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-[#C14E2A]">
          证据工作台 / 趋势机会研究
        </p>
        <div className="mt-4 grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <h1 className="text-3xl font-semibold leading-tight text-[#102033]">趋势机会研究流</h1>
            <p className="mt-3 max-w-4xl text-sm leading-6 text-[#35506B]">
              从招生计划变化、公开舆情、网页证据到顾问复核，逐层判断一个“趋势机会”能不能进入家庭表达。
              这里的核心不是生成一段漂亮话，而是让每个趋势判断都有证据账本和反证要求。
            </p>
          </div>
          <div className="grid grid-cols-2 border border-[#C8D8EA] bg-[#F8FBFF] text-sm">
            <div className="border-b border-r border-[#C8D8EA] p-3">
              <span className="block font-mono text-[11px] uppercase text-[#64748B]">学生</span>
              <b>{demo.studentName}</b>
            </div>
            <div className="border-b border-[#C8D8EA] p-3">
              <span className="block font-mono text-[11px] uppercase text-[#64748B]">证据任务</span>
              <b>{readyCoverage.completedBlockingTasks} / {readyCoverage.blockingTasks}</b>
            </div>
            <div className="border-r border-[#C8D8EA] p-3">
              <span className="block font-mono text-[11px] uppercase text-[#64748B]">趋势门禁</span>
              <b>{trendLanguageGate?.status ?? "review"}</b>
            </div>
            <div className="p-3">
              <span className="block font-mono text-[11px] uppercase text-[#64748B]">边界</span>
              <b>顾问复核签字</b>
            </div>
          </div>
        </div>
      </header>

      <CareerChoiceSimulator profile={demoCareerProfile} rows={demoCareerRows} />

      <div className="workbench-grid grid grid-cols-1 gap-5 xl:grid-cols-[280px_minmax(0,1fr)_320px]">
        <aside className="workbench-rail border border-[#C8D8EA] bg-white p-4">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-[#0F766E]">案例输入</p>
          <h2 className="mt-3 text-xl font-semibold text-[#102033]">从“可能有机会”到“能不能说”</h2>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-[#35506B]">
            <li>计划变化先作为信号，不直接写成确定机会。</li>
            <li>公众号和公开讨论只能做舆情线索，必须再找权威或多源证据。</li>
            <li>家庭表达前要经过趋势措辞门禁和顾问复核。</li>
          </ul>
        </aside>

        <main className="workbench-main min-w-0">
      <div className="border border-[#C8D8EA] bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h3 className="text-xl font-bold text-gray-900">趋势机会研究演示案例</h3>
            <p className="mt-1 max-w-3xl text-sm leading-6 text-gray-600">
              从官方招生计划差异、舆情假设、证据采集到顾问复核，完整展示一条趋势机会如何进入家庭可读解释。
            </p>
          </div>
          <div className="rounded-md border border-gray-200 bg-gray-50 px-4 py-2 text-right">
            <div className="text-xs font-semibold uppercase text-gray-500">学生</div>
            <div className="text-lg font-bold text-gray-900">{demo.studentName}</div>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-4">
          <Metric label="初始状态" value={demo.partialWorkspace.status} />
          <Metric label="初始阻塞项" value={`${partialCoverage.completedBlockingTasks} / ${partialCoverage.blockingTasks}`} />
          <Metric label="复核状态" value={demo.readyWorkspace.status} />
          <Metric label="复核阻塞项" value={`${readyCoverage.completedBlockingTasks} / ${readyCoverage.blockingTasks}`} />
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <PanelBlock title="舆情线索门禁">
            <div className="space-y-2">
              {publicOpinionGuards.map(({ id, opportunityKind, guard }) => (
                <div key={id} className="rounded-md border border-cyan-200 bg-cyan-50 px-3 py-2 text-sm text-cyan-950">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold">{guard.status}</span>
                    <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">{guard.opportunitySignal}</span>
                    <span className="text-xs text-cyan-800">置信度 {guard.confidence}</span>
                  </div>
                  <div className="mt-1 text-xs leading-5">{opportunityKind}: {guard.summary}</div>
                  <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5">
                    {guard.nextActions.map((action) => (
                      <li key={action}>{action}</li>
                    ))}
                  </ul>
                </div>
              ))}
              {trendLanguageGate && (
                <div className="rounded-md border border-teal-200 bg-teal-50 px-3 py-2 text-sm text-teal-950">
                  <div className="font-semibold">趋势措辞门禁</div>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
                    <span>{trendLanguageGate.protocol}</span>
                    <span className="rounded bg-white px-2 py-0.5 font-semibold">{trendLanguageGate.status}</span>
                    <span>评分：{trendLanguageGate.score}</span>
                    <span>隐藏机会标签：{trendLanguageGate.canUseHiddenOpportunityLabel ? "允许" : "阻塞"}</span>
                  </div>
                  <p className="mt-2 text-xs leading-5">{trendLanguageGate.familySafeWording}</p>
                  <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                    <MiniList title="必需证据" items={trendLanguageGate.requiredEvidence} />
                    <MiniList title="禁用措辞" items={trendLanguageGate.forbiddenWording} />
                  </div>
                </div>
              )}
            </div>
          </PanelBlock>

          <PanelBlock title="采集任务表">
            <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950">
              <div className="font-semibold">{demo.captureWorksheet.status}</div>
              <div className="mt-1 text-xs leading-5">
                待处理任务：{demo.captureWorksheet.pendingRows.map((row) => row.taskType).join(", ")}
              </div>
            </div>
          </PanelBlock>

          <PanelBlock title="搜索执行记录">
            <div className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-950">
              <div className="font-semibold">{demo.operatorSearchRun.protocol}</div>
              <div className="mt-1 text-xs leading-5">
                {demo.operatorSearchRun.status}；来源响应：{demo.operatorSearchRun.providerResponseCount}；
                采纳：{demo.operatorSearchRun.acceptedEvidenceResults.length}；
                拒绝：{demo.operatorSearchRun.rejectedAdapterResults.length + demo.operatorSearchRun.rejectedCaptureSubmissions.length}；
                未返回：{demo.operatorSearchRun.unreturnedTaskIds.length}
              </div>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5">
                {demo.operatorSearchRun.nextActions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
            </div>
          </PanelBlock>

          <PanelBlock title="缺口补采复跑">
            <div className="rounded-md border border-violet-200 bg-violet-50 px-3 py-2 text-sm text-violet-950">
              <div className="font-semibold">{demo.gapSearchRerun.protocol}</div>
              <div className="mt-1 text-xs leading-5">
                {demo.gapSearchRerun.searchRun.status};
                采纳补充证据：{demo.gapSearchRerun.searchRun.acceptedEvidenceResults.length}；
                合并证据：{demo.gapSearchRerun.mergedEvidenceResults.length}；
                刷新状态：{demo.gapSearchRerun.refreshedWorkspace.status}；
                缺口状态：{demo.gapSearchRerun.refreshedWorkspace.evidenceGapSearchPlan.status}
              </div>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5">
                {demo.gapSearchRerun.nextActions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
              <div className="mt-2 text-xs leading-5 text-violet-800">
                已合并 {demo.gapSearchRerun.mergedEvidenceResults.length} 条证据结果
              </div>
            </div>
          </PanelBlock>

          <PanelBlock title="人工采集归一化">
            <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-950">
              <div className="font-semibold">{demo.operatorCaptureNormalization.evidenceResults.length} 条归一化证据结果</div>
              <div className="mt-1 text-xs leading-5">
                被拒绝提交：{demo.operatorCaptureNormalization.rejectedSubmissions.length}
              </div>
            </div>
          </PanelBlock>
        </div>

        <PanelBlock title="操作员执行手册">
          <ol className="space-y-2 text-sm leading-6 text-gray-700">
            {demo.operatorRunbook.map((step) => (
              <li key={step} className="rounded-md bg-gray-50 px-3 py-2">
                {step}
              </li>
            ))}
          </ol>
        </PanelBlock>

        <PanelBlock title="家庭解释预览">
          <p className="text-sm leading-6 text-gray-700">{demo.familyExplanationPreview}</p>
        </PanelBlock>

        {decisionBrief && (
          <PanelBlock title="决策简报">
            <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-900">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold">{decisionBrief.protocol}</span>
                <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">{decisionBrief.status}</span>
              </div>
              <p className="mt-2 text-xs leading-5">{decisionBrief.interestFitSummary}</p>
              <p className="mt-2 text-xs leading-5">{decisionBrief.riskPosture}</p>
              <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
                <div className="font-semibold text-slate-900">概念理解准备度</div>
                <div className="mt-1">
                  {decisionBrief.conceptReadiness.protocol}；状态：{decisionBrief.conceptReadiness.status}
                </div>
                <p className="mt-1">{decisionBrief.conceptReadiness.nextAction}</p>
                <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                  {decisionBrief.conceptReadiness.checkpoints.map((checkpoint) => (
                    <div key={checkpoint.concept} className="rounded bg-slate-50 px-2 py-1">
                      <span className="font-semibold">{checkpoint.concept}</span>: {checkpoint.status}
                      <div className="mt-1">{checkpoint.familyQuestion}</div>
                      {checkpoint.misconception ? <div className="mt-1">{checkpoint.misconception}</div> : null}
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                <MiniList title="概念检查点" items={decisionBrief.conceptCheckpoints} />
                <MiniList title="决策问题" items={decisionBrief.decisionQuestions} />
                <MiniList title="硬边界" items={decisionBrief.hardBoundaries} />
                <MiniList title="不能声称" items={decisionBrief.cannotClaim} />
              </div>
            </div>
          </PanelBlock>
        )}

        <PanelBlock title="Hidden opportunity audit">
          <div className="rounded-md border border-orange-200 bg-orange-50 px-3 py-3 text-sm text-orange-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{demo.hiddenOpportunityAudit.protocol}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {demo.hiddenOpportunityAudit.status}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {demo.hiddenOpportunityAudit.labelPermission}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                score: {demo.hiddenOpportunityAudit.score}
              </span>
            </div>
            <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
              {demo.hiddenOpportunityAudit.scoreBands.map((band) => (
                <div key={band.factor} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-orange-950">{band.factor}</span>
                    <span className="rounded bg-orange-50 px-2 py-0.5 font-semibold">
                      {band.points} / {band.maxPoints}
                    </span>
                  </div>
                  <p className="mt-2">{band.rationale}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-orange-950">Review gate</div>
              <div className="mt-1 grid grid-cols-1 gap-1 sm:grid-cols-2">
                <div>can enter ledger: {demo.hiddenOpportunityAudit.reviewGate.canEnterLedger ? "yes" : "no"}</div>
                <div>
                  hidden label: {demo.hiddenOpportunityAudit.reviewGate.canUseHiddenOpportunityLabel ? "allowed" : "blocked"}
                </div>
                <div>
                  must stay hypothesis-only: {demo.hiddenOpportunityAudit.reviewGate.mustStayHypothesisOnly ? "yes" : "no"}
                </div>
                <div>
                  counselor signoff: {demo.hiddenOpportunityAudit.reviewGate.counselorSignoffRequired ? "required" : "not required"}
                </div>
              </div>
              <MiniList title="Gate reasons" items={demo.hiddenOpportunityAudit.reviewGate.reasons} />
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <MiniList title="Positive signals" items={demo.hiddenOpportunityAudit.positiveSignals} />
              <MiniList title="Negative signals" items={demo.hiddenOpportunityAudit.negativeSignals} />
              <MiniList
                title="Before family wording"
                items={demo.hiddenOpportunityAudit.requiredBeforeFamilyWording}
              />
              <MiniList title="Forbidden claims" items={demo.hiddenOpportunityAudit.forbiddenClaims} />
            </div>
            <p className="mt-3 text-xs leading-5 text-orange-800">{demo.hiddenOpportunityAudit.claimBoundary}</p>
          </div>
        </PanelBlock>

        <PanelBlock title="Plan change ledger handoff">
          <div className="rounded-md border border-fuchsia-200 bg-fuchsia-50 px-3 py-3 text-sm text-fuchsia-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{demo.planChangeOpportunityLedger.protocol}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {demo.planChangeOpportunityLedger.status}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                score: {demo.planChangeOpportunityLedger.score}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                gate: {demo.planChangeOpportunityLedger.hiddenOpportunityGate.status}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{demo.planChangeOpportunityLedger.summary}</p>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-fuchsia-950">Hidden opportunity gate</div>
              <div className="mt-1">
                {demo.planChangeOpportunityLedger.hiddenOpportunityGate.labelPermission};
                can enter ledger: {demo.planChangeOpportunityLedger.hiddenOpportunityGate.canEnterLedger ? "yes" : "no"};
                score: {demo.planChangeOpportunityLedger.hiddenOpportunityGate.score ?? "not supplied"}
              </div>
              <MiniList title="Gate reasons" items={demo.planChangeOpportunityLedger.hiddenOpportunityGate.reasons} />
            </div>
            <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
              {demo.planChangeOpportunityLedger.opportunities.map((opportunity) => (
                <div key={opportunity.id} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-fuchsia-950">
                      {opportunity.affectedRows[0]?.schoolName ?? "Unknown school"}
                    </span>
                    <span className="rounded bg-fuchsia-50 px-2 py-0.5 font-semibold">{opportunity.diffType}</span>
                    <span>{opportunity.status}</span>
                  </div>
                  <p className="mt-2">
                    rank delta: {opportunity.rankDeltaEstimate.direction} {opportunity.rankDeltaEstimate.rankDelta ?? "unknown"}
                  </p>
                  <p className="mt-1">
                    competitor missed: {opportunity.competitorMissed.status}; action: {opportunity.recommendationAction}
                  </p>
                  <MiniList title="Risk guard" items={opportunity.riskGuard.checks} />
                  <MiniList title="Audit trail" items={opportunity.auditTrail.slice(-3)} />
                </div>
              ))}
            </div>
            {demo.planChangeOpportunityLedger.blockedClaims.length > 0 ? (
              <MiniList title="Blocked claims" items={demo.planChangeOpportunityLedger.blockedClaims} />
            ) : null}
            <p className="mt-3 text-xs leading-5 text-fuchsia-800">{demo.planChangeOpportunityLedger.claimBoundary}</p>
          </div>
        </PanelBlock>

        <PanelBlock title="Evidence-backed plan narrative">
          <div className="rounded-md border border-cyan-200 bg-cyan-50 px-3 py-3 text-sm text-cyan-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{demo.volunteerPlanNarrativePackage.protocol}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {demo.volunteerPlanNarrativePackage.status}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                family: {demo.volunteerPlanNarrativePackage.deliveryGate.canShowToFamily ? "ready" : "blocked"}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{demo.volunteerPlanNarrativePackage.headline}</p>
            <div className="mt-3 grid grid-cols-1 gap-2">
              {demo.volunteerPlanNarrativePackage.planRows.map((row) => (
                <div key={row.id} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-cyan-950">{row.displayName}</span>
                    <span className="rounded bg-cyan-50 px-2 py-0.5 font-semibold">{row.position}</span>
                    <span>{row.labelPermission}</span>
                    <span>hypothesis-only: {row.mustStayHypothesisOnly ? "yes" : "no"}</span>
                  </div>
                  <p className="mt-2">{row.familyWording}</p>
                  <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
                    {row.evidencePillars.slice(0, 6).map((pillar) => (
                      <div key={`${row.id}-${pillar.claim}-${pillar.stance}`} className="rounded bg-cyan-50 px-2 py-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-semibold">{pillar.claim}</span>
                          <span className="rounded bg-white px-2 py-0.5 font-semibold">{pillar.stance}</span>
                        </div>
                        <p className="mt-1">{pillar.familyWording}</p>
                        <MiniList title="Evidence basis" items={pillar.evidenceBasis.slice(0, 2)} />
                        <MiniList title="Counter checks" items={pillar.counterChecks.slice(0, 2)} />
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                    <MiniList title="Search follow-ups" items={row.searchFollowUps} />
                    <MiniList title="Concept prompts" items={row.conceptPrompts} />
                    <MiniList title="Interest prompts" items={row.interestPrompts} />
                    <MiniList title="Risk guard" items={row.riskGuard} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <MiniList title="Conversation flow" items={demo.volunteerPlanNarrativePackage.conversationFlow} />
              <MiniList title="Forbidden claims" items={demo.volunteerPlanNarrativePackage.forbiddenClaims} />
              <MiniList title="Next actions" items={demo.volunteerPlanNarrativePackage.nextActions} />
              {demo.volunteerPlanNarrativePackage.deliveryGate.blockedReasons.length > 0 ? (
                <MiniList title="Blocked reasons" items={demo.volunteerPlanNarrativePackage.deliveryGate.blockedReasons} />
              ) : null}
            </div>
            <p className="mt-3 text-xs leading-5 text-cyan-800">{demo.volunteerPlanNarrativePackage.claimBoundary}</p>
          </div>
        </PanelBlock>

        <PanelBlock title="Detailed interpretation">
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-3 text-sm text-rose-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{demo.detailedInterpretation.protocol}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {demo.detailedInterpretation.status}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {demo.detailedInterpretation.planPosition.rowUse}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{demo.detailedInterpretation.headline}</p>
            <p className="mt-2 text-xs leading-5">{demo.detailedInterpretation.summary}</p>
            <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
              {demo.detailedInterpretation.claimRows.map((row) => (
                <div key={row.claim} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-rose-950">{row.claim}</span>
                    <span className="rounded bg-rose-50 px-2 py-0.5 font-semibold">{row.stance}</span>
                  </div>
                  <p className="mt-2">{row.familyWording}</p>
                  <MiniList title="Evidence basis" items={row.evidenceBasis.slice(0, 3)} />
                  <MiniList title="Sources" items={row.sourceRefs.slice(0, 3)} />
                  {row.counterChecks.length > 0 ? (
                    <MiniList title="Counter checks" items={row.counterChecks.slice(0, 3)} />
                  ) : null}
                  <p className="mt-2 text-rose-800">{row.claimBoundary}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <div className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                <div className="font-semibold text-rose-950">Family decision path</div>
                <div className="mt-1">
                  {demo.detailedInterpretation.familyDecisionPath.conceptReadinessProtocol};
                  status: {demo.detailedInterpretation.familyDecisionPath.conceptReadinessStatus}
                </div>
                <MiniList
                  title="Required questions"
                  items={demo.detailedInterpretation.familyDecisionPath.requiredQuestions}
                />
                <MiniList title="Hard stops" items={demo.detailedInterpretation.familyDecisionPath.hardStops} />
              </div>
              <div className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                <div className="font-semibold text-rose-950">Plan position</div>
                <div className="mt-1">{demo.detailedInterpretation.planPosition.rowUse}</div>
                <MiniList
                  title="Not recommendation reasons"
                  items={demo.detailedInterpretation.planPosition.notARecommendationReasons}
                />
                <MiniList title="Next actions" items={demo.detailedInterpretation.nextActions} />
              </div>
            </div>
          </div>
        </PanelBlock>

        <PanelBlock title="Web research strategy">
          <div className="rounded-md border border-sky-200 bg-sky-50 px-3 py-3 text-sm text-sky-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{demo.researchStrategy.protocol}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {demo.researchStrategy.status}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{demo.researchStrategy.presentationGate}</p>
            <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
              {demo.researchStrategy.researchPillars.map((pillar) => (
                <div key={pillar.pillar} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-sky-950">{pillar.pillar}</span>
                    <span className="rounded bg-sky-50 px-2 py-0.5 font-semibold">{pillar.status}</span>
                    <span>{pillar.evidenceCount} evidence</span>
                  </div>
                  <p className="mt-2">{pillar.nextCheck}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-sky-950">Priority queries</div>
              <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                {demo.researchStrategy.priorityQueries.slice(0, 6).map((query) => (
                  <div key={query.id} className="rounded bg-sky-50 px-2 py-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold">{query.searchIntent ?? query.taskType}</span>
                      <span className="rounded bg-white px-2 py-0.5 font-semibold">{query.priority}</span>
                      <span>{query.status}</span>
                    </div>
                    <p className="mt-1">{query.evidenceQuestion}</p>
                    <p className="mt-1 break-words text-sky-800">{query.query}</p>
                    <div className="mt-1">rejects as proof: {query.rejectsAsProof.join(", ") || "none"}</div>
                    <div className="mt-1">{query.escalationRule}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <MiniList title="Contradiction tests" items={demo.researchStrategy.contradictionTests.slice(0, 6)} />
              <MiniList title="Minimum evidence rules" items={demo.researchStrategy.minimumEvidenceRules} />
              <MiniList title="Operator brief" items={demo.researchStrategy.operatorBrief} />
            </div>
          </div>
        </PanelBlock>

        <PanelBlock title="Family clarity roadmap">
          <div className="rounded-md border border-lime-200 bg-lime-50 px-3 py-3 text-sm text-lime-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{demo.familyClarityRoadmap.protocol}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {demo.familyClarityRoadmap.status}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                rows: {demo.familyClarityRoadmap.rowDiscussionGate.canDiscussRows ? "ready" : "blocked"}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{demo.familyClarityRoadmap.rowDiscussionGate.nextAction}</p>
            <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
              {demo.familyClarityRoadmap.conceptCards.map((card) => (
                <div key={card.concept} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-lime-950">{card.concept}</span>
                    <span className="rounded bg-lime-50 px-2 py-0.5 font-semibold">{card.status}</span>
                  </div>
                  <p className="mt-2">{card.plainMeaning}</p>
                  <p className="mt-2">{card.familyQuestion}</p>
                  <p className="mt-2 text-lime-800">{card.decisionImpact}</p>
                  {card.misconception ? <p className="mt-2">{card.misconception}</p> : null}
                  <p className="mt-2">{card.repairAction}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-lime-950">Interest axes</div>
              <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                {demo.familyClarityRoadmap.interestAxes.map((axis) => (
                  <div key={axis.axis} className="rounded bg-lime-50 px-2 py-2">
                    <div className="font-semibold">{axis.axis}</div>
                    <p className="mt-1">{axis.prompt}</p>
                    <p className="mt-1 text-lime-800">{axis.whyItMatters}</p>
                    <p className="mt-1">{axis.evidenceToCollect}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <MiniList title="Alignment questions" items={demo.familyClarityRoadmap.parentStudentAlignment.questions} />
              <MiniList title="Hard stops" items={demo.familyClarityRoadmap.parentStudentAlignment.hardStops} />
              {demo.familyClarityRoadmap.rowDiscussionGate.blockedReasons.length > 0 ? (
                <MiniList title="Blocked reasons" items={demo.familyClarityRoadmap.rowDiscussionGate.blockedReasons} />
              ) : null}
            </div>
          </div>
        </PanelBlock>

        <PanelBlock title="Counselor review dossier">
          <div className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-3 text-sm text-indigo-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{demo.counselorReviewDossier.protocol}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {demo.counselorReviewDossier.status}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{demo.counselorReviewDossier.caseSummary.summary}</p>
            <p className="mt-2 text-xs leading-5">{demo.counselorReviewDossier.opportunityThesis}</p>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-indigo-950">Trend wording boundary</div>
              <div className="mt-1">
                status: {demo.counselorReviewDossier.publicOpinionPosition.wordingGateStatus};
                score: {demo.counselorReviewDossier.publicOpinionPosition.wordingGateScore};
                hidden label: {demo.counselorReviewDossier.publicOpinionPosition.canUseHiddenOpportunityLabel ? "allowed" : "blocked"}
              </div>
              <p className="mt-2">{demo.counselorReviewDossier.publicOpinionPosition.familySafeWording}</p>
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <MiniList title="What we can say" items={demo.counselorReviewDossier.whatWeCanSay} />
              <MiniList title="What we cannot say" items={demo.counselorReviewDossier.whatWeCannotSay} />
              <MiniList title="Counselor checklist" items={demo.counselorReviewDossier.counselorReviewChecklist} />
              <MiniList title="Family questions" items={demo.counselorReviewDossier.familyQuestions} />
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              Evidence trail: {demo.counselorReviewDossier.evidenceTrail.length} accepted items;
              gaps: {demo.counselorReviewDossier.gapPosition.status};
              triangulation: {demo.counselorReviewDossier.gapPosition.triangulationStatus};
              public opinion: {demo.counselorReviewDossier.publicOpinionPosition.evidenceRole}
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-indigo-950">Search provenance</div>
              <div className="mt-1">
                {demo.counselorReviewDossier.searchProvenance.protocol};
                runs: {demo.counselorReviewDossier.searchProvenance.runCount};
                providers: {demo.counselorReviewDossier.searchProvenance.providerIds.join(", ") || "none"};
                accepted: {demo.counselorReviewDossier.searchProvenance.summary.acceptedRows};
                rejected: {demo.counselorReviewDossier.searchProvenance.summary.rejectedRows};
                unreturned: {demo.counselorReviewDossier.searchProvenance.summary.unreturnedRows}
              </div>
              <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                {demo.counselorReviewDossier.searchProvenance.queryRows.slice(0, 8).map((row) => (
                  <div key={`${row.requestId}-${row.query}`} className="rounded bg-indigo-50 px-2 py-1">
                    <span className="font-semibold">{row.searchIntent ?? row.taskType}</span>: {row.query}
                    {row.evidenceQuestion ? <div className="mt-1">{row.evidenceQuestion}</div> : null}
                    {row.rejectsAsProof && row.rejectsAsProof.length > 0 ? (
                      <div className="mt-1">rejects as proof: {row.rejectsAsProof.join(", ")}</div>
                    ) : null}
                  </div>
                ))}
              </div>
              <ul className="mt-2 list-disc space-y-1 pl-4">
                {demo.counselorReviewDossier.searchProvenance.resultRows.slice(0, 4).map((row, index) => (
                  <li key={`${row.taskId}-${row.sourceTitle ?? row.outcome}-${index}`}>
                    {row.provider ?? "no provider"} {row.outcome}: {row.sourceTitle ?? row.taskType}
                    {row.rejectionReason ? ` (${row.rejectionReason})` : ""}
                  </li>
                ))}
              </ul>
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-indigo-950">Evidence quality</div>
              <div className="mt-1">
                {demo.counselorReviewDossier.evidenceQuality.protocol};
                status: {demo.counselorReviewDossier.evidenceQuality.status};
                authoritative: {demo.counselorReviewDossier.evidenceQuality.summary.authoritativeSources};
                current cycle: {demo.counselorReviewDossier.evidenceQuality.summary.currentCycleSources};
                stale: {demo.counselorReviewDossier.evidenceQuality.summary.staleSources};
                conflicts: {demo.counselorReviewDossier.evidenceQuality.summary.conflictedClaims}
              </div>
              <p className="mt-2">{demo.counselorReviewDossier.evidenceQuality.familyPresentationGate}</p>
              {demo.counselorReviewDossier.evidenceQuality.blockingConcerns.length > 0 && (
                <MiniList
                  title="Quality blockers"
                  items={demo.counselorReviewDossier.evidenceQuality.blockingConcerns}
                />
              )}
              <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                {demo.counselorReviewDossier.evidenceQuality.sourceRows.slice(0, 4).map((row) => (
                  <div key={`${row.taskId}-${row.claim}-${row.sourceTitle}`} className="rounded bg-indigo-50 px-2 py-1">
                    <span className="font-semibold">{row.claim}</span>: {row.authorityLevel}, {row.freshness}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </PanelBlock>

        <div className="rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-xs leading-5 text-gray-600">
          {demo.claimBoundary}
        </div>
      </div>

        </main>

        <aside className="workbench-decision border border-[#C8D8EA] bg-[#1F5E99] p-4 text-[#F8FBFF]">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-[#FFA02F]">判断输出</p>
          <h2 className="mt-3 text-xl font-semibold">趋势机会必须带反证条件</h2>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-[#EAF3FF]">
            <li>Hidden opportunity 只能在门禁允许后进入家庭话术。</li>
            <li>就业、考研保研、考公方向需要真实证据，不允许泛泛而谈。</li>
            <li>未完成证据缺口时，只能写成 hypothesis-only。</li>
          </ul>
          <div className="mt-5 border border-[#78A7D8] p-3 font-mono text-xs text-[#FFA02F]">
            趋势分析必须包含证据账本、反证检查和顾问复核签字。
          </div>
        </aside>
      </div>

      <div className="border border-[#C8D8EA] bg-white p-4">
        <EvidenceCollectionWorkspacePanel workspace={demo.readyWorkspace} />
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
      <div className="text-xs font-semibold uppercase text-gray-500">{label}</div>
      <div className="mt-1 break-words text-base font-bold text-gray-900">{value}</div>
    </div>
  );
}

function PanelBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-5 rounded-md border border-gray-200 bg-white px-4 py-4">
      <h4 className="text-sm font-bold text-gray-900">{title}</h4>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function MiniList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md bg-white px-3 py-2 text-xs leading-5">
      <div className="font-semibold text-slate-900">{title}</div>
      <ul className="mt-1 list-disc space-y-1 pl-4 text-slate-700">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

import { useMemo, useState } from "react";
import {
  buildJobEvidenceBrief,
  exampleJobEvidenceText,
  type JobEvidenceSourceType,
} from "../lib/jobEvidence";

const sourceTypeLabels: Record<JobEvidenceSourceType, string> = {
  manual_jd: "手动粘贴 JD",
  public_report: "公开报告摘录",
  campus_recruitment: "校招公告/企业官网",
  civil_service_table: "考公/事业单位职位表",
};

const sourceTypeOptions = Object.entries(sourceTypeLabels) as Array<[JobEvidenceSourceType, string]>;

export function JobEvidenceWorkbench() {
  const [sourceType, setSourceType] = useState<JobEvidenceSourceType>("manual_jd");
  const [text, setText] = useState(exampleJobEvidenceText);
  const brief = useMemo(
    () => buildJobEvidenceBrief({ sourceType, text, capturedAt: "2026-06-20" }),
    [sourceType, text],
  );

  return (
    <section className="job-evidence-workbench border border-[#C8D8EA] bg-white p-5">
      <div className="grid gap-5 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <span className="border border-[#1F5E99] bg-[#EAF3FF] px-2 py-1 text-xs font-semibold text-[#1F5E99]">
              岗位证据工作台
            </span>
            <span className="text-xs font-semibold text-[#64748B]">请粘贴你有权查看或保存的 JD</span>
          </div>
          <h3 className="mt-3 text-xl font-semibold leading-snug text-[#102033]">
            把 BOSS、智联、校招官网或职位表里的岗位文本，转成可讨论的证据
          </h3>
          <p className="mt-2 text-sm leading-6 text-[#35506B]">
            不支持绕过平台反爬抓取。这里先做人工可追溯文本解析，再和就业质量报告、校招名单、考公职位表交叉验证。
          </p>

          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {sourceTypeOptions.map(([value, label]) => (
              <button
                key={value}
                className={`border px-3 py-2 text-left text-sm font-semibold transition ${
                  sourceType === value
                    ? "border-[#102033] bg-[#102033] text-white"
                    : "border-[#C8D8EA] bg-[#F8FBFF] text-[#102033] hover:bg-[#EAF3FF]"
                }`}
                onClick={() => setSourceType(value)}
                type="button"
              >
                {label}
              </button>
            ))}
          </div>

          <label className="mt-4 block text-sm font-semibold text-[#102033]" htmlFor="job-evidence-textarea">
            岗位原文
          </label>
          <textarea
            className="mt-2 min-h-[260px] w-full resize-y border border-[#C8D8EA] bg-[#F8FBFF] p-3 text-sm leading-6 text-[#102033] outline-none focus:border-[#1F5E99] focus:bg-white"
            id="job-evidence-textarea"
            onChange={(event) => setText(event.target.value)}
            value={text}
          />
          <p className="mt-2 text-xs leading-5 text-[#64748B]">{brief.platformPolicyNote}</p>
        </div>

        <div className="min-w-0 border border-[#C8D8EA] bg-[#F8FBFF]">
          <div className="border-b border-[#C8D8EA] bg-[#EAF3FF] p-4">
            <span className="text-xs font-semibold text-[#64748B]">岗位路径判断</span>
            <h3 className="mt-1 text-2xl font-semibold text-[#102033]">{brief.jobTitle}</h3>
            <p className="mt-2 text-sm leading-6 text-[#35506B]">{brief.summary}</p>
          </div>

          <div className="grid border-b border-[#C8D8EA] text-sm sm:grid-cols-2">
            <Metric label="岗位族" value={brief.normalizedRoleFamily} />
            <Metric label="来源类型" value={sourceTypeLabels[brief.sourceType]} />
            <Metric label="城市" value={brief.cities.join("、") || "未明确"} />
            <Metric label="学历 / 经验" value={`${brief.educationRequirement} / ${brief.experienceRequirement}`} />
          </div>

          <section className="border-b border-[#C8D8EA] p-4">
            <h4 className="text-sm font-semibold text-[#102033]">JD 关键词</h4>
            <div className="mt-3 flex flex-wrap gap-2">
              {(brief.skillKeywords.length ? brief.skillKeywords : ["待补充"]).map((skill) => (
                <span key={skill} className="border border-[#C8D8EA] bg-white px-2 py-1 text-xs text-[#35506B]">
                  {skill}
                </span>
              ))}
            </div>
          </section>

          <section className="grid gap-3 p-4 lg:grid-cols-3">
            <SignalCard title="本科就业" items={brief.routeSignals.employment} />
            <SignalCard title="读研/保研" items={brief.routeSignals.graduate} />
            <SignalCard title="考公/事业单位" items={brief.routeSignals.civilService} />
          </section>

          <section className="border-t border-[#C8D8EA] p-4">
            <h4 className="text-sm font-semibold text-[#102033]">下一步补证问题</h4>
            <ul className="mt-2 space-y-2 text-xs leading-5 text-[#35506B]">
              {brief.evidenceQuestions.map((question) => (
                <li key={question} className="border-l-2 border-[#1F5E99] pl-3">
                  {question}
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-b border-r border-[#C8D8EA] bg-white p-3 last:border-r-0 sm:[&:nth-child(2n)]:border-r-0">
      <span className="block text-xs font-semibold text-[#64748B]">{label}</span>
      <b className="mt-1 block break-words text-[#102033]">{value}</b>
    </div>
  );
}

function SignalCard({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="border border-[#C8D8EA] bg-white p-3">
      <h4 className="text-sm font-semibold text-[#102033]">{title}</h4>
      <ul className="mt-2 space-y-2 text-xs leading-5 text-[#35506B]">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

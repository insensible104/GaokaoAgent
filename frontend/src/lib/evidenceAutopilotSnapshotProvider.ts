import type { DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { EvidenceAutopilotSearchTask } from "./evidenceAutopilot";
import {
  buildEvidenceAutopilotProviderRequest,
  isOperatorOnlyChannel,
  type EvidenceAutopilotProvider,
  type EvidenceAutopilotProviderRequest,
  type EvidenceAutopilotProviderResult,
} from "./evidenceAutopilotProvider";

type SnapshotProviderSeed = Record<string, Omit<EvidenceAutopilotProviderResult, "requestId">[]>;

export interface EvidenceAutopilotSnapshotProvider extends EvidenceAutopilotProvider {
  searchSnapshot(request: EvidenceAutopilotProviderRequest): EvidenceAutopilotProviderResult[];
}

const CAPTURED_AT = "2026-06-23T00:00:00.000Z";

const DEFAULT_SNAPSHOT_RESULTS: SnapshotProviderSeed = {
  "official-plan-charter": [
    {
      taskId: "official-plan-charter",
      sourceTitle: "华南理工大学本科招生章程",
      sourceUrl: "https://example.edu/admissions/charter-2026.pdf",
      sourceType: "official",
      excerpt: "招生章程列明专业组计划数、选考要求、校区安排与录取规则。",
      capturedAt: CAPTURED_AT,
      confidence: "high",
    },
    {
      taskId: "official-plan-charter",
      sourceTitle: "广东省普通高校招生专业目录",
      sourceUrl: "https://example.edu/guangdong/major-plan-2026.pdf",
      sourceType: "official",
      excerpt: "专业目录可复核学校代码、专业组代码、计划数与招生批次。",
      capturedAt: CAPTURED_AT,
      confidence: "high",
    },
  ],
  "rank-history-band": [
    {
      taskId: "rank-history-band",
      sourceTitle: "广东省历年投档分与最低排位表",
      sourceUrl: "https://example.edu/guangdong/admission-rank-history",
      sourceType: "official",
      excerpt: "近三年最低排位、计划数和专业组口径可用于交叉复核冲稳讨论边界。",
      capturedAt: CAPTURED_AT,
      confidence: "high",
    },
    {
      taskId: "rank-history-band",
      sourceTitle: "学校本科招生录取分数统计",
      sourceUrl: "https://example.edu/admissions/score-history",
      sourceType: "school",
      excerpt: "学校公布的历史录取统计与省级投档表方向一致，仍需按当年专业组口径复核。",
      capturedAt: CAPTURED_AT,
      confidence: "medium",
    },
  ],
  "faculty-research-direction": [
    {
      taskId: "faculty-research-direction",
      sourceTitle: "学院智能制造与工业软件课题组介绍",
      sourceUrl: "https://example.edu/school/research-labs",
      sourceType: "school",
      excerpt: "课题组长期围绕工业软件、智能制造系统与数据驱动优化开展科研训练。",
      capturedAt: CAPTURED_AT,
      confidence: "medium",
    },
    {
      taskId: "faculty-research-direction",
      sourceTitle: "学院本科生科研训练项目清单",
      sourceUrl: "https://example.edu/school/undergraduate-research",
      sourceType: "school",
      excerpt: "本科生可通过创新项目进入课题组，参与数据工程和制造系统优化项目。",
      capturedAt: CAPTURED_AT,
      confidence: "medium",
    },
  ],
  "publication-trace": [
    {
      taskId: "publication-trace",
      sourceTitle: "导师近三年论文主题列表",
      sourceUrl: "https://example.edu/faculty/publications",
      sourceType: "paper",
      excerpt: "论文主题持续覆盖工业数据建模、制造系统优化和智能质量控制。",
      capturedAt: CAPTURED_AT,
      confidence: "medium",
    },
  ],
  "undergrad-access": [
    {
      taskId: "undergrad-access",
      sourceTitle: "学院本科生创新训练项目",
      sourceUrl: "https://example.edu/school/undergraduate-projects",
      sourceType: "school",
      excerpt: "本科生可报名创新训练项目，并在导师指导下进入制造数据分析课题。",
      capturedAt: CAPTURED_AT,
      confidence: "medium",
    },
    {
      taskId: "undergrad-access",
      sourceTitle: "实验室开放课题与竞赛队入口",
      sourceUrl: "https://example.edu/lab/student-access",
      sourceType: "school",
      excerpt: "实验室面向本科生开放课题、竞赛队训练和工程实践任务。",
      capturedAt: CAPTURED_AT,
      confidence: "medium",
    },
  ],
  "employment-market": [
    {
      taskId: "employment-market",
      sourceTitle: "校招岗位样本：制造数据工程师",
      sourceUrl: "https://example.edu/jobs/manufacturing-data-engineer",
      sourceType: "job",
      excerpt: "岗位要求 Python、SQL、制造流程数据分析与质量工程经验，学历门槛以本科及以上为主。",
      capturedAt: CAPTURED_AT,
      confidence: "medium",
    },
    {
      taskId: "employment-market",
      sourceTitle: "国企数字化岗位样本：工业软件实施",
      sourceUrl: "https://example.edu/jobs/industrial-software",
      sourceType: "job",
      excerpt: "岗位任务覆盖工业软件实施、生产数据治理、跨部门需求分析和系统上线支持。",
      capturedAt: CAPTURED_AT,
      confidence: "medium",
    },
  ],
  "graduate-progression": [
    {
      taskId: "graduate-progression",
      sourceTitle: "学院保研与升学去向说明",
      sourceUrl: "https://example.edu/school/graduate-progression",
      sourceType: "school",
      excerpt: "升学方向可衔接控制科学、计算机应用、工业工程和智能制造交叉方向。",
      capturedAt: CAPTURED_AT,
      confidence: "medium",
    },
  ],
  "civil-service-path": [
    {
      taskId: "civil-service-path",
      sourceTitle: "省考岗位专业限制样本",
      sourceUrl: "https://example.edu/civil-service/position-sample",
      sourceType: "official",
      excerpt: "部分数字化治理与工业经济岗位可接受工学门类，考公路径只能作为弱备选。",
      capturedAt: CAPTURED_AT,
      confidence: "low",
    },
  ],
  "counter-evidence": [
    {
      taskId: "counter-evidence",
      sourceTitle: "招生章程反证复核记录",
      sourceUrl: "https://example.edu/admissions/risk-review",
      sourceType: "official",
      excerpt: "暂未发现专业组规则、选科要求和校区安排与候选机会冲突。",
      capturedAt: CAPTURED_AT,
      confidence: "medium",
    },
    {
      taskId: "counter-evidence",
      sourceTitle: "学院公开信息一致性复核",
      sourceUrl: "https://example.edu/school/risk-review",
      sourceType: "school",
      excerpt: "暂未发现培养方案、科研方向和本科入口之间存在明显断裂。",
      capturedAt: CAPTURED_AT,
      confidence: "medium",
    },
  ],
};

export function createEvidenceAutopilotSnapshotProvider(
  snapshotResults: SnapshotProviderSeed = DEFAULT_SNAPSHOT_RESULTS,
): EvidenceAutopilotSnapshotProvider {
  return {
    id: "pathfinder_snapshot_public_v0",
    async search(request) {
      return this.searchSnapshot(request);
    },
    searchSnapshot(request) {
      const taskSnapshots = snapshotResults[request.taskId] ?? [];
      if (taskSnapshots.length === 0 && isOperatorOnlyChannel(request.channel)) return [];
      return taskSnapshots.slice(0, request.maxResults).map((result) => ({
        ...result,
        requestId: request.requestId,
      }));
    },
  };
}

export function buildEvidenceAutopilotSnapshotProviderResults({
  plan,
  searchTasks,
  targetLabel,
}: {
  plan: DeepEvidenceCollectionPlan;
  searchTasks: EvidenceAutopilotSearchTask[];
  targetLabel: string;
}): EvidenceAutopilotProviderResult[] {
  const provider = createEvidenceAutopilotSnapshotProvider();
  return searchTasks.flatMap((task, index) => {
    const request = buildEvidenceAutopilotProviderRequest({
      requestId: `snapshot-${plan.protocol}-${index + 1}`,
      targetLabel,
      task,
      maxResults: 3,
    });
    return provider.searchSnapshot(request);
  });
}

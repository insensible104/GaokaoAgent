import type {
  DeepEvidenceCollectionPlan,
  DeepEvidenceTask,
} from "./deepEvidenceCollectionPlan";
import type { EvidenceAutopilotProviderResult } from "./evidenceAutopilotProvider";
import type { DeepEvidenceResult } from "./deepOpportunityEvaluator";

const COUNTER_EVIDENCE_BLOCKING_TERMS = ["黑名单", "校区冲突", "调剂风险", "断档", "投诉"];

export function normalizeEvidenceAutopilotResults({
  plan,
  providerResults,
}: {
  plan: DeepEvidenceCollectionPlan;
  providerResults: EvidenceAutopilotProviderResult[];
}): DeepEvidenceResult[] {
  const resultsByTask = groupByTaskId(providerResults);

  return plan.tasks.map((task) => {
    const results = resultsByTask.get(task.id) ?? [];
    if (results.length === 0) {
      return missingResult(task);
    }

    const excerpts = results.map(formatEvidenceNote);
    const note = excerpts.join("；");
    if (task.claim === "counter_evidence" && containsBlockingCounterEvidence(results)) {
      return {
        taskId: task.id,
        claim: task.claim,
        status: "counter_hit",
        sourceCount: results.length,
        excerpts,
        note,
      };
    }

    return {
      taskId: task.id,
      claim: task.claim,
      status: results.length >= requiredSourceCount(task) ? "verified" : "weak",
      sourceCount: results.length,
      excerpts,
      note,
    };
  });
}

function groupByTaskId(providerResults: EvidenceAutopilotProviderResult[]) {
  const grouped = new Map<string, EvidenceAutopilotProviderResult[]>();
  for (const result of providerResults) {
    const taskResults = grouped.get(result.taskId) ?? [];
    taskResults.push(result);
    grouped.set(result.taskId, taskResults);
  }
  return grouped;
}

function missingResult(task: DeepEvidenceTask): DeepEvidenceResult {
  return {
    taskId: task.id,
    claim: task.claim,
    status: "missing",
    sourceCount: 0,
    excerpts: [],
    note: "尚未采集到可审计来源、原文摘录和时间/provenance，不能进入机会结论。",
  };
}

function formatEvidenceNote(result: EvidenceAutopilotProviderResult) {
  return `${result.sourceTitle}：${result.excerpt}`;
}

function containsBlockingCounterEvidence(results: EvidenceAutopilotProviderResult[]) {
  return results.some((result) => {
    const text = `${result.sourceTitle} ${result.excerpt}`;
    return COUNTER_EVIDENCE_BLOCKING_TERMS.some((term) => text.includes(term));
  });
}

function requiredSourceCount(task: DeepEvidenceTask) {
  if (task.claim === "civil_service_path") return 1;
  return task.priority === "P0" ? 2 : 1;
}

"""Evaluate orchestration policies and generate baseline comparison reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys
from typing import Any, Dict, Iterable, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rl.orchestration_alignment import SupervisorActionRanker  # noqa: E402
from rl.orchestration_data_pipeline import load_rollout_records  # noqa: E402
from rl.reward_model_scorer import SupervisorRewardModelScorer  # noqa: E402


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return round(float(statistics.mean(values)), 4) if values else 0.0


def summarize_rollouts(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(records)
    rewards = [float(record.get("summary", {}).get("reward", 0.0) or 0.0) for record in records]
    trace_lengths = [int(record.get("summary", {}).get("trace_length", 0) or 0) for record in records]
    retries = [int(record.get("summary", {}).get("retry_count", 0) or 0) for record in records]
    approvals = [bool(record.get("summary", {}).get("approved", False)) for record in records]
    successes = [bool(record.get("summary", {}).get("success", False)) for record in records]
    deep_research_cases = 0
    error_cases = 0
    agentic_rl_cases = 0
    stage_counts: Dict[str, int] = {}

    for record in records:
        trace = record.get("trace", [])
        if any(step.get("selected_action") == "deep_research" for step in trace):
            deep_research_cases += 1
        if record.get("error"):
            error_cases += 1
        game_stats = record.get("game_matrix_stats") or {}
        if game_stats.get("agentic_rl_used"):
            agentic_rl_cases += 1
        for step in trace:
            stage = step.get("stage", "unknown")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

    return {
        "case_count": total,
        "avg_reward": _mean(rewards),
        "avg_trace_length": _mean(trace_lengths),
        "avg_retry_count": _mean(retries),
        "approval_rate": round(sum(approvals) / total, 4) if total else 0.0,
        "success_rate": round(sum(successes) / total, 4) if total else 0.0,
        "deep_research_rate": round(deep_research_cases / total, 4) if total else 0.0,
        "error_rate": round(error_cases / total, 4) if total else 0.0,
        "agentic_rl_usage_rate": round(agentic_rl_cases / total, 4) if total else 0.0,
        "stage_counts": stage_counts,
    }


def evaluate_ranker(pairwise_records: List[Dict[str, Any]], ranker: SupervisorActionRanker) -> Dict[str, Any]:
    if not pairwise_records:
        return {"pairwise_count": 0, "accuracy": 0.0, "avg_margin_on_correct": 0.0}

    total = 0
    correct = 0
    correct_margins: List[float] = []
    by_stage: Dict[str, Dict[str, float]] = {}

    for record in pairwise_records:
        chosen_action = record.get("chosen_action")
        rejected_action = record.get("rejected_action")
        if not chosen_action or not rejected_action:
            continue
        total += 1
        scores = ranker.score_actions(
            stage=record.get("stage", "unknown"),
            observation=record.get("observation", {}),
            candidate_actions=[chosen_action, rejected_action],
        )
        chosen_score = float(scores.get(chosen_action, 0.0))
        rejected_score = float(scores.get(rejected_action, 0.0))
        stage = record.get("stage", "unknown")
        by_stage.setdefault(stage, {"total": 0.0, "correct": 0.0})
        by_stage[stage]["total"] += 1.0
        if chosen_score >= rejected_score:
            correct += 1
            correct_margins.append(chosen_score - rejected_score)
            by_stage[stage]["correct"] += 1.0

    stage_accuracy = {
        stage: round(stats["correct"] / stats["total"], 4)
        for stage, stats in by_stage.items()
        if stats["total"] > 0
    }
    return {
        "pairwise_count": total,
        "accuracy": round(correct / total, 4) if total else 0.0,
        "avg_margin_on_correct": _mean(correct_margins),
        "stage_accuracy": stage_accuracy,
    }


def evaluate_reward_model(
    pairwise_records: List[Dict[str, Any]],
    reward_model: SupervisorRewardModelScorer,
) -> Dict[str, Any]:
    if not pairwise_records:
        return {"pairwise_count": 0, "accuracy": 0.0, "avg_margin_on_correct": 0.0}

    total = 0
    correct = 0
    correct_margins: List[float] = []
    by_stage: Dict[str, Dict[str, float]] = {}

    for record in pairwise_records:
        chosen_action = record.get("chosen_action")
        rejected_action = record.get("rejected_action")
        if not chosen_action or not rejected_action:
            continue
        total += 1
        scores = reward_model.score_actions(
            message=record.get("message"),
            stage=record.get("stage", "unknown"),
            observation=record.get("observation", {}),
            candidate_actions=[chosen_action, rejected_action],
        )
        chosen_score = float(scores.get(chosen_action, 0.0))
        rejected_score = float(scores.get(rejected_action, 0.0))
        stage = record.get("stage", "unknown")
        by_stage.setdefault(stage, {"total": 0.0, "correct": 0.0})
        by_stage[stage]["total"] += 1.0
        if chosen_score >= rejected_score:
            correct += 1
            correct_margins.append(chosen_score - rejected_score)
            by_stage[stage]["correct"] += 1.0

    stage_accuracy = {
        stage: round(stats["correct"] / stats["total"], 4)
        for stage, stats in by_stage.items()
        if stats["total"] > 0
    }
    return {
        "pairwise_count": total,
        "accuracy": round(correct / total, 4) if total else 0.0,
        "avg_margin_on_correct": _mean(correct_margins),
        "stage_accuracy": stage_accuracy,
        "backend": reward_model.backend,
    }


def compare_rollout_summaries(
    baseline_summary: Dict[str, Any],
    candidate_summary: Dict[str, Any],
) -> Dict[str, Any]:
    numeric_keys = [
        "avg_reward",
        "avg_trace_length",
        "avg_retry_count",
        "approval_rate",
        "success_rate",
        "deep_research_rate",
        "error_rate",
        "agentic_rl_usage_rate",
    ]
    delta = {}
    for key in numeric_keys:
        delta[key] = round(
            float(candidate_summary.get(key, 0.0)) - float(baseline_summary.get(key, 0.0)),
            4,
        )
    return delta


def build_markdown_report(result: Dict[str, Any]) -> str:
    lines = ["# Orchestration Policy Evaluation Report", ""]

    if "rollout_summary" in result:
        summary = result["rollout_summary"]
        lines.extend(
            [
                "## 单组 Rollout 汇总",
                f"- Case 数量：{summary['case_count']}",
                f"- 平均代理奖励：{summary['avg_reward']}",
                f"- 通过率：{summary['approval_rate']}",
                f"- 成功率：{summary['success_rate']}",
                f"- 平均轨迹长度：{summary['avg_trace_length']}",
                f"- 平均重试次数：{summary['avg_retry_count']}",
                f"- 深度调研触发率：{summary['deep_research_rate']}",
                f"- 错误率：{summary['error_rate']}",
                "",
            ]
        )

    if "baseline_comparison" in result:
        comparison = result["baseline_comparison"]
        lines.append("## 基线对比")
        lines.append("")
        lines.append("| 指标 | Baseline | Candidate | 差值 |")
        lines.append("| --- | ---: | ---: | ---: |")
        for key in [
            "avg_reward",
            "approval_rate",
            "success_rate",
            "avg_trace_length",
            "avg_retry_count",
            "deep_research_rate",
            "error_rate",
            "agentic_rl_usage_rate",
        ]:
            baseline_value = comparison["baseline"].get(key, 0.0)
            candidate_value = comparison["candidate"].get(key, 0.0)
            delta = comparison["delta"].get(key, 0.0)
            lines.append(f"| {key} | {baseline_value} | {candidate_value} | {delta:+.4f} |")
        lines.append("")

    if "ranker_eval" in result:
        ranker_eval = result["ranker_eval"]
        lines.extend(
            [
                "## Learned Ranker 偏好评测",
                f"- Pairwise 数量：{ranker_eval['pairwise_count']}",
                f"- 准确率：{ranker_eval['accuracy']}",
                f"- 正确样本平均间隔：{ranker_eval['avg_margin_on_correct']}",
                "",
            ]
        )

    if "reward_model_eval" in result:
        reward_eval = result["reward_model_eval"]
        lines.extend(
            [
                "## Reward Model 偏好评测",
                f"- 后端：{reward_eval.get('backend', 'unknown')}",
                f"- Pairwise 数量：{reward_eval['pairwise_count']}",
                f"- 准确率：{reward_eval['accuracy']}",
                f"- 正确样本平均间隔：{reward_eval['avg_margin_on_correct']}",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rollouts", help="Single rollout JSONL to summarize")
    parser.add_argument("--baseline-rollouts", help="Baseline rollout JSONL")
    parser.add_argument("--candidate-rollouts", help="Candidate rollout JSONL")
    parser.add_argument("--pairwise", help="Pairwise JSONL to evaluate")
    parser.add_argument("--ranker", help="Path to trained supervisor action ranker")
    parser.add_argument("--reward-model", help="Path to reward model checkpoint or ruleset JSON")
    parser.add_argument("--output", help="Optional JSON output path")
    parser.add_argument("--report-md", help="Optional markdown report output path")
    args = parser.parse_args()

    result: Dict[str, Any] = {}

    if args.rollouts:
        result["rollout_summary"] = summarize_rollouts(load_rollout_records(args.rollouts))

    if args.baseline_rollouts and args.candidate_rollouts:
        baseline_summary = summarize_rollouts(load_rollout_records(args.baseline_rollouts))
        candidate_summary = summarize_rollouts(load_rollout_records(args.candidate_rollouts))
        result["baseline_comparison"] = {
            "baseline": baseline_summary,
            "candidate": candidate_summary,
            "delta": compare_rollout_summaries(baseline_summary, candidate_summary),
        }

    pairwise_records = load_rollout_records(args.pairwise) if args.pairwise else None

    if pairwise_records and args.ranker:
        ranker = SupervisorActionRanker.load(args.ranker)
        result["ranker_eval"] = evaluate_ranker(pairwise_records, ranker)

    if pairwise_records and args.reward_model:
        reward_model = SupervisorRewardModelScorer.load(args.reward_model)
        result["reward_model_eval"] = evaluate_reward_model(pairwise_records, reward_model)

    if not result:
        raise ValueError(
            "Provide --rollouts, or --baseline-rollouts with --candidate-rollouts, "
            "or --pairwise with --ranker/--reward-model."
        )

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
        print(f"saved evaluation json to {output_path}")
    else:
        print(payload)

    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_report(result), encoding="utf-8")
        print(f"saved evaluation report to {report_path}")


if __name__ == "__main__":
    main()

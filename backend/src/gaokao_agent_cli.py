"""Unified command-line entrypoint for GaokaoAgent experiments and checks."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

from evaluation.ablation_2025 import (
    DEFAULT_ABLATION_VARIANTS,
    build_markdown_ablation_report,
    run_ablation_backtest_records,
)
from evaluation.backtest_2025 import load_actual_outcomes_csv, run_plan_backtest, summarize_backtests
from evaluation.schemas import PlanBacktestResult
from models.game_matrix import VolunteerPlan
from rl.orchestration_data_pipeline import (
    build_pairwise_preferences,
    load_cases,
    load_rollout_records,
    rollout_cases,
    save_jsonl,
)


BACKEND_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BACKEND_DIR / "scripts"

DEFAULT_SMOKE_TESTS = [
    "test_encoding_smoke.py",
    "test_backend_api_status_smoke.py",
    "test_tradeoff_policy_smoke.py",
    "test_volunteer_plan_schema_smoke.py",
    "test_first_hit_prefix_smoke.py",
    "test_multi_agent_deliberation_smoke.py",
    "test_agent_protocol_smoke.py",
    "test_supervisor_policy_smoke.py",
    "test_orchestration_data_pipeline_smoke.py",
    "test_orchestration_trl_utils_smoke.py",
    "test_backtest_2025_smoke.py",
    "test_ablation_2025_smoke.py",
]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_plan_record(record: dict[str, Any]) -> tuple[str, int, VolunteerPlan, list[str], list[str]]:
    plan_payload = record.get("plan") or record.get("volunteer_plan")
    if not plan_payload:
        raise ValueError("Each plan record must contain `plan` or `volunteer_plan`.")
    plan = VolunteerPlan(**plan_payload)
    user_rank = record.get("user_rank") or plan.user_rank
    if user_rank is None:
        raise ValueError("Each plan record must contain `user_rank`, or plan.user_rank must be set.")
    return (
        str(record.get("case_id") or ""),
        int(user_rank),
        plan,
        list(record.get("preferred_majors") or []),
        list(record.get("blacklist_majors") or []),
    )


def cmd_smoke(args: argparse.Namespace) -> int:
    selected_tests = args.tests or DEFAULT_SMOKE_TESTS
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    failed: list[str] = []
    for test_name in selected_tests:
        test_path = SRC_DIR / test_name
        if not test_path.exists():
            raise FileNotFoundError(f"Smoke test not found: {test_path}")
        print(f"[smoke] {test_name}")
        result = subprocess.run([sys.executable, str(test_path)], cwd=BACKEND_DIR, env=env, check=False)
        if result.returncode != 0:
            failed.append(test_name)
            if args.fail_fast:
                break
    if failed:
        print(f"[smoke] failed: {failed}", file=sys.stderr)
        return 1
    print(f"[smoke] passed {len(selected_tests)} tests")
    return 0


def cmd_rollout(args: argparse.Namespace) -> int:
    cases = load_cases(Path(args.input))
    if args.limit is not None:
        cases = cases[: args.limit]
    output_path = rollout_cases(
        cases=cases,
        output_path=Path(args.output),
        recursion_limit=args.recursion_limit,
    )
    print(f"rolled out {len(cases)} cases -> {output_path}")
    return 0


def cmd_build_pairwise(args: argparse.Namespace) -> int:
    rollout_records = load_rollout_records(Path(args.input))
    preferences = build_pairwise_preferences(rollout_records)
    output_path = save_jsonl(preferences, Path(args.output))
    print(f"built {len(preferences)} pairwise samples -> {output_path}")
    return 0


def cmd_eval_orchestration(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(SCRIPTS_DIR))
    from evaluate_orchestration_policies import (  # noqa: PLC0415
        build_markdown_report,
        compare_rollout_summaries,
        evaluate_ranker,
        evaluate_reward_model,
        summarize_rollouts,
    )
    from rl.orchestration_alignment import SupervisorActionRanker  # noqa: PLC0415
    from rl.reward_model_scorer import SupervisorRewardModelScorer  # noqa: PLC0415

    result: dict[str, Any] = {}
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
        result["ranker_eval"] = evaluate_ranker(pairwise_records, SupervisorActionRanker.load(args.ranker))
    if pairwise_records and args.reward_model:
        result["reward_model_eval"] = evaluate_reward_model(
            pairwise_records,
            SupervisorRewardModelScorer.load(args.reward_model),
        )
    if not result:
        raise ValueError("No evaluation target provided.")

    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved evaluation json -> {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_report(result), encoding="utf-8")
        print(f"saved evaluation report -> {report_path}")
    return 0


def cmd_backtest_2025(args: argparse.Namespace) -> int:
    actual_outcomes = load_actual_outcomes_csv(args.actual_outcomes, encoding=args.encoding)
    records = _read_jsonl(Path(args.plans_jsonl))
    results: list[PlanBacktestResult] = []
    for record in records:
        case_id, user_rank, plan, preferred_majors, blacklist_majors = _load_plan_record(record)
        results.append(
            run_plan_backtest(
                plan=plan,
                actual_outcomes=actual_outcomes,
                user_rank=user_rank,
                preferred_majors=preferred_majors,
                blacklist_majors=blacklist_majors,
                case_id=case_id,
            )
        )

    summary = summarize_backtests(results)
    if args.results_jsonl:
        _write_jsonl(Path(args.results_jsonl), [result.model_dump() for result in results])
        print(f"saved per-case backtest results -> {args.results_jsonl}")
    if args.output:
        _write_json(Path(args.output), summary)
        print(f"saved backtest summary -> {args.output}")
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def cmd_ablate_2025(args: argparse.Namespace) -> int:
    actual_outcomes = load_actual_outcomes_csv(args.actual_outcomes, encoding=args.encoding)
    records = _read_jsonl(Path(args.plans_jsonl))
    result = run_ablation_backtest_records(
        records=records,
        actual_outcomes=actual_outcomes,
        variants=args.variants or DEFAULT_ABLATION_VARIANTS,
    )

    if args.results_jsonl:
        _write_jsonl(Path(args.results_jsonl), result["per_case"])
        print(f"saved per-case ablation results -> {args.results_jsonl}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_ablation_report(result), encoding="utf-8")
        print(f"saved ablation report -> {report_path}")
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved ablation summary -> {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    smoke = subparsers.add_parser("smoke", help="Run stable smoke tests.")
    smoke.add_argument("--tests", nargs="*", help="Optional explicit smoke test filenames.")
    smoke.add_argument("--fail-fast", action="store_true")
    smoke.set_defaults(func=cmd_smoke)

    rollout = subparsers.add_parser("rollout", help="Run supervisor rollouts.")
    rollout.add_argument("--input", default="logs/orchestration_cases.jsonl")
    rollout.add_argument("--output", default="logs/orchestration_rollouts.jsonl")
    rollout.add_argument("--limit", type=int, default=None)
    rollout.add_argument("--recursion-limit", type=int, default=50)
    rollout.set_defaults(func=cmd_rollout)

    pairwise = subparsers.add_parser("build-pairwise", help="Build pairwise preferences from rollouts.")
    pairwise.add_argument("--input", default="logs/orchestration_rollouts.jsonl")
    pairwise.add_argument("--output", default="logs/orchestration_pairwise.jsonl")
    pairwise.set_defaults(func=cmd_build_pairwise)

    evaluate = subparsers.add_parser("eval-orchestration", help="Evaluate rollout or preference artifacts.")
    evaluate.add_argument("--rollouts")
    evaluate.add_argument("--baseline-rollouts")
    evaluate.add_argument("--candidate-rollouts")
    evaluate.add_argument("--pairwise")
    evaluate.add_argument("--ranker")
    evaluate.add_argument("--reward-model")
    evaluate.add_argument("--output")
    evaluate.add_argument("--report-md")
    evaluate.set_defaults(func=cmd_eval_orchestration)

    backtest = subparsers.add_parser("backtest-2025", help="Run post-hoc 2025 volunteer-plan backtests.")
    backtest.add_argument("--actual-outcomes", required=True, help="CSV with actual 2025 group/major outcomes.")
    backtest.add_argument("--plans-jsonl", required=True, help="Frozen plan JSONL.")
    backtest.add_argument("--encoding", default="utf-8-sig")
    backtest.add_argument("--output", help="Summary JSON output path.")
    backtest.add_argument("--results-jsonl", help="Per-case result JSONL output path.")
    backtest.set_defaults(func=cmd_backtest_2025)

    ablate = subparsers.add_parser("ablate-2025", help="Run 2025 full-vs-baseline ablation backtests.")
    ablate.add_argument("--actual-outcomes", required=True, help="CSV with actual 2025 group/major outcomes.")
    ablate.add_argument("--plans-jsonl", required=True, help="Frozen plan JSONL with candidate_rows for baselines.")
    ablate.add_argument("--encoding", default="utf-8-sig")
    ablate.add_argument(
        "--variants",
        nargs="*",
        default=None,
        help=f"Variants to compare. Default: {' '.join(DEFAULT_ABLATION_VARIANTS)}",
    )
    ablate.add_argument("--output", help="Ablation summary JSON output path.")
    ablate.add_argument("--results-jsonl", help="Per-case ablation result JSONL output path.")
    ablate.add_argument("--report-md", help="Markdown ablation report output path.")
    ablate.set_defaults(func=cmd_ablate_2025)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

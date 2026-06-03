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
from evaluation.calibration import build_markdown_calibration_report, run_quant_calibration_records
from evaluation.delivery_bundle import build_delivery_bundle
from evaluation.expectation_packet import build_expectation_packet, build_markdown_expectation_packet
from evaluation.improvement_audit import build_improvement_audit, build_markdown_improvement_audit
from evaluation.intake_audit import build_intake_audit, build_markdown_intake_audit
from evaluation.quant_tuning import build_markdown_quant_tuning_report, tune_quant_probability_blends
from evaluation.report_quality import audit_report_quality, build_markdown_report_quality_audit
from evaluation.schemas import PlanBacktestResult
from models.game_matrix import VolunteerPlan
from models.user_profile import UserProfile
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
    "test_import_boundaries_smoke.py",
    "test_encoding_smoke.py",
    "test_backend_api_status_smoke.py",
    "test_prediction_data_boundary_smoke.py",
    "test_user_profile_null_defaults_smoke.py",
    "test_game_agent_score_bounds_smoke.py",
    "test_report_decision_evidence_smoke.py",
    "test_quant_scorecard_smoke.py",
    "test_tradeoff_policy_smoke.py",
    "test_volunteer_plan_schema_smoke.py",
    "test_first_hit_prefix_smoke.py",
    "test_multi_agent_deliberation_smoke.py",
    "test_agent_protocol_smoke.py",
    "test_supervisor_policy_smoke.py",
    "test_orchestration_data_pipeline_smoke.py",
    "test_orchestration_trl_utils_smoke.py",
    "test_backtest_2025_smoke.py",
    "test_quant_calibration_smoke.py",
    "test_quant_tuning_smoke.py",
    "test_improvement_audit_smoke.py",
    "test_intake_audit_smoke.py",
    "test_report_quality_smoke.py",
    "test_expectation_packet_smoke.py",
    "test_delivery_bundle_smoke.py",
    "test_ablation_2025_smoke.py",
    "test_market_evidence_smoke.py",
    "test_market_simulation_smoke.py",
    "test_prefix_optimizer_smoke.py",
    "test_enrollment_diff_smoke.py",
    "test_plan_change_signals_smoke.py",
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


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def cmd_quant_calibrate_2025(args: argparse.Namespace) -> int:
    actual_outcomes = load_actual_outcomes_csv(args.actual_outcomes, encoding=args.encoding)
    records = _read_jsonl(Path(args.plans_jsonl))
    result = run_quant_calibration_records(
        records=records,
        actual_outcomes=actual_outcomes,
    )

    if args.choice_rows_jsonl:
        _write_jsonl(Path(args.choice_rows_jsonl), result["choice_rows"])
        print(f"saved choice-level calibration rows -> {args.choice_rows_jsonl}")
    export_result = {key: value for key, value in result.items() if key != "choice_rows"}
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_calibration_report(result), encoding="utf-8")
        print(f"saved quant calibration report -> {report_path}")
    if args.output:
        _write_json(Path(args.output), export_result)
        print(f"saved quant calibration summary -> {args.output}")
    else:
        print(json.dumps(export_result, ensure_ascii=False, indent=2))
    return 0


def cmd_quant_tune(args: argparse.Namespace) -> int:
    choice_rows = _read_jsonl(Path(args.choice_rows_jsonl))
    result = tune_quant_probability_blends(
        choice_rows=choice_rows,
        step=args.step,
        min_prob_weight=args.min_prob_weight,
        holdout_fraction=args.holdout_fraction,
        top_k=args.top_k,
    )
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_quant_tuning_report(result), encoding="utf-8")
        print(f"saved quant tuning report -> {report_path}")
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved quant tuning summary -> {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_improvement_audit(args: argparse.Namespace) -> int:
    backtest_summary = _read_json(Path(args.backtest_summary)) if args.backtest_summary else None
    calibration_summary = _read_json(Path(args.calibration_summary)) if args.calibration_summary else None
    ablation_summary = _read_json(Path(args.ablation_summary)) if args.ablation_summary else None
    tuning_summary = _read_json(Path(args.tuning_summary)) if args.tuning_summary else None
    if not any((backtest_summary, calibration_summary, ablation_summary, tuning_summary)):
        raise ValueError(
            "Provide at least one of --backtest-summary, --calibration-summary, "
            "--ablation-summary, or --tuning-summary."
        )

    result = build_improvement_audit(
        backtest_summary=backtest_summary,
        calibration_summary=calibration_summary,
        ablation_summary=ablation_summary,
        tuning_summary=tuning_summary,
    )
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_improvement_audit(result), encoding="utf-8")
        print(f"saved improvement audit report -> {report_path}")
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved improvement audit summary -> {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_report_quality_audit(args: argparse.Namespace) -> int:
    if args.report_json:
        payload = _read_json(Path(args.report_json))
    else:
        payload = Path(args.report_md).read_text(encoding="utf-8")
    result = audit_report_quality(payload)
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved report quality audit summary -> {args.output}")
    if args.audit_md:
        audit_path = Path(args.audit_md)
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(build_markdown_report_quality_audit(result), encoding="utf-8")
        print(f"saved report quality audit report -> {audit_path}")
    if not args.output and not args.audit_md:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_expectation_packet(args: argparse.Namespace) -> int:
    profile = UserProfile(**_read_json(Path(args.profile_json)))
    packet = build_expectation_packet(profile)
    if args.output:
        _write_json(Path(args.output), packet)
        print(f"saved expectation packet json -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_expectation_packet(packet), encoding="utf-8")
        print(f"saved expectation packet markdown -> {report_path}")
    if not args.output and not args.report_md:
        print(json.dumps(packet, ensure_ascii=False, indent=2))
    return 0


def cmd_intake_audit(args: argparse.Namespace) -> int:
    profile = UserProfile(**_read_json(Path(args.profile_json)))
    result = build_intake_audit(profile)
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved intake audit json -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_intake_audit(result), encoding="utf-8")
        print(f"saved intake audit markdown -> {report_path}")
    if not args.output and not args.report_md:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_delivery_bundle(args: argparse.Namespace) -> int:
    profile = UserProfile(**_read_json(Path(args.profile_json)))
    if args.report_json:
        report_payload = _read_json(Path(args.report_json))
    else:
        report_payload = Path(args.report_md).read_text(encoding="utf-8")
    manifest = build_delivery_bundle(
        profile=profile,
        report_payload=report_payload,
        output_dir=Path(args.output_dir),
        case_id=args.case_id or "",
    )
    print(f"saved delivery bundle -> {args.output_dir}")
    print(json.dumps({key: manifest[key] for key in ("case_id", "status")}, ensure_ascii=False))
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

    calibrate = subparsers.add_parser(
        "quant-calibrate-2025",
        help="Evaluate prediction calibration for frozen quant-scored plans.",
    )
    calibrate.add_argument("--actual-outcomes", required=True, help="CSV with actual 2025 group/major outcomes.")
    calibrate.add_argument("--plans-jsonl", required=True, help="Frozen plan JSONL.")
    calibrate.add_argument("--encoding", default="utf-8-sig")
    calibrate.add_argument("--output", help="Calibration summary JSON output path.")
    calibrate.add_argument("--choice-rows-jsonl", help="Choice-level calibration rows JSONL output path.")
    calibrate.add_argument("--report-md", help="Markdown calibration report output path.")
    calibrate.set_defaults(func=cmd_quant_calibrate_2025)

    tune = subparsers.add_parser(
        "quant-tune",
        help="Search offline probability/quant-score blend weights from calibration rows.",
    )
    tune.add_argument("--choice-rows-jsonl", required=True, help="JSONL produced by quant-calibrate-2025.")
    tune.add_argument("--step", type=float, default=0.20, help="Grid step for feature weights.")
    tune.add_argument("--min-prob-weight", type=float, default=0.40, help="Minimum weight kept on admission probability.")
    tune.add_argument("--holdout-fraction", type=float, default=0.25, help="Case-level holdout fraction for validation.")
    tune.add_argument("--top-k", type=int, default=10)
    tune.add_argument("--output", help="Quant tuning JSON output path.")
    tune.add_argument("--report-md", help="Markdown quant tuning report output path.")
    tune.set_defaults(func=cmd_quant_tune)

    audit = subparsers.add_parser(
        "improvement-audit",
        help="Convert experiment metrics into prioritized self-improvement tasks.",
    )
    audit.add_argument("--backtest-summary", help="JSON produced by backtest-2025 --output.")
    audit.add_argument("--calibration-summary", help="JSON produced by quant-calibrate-2025 --output.")
    audit.add_argument("--ablation-summary", help="JSON produced by ablate-2025 --output.")
    audit.add_argument("--tuning-summary", help="JSON produced by quant-tune --output.")
    audit.add_argument("--output", help="Improvement audit JSON output path.")
    audit.add_argument("--report-md", help="Markdown improvement audit output path.")
    audit.set_defaults(func=cmd_improvement_audit)

    report_audit = subparsers.add_parser(
        "report-quality-audit",
        help="Audit a generated report for agency-grade delivery completeness.",
    )
    source = report_audit.add_mutually_exclusive_group(required=True)
    source.add_argument("--report-md", help="Generated report Markdown path.")
    source.add_argument("--report-json", help="ReportDraft JSON path.")
    report_audit.add_argument("--output", help="Report-quality audit JSON output path.")
    report_audit.add_argument("--audit-md", help="Markdown report-quality audit output path.")
    report_audit.set_defaults(func=cmd_report_quality_audit)

    expectation = subparsers.add_parser(
        "expectation-packet",
        help="Generate a pre-recommendation expectation and constraint confirmation packet.",
    )
    expectation.add_argument("--profile-json", required=True, help="UserProfile JSON path.")
    expectation.add_argument("--output", help="Expectation packet JSON output path.")
    expectation.add_argument("--report-md", help="Expectation packet Markdown output path.")
    expectation.set_defaults(func=cmd_expectation_packet)

    intake = subparsers.add_parser(
        "intake-audit",
        help="Audit whether a profile has enough intake information before recommendation.",
    )
    intake.add_argument("--profile-json", required=True, help="UserProfile JSON path.")
    intake.add_argument("--output", help="Intake audit JSON output path.")
    intake.add_argument("--report-md", help="Intake audit Markdown output path.")
    intake.set_defaults(func=cmd_intake_audit)

    bundle = subparsers.add_parser(
        "delivery-bundle",
        help="Build a client-facing delivery bundle with expectation packet and report audit.",
    )
    bundle.add_argument("--profile-json", required=True, help="UserProfile JSON path.")
    report_source = bundle.add_mutually_exclusive_group(required=True)
    report_source.add_argument("--report-md", help="Generated report Markdown path.")
    report_source.add_argument("--report-json", help="ReportDraft JSON path.")
    bundle.add_argument("--output-dir", required=True, help="Directory to write delivery bundle artifacts.")
    bundle.add_argument("--case-id", default="", help="Optional case id for the bundle manifest.")
    bundle.set_defaults(func=cmd_delivery_bundle)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

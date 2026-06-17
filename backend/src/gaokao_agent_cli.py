"""Unified command-line entrypoint for GaokaoAgent experiments and checks."""

from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable

from evaluation.ablation_2025 import (
    DEFAULT_ABLATION_VARIANTS,
    QUANT_TUNED_SHADOW_VARIANT,
    build_markdown_ablation_report,
    run_ablation_backtest_records,
)
from evaluation.backtest_2025 import load_actual_outcomes_csv, run_plan_backtest, summarize_backtests
from evaluation.benchmark_coverage import (
    audit_benchmark_coverage,
    build_coverage_repair_plan,
    build_markdown_benchmark_coverage,
    build_markdown_benchmark_coverage_comparison,
    build_markdown_coverage_repair_plan,
    compare_benchmark_coverage,
)
from evaluation.calibration import build_markdown_calibration_report, run_quant_calibration_records
from evaluation.claim_portfolio import (
    build_claim_readiness_portfolio,
    build_markdown_claim_readiness_portfolio,
)
from evaluation.claim_readiness import build_claim_readiness, build_markdown_claim_readiness
from evaluation.delivery_bundle import build_delivery_bundle
from evaluation.delivery_portfolio import audit_delivery_portfolio, build_markdown_delivery_portfolio_audit
from evaluation.expectation_packet import build_expectation_packet, build_markdown_expectation_packet
from evaluation.failure_mining import mine_ablation_failure_deltas, mine_backtest_failures
from evaluation.experiment_leaderboard import (
    build_markdown_quant_lab_leaderboard,
    build_quant_lab_leaderboard,
)
from evaluation.improvement_audit import build_improvement_audit, build_markdown_improvement_audit
from evaluation.intake_audit import build_intake_audit, build_markdown_intake_audit
from evaluation.next_iteration_plan import build_markdown_next_iteration_plan, build_next_iteration_plan
from evaluation.parallel_worlds import build_markdown_parallel_world_analysis, run_parallel_world_analysis
from evaluation.plan_quality_audit import audit_plan_quality, build_markdown_plan_quality_audit
from evaluation.quant_lab import (
    build_artifact_manifest,
    build_markdown_quant_lab_report,
    build_quant_lab_experiment,
)
from evaluation.quant_tuning import build_markdown_quant_tuning_report, tune_quant_probability_blends
from evaluation.replay_queue import build_failure_replay_queue, build_markdown_replay_queue
from evaluation.report_quality import audit_report_quality, build_markdown_report_quality_audit
from evaluation.research_evidence_audit import (
    audit_research_evidence_cards,
    build_markdown_research_evidence_audit,
)
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
    "test_deep_research_evidence_smoke.py",
    "test_research_evidence_audit_smoke.py",
    "test_supervisor_policy_smoke.py",
    "test_orchestration_data_pipeline_smoke.py",
    "test_orchestration_trl_utils_smoke.py",
    "test_backtest_2025_smoke.py",
    "test_quant_calibration_smoke.py",
    "test_quant_tuning_smoke.py",
    "test_benchmark_coverage_smoke.py",
    "test_claim_readiness_smoke.py",
    "test_claim_portfolio_smoke.py",
    "test_quant_lab_smoke.py",
    "test_experiment_leaderboard_smoke.py",
    "test_failure_mining_smoke.py",
    "test_replay_queue_smoke.py",
    "test_improvement_audit_smoke.py",
    "test_next_iteration_plan_smoke.py",
    "test_intake_audit_smoke.py",
    "test_parallel_worlds_smoke.py",
    "test_plan_quality_audit_smoke.py",
    "test_report_quality_smoke.py",
    "test_expectation_packet_smoke.py",
    "test_delivery_bundle_smoke.py",
    "test_delivery_portfolio_smoke.py",
    "test_agency_command_center_smoke.py",
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


def _extract_research_evidence_cards(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    cards = payload.get("research_evidence_cards")
    if cards is None:
        cards = payload.get("evidence_cards")
    if cards is None and isinstance(payload.get("controlled_signals"), dict):
        cards = payload.get("controlled_signals", {}).get("feature_cards")
    if isinstance(cards, list):
        return [dict(item) for item in cards if isinstance(item, dict)]
    return []


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
    tuning_summary = _read_json(Path(args.tuning_summary)) if args.tuning_summary else None
    quant_shadow_weights = _extract_quant_shadow_weights(tuning_summary) if tuning_summary else None
    result = run_ablation_backtest_records(
        records=records,
        actual_outcomes=actual_outcomes,
        variants=args.variants or DEFAULT_ABLATION_VARIANTS,
        quant_shadow_weights=quant_shadow_weights,
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


def _extract_quant_shadow_weights(tuning_summary: dict[str, Any]) -> dict[str, float]:
    weights = ((tuning_summary.get("best") or {}).get("weights") or {})
    if not weights:
        raise ValueError("Tuning summary does not contain `best.weights` for quant shadow ablation.")
    return {str(key): float(value) for key, value in weights.items()}


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


def _read_research_evidence_paths(paths: list[str] | None, patterns: list[str] | None) -> list[Path]:
    selected: list[Path] = []
    for path in paths or []:
        selected.append(Path(path))
    for pattern in patterns or []:
        selected.extend(Path(match) for match in sorted(glob.glob(pattern)))
    unique: dict[str, Path] = {}
    for path in selected:
        unique[str(path)] = path
    return list(unique.values())


def cmd_research_evidence_audit(args: argparse.Namespace) -> int:
    paths = _read_research_evidence_paths(args.evidence_json, args.evidence_glob)
    if not paths:
        raise ValueError("Provide at least one --evidence-json or --evidence-glob.")
    cards: list[dict[str, Any]] = []
    for path in paths:
        cards.extend(_extract_research_evidence_cards(_read_json(path)))
    result = audit_research_evidence_cards(cards, scope_terms=args.scope_term)
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved research evidence audit -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_research_evidence_audit(result), encoding="utf-8")
        print(f"saved research evidence audit report -> {report_path}")
    if not args.output and not args.report_md:
        print(json.dumps(result, ensure_ascii=False, indent=2))
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


def _read_optional_json(path: str | None) -> dict[str, Any] | None:
    return _read_json(Path(path)) if path else None


def cmd_quant_lab_register(args: argparse.Namespace) -> int:
    artifacts = build_artifact_manifest(
        {
            "plans_jsonl": args.plans_jsonl,
            "actual_outcomes": args.actual_outcomes,
            "backtest_summary": args.backtest_summary,
            "backtest_results_jsonl": args.backtest_results_jsonl,
            "calibration_summary": args.calibration_summary,
            "tuning_summary": args.tuning_summary,
            "ablation_summary": args.ablation_summary,
            "ablation_results_jsonl": args.ablation_results_jsonl,
            "improvement_audit": args.improvement_audit,
            "failure_replay_queue_jsonl": args.failure_replay_queue_jsonl,
            "failure_replay_queue_summary": args.failure_replay_queue_summary,
            "benchmark_coverage": args.benchmark_coverage,
        }
    )
    backtest_results = _read_jsonl(Path(args.backtest_results_jsonl)) if args.backtest_results_jsonl else None
    ablation_results = _read_jsonl(Path(args.ablation_results_jsonl)) if args.ablation_results_jsonl else None
    manifest = build_quant_lab_experiment(
        experiment_id=args.experiment_id,
        config={
            "notes": args.notes or "",
            "source": "gaokao_agent_cli.quant-lab-register",
        },
        artifacts=artifacts,
        backtest_summary=_read_optional_json(args.backtest_summary),
        calibration_summary=_read_optional_json(args.calibration_summary),
        tuning_summary=_read_optional_json(args.tuning_summary),
        ablation_summary=_read_optional_json(args.ablation_summary),
        improvement_audit=_read_optional_json(args.improvement_audit),
        failure_mining=mine_backtest_failures(backtest_results) if backtest_results else None,
        ablation_failure_deltas=mine_ablation_failure_deltas(ablation_results) if ablation_results else None,
        replay_queue_summary=_read_optional_json(args.failure_replay_queue_summary),
        benchmark_coverage=_read_optional_json(args.benchmark_coverage),
    )
    if args.output:
        _write_json(Path(args.output), manifest)
        print(f"saved quant lab manifest -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_quant_lab_report(manifest), encoding="utf-8")
        print(f"saved quant lab report -> {report_path}")
    if not args.output and not args.report_md:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def cmd_benchmark_coverage(args: argparse.Namespace) -> int:
    records = _read_jsonl(Path(args.plans_jsonl))
    result = audit_benchmark_coverage(
        records,
        min_cases_per_tag=args.min_cases_per_tag,
        min_cases_per_pair=args.min_cases_per_pair,
    )
    repair_plan = build_coverage_repair_plan(result, max_specs=args.repair_max_specs)
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved benchmark coverage audit -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_benchmark_coverage(result), encoding="utf-8")
        print(f"saved benchmark coverage report -> {report_path}")
    if args.repair_plan_output:
        _write_json(Path(args.repair_plan_output), repair_plan)
        print(f"saved benchmark coverage repair plan -> {args.repair_plan_output}")
    if args.repair_plan_md:
        report_path = Path(args.repair_plan_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_coverage_repair_plan(repair_plan), encoding="utf-8")
        print(f"saved benchmark coverage repair plan report -> {report_path}")
    if not any((args.output, args.report_md, args.repair_plan_output, args.repair_plan_md)):
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_benchmark_coverage_compare(args: argparse.Namespace) -> int:
    before = _read_json(Path(args.before))
    after = _read_json(Path(args.after))
    result = compare_benchmark_coverage(before, after)
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved benchmark coverage comparison -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_benchmark_coverage_comparison(result), encoding="utf-8")
        print(f"saved benchmark coverage comparison report -> {report_path}")
    if not args.output and not args.report_md:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_build_replay_queue(args: argparse.Namespace) -> int:
    if not args.backtest_results_jsonl and not args.ablation_results_jsonl:
        raise ValueError("Provide --backtest-results-jsonl, --ablation-results-jsonl, or both.")
    records = _read_jsonl(Path(args.plans_jsonl))
    backtest_results = _read_jsonl(Path(args.backtest_results_jsonl)) if args.backtest_results_jsonl else None
    ablation_results = _read_jsonl(Path(args.ablation_results_jsonl)) if args.ablation_results_jsonl else None
    result = build_failure_replay_queue(
        records,
        failure_mining=mine_backtest_failures(backtest_results, top_k=args.top_k) if backtest_results else None,
        ablation_failure_deltas=mine_ablation_failure_deltas(ablation_results, top_k=args.top_k)
        if ablation_results
        else None,
        top_k=args.top_k,
        include_ablation_regressions=not args.no_ablation_regressions,
    )
    _write_jsonl(Path(args.output), result["items"])
    print(f"saved failure replay queue -> {args.output}")
    if args.summary_json:
        _write_json(Path(args.summary_json), result)
        print(f"saved failure replay queue summary -> {args.summary_json}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_replay_queue(result), encoding="utf-8")
        print(f"saved failure replay queue report -> {report_path}")
    return 0


def _read_quant_lab_manifest_paths(paths: list[str] | None, patterns: list[str] | None) -> list[Path]:
    selected: list[Path] = []
    for path in paths or []:
        selected.append(Path(path))
    for pattern in patterns or []:
        selected.extend(Path(match) for match in sorted(glob.glob(pattern)))
    unique: dict[str, Path] = {}
    for path in selected:
        unique[str(path)] = path
    return list(unique.values())


def _read_claim_readiness_paths(paths: list[str] | None, patterns: list[str] | None) -> list[Path]:
    selected: list[Path] = []
    for path in paths or []:
        selected.append(Path(path))
    for pattern in patterns or []:
        selected.extend(Path(match) for match in sorted(glob.glob(pattern)))
    unique: dict[str, Path] = {}
    for path in selected:
        unique[str(path)] = path
    return list(unique.values())


def cmd_quant_lab_leaderboard(args: argparse.Namespace) -> int:
    paths = _read_quant_lab_manifest_paths(args.manifest, args.manifest_glob)
    if not paths:
        raise ValueError("Provide at least one --manifest or --manifest-glob.")
    manifests = [_read_json(path) for path in paths]
    result = build_quant_lab_leaderboard(
        manifests,
        baseline_experiment_id=args.baseline_experiment_id,
    )
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved quant lab leaderboard -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_quant_lab_leaderboard(result), encoding="utf-8")
        print(f"saved quant lab leaderboard report -> {report_path}")
    if not args.output and not args.report_md:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_claim_readiness(args: argparse.Namespace) -> int:
    manifest = _read_json(Path(args.quant_lab_manifest))
    result = build_claim_readiness(manifest)
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved claim readiness audit -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_claim_readiness(result), encoding="utf-8")
        print(f"saved claim readiness report -> {report_path}")
    if not args.output and not args.report_md:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_claim_readiness_portfolio(args: argparse.Namespace) -> int:
    paths = _read_claim_readiness_paths(args.claim_json, args.claim_glob)
    if not paths:
        raise ValueError("Provide at least one --claim-json or --claim-glob.")
    reports = [_read_json(path) for path in paths]
    result = build_claim_readiness_portfolio(reports)
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved claim readiness portfolio -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_claim_readiness_portfolio(result), encoding="utf-8")
        print(f"saved claim readiness portfolio report -> {report_path}")
    if not args.output and not args.report_md:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_improvement_audit(args: argparse.Namespace) -> int:
    backtest_summary = _read_json(Path(args.backtest_summary)) if args.backtest_summary else None
    backtest_results = _read_jsonl(Path(args.backtest_results_jsonl)) if args.backtest_results_jsonl else None
    calibration_summary = _read_json(Path(args.calibration_summary)) if args.calibration_summary else None
    ablation_summary = _read_json(Path(args.ablation_summary)) if args.ablation_summary else None
    ablation_results = _read_jsonl(Path(args.ablation_results_jsonl)) if args.ablation_results_jsonl else None
    tuning_summary = _read_json(Path(args.tuning_summary)) if args.tuning_summary else None
    intake_audit = _read_json(Path(args.intake_audit)) if args.intake_audit else None
    plan_quality_audit = _read_json(Path(args.plan_quality_audit)) if args.plan_quality_audit else None
    report_quality_audit = _read_json(Path(args.report_quality_audit)) if args.report_quality_audit else None
    delivery_bundle = _read_json(Path(args.delivery_bundle)) if args.delivery_bundle else None
    delivery_portfolio = _read_json(Path(args.delivery_portfolio)) if args.delivery_portfolio else None
    research_evidence_audit = _read_json(Path(args.research_evidence_audit)) if args.research_evidence_audit else None
    if not any(
        (
            backtest_summary,
            backtest_results,
            calibration_summary,
            ablation_summary,
            ablation_results,
            tuning_summary,
            intake_audit,
            plan_quality_audit,
            report_quality_audit,
            delivery_bundle,
            delivery_portfolio,
            research_evidence_audit,
        )
    ):
        raise ValueError(
            "Provide at least one of --backtest-summary, --backtest-results-jsonl, "
            "--calibration-summary, --ablation-summary, --ablation-results-jsonl, "
            "--tuning-summary, --intake-audit, "
            "--plan-quality-audit, --report-quality-audit, --delivery-bundle, "
            "--delivery-portfolio, or --research-evidence-audit."
        )

    result = build_improvement_audit(
        backtest_summary=backtest_summary,
        calibration_summary=calibration_summary,
        ablation_summary=ablation_summary,
        tuning_summary=tuning_summary,
        intake_audit=intake_audit,
        plan_quality_audit=plan_quality_audit,
        report_quality_audit=report_quality_audit,
        delivery_bundle=delivery_bundle,
        delivery_portfolio=delivery_portfolio,
        research_evidence_audit=research_evidence_audit,
        failure_mining=mine_backtest_failures(backtest_results) if backtest_results else None,
        ablation_failure_deltas=mine_ablation_failure_deltas(ablation_results) if ablation_results else None,
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


def _read_plan_json(path: Path) -> VolunteerPlan:
    payload = _read_json(path)
    if isinstance(payload, dict) and "plan" in payload:
        payload = payload["plan"]
    if isinstance(payload, dict) and "volunteer_plan" in payload:
        payload = payload["volunteer_plan"]
    return VolunteerPlan(**payload)


def cmd_plan_quality_audit(args: argparse.Namespace) -> int:
    plan = _read_plan_json(Path(args.plan_json))
    profile = UserProfile(**_read_json(Path(args.profile_json))) if args.profile_json else None
    result = audit_plan_quality(plan, profile)
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved plan quality audit json -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_plan_quality_audit(result), encoding="utf-8")
        print(f"saved plan quality audit markdown -> {report_path}")
    if not args.output and not args.report_md:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_parallel_worlds(args: argparse.Namespace) -> int:
    plan = _read_plan_json(Path(args.plan_json))
    profile = UserProfile(**_read_json(Path(args.profile_json))) if args.profile_json else None
    result = run_parallel_world_analysis(plan=plan, profile=profile)
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved parallel-world analysis json -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_parallel_world_analysis(result), encoding="utf-8")
        print(f"saved parallel-world analysis markdown -> {report_path}")
    if not args.output and not args.report_md:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_delivery_bundle(args: argparse.Namespace) -> int:
    profile = UserProfile(**_read_json(Path(args.profile_json)))
    plan = _read_plan_json(Path(args.plan_json)) if args.plan_json else None
    if args.report_json:
        report_payload = _read_json(Path(args.report_json))
    else:
        report_payload = Path(args.report_md).read_text(encoding="utf-8")
    manifest = build_delivery_bundle(
        profile=profile,
        report_payload=report_payload,
        output_dir=Path(args.output_dir),
        plan=plan,
        case_id=args.case_id or "",
    )
    print(f"saved delivery bundle -> {args.output_dir}")
    print(json.dumps({key: manifest[key] for key in ("case_id", "status")}, ensure_ascii=False))
    return 0


def _read_delivery_bundle_paths(paths: list[str] | None, globs: list[str] | None) -> list[Path]:
    bundle_paths: list[Path] = []
    for item in paths or []:
        bundle_paths.append(Path(item))
    for pattern in globs or []:
        bundle_paths.extend(Path(match) for match in sorted(glob.glob(pattern)))
    unique: dict[str, Path] = {}
    for path in bundle_paths:
        unique[str(path)] = path
    return list(unique.values())


def cmd_delivery_portfolio_audit(args: argparse.Namespace) -> int:
    paths = _read_delivery_bundle_paths(args.bundle_json, args.bundle_glob)
    if not paths:
        raise ValueError("Provide at least one --bundle-json or --bundle-glob.")
    manifests = [_read_json(path) for path in paths]
    result = audit_delivery_portfolio(manifests)
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved delivery portfolio audit json -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_delivery_portfolio_audit(result), encoding="utf-8")
        print(f"saved delivery portfolio audit markdown -> {report_path}")
    if not args.output and not args.report_md:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_next_iteration_plan(args: argparse.Namespace) -> int:
    improvement_audit = _read_json(Path(args.improvement_audit)) if args.improvement_audit else None
    coverage_repair_plan = _read_json(Path(args.coverage_repair_plan)) if args.coverage_repair_plan else None
    replay_queue_summary = _read_json(Path(args.replay_queue_summary)) if args.replay_queue_summary else None
    claim_readiness_portfolio = (
        _read_json(Path(args.claim_readiness_portfolio))
        if args.claim_readiness_portfolio
        else None
    )
    research_evidence_audit = _read_json(Path(args.research_evidence_audit)) if args.research_evidence_audit else None
    if not any(
        (
            improvement_audit,
            coverage_repair_plan,
            replay_queue_summary,
            claim_readiness_portfolio,
            research_evidence_audit,
        )
    ):
        raise ValueError(
            "Provide at least one audit artifact, such as --improvement-audit "
            "or --coverage-repair-plan."
        )
    source_paths = {
        key: value
        for key, value in {
            "coverage_repair_plan": args.coverage_repair_plan,
            "replay_queue_jsonl": args.replay_queue_jsonl,
            "delivery_bundle_glob": args.delivery_bundle_glob,
        }.items()
        if value
    }
    result = build_next_iteration_plan(
        improvement_audit=improvement_audit,
        coverage_repair_plan=coverage_repair_plan,
        replay_queue_summary=replay_queue_summary,
        claim_readiness_portfolio=claim_readiness_portfolio,
        research_evidence_audit=research_evidence_audit,
        source_paths=source_paths,
    )
    if args.output:
        _write_json(Path(args.output), result)
        print(f"saved next iteration plan json -> {args.output}")
    if args.report_md:
        report_path = Path(args.report_md)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(build_markdown_next_iteration_plan(result), encoding="utf-8")
        print(f"saved next iteration plan markdown -> {report_path}")
    if not args.output and not args.report_md:
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
    ablate.add_argument(
        "--tuning-summary",
        help=(
            "Optional quant-tune JSON. When provided, adds "
            f"`{QUANT_TUNED_SHADOW_VARIANT}` as an offline shadow variant."
        ),
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

    research_audit = subparsers.add_parser(
        "research-evidence-audit",
        help="Audit deep-research evidence cards before quant-feature ingestion.",
    )
    research_audit.add_argument(
        "--evidence-json",
        nargs="*",
        help="JSON file(s) containing research_evidence_cards or a raw card list.",
    )
    research_audit.add_argument(
        "--evidence-glob",
        nargs="*",
        help="Glob pattern(s), such as logs/research/*/research_state.json.",
    )
    research_audit.add_argument(
        "--scope-term",
        nargs="*",
        help="Optional school, major, or group terms used for scoped signal extraction.",
    )
    research_audit.add_argument("--output", help="Research evidence audit JSON output path.")
    research_audit.add_argument("--report-md", help="Research evidence audit Markdown output path.")
    research_audit.set_defaults(func=cmd_research_evidence_audit)

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

    quant_lab = subparsers.add_parser(
        "quant-lab-register",
        help="Register one quant experiment with artifact hashes, metrics, and promotion gates.",
    )
    quant_lab.add_argument("--experiment-id", required=True)
    quant_lab.add_argument("--plans-jsonl", help="Frozen plan JSONL used by the experiment.")
    quant_lab.add_argument("--actual-outcomes", help="Actual outcome CSV used post-hoc.")
    quant_lab.add_argument("--backtest-summary", help="JSON produced by backtest-2025 --output.")
    quant_lab.add_argument("--backtest-results-jsonl", help="JSONL produced by backtest-2025 --results-jsonl.")
    quant_lab.add_argument("--calibration-summary", help="JSON produced by quant-calibrate-2025 --output.")
    quant_lab.add_argument("--tuning-summary", help="JSON produced by quant-tune --output.")
    quant_lab.add_argument("--ablation-summary", help="JSON produced by ablate-2025 --output.")
    quant_lab.add_argument("--ablation-results-jsonl", help="JSONL produced by ablate-2025 --results-jsonl.")
    quant_lab.add_argument("--improvement-audit", help="JSON produced by improvement-audit --output.")
    quant_lab.add_argument("--failure-replay-queue-jsonl", help="JSONL produced by build-replay-queue --output.")
    quant_lab.add_argument("--failure-replay-queue-summary", help="JSON produced by build-replay-queue --summary-json.")
    quant_lab.add_argument("--benchmark-coverage", help="JSON produced by benchmark-coverage --output.")
    quant_lab.add_argument("--notes", default="")
    quant_lab.add_argument("--output", help="QuantLab manifest JSON output path.")
    quant_lab.add_argument("--report-md", help="QuantLab Markdown report output path.")
    quant_lab.set_defaults(func=cmd_quant_lab_register)

    coverage = subparsers.add_parser(
        "benchmark-coverage",
        help="Audit whether frozen benchmark cases cover critical user slices.",
    )
    coverage.add_argument("--plans-jsonl", required=True, help="Frozen plan JSONL to audit.")
    coverage.add_argument("--min-cases-per-tag", type=int, default=2)
    coverage.add_argument("--min-cases-per-pair", type=int, default=1)
    coverage.add_argument("--output", help="Benchmark coverage JSON output path.")
    coverage.add_argument("--report-md", help="Benchmark coverage Markdown output path.")
    coverage.add_argument("--repair-plan-output", help="Coverage repair profile-spec JSON output path.")
    coverage.add_argument("--repair-plan-md", help="Coverage repair Markdown output path.")
    coverage.add_argument("--repair-max-specs", type=int, default=50)
    coverage.set_defaults(func=cmd_benchmark_coverage)

    coverage_compare = subparsers.add_parser(
        "benchmark-coverage-compare",
        help="Compare before/after benchmark coverage audits after repair.",
    )
    coverage_compare.add_argument("--before", required=True, help="Baseline benchmark_coverage.json.")
    coverage_compare.add_argument("--after", required=True, help="Repaired benchmark_coverage.json.")
    coverage_compare.add_argument("--output", help="Coverage comparison JSON output path.")
    coverage_compare.add_argument("--report-md", help="Coverage comparison Markdown output path.")
    coverage_compare.set_defaults(func=cmd_benchmark_coverage_compare)

    replay = subparsers.add_parser(
        "build-replay-queue",
        help="Build a frozen-plan replay queue from backtest failures and ablation regressions.",
    )
    replay.add_argument("--plans-jsonl", required=True, help="Frozen plan JSONL used by the source experiment.")
    replay.add_argument("--backtest-results-jsonl", help="JSONL produced by backtest-2025 --results-jsonl.")
    replay.add_argument("--ablation-results-jsonl", help="JSONL produced by ablate-2025 --results-jsonl.")
    replay.add_argument("--output", required=True, help="Replay queue JSONL output path.")
    replay.add_argument("--summary-json", help="Replay queue summary JSON output path.")
    replay.add_argument("--report-md", help="Replay queue Markdown report output path.")
    replay.add_argument("--top-k", type=int, default=20)
    replay.add_argument("--no-ablation-regressions", action="store_true")
    replay.set_defaults(func=cmd_build_replay_queue)

    leaderboard = subparsers.add_parser(
        "quant-lab-leaderboard",
        help="Compare multiple QuantLab manifests as a research leaderboard.",
    )
    leaderboard.add_argument("--manifest", nargs="*", help="One or more quant_lab_manifest.json paths.")
    leaderboard.add_argument(
        "--manifest-glob",
        nargs="*",
        help="Glob pattern(s), such as logs/experiments/*/quant_lab_manifest.json.",
    )
    leaderboard.add_argument("--baseline-experiment-id", help="Optional experiment id for delta columns.")
    leaderboard.add_argument("--output", help="Leaderboard JSON output path.")
    leaderboard.add_argument("--report-md", help="Leaderboard Markdown output path.")
    leaderboard.set_defaults(func=cmd_quant_lab_leaderboard)

    claim = subparsers.add_parser(
        "claim-readiness",
        help="Audit which public claims a QuantLab experiment can support.",
    )
    claim.add_argument("--quant-lab-manifest", required=True, help="QuantLab manifest JSON path.")
    claim.add_argument("--output", help="Claim readiness JSON output path.")
    claim.add_argument("--report-md", help="Claim readiness Markdown output path.")
    claim.set_defaults(func=cmd_claim_readiness)

    claim_portfolio = subparsers.add_parser(
        "claim-readiness-portfolio",
        help="Aggregate many claim_readiness.json files into public-claim review metrics.",
    )
    claim_portfolio.add_argument("--claim-json", nargs="*", help="One or more claim_readiness.json paths.")
    claim_portfolio.add_argument(
        "--claim-glob",
        nargs="*",
        help="Glob pattern(s), such as logs/experiments/*/claim_readiness.json.",
    )
    claim_portfolio.add_argument("--output", help="Claim-readiness portfolio JSON output path.")
    claim_portfolio.add_argument("--report-md", help="Claim-readiness portfolio Markdown output path.")
    claim_portfolio.set_defaults(func=cmd_claim_readiness_portfolio)

    audit = subparsers.add_parser(
        "improvement-audit",
        help="Convert experiment metrics into prioritized self-improvement tasks.",
    )
    audit.add_argument("--backtest-summary", help="JSON produced by backtest-2025 --output.")
    audit.add_argument("--backtest-results-jsonl", help="JSONL produced by backtest-2025 --results-jsonl.")
    audit.add_argument("--calibration-summary", help="JSON produced by quant-calibrate-2025 --output.")
    audit.add_argument("--ablation-summary", help="JSON produced by ablate-2025 --output.")
    audit.add_argument("--ablation-results-jsonl", help="JSONL produced by ablate-2025 --results-jsonl.")
    audit.add_argument("--tuning-summary", help="JSON produced by quant-tune --output.")
    audit.add_argument("--intake-audit", help="JSON produced by intake-audit --output.")
    audit.add_argument("--plan-quality-audit", help="JSON produced by plan-quality-audit --output.")
    audit.add_argument("--report-quality-audit", help="JSON produced by report-quality-audit --output.")
    audit.add_argument("--delivery-bundle", help="JSON produced by delivery-bundle in the output directory.")
    audit.add_argument("--delivery-portfolio", help="JSON produced by delivery-portfolio-audit --output.")
    audit.add_argument("--research-evidence-audit", help="JSON produced by research-evidence-audit --output.")
    audit.add_argument("--output", help="Improvement audit JSON output path.")
    audit.add_argument("--report-md", help="Markdown improvement audit output path.")
    audit.set_defaults(func=cmd_improvement_audit)

    iteration_plan = subparsers.add_parser(
        "next-iteration-plan",
        help="Build a unified next-run plan from audit and replay artifacts.",
    )
    iteration_plan.add_argument("--improvement-audit", help="JSON produced by improvement-audit --output.")
    iteration_plan.add_argument("--coverage-repair-plan", help="JSON produced by benchmark-coverage repair planning.")
    iteration_plan.add_argument("--replay-queue-summary", help="JSON produced by build-replay-queue --summary-json.")
    iteration_plan.add_argument("--replay-queue-jsonl", help="JSONL produced by build-replay-queue --output.")
    iteration_plan.add_argument(
        "--delivery-bundle-glob",
        help="Glob for delivery_bundle.json files when delivery portfolio work is planned.",
    )
    iteration_plan.add_argument(
        "--claim-readiness-portfolio",
        help="JSON produced by claim-readiness-portfolio --output.",
    )
    iteration_plan.add_argument("--research-evidence-audit", help="JSON produced by research-evidence-audit --output.")
    iteration_plan.add_argument("--output", help="Next-iteration plan JSON output path.")
    iteration_plan.add_argument("--report-md", help="Next-iteration plan Markdown output path.")
    iteration_plan.set_defaults(func=cmd_next_iteration_plan)

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

    plan_audit = subparsers.add_parser(
        "plan-quality-audit",
        help="Audit whether an ordered volunteer plan meets agency-grade structure gates.",
    )
    plan_audit.add_argument("--plan-json", required=True, help="VolunteerPlan JSON path, or a record containing `plan`.")
    plan_audit.add_argument("--profile-json", help="Optional UserProfile JSON path for risk-policy thresholds.")
    plan_audit.add_argument("--output", help="Plan-quality audit JSON output path.")
    plan_audit.add_argument("--report-md", help="Plan-quality audit Markdown output path.")
    plan_audit.set_defaults(func=cmd_plan_quality_audit)

    parallel_worlds = subparsers.add_parser(
        "parallel-worlds",
        help="Stress-test one volunteer plan under explicit parallel-world scenarios.",
    )
    parallel_worlds.add_argument("--plan-json", required=True, help="VolunteerPlan JSON path, or a record containing `plan`.")
    parallel_worlds.add_argument("--profile-json", help="Optional UserProfile JSON path for risk-policy thresholds.")
    parallel_worlds.add_argument("--output", help="Parallel-world analysis JSON output path.")
    parallel_worlds.add_argument("--report-md", help="Parallel-world Markdown output path.")
    parallel_worlds.set_defaults(func=cmd_parallel_worlds)

    bundle = subparsers.add_parser(
        "delivery-bundle",
        help="Build a client-facing delivery bundle with expectation packet and report audit.",
    )
    bundle.add_argument("--profile-json", required=True, help="UserProfile JSON path.")
    report_source = bundle.add_mutually_exclusive_group(required=True)
    report_source.add_argument("--report-md", help="Generated report Markdown path.")
    report_source.add_argument("--report-json", help="ReportDraft JSON path.")
    bundle.add_argument("--plan-json", help="VolunteerPlan JSON path, or a record containing `plan`.")
    bundle.add_argument("--output-dir", required=True, help="Directory to write delivery bundle artifacts.")
    bundle.add_argument("--case-id", default="", help="Optional case id for the bundle manifest.")
    bundle.set_defaults(func=cmd_delivery_bundle)

    portfolio = subparsers.add_parser(
        "delivery-portfolio-audit",
        help="Aggregate many delivery_bundle.json files into service-quality metrics.",
    )
    portfolio.add_argument("--bundle-json", nargs="*", help="One or more delivery_bundle.json paths.")
    portfolio.add_argument("--bundle-glob", nargs="*", help="Glob pattern(s) such as logs/delivery_*/delivery_bundle.json.")
    portfolio.add_argument("--output", help="Delivery portfolio audit JSON output path.")
    portfolio.add_argument("--report-md", help="Delivery portfolio Markdown output path.")
    portfolio.set_defaults(func=cmd_delivery_portfolio_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

"""Run the standard GaokaoAgent experiment suite from one script."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BACKEND_DIR / "src"
CLI = SRC_DIR / "gaokao_agent_cli.py"


def _run(args: list[str], *, dry_run: bool = False) -> int:
    cmd = [sys.executable, str(CLI), *args]
    print("+ " + " ".join(str(part) for part in cmd))
    if dry_run:
        return 0
    return subprocess.run(cmd, cwd=BACKEND_DIR, check=False).returncode


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="logs/experiments/latest")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--cases", help="Optional orchestration case JSONL.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--actual-outcomes", help="Optional 2025 actual outcome CSV.")
    parser.add_argument("--plans-jsonl", help="Optional frozen plan JSONL for 2025 backtest.")
    parser.add_argument(
        "--run-ablation",
        action="store_true",
        help="Also run full-vs-baseline 2025 ablations. Frozen records must include candidate_rows and user_profile.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--experiment-id", help="Optional stable QuantLab experiment id.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    experiment_id = args.experiment_id or output_dir.name or "latest"
    manifest: dict[str, Any] = {
        "output_dir": str(output_dir),
        "experiment_id": experiment_id,
        "stages": [],
    }
    benchmark_coverage = output_dir / "benchmark_coverage.json"
    benchmark_coverage_report = output_dir / "benchmark_coverage.md"
    benchmark_coverage_repair = output_dir / "benchmark_coverage_repair_plan.json"
    benchmark_coverage_repair_report = output_dir / "benchmark_coverage_repair_plan.md"

    def run_stage(name: str, cli_args: list[str]) -> int:
        status = _run(cli_args, dry_run=args.dry_run)
        manifest["stages"].append({"name": name, "args": cli_args, "status": status})
        return status

    if not args.skip_smoke:
        status = run_stage("smoke", ["smoke", "--fail-fast"])
        if status != 0:
            _write_manifest(output_dir / "manifest.json", manifest)
            return status

    if args.cases:
        rollout_path = output_dir / "orchestration_rollouts.jsonl"
        pairwise_path = output_dir / "orchestration_pairwise.jsonl"
        eval_json = output_dir / "orchestration_eval.json"
        eval_md = output_dir / "orchestration_eval.md"
        rollout_args = [
            "rollout",
            "--input",
            args.cases,
            "--output",
            str(rollout_path),
        ]
        if args.limit is not None:
            rollout_args.extend(["--limit", str(args.limit)])
        for name, cli_args in [
            ("rollout", rollout_args),
            ("build_pairwise", ["build-pairwise", "--input", str(rollout_path), "--output", str(pairwise_path)]),
            (
                "eval_orchestration",
                [
                    "eval-orchestration",
                    "--rollouts",
                    str(rollout_path),
                    "--pairwise",
                    str(pairwise_path),
                    "--output",
                    str(eval_json),
                    "--report-md",
                    str(eval_md),
                ],
            ),
        ]:
            status = run_stage(name, cli_args)
            if status != 0:
                _write_manifest(output_dir / "manifest.json", manifest)
                return status

    if args.plans_jsonl:
        status = run_stage(
            "benchmark_coverage",
            [
                "benchmark-coverage",
                "--plans-jsonl",
                args.plans_jsonl,
                "--output",
                str(benchmark_coverage),
                "--report-md",
                str(benchmark_coverage_report),
                "--repair-plan-output",
                str(benchmark_coverage_repair),
                "--repair-plan-md",
                str(benchmark_coverage_repair_report),
            ],
        )
        if status != 0:
            _write_manifest(output_dir / "manifest.json", manifest)
            return status

    if args.actual_outcomes and args.plans_jsonl:
        backtest_summary = output_dir / "backtest_2025_summary.json"
        backtest_results = output_dir / "backtest_2025_results.jsonl"
        calibration_summary = output_dir / "quant_calibration_summary.json"
        calibration_choices = output_dir / "quant_calibration_choices.jsonl"
        tuning_summary = output_dir / "quant_tuning_summary.json"
        ablation_summary = output_dir / "ablation_2025_summary.json"
        ablation_results = output_dir / "ablation_2025_results.jsonl"
        replay_queue = output_dir / "failure_replay_queue.jsonl"
        replay_summary = output_dir / "failure_replay_queue.json"
        replay_report = output_dir / "failure_replay_queue.md"
        quant_lab_manifest = output_dir / "quant_lab_manifest.json"
        quant_lab_report = output_dir / "quant_lab_report.md"
        claim_readiness = output_dir / "claim_readiness.json"
        claim_readiness_report = output_dir / "claim_readiness.md"
        claim_readiness_portfolio = output_dir / "claim_readiness_portfolio.json"
        claim_readiness_portfolio_report = output_dir / "claim_readiness_portfolio.md"
        quant_lab_leaderboard = output_dir / "quant_lab_leaderboard.json"
        quant_lab_leaderboard_report = output_dir / "quant_lab_leaderboard.md"
        status = run_stage(
            "backtest_2025",
            [
                "backtest-2025",
                "--actual-outcomes",
                args.actual_outcomes,
                "--plans-jsonl",
                args.plans_jsonl,
                "--output",
                str(backtest_summary),
                "--results-jsonl",
                str(backtest_results),
            ],
        )
        if status != 0:
            _write_manifest(output_dir / "manifest.json", manifest)
            return status

        status = run_stage(
            "quant_calibration_2025",
            [
                "quant-calibrate-2025",
                "--actual-outcomes",
                args.actual_outcomes,
                "--plans-jsonl",
                args.plans_jsonl,
                "--output",
                str(calibration_summary),
                "--choice-rows-jsonl",
                str(calibration_choices),
                "--report-md",
                str(output_dir / "quant_calibration_report.md"),
            ],
        )
        if status != 0:
            _write_manifest(output_dir / "manifest.json", manifest)
            return status

        status = run_stage(
            "quant_tuning",
            [
                "quant-tune",
                "--choice-rows-jsonl",
                str(calibration_choices),
                "--output",
                str(tuning_summary),
                "--report-md",
                str(output_dir / "quant_tuning_report.md"),
            ],
        )
        if status != 0:
            _write_manifest(output_dir / "manifest.json", manifest)
            return status

        if args.run_ablation:
            status = run_stage(
                "ablation_2025",
                [
                    "ablate-2025",
                    "--actual-outcomes",
                    args.actual_outcomes,
                    "--plans-jsonl",
                    args.plans_jsonl,
                    "--output",
                    str(ablation_summary),
                    "--results-jsonl",
                    str(ablation_results),
                    "--report-md",
                    str(output_dir / "ablation_2025_report.md"),
                    "--tuning-summary",
                    str(tuning_summary),
                ],
            )
            if status != 0:
                _write_manifest(output_dir / "manifest.json", manifest)
                return status

        audit_args = [
            "improvement-audit",
            "--backtest-summary",
            str(backtest_summary),
            "--backtest-results-jsonl",
            str(backtest_results),
            "--calibration-summary",
            str(calibration_summary),
            "--tuning-summary",
            str(tuning_summary),
            "--output",
            str(output_dir / "improvement_audit.json"),
            "--report-md",
            str(output_dir / "improvement_audit.md"),
        ]
        if args.run_ablation:
            audit_args.extend([
                "--ablation-summary",
                str(ablation_summary),
                "--ablation-results-jsonl",
                str(ablation_results),
            ])
        status = run_stage("improvement_audit", audit_args)
        if status != 0:
            _write_manifest(output_dir / "manifest.json", manifest)
            return status

        replay_args = [
            "build-replay-queue",
            "--plans-jsonl",
            args.plans_jsonl,
            "--backtest-results-jsonl",
            str(backtest_results),
            "--output",
            str(replay_queue),
            "--summary-json",
            str(replay_summary),
            "--report-md",
            str(replay_report),
        ]
        if args.run_ablation:
            replay_args.extend([
                "--ablation-results-jsonl",
                str(ablation_results),
            ])
        status = run_stage("failure_replay_queue", replay_args)
        if status != 0:
            _write_manifest(output_dir / "manifest.json", manifest)
            return status

        quant_lab_args = [
            "quant-lab-register",
            "--experiment-id",
            experiment_id,
            "--actual-outcomes",
            args.actual_outcomes,
            "--plans-jsonl",
            args.plans_jsonl,
            "--backtest-summary",
            str(backtest_summary),
            "--backtest-results-jsonl",
            str(backtest_results),
            "--calibration-summary",
            str(calibration_summary),
            "--tuning-summary",
            str(tuning_summary),
            "--improvement-audit",
            str(output_dir / "improvement_audit.json"),
            "--failure-replay-queue-jsonl",
            str(replay_queue),
            "--failure-replay-queue-summary",
            str(replay_summary),
            "--benchmark-coverage",
            str(benchmark_coverage),
            "--output",
            str(quant_lab_manifest),
            "--report-md",
            str(quant_lab_report),
            "--notes",
            "standard experiment suite",
        ]
        if args.run_ablation:
            quant_lab_args.extend([
                "--ablation-summary",
                str(ablation_summary),
                "--ablation-results-jsonl",
                str(ablation_results),
            ])
        status = run_stage("quant_lab_register", quant_lab_args)
        if status != 0:
            _write_manifest(output_dir / "manifest.json", manifest)
            return status

        status = run_stage(
            "claim_readiness",
            [
                "claim-readiness",
                "--quant-lab-manifest",
                str(quant_lab_manifest),
                "--output",
                str(claim_readiness),
                "--report-md",
                str(claim_readiness_report),
            ],
        )
        if status != 0:
            _write_manifest(output_dir / "manifest.json", manifest)
            return status

        status = run_stage(
            "claim_readiness_portfolio",
            [
                "claim-readiness-portfolio",
                "--claim-json",
                str(claim_readiness),
                "--output",
                str(claim_readiness_portfolio),
                "--report-md",
                str(claim_readiness_portfolio_report),
            ],
        )
        if status != 0:
            _write_manifest(output_dir / "manifest.json", manifest)
            return status

        status = run_stage(
            "quant_lab_leaderboard",
            [
                "quant-lab-leaderboard",
                "--manifest",
                str(quant_lab_manifest),
                "--output",
                str(quant_lab_leaderboard),
                "--report-md",
                str(quant_lab_leaderboard_report),
            ],
        )
        if status != 0:
            _write_manifest(output_dir / "manifest.json", manifest)
            return status

    _write_manifest(output_dir / "manifest.json", manifest)
    print(f"saved experiment manifest -> {output_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

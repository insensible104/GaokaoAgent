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
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    manifest: dict[str, Any] = {
        "output_dir": str(output_dir),
        "stages": [],
    }

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

    if args.actual_outcomes and args.plans_jsonl:
        status = run_stage(
            "backtest_2025",
            [
                "backtest-2025",
                "--actual-outcomes",
                args.actual_outcomes,
                "--plans-jsonl",
                args.plans_jsonl,
                "--output",
                str(output_dir / "backtest_2025_summary.json"),
                "--results-jsonl",
                str(output_dir / "backtest_2025_results.jsonl"),
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

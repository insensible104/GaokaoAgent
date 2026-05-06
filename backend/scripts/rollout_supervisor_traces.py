"""Roll out supervisor traces and persist them as JSONL."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from rl.orchestration_data_pipeline import load_cases, rollout_cases


def main() -> None:
    parser = argparse.ArgumentParser(description="Run supervisor rollouts for a case file.")
    parser.add_argument(
        "--input",
        type=str,
        default="logs/orchestration_cases.jsonl",
        help="Input case file (.jsonl or .json), relative to backend/.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="logs/orchestration_rollouts.jsonl",
        help="Output JSONL path for rollout records, relative to backend/.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional case limit.")
    parser.add_argument("--recursion-limit", type=int, default=50, help="LangGraph recursion limit.")
    args = parser.parse_args()

    cases = load_cases(Path(args.input))
    if args.limit is not None:
        cases = cases[: args.limit]

    output_path = rollout_cases(
        cases=cases,
        output_path=Path(args.output),
        recursion_limit=args.recursion_limit,
    )
    print(f"rolled out {len(cases)} cases -> {output_path}")


if __name__ == "__main__":
    main()

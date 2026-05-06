"""Generate synthetic user requests for orchestration RL."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from rl.orchestration_data_pipeline import generate_synthetic_cases, save_cases_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic orchestration cases.")
    parser.add_argument("--num-cases", type=int, default=300, help="Number of cases to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--output",
        type=str,
        default="logs/orchestration_cases.jsonl",
        help="Output JSONL path, relative to backend/.",
    )
    parser.add_argument(
        "--no-seed-cases",
        action="store_true",
        help="Do not include normalized cases from backend/tests/test_cases.json.",
    )
    args = parser.parse_args()

    cases = generate_synthetic_cases(
        num_cases=args.num_cases,
        seed=args.seed,
        include_seed_cases=not args.no_seed_cases,
    )
    output_path = save_cases_jsonl(cases, Path(args.output))
    print(f"generated {len(cases)} cases -> {output_path}")


if __name__ == "__main__":
    main()

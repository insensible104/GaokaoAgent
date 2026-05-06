"""Build pairwise preferences from recorded orchestration traces."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from rl.orchestration_data_pipeline import (
    build_pairwise_preferences,
    load_rollout_records,
    save_jsonl,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build pairwise preferences from rollout traces.")
    parser.add_argument(
        "--input",
        type=str,
        default="logs/orchestration_rollouts.jsonl",
        help="Input rollout JSONL path, relative to backend/.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="logs/orchestration_pairwise.jsonl",
        help="Output pairwise JSONL path, relative to backend/.",
    )
    args = parser.parse_args()

    rollout_records = load_rollout_records(Path(args.input))
    preferences = build_pairwise_preferences(rollout_records)
    output_path = save_jsonl(preferences, Path(args.output))
    print(f"built {len(preferences)} pairwise samples -> {output_path}")


if __name__ == "__main__":
    main()

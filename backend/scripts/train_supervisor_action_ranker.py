"""Train a learned supervisor action ranker from pairwise orchestration preferences."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rl.orchestration_alignment import SupervisorActionRanker  # noqa: E402
from rl.orchestration_data_pipeline import load_rollout_records  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input pairwise JSONL")
    parser.add_argument(
        "--output",
        default=str(Path("backend/rl_checkpoints/supervisor_action_ranker.pkl")),
        help="Output model path",
    )
    args = parser.parse_args()

    records = load_rollout_records(args.input)
    ranker = SupervisorActionRanker()
    metrics = ranker.fit(records)
    output_path = ranker.save(args.output)

    print(f"saved model: {output_path}")
    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

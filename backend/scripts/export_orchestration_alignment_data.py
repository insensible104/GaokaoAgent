"""Export SFT / preference / GRPO-ready orchestration datasets from rollout logs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rl.orchestration_alignment import (  # noqa: E402
    build_grpo_tasks_from_rollouts,
    build_preference_examples,
    build_sft_examples_from_rollouts,
    save_jsonl,
)
from rl.orchestration_data_pipeline import load_rollout_records  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rollouts", required=True, help="Input rollout JSONL")
    parser.add_argument("--pairwise", required=True, help="Input pairwise JSONL")
    parser.add_argument("--output-dir", required=True, help="Directory for exported datasets")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rollout_records = load_rollout_records(args.rollouts)
    pairwise_records = load_rollout_records(args.pairwise)

    sft_path = save_jsonl(
        build_sft_examples_from_rollouts(rollout_records),
        output_dir / "orchestration_sft.jsonl",
    )
    preference_path = save_jsonl(
        build_preference_examples(pairwise_records),
        output_dir / "orchestration_preference.jsonl",
    )
    grpo_path = save_jsonl(
        build_grpo_tasks_from_rollouts(rollout_records),
        output_dir / "orchestration_grpo_tasks.jsonl",
    )

    print(f"sft dataset: {sft_path}")
    print(f"preference dataset: {preference_path}")
    print(f"grpo task dataset: {grpo_path}")


if __name__ == "__main__":
    main()

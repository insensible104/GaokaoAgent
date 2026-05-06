#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "datasets>=3.2.0",
#   "transformers>=4.46.0",
#   "trl>=0.12.2",
#   "peft>=0.13.0",
#   "accelerate>=1.1.1",
#   "torch>=2.4.0",
# ]
# ///
"""Train a TRL reward model for orchestration action preferences."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from datasets import Dataset
from peft import LoraConfig
from transformers import AutoTokenizer
from trl import RewardConfig, RewardTrainer

from rl.orchestration_trl_utils import build_reward_model_examples, load_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Preference JSONL exported by export_orchestration_alignment_data.py")
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct", help="Base reward model checkpoint")
    parser.add_argument("--output-dir", required=True, help="Local output directory")
    parser.add_argument("--hub-model-id", default=None, help="Optional Hub repo to push the reward model")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--eval-ratio", type=float, default=0.1)
    parser.add_argument("--report-to", default="none", help="Trainer reporting backend, e.g. none or trackio")
    parser.add_argument("--use-lora", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    raw_records = load_jsonl(args.input)
    examples = build_reward_model_examples(raw_records)
    if not examples:
        raise ValueError("No valid reward-model examples were found in the input file.")

    dataset = Dataset.from_list(examples)
    dataset_split = dataset.train_test_split(test_size=args.eval_ratio, seed=42)

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    peft_config = None
    if args.use_lora:
        peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            bias="none",
            task_type="SEQ_CLS",
            modules_to_save=["score"],
        )

    config = RewardConfig(
        output_dir=args.output_dir,
        learning_rate=args.learning_rate,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        max_length=args.max_length,
        eval_strategy="steps",
        eval_steps=25,
        save_steps=25,
        logging_steps=5,
        report_to=args.report_to,
        remove_unused_columns=False,
        push_to_hub=bool(args.hub_model_id),
        hub_model_id=args.hub_model_id,
    )

    trainer = RewardTrainer(
        model=args.model,
        args=config,
        processing_class=tokenizer,
        train_dataset=dataset_split["train"],
        eval_dataset=dataset_split["test"],
        peft_config=peft_config,
    )
    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    if args.hub_model_id:
        trainer.push_to_hub()

    print(f"reward model saved to {args.output_dir}")


if __name__ == "__main__":
    main()

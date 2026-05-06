#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "datasets>=3.2.0",
#   "transformers>=4.46.0",
#   "trl>=0.12.2",
#   "peft>=0.13.0",
#   "accelerate>=1.1.1",
#   "torch>=2.4.0",
#   "trackio>=0.3.0",
# ]
# ///
"""Hugging Face Jobs-ready GRPO trainer for orchestration policy learning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from datasets import Dataset, load_dataset
from peft import LoraConfig
from transformers import AutoTokenizer
from trl import GRPOConfig, GRPOTrainer

from rl.orchestration_trl_utils import (
    build_grpo_examples,
    format_reward_func,
    load_jsonl,
    proxy_reward_shaping_func,
    reference_match_reward_func,
    valid_action_reward_func,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--dataset-name", help="Hub dataset repo, e.g. username/gaokao-orchestration")
    source.add_argument("--jsonl-url", help="Remote JSONL URL for orchestration GRPO tasks")
    source.add_argument("--jsonl-path", help="Local JSONL path (useful for local dry-runs before Jobs)")
    parser.add_argument("--split", default="train", help="Dataset split for --dataset-name")
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct", help="Base policy model")
    parser.add_argument("--reward-model", default=None, help="Optional reward model checkpoint")
    parser.add_argument("--output-dir", default="orchestration-grpo-policy", help="Job-local output dir")
    parser.add_argument("--hub-model-id", required=True, help="Destination Hub repo for checkpoints")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=5e-6)
    parser.add_argument("--max-prompt-length", type=int, default=768)
    parser.add_argument("--max-completion-length", type=int, default=96)
    parser.add_argument("--num-generations", type=int, default=4)
    parser.add_argument("--run-name", default="orchestration-grpo")
    parser.add_argument("--use-lora", action="store_true")
    return parser.parse_args()


def _load_examples(args: argparse.Namespace) -> list[dict]:
    if args.dataset_name:
        dataset = load_dataset(args.dataset_name, split=args.split)
        return list(dataset)
    if args.jsonl_url:
        dataset = load_dataset("json", data_files=args.jsonl_url, split="train")
        return build_grpo_examples(list(dataset))
    if args.jsonl_path:
        return build_grpo_examples(load_jsonl(args.jsonl_path))
    raise ValueError("No dataset source was provided.")


def main() -> None:
    args = parse_args()
    examples = _load_examples(args)
    if not examples:
        raise ValueError("No valid GRPO examples were found.")

    dataset = Dataset.from_list(examples)
    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    reward_funcs = [
        format_reward_func,
        valid_action_reward_func,
        reference_match_reward_func,
        proxy_reward_shaping_func,
    ]
    reward_processing_classes = [None, None, None, None]

    if args.reward_model:
        reward_tokenizer = AutoTokenizer.from_pretrained(args.reward_model, use_fast=True)
        if reward_tokenizer.pad_token is None:
            reward_tokenizer.pad_token = reward_tokenizer.eos_token
        reward_funcs.append(args.reward_model)
        reward_processing_classes.append(reward_tokenizer)

    peft_config = None
    if args.use_lora:
        peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
        )

    config = GRPOConfig(
        output_dir=args.output_dir,
        learning_rate=args.learning_rate,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        logging_steps=1,
        save_steps=25,
        report_to="trackio",
        run_name=args.run_name,
        max_prompt_length=args.max_prompt_length,
        max_completion_length=args.max_completion_length,
        num_generations=args.num_generations,
        push_to_hub=True,
        hub_model_id=args.hub_model_id,
    )

    trainer = GRPOTrainer(
        model=args.model,
        reward_funcs=reward_funcs,
        args=config,
        train_dataset=dataset,
        processing_class=tokenizer,
        reward_processing_classes=reward_processing_classes,
        peft_config=peft_config,
    )

    print(json.dumps({"train_examples": len(dataset), "hub_model_id": args.hub_model_id}, ensure_ascii=False))
    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    trainer.push_to_hub()

    print(f"hf-jobs grpo policy saved to {args.output_dir} and pushed to {args.hub_model_id}")


if __name__ == "__main__":
    main()

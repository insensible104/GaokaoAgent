"""Train a minimal local reward model for supervisor action scoring."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
import sys
from typing import Any, Dict, List

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rl.orchestration_alignment import format_supervisor_prompt  # noqa: E402
from rl.orchestration_data_pipeline import load_rollout_records  # noqa: E402


class RewardTextDataset(Dataset):
    def __init__(self, records: List[Dict[str, Any]], tokenizer, max_length: int) -> None:
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> Dict[str, torch.Tensor]:
        item = self.records[index]
        encoded = self.tokenizer(
            item["text"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "labels": torch.tensor(item["label"], dtype=torch.float32),
        }


def build_binary_examples(pairwise_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    examples: List[Dict[str, Any]] = []
    for record in pairwise_records:
        stage = record.get("stage", "unknown")
        observation = record.get("observation", {})
        message = record.get("message")
        chosen_action = record.get("chosen_action")
        rejected_action = record.get("rejected_action")
        if not chosen_action or not rejected_action:
            continue
        prompt = format_supervisor_prompt(
            message=message,
            stage=stage,
            observation=observation,
            candidate_actions=[chosen_action, rejected_action],
        )
        examples.append(
            {
                "text": prompt + "\nAssistant response:\n" + json.dumps({"next_action": chosen_action}, ensure_ascii=False),
                "label": 1.0,
            }
        )
        examples.append(
            {
                "text": prompt + "\nAssistant response:\n" + json.dumps({"next_action": rejected_action}, ensure_ascii=False),
                "label": 0.0,
            }
        )
    return examples


def evaluate_accuracy(model, dataloader, device) -> float:
    model.eval()
    total = 0
    correct = 0
    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            logits = model(input_ids=input_ids, attention_mask=attention_mask).logits.squeeze(-1)
            predictions = (torch.sigmoid(logits) >= 0.5).float()
            total += int(labels.numel())
            correct += int((predictions == labels).sum().item())
    return correct / total if total else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Pairwise JSONL input")
    parser.add_argument("--model", default="sshleifer/tiny-distilbert-base-cased", help="Base checkpoint")
    parser.add_argument("--output-dir", required=True, help="Output checkpoint directory")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    pairwise_records = load_rollout_records(args.input)
    examples = build_binary_examples(pairwise_records)
    if not examples:
        raise ValueError("No valid examples found in pairwise input.")

    random.shuffle(examples)
    split = max(1, int(len(examples) * 0.8))
    train_examples = examples[:split]
    eval_examples = examples[split:] or examples[:1]

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model,
        num_labels=1,
        ignore_mismatched_sizes=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token or tokenizer.sep_token
    model.config.pad_token_id = tokenizer.pad_token_id

    train_dataset = RewardTextDataset(train_examples, tokenizer, args.max_length)
    eval_dataset = RewardTextDataset(eval_examples, tokenizer, args.max_length)
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    eval_loader = DataLoader(eval_dataset, batch_size=args.batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    loss_fn = nn.BCEWithLogitsLoss()

    for epoch in range(args.epochs):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)
            logits = model(input_ids=input_ids, attention_mask=attention_mask).logits.squeeze(-1)
            loss = loss_fn(logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item())

        train_acc = evaluate_accuracy(model, train_loader, device)
        eval_acc = evaluate_accuracy(model, eval_loader, device)
        print(
            f"epoch={epoch + 1} loss={total_loss / max(len(train_loader), 1):.4f} "
            f"train_acc={train_acc:.4f} eval_acc={eval_acc:.4f}"
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"saved reward model to {output_dir}")


if __name__ == "__main__":
    main()

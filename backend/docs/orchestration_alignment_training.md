# Orchestration Alignment Training

This document describes the minimum end-to-end pipeline for alignment training on the supervisor orchestration policy.

The main idea is trajectory-level optimization, not base-model fine-tuning for the recommendation generator. The LLM and deterministic recommendation modules can stay frozen; the learnable object is the supervisor policy that chooses when to profile, recommend, research, critique, retry, or stop.

## 1. Generate rollouts and pairwise preferences

```powershell
cd c:\GaokaoAgent\backend

python scripts\generate_orchestration_cases.py --num-cases 300 --output logs\orchestration_cases.jsonl
python scripts\rollout_supervisor_traces.py --input logs\orchestration_cases.jsonl --output logs\orchestration_rollouts.jsonl
python scripts\build_pairwise_orchestration_dataset.py --input logs\orchestration_rollouts.jsonl --output logs\orchestration_pairwise.jsonl
```

## 2. Export alignment datasets

```powershell
python scripts\export_orchestration_alignment_data.py --rollouts logs\orchestration_rollouts.jsonl --pairwise logs\orchestration_pairwise.jsonl --output-dir logs\alignment
```

Outputs:

- `logs/alignment/orchestration_sft.jsonl`
- `logs/alignment/orchestration_preference.jsonl`
- `logs/alignment/orchestration_grpo_tasks.jsonl`

These files should be read as supervision over orchestration traces. `orchestration_sft.jsonl` imitates high-quality routing decisions, `orchestration_preference.jsonl` compares chosen and rejected next actions, and `orchestration_grpo_tasks.jsonl` groups alternative trajectories for the same task.

## 3. Train a lightweight learned supervisor ranker

```powershell
python scripts\train_supervisor_action_ranker.py --input logs\orchestration_pairwise.jsonl --output backend\rl_checkpoints\supervisor_action_ranker.pkl
```

Enable online usage:

```powershell
$env:ENABLE_LEARNED_SUPERVISOR_POLICY="1"
$env:ENABLE_LLM_SUPERVISOR_POLICY="1"   # optional: let an LLM supervisor consume the learned prior
$env:ENABLE_REWARD_MODEL_SUPERVISOR="1" # optional: let a reward model rerank final candidate actions
```

## 4. Train a reward model with TRL

```powershell
uv run scripts\train_orchestration_reward_model.py `
  --input logs\alignment\orchestration_preference.jsonl `
  --model Qwen/Qwen2.5-1.5B-Instruct `
  --output-dir outputs\orchestration_reward_model `
  --use-lora
```

If you only need a lightweight local checkpoint for runtime validation on this machine, you can also use the minimal trainer that depends only on `transformers + torch`:

```powershell
python scripts\train_minimal_supervisor_reward_model.py `
  --input logs\orchestration_pairwise.jsonl `
  --model distilbert-base-uncased `
  --output-dir backend\rl_checkpoints\distilbert_supervisor_reward_model `
  --epochs 3
```

## 5. Optional: train a GRPO-style supervisor policy

```powershell
uv run scripts\train_orchestration_grpo.py `
  --input logs\alignment\orchestration_grpo_tasks.jsonl `
  --model Qwen/Qwen2.5-1.5B-Instruct `
  --output-dir outputs\orchestration_grpo_policy `
  --reward-model outputs\orchestration_reward_model `
  --use-lora
```

This step is optional and experimental. The cleaner production path is still the frozen-model runtime policy plus a lightweight ranker or reward-model reranker. In interview terms, this is "GRPO-style trajectory optimization": compare multiple candidate action sequences under the same user case, reward the sequence that reaches an approved, evidence-backed, low-risk result with fewer unnecessary loops, and deploy the learned routing prior without changing the recommendation model itself.

## 6. Train on Hugging Face Jobs

For cloud GPU training, use the Jobs-ready script:

```powershell
uv run scripts\train_orchestration_grpo_hf_job.py `
  --dataset-name username/gaokao-orchestration-grpo `
  --model Qwen/Qwen2.5-1.5B-Instruct `
  --hub-model-id username/orchestration-grpo-policy `
  --use-lora
```

## Notes

- The learned ranker is the cheapest path to online deployment.
- The reward model and GRPO scripts are intended for GPU training and use TRL-compatible dataset formats.
- `train_orchestration_grpo_hf_job.py` is the preferred entrypoint for Hugging Face Jobs.
- The current online supervisor still keeps the heuristic policy as a safe fallback.
- Runtime RL does not directly optimize school ranking scores. It optimizes the trajectory: action choice, deep-research timing, critic reroute, retry budget, and stop condition.
- Communication quality is part of the reward. Missing required proposal/vote messages are recorded as `protocol_violations`, exposed to the supervisor observation, and penalized through `protocol_violation_penalty`.

## 7. Evaluate rollout quality and learned policies

```powershell
python scripts\evaluate_orchestration_policies.py `
  --rollouts logs\orchestration_rollouts.jsonl `
  --pairwise logs\orchestration_pairwise.jsonl `
  --ranker backend\rl_checkpoints\supervisor_action_ranker.pkl `
  --output logs\alignment\orchestration_eval.json
```

To compare two rollout variants and emit a Markdown report:

```powershell
python scripts\evaluate_orchestration_policies.py `
  --baseline-rollouts logs\baseline_rollouts.jsonl `
  --candidate-rollouts logs\candidate_rollouts.jsonl `
  --pairwise logs\orchestration_pairwise.jsonl `
  --ranker backend\rl_checkpoints\supervisor_action_ranker.pkl `
  --reward-model backend\rl_checkpoints\distilbert_supervisor_reward_model `
  --output logs\alignment\orchestration_compare.json `
  --report-md logs\alignment\orchestration_compare.md
```

The evaluation script currently summarizes:

- average proxy reward
- approval / success rate
- average trace length and retry count
- deep research trigger rate
- learned ranker accuracy on pairwise preferences
- reward model accuracy on pairwise preferences
- baseline vs candidate rollout deltas


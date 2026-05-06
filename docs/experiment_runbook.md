# GaokaoAgent Experiment Runbook

This runbook keeps the project entrypoints small and auditable. The rule is:
use one CLI for checks, rollouts, pairwise data, orchestration evaluation, and
2025 backtesting.

## Unified CLI

From the repository root:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py --help
```

Available commands:

```text
smoke
rollout
build-pairwise
eval-orchestration
backtest-2025
```

## Smoke Checks

Run the stable project checks:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py smoke --fail-fast
```

Run selected checks:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py smoke --tests test_tradeoff_policy_smoke.py test_backtest_2025_smoke.py --fail-fast
```

## Orchestration Experiments

Roll out supervisor traces:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py rollout --input logs\orchestration_cases.jsonl --output logs\orchestration_rollouts.jsonl
```

Build pairwise preferences:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py build-pairwise --input logs\orchestration_rollouts.jsonl --output logs\orchestration_pairwise.jsonl
```

Evaluate rollout behavior:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py eval-orchestration --rollouts logs\orchestration_rollouts.jsonl --output logs\orchestration_eval.json --report-md logs\orchestration_eval.md
```

## 2025 Backtest

The 2025 actual results are post-hoc labels. They must not be used during plan
generation.

Input plan JSONL format:

```json
{"case_id":"case_001","user_rank":12000,"preferred_majors":["计算机"],"blacklist_majors":["土木"],"plan":{ "...": "VolunteerPlan JSON" }}
```

Run:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py backtest-2025 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl --output logs\backtest_2025_summary.json --results-jsonl logs\backtest_2025_results.jsonl
```

## One-Shot Suite

Use this when you want one command to create an experiment folder:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\run_experiment_suite.py --output-dir logs\experiments\run_001 --cases logs\orchestration_cases.jsonl --limit 20
```

Add post-hoc 2025 evaluation when frozen plans and actual outcomes are ready:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\run_experiment_suite.py --output-dir logs\experiments\run_001 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl
```

## Claim-Evidence Mapping

Use these outputs for project claims:

| Claim | Evidence artifact |
| --- | --- |
| Recommendation core is backtestable | `backtest_2025_summary.json`, `backtest_2025_results.jsonl` |
| Agentic orchestration is not decorative | `orchestration_rollouts.jsonl`, `orchestration_eval.json` |
| RL/reward direction has trainable traces | `orchestration_pairwise.jsonl` |
| LLM components can be ablated | compare runs with `ENABLE_LLM_ADVISORS` / `ENABLE_LLM_CRITIC` on and off |


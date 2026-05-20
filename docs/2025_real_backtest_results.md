# 2025 Real Backtest Results

Date: 2026-05-20

This run evaluates frozen GaokaoAgent volunteer plans against the parsed 2025 Guangdong major-level admission outcomes. The plan generator uses prediction-time inputs only: 2021-2024 historical admission data, 2025 enrollment plans, and 2025 score-rank tables for score approximation. The actual 2025 outcome labels are only loaded by `backtest-2025` and `ablate-2025`.

## Commands

```powershell
backend\.venv\Scripts\python.exe backend\scripts\generate_frozen_plans_2025.py --output logs\frozen_plans_2025.jsonl --num-cases 24 --target-count 500 --max-choices 30 --min-probability 0.0 *> logs\frozen_plans_2025_generation.log

backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py backtest-2025 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl --output logs\backtest_2025_summary.json --results-jsonl logs\backtest_2025_results.jsonl *> logs\backtest_2025_run.log

backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py ablate-2025 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl --output logs\ablation_2025_summary.json --results-jsonl logs\ablation_2025_results.jsonl --report-md logs\ablation_2025_report.md *> logs\ablation_2025_run.log
```

## Frozen Plans

| Item | Value |
| --- | ---: |
| Requested cases | 24 |
| Generated cases | 23 |
| Skipped cases | 1 |
| Min plan choices | 10 |
| Max plan choices | 30 |
| Uses actual 2025 labels during generation | false |

The skipped case was `历史_rank_130000`, because the current prediction-time filters found too few viable candidates for that case after requiring a matching 2025 enrollment-plan group.

## Backtest Summary

| Metric | Value |
| --- | ---: |
| Cases | 23 |
| Success rate | 95.7% |
| Sliding rate | 4.3% |
| Selected-major hit rate | 69.6% |
| Preferred-major hit rate | 21.7% |
| Blacklist hit rate | 0.0% |
| Tail-assignment rate | 39.1% |
| Wasted-score rate | 21.7% |
| Average first-hit index | 2.50 |
| Average first-hit margin | 7,990.91 |
| Average assigned-major utility | 0.493 |

## Ablation Results

| Variant | Cases | Success | Preferred | Blacklist | Tail | Wasted | First-hit idx | Avg utility | Delta success | Delta preferred |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full` | 23 | 95.7% | 21.7% | 0.0% | 39.1% | 21.7% | 2.50 | 0.493 | +0.0% | +0.0% |
| `probability_only` | 23 | 95.7% | 13.0% | 0.0% | 52.2% | 21.7% | 2.18 | 0.449 | +0.0% | -8.7% |
| `history_tight_rank` | 23 | 95.7% | 13.0% | 4.3% | 60.9% | 21.7% | 2.68 | 0.430 | +0.0% | -8.7% |
| `safe_first` | 23 | 95.7% | 8.7% | 0.0% | 47.8% | 21.7% | 2.09 | 0.433 | +0.0% | -13.0% |
| `no_tradeoff_policy` | 23 | 95.7% | 47.8% | 0.0% | 30.4% | 17.4% | 1.95 | 0.620 | +0.0% | +26.1% |

## Integrity Notes

- Ground truth provenance: `data/actual_2025.csv` is parsed from the provided 2025 major-level admission spreadsheet and is only used by the evaluation commands.
- Data-boundary fix: the runtime recommendation engine now ignores files named like `actual_2025*.csv` when loading prediction-time data.
- Coverage: 537 of 659 evaluated choice outcomes matched a 2025 actual outcome row, for an 81.5% choice-level coverage rate. The remaining 122 choices were marked `missing_actual_outcome`.
- Coverage improvement: the previous run matched 218 of 681 choices, or 32.0%. The new generator requires a matching 2025 enrollment-plan group before a historical candidate can enter the frozen plan, and the evaluator also supports school-code + major-group fallback for renamed schools.
- Scope: this is the first real-label backtest over frozen synthetic case profiles. It supports a stronger data-alignment claim than the previous run, but it is not yet a final large-scale benchmark.

## Readout

The coverage fix changes the interpretation. The full policy still keeps the same 95.7% success rate and lowers tail-assignment risk versus `probability_only`, `history_tight_rank`, and `safe_first`, but `no_tradeoff_policy` now has higher preferred-major hit rate and utility on this covered slice. That is useful negative evidence: the data alignment is much better, and the next method work should inspect whether the current tradeoff policy over-penalizes preference-heavy options.

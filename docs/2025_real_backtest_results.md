# 2025 Real Backtest Results

Date: 2026-05-20

This run evaluates frozen GaokaoAgent volunteer plans against the parsed 2025 Guangdong major-level admission outcomes. The plan generator uses prediction-time inputs only: 2021-2024 historical admission data, 2025 enrollment plans, and 2025 score-rank tables for score approximation. The actual 2025 outcome labels are only loaded by `backtest-2025` and `ablate-2025`.

## Commands

```powershell
backend\.venv\Scripts\python.exe backend\scripts\generate_frozen_plans_2025.py --output logs\frozen_plans_2025.jsonl --num-cases 24 --target-count 300 --max-choices 30 --min-probability 0.03 *> logs\frozen_plans_2025_generation.log

backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py backtest-2025 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl --output logs\backtest_2025_summary.json --results-jsonl logs\backtest_2025_results.jsonl *> logs\backtest_2025_run.log

backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py ablate-2025 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl --output logs\ablation_2025_summary.json --results-jsonl logs\ablation_2025_results.jsonl --report-md logs\ablation_2025_report.md *> logs\ablation_2025_run.log
```

## Frozen Plans

| Item | Value |
| --- | ---: |
| Requested cases | 24 |
| Generated cases | 23 |
| Skipped cases | 1 |
| Min plan choices | 21 |
| Max plan choices | 30 |
| Uses actual 2025 labels during generation | false |

The skipped case was `历史_rank_130000`, because the current prediction-time filters found too few viable candidates for that case.

## Backtest Summary

| Metric | Value |
| --- | ---: |
| Cases | 23 |
| Success rate | 95.7% |
| Sliding rate | 4.3% |
| Selected-major hit rate | 43.5% |
| Preferred-major hit rate | 21.7% |
| Blacklist hit rate | 0.0% |
| Tail-assignment rate | 65.2% |
| Wasted-score rate | 52.2% |
| Average first-hit index | 3.27 |
| Average first-hit margin | 29,147.18 |
| Average assigned-major utility | 0.453 |

## Ablation Results

| Variant | Cases | Success | Preferred | Blacklist | Tail | Wasted | First-hit idx | Avg utility | Delta success | Delta preferred |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full` | 23 | 95.7% | 21.7% | 0.0% | 65.2% | 52.2% | 3.27 | 0.453 | +0.0% | +0.0% |
| `probability_only` | 23 | 87.0% | 8.7% | 0.0% | 56.5% | 47.8% | 5.30 | 0.454 | -8.7% | -13.0% |
| `history_tight_rank` | 23 | 91.3% | 13.0% | 4.3% | 56.5% | 47.8% | 8.33 | 0.436 | -4.3% | -8.7% |
| `safe_first` | 23 | 87.0% | 4.3% | 0.0% | 56.5% | 52.2% | 5.25 | 0.439 | -8.7% | -17.4% |
| `no_tradeoff_policy` | 23 | 91.3% | 17.4% | 0.0% | 69.6% | 43.5% | 4.95 | 0.472 | -4.3% | -4.3% |

## Integrity Notes

- Ground truth provenance: `data/actual_2025.csv` is parsed from the provided 2025 major-level admission spreadsheet and is only used by the evaluation commands.
- Data-boundary fix: the runtime recommendation engine now ignores files named like `actual_2025*.csv` when loading prediction-time data.
- Coverage: 218 of 681 evaluated choice outcomes matched a 2025 actual outcome row, for a 32.0% choice-level coverage rate. The remaining 463 choices were marked `missing_actual_outcome`.
- Scope: this is the first real-label backtest over frozen synthetic case profiles. It supports an engineering-research claim that the full policy beats the included baselines on this covered slice, but it is not yet a final large-scale benchmark.

## Readout

The full policy improves success rate over `probability_only` and `safe_first` by 8.7 percentage points and improves preferred-major hit rate over all included baselines. The strongest caveat is coverage: many generated choices do not yet align exactly with the parsed 2025 outcome keyspace, so the next experiment should improve school/group/code normalization and then rerun the same frozen-plan protocol.

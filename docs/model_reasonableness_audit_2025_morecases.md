# 2025 Quant Model Reasonableness Audit

Date: 2026-05-21

This audit checks whether the current quantitative arbitrage model is accurate enough to support research claims.

## Scope

Inputs:

- Frozen plans: `logs/frozen_plans_2025_arbitrage_driven_morecases.jsonl`
- Ablation results: `logs/ablation_2025_arbitrage_driven_morecases_v2_results.jsonl`
- Actual labels: `data/actual_2025.csv`
- Diagnostic JSON: `logs/model_reasonableness_audit_2025_morecases.json`

Sample:

- 73 frozen cases
- 537 evaluated plan choices with actual outcome matches
- 132 plan choices missing actual outcome matches
- 1,077 candidate rows with actual outcome matches

## Integrity

Data-boundary check passes.

The frozen-plan generator explicitly marks `uses_actual_2025: false` and does not read `data/actual_2025.csv`. Actual 2025 outcomes are loaded only by the post-hoc evaluation modules.

Relevant files:

- `backend/scripts/generate_frozen_plans_2025.py`
- `backend/src/evaluation/backtest_2025.py`
- `backend/src/evaluation/ablation_2025.py`
- `backend/src/engines/quant_engine.py`

## Group Admission Probability

The admission probability is directionally useful but not well calibrated.

Metrics over full-plan choices:

```text
Brier score: 0.293
Pearson correlation: 0.305
AUC: 0.667
ECE: 0.221
```

The model separates admitted from non-admitted groups better than random, but the probability values are overconfident, especially in high-probability bins:

| Predicted Bin | Mean Predicted | Actual Admit Rate | N |
| --- | ---: | ---: | ---: |
| 0.7-0.8 | 0.751 | 0.718 | 39 |
| 0.8-0.9 | 0.866 | 0.511 | 47 |
| 0.9-1.0 | 0.983 | 0.560 | 175 |

Conclusion:

```text
The admission score can be used as a ranking signal.
It should not yet be presented as a calibrated probability.
```

## Front-Major Probability

The current `front_major_hit_prob` is not calibrated as a real probability.

Conditional on group admission:

```text
N: 232
Selected-major hit rate: 74.1%
Preferred-major hit rate: 19.8%
Pearson vs selected-major hit: -0.318
Pearson vs preferred-major hit: 0.113
AUC vs selected-major hit: 0.263
AUC vs preferred-major hit: 0.551
ECE vs preferred-major hit: 0.445
```

The proxy is weak for predicting exact preferred-major outcomes. It is especially problematic in the 0.9-1.0 predicted bin:

| Predicted Bin | Mean Predicted | Preferred Hit | Tail Hit | N |
| --- | ---: | ---: | ---: | ---: |
| 0.9-1.0 | 0.944 | 0.180 | 0.557 | 61 |

Conclusion:

```text
`front_major_hit_prob` should be renamed or recalibrated before being shown as a probability.
It is currently better understood as a heuristic opportunity signal.
```

## Candidate Ranking

At the candidate-row level:

```text
admission_prob AUC vs group_admitted: 0.712
comprehensive_score AUC vs group_admitted: 0.608
arbitrage_score AUC vs group_admitted: 0.603
front_major_arbitrage_score AUC vs group_admitted: 0.647
```

Interpretation:

- `admission_prob` remains the best pure group-admission ranking signal.
- `arbitrage_score` is not a good replacement for admission probability.
- `front_major_arbitrage_score` contains some group-admission information, but its main value should be tested on assignment quality, not group admission alone.

## Ablation Robustness

`front_major_boost` improves preferred-major hit versus `full`:

```text
Preferred-major gains vs full: 11 cases
Preferred-major losses vs full: 0 cases
Two-sided sign-test p-value: 0.00098
```

This is the strongest current evidence in favor of the modeling direction.

However, the gain is not enough to say the whole current production-style `full` policy is superior to all baselines, because `full` underperforms `no_tradeoff_policy` and `front_major_boost` on preference/utility metrics.

## Verdict

The modeling idea is reasonable, but the model is not yet accurate enough to be called calibrated or final.

Current status:

```text
Conceptual model: reasonable
Data boundary: acceptable
Group-admission ranking: moderately useful
Group-admission probability calibration: weak
Front-major probability calibration: poor
Ablation evidence for front-major objective: strong enough to justify next iteration
Overall claim readiness: not yet
```

Allowed claim:

```text
The 2025 ablation suggests that explicitly optimizing within-group front-major opportunity can improve preferred-major hit without reducing group-admission success in the current 73-case evaluation.
```

Not allowed yet:

```text
The current full strategy is generally superior to all baselines.
The current probabilities are well calibrated.
The model can accurately predict exact in-group major assignment.
```

## Next Fixes

1. Calibrate `admission_prob` using isotonic or Platt scaling on pre-2025-style validation labels.
2. Rename `front_major_hit_prob` to `front_major_opportunity_signal` until it is calibrated.
3. Train or fit a separate assignment model for:

```text
P(selected_major_hit | group_admitted)
P(preferred_major_hit | group_admitted)
P(tail_assignment | group_admitted)
```

4. Promote `front_major_boost` into a constrained policy:

```text
maximize preferred/front-major hit
subject to sliding risk <= budget
and tail-assignment risk <= budget
and sacrifice cost <= student tolerance
```


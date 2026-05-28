# 2025 Backtest Ablation Report

Cases: 239

| Variant | Cases | Success | Preferred Major | Blacklist | Tail Assignment | Avg Utility | Delta Success | Delta Preferred |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full` | 239 | 66.5% | 15.1% | 0.0% | 13.8% | 0.502 | 0.0% | 0.0% |
| `probability_only` | 239 | 66.5% | 12.6% | 0.0% | 18.8% | 0.483 | 0.0% | -2.5% |
| `history_tight_rank` | 239 | 69.0% | 5.4% | 1.3% | 22.2% | 0.435 | 2.5% | -9.6% |
| `safe_first` | 239 | 66.5% | 7.1% | 0.0% | 18.8% | 0.454 | 0.0% | -7.9% |
| `no_tradeoff_policy` | 239 | 65.7% | 24.7% | 0.0% | 12.6% | 0.565 | -0.8% | 9.6% |
| `no_arbitrage` | 239 | 66.5% | 24.3% | 0.0% | 13.4% | 0.559 | 0.0% | 9.2% |
| `arbitrage_only` | 239 | 65.3% | 18.0% | 0.0% | 12.1% | 0.530 | -1.3% | 2.9% |
| `front_major_boost` | 239 | 66.5% | 21.8% | 0.0% | 13.4% | 0.547 | 0.0% | 6.7% |
| `segment_market` | 239 | 66.5% | 24.7% | 0.0% | 13.4% | 0.562 | 0.0% | 9.6% |
| `guarded_arbitrage` | 239 | 66.5% | 21.8% | 0.0% | 13.4% | 0.547 | 0.0% | 6.7% |
| `prefix_optimizer` | 239 | 65.3% | 27.6% | 0.0% | 13.0% | 0.581 | -1.3% | 12.6% |
| `plan_change_guarded` | 239 | 67.4% | 27.6% | 0.0% | 13.4% | 0.576 | 0.8% | 12.6% |

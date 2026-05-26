# 2025 Backtest Ablation Report

Cases: 29

| Variant | Cases | Success | Preferred Major | Blacklist | Tail Assignment | Avg Utility | Delta Success | Delta Preferred |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full` | 29 | 72.4% | 17.2% | 0.0% | 34.5% | 0.506 | 0.0% | 0.0% |
| `probability_only` | 29 | 72.4% | 6.9% | 0.0% | 34.5% | 0.436 | 0.0% | -10.3% |
| `history_tight_rank` | 29 | 72.4% | 13.8% | 3.4% | 37.9% | 0.465 | 0.0% | -3.4% |
| `safe_first` | 29 | 72.4% | 3.4% | 0.0% | 31.0% | 0.390 | 0.0% | -13.8% |
| `no_tradeoff_policy` | 29 | 72.4% | 17.2% | 0.0% | 20.7% | 0.512 | 0.0% | 0.0% |
| `no_arbitrage` | 29 | 72.4% | 17.2% | 0.0% | 20.7% | 0.512 | 0.0% | 0.0% |
| `arbitrage_only` | 29 | 72.4% | 20.7% | 0.0% | 20.7% | 0.510 | 0.0% | 3.4% |
| `front_major_boost` | 29 | 72.4% | 17.2% | 0.0% | 37.9% | 0.507 | 0.0% | 0.0% |
| `segment_market` | 29 | 72.4% | 17.2% | 0.0% | 20.7% | 0.512 | 0.0% | 0.0% |
| `guarded_arbitrage` | 29 | 72.4% | 17.2% | 0.0% | 31.0% | 0.517 | 0.0% | 0.0% |
| `prefix_optimizer` | 29 | 72.4% | 20.7% | 0.0% | 34.5% | 0.524 | 0.0% | 3.4% |

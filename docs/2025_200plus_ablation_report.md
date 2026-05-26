# 2025 Backtest Ablation Report

Cases: 228

| Variant | Cases | Success | Preferred Major | Blacklist | Tail Assignment | Avg Utility | Delta Success | Delta Preferred |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full` | 228 | 64.5% | 18.4% | 0.4% | 15.8% | 0.518 | 0.0% | 0.0% |
| `probability_only` | 228 | 64.5% | 9.6% | 0.0% | 20.6% | 0.462 | 0.0% | -8.8% |
| `history_tight_rank` | 228 | 65.8% | 8.3% | 2.2% | 22.8% | 0.463 | 1.3% | -10.1% |
| `safe_first` | 228 | 64.5% | 7.0% | 0.0% | 20.6% | 0.448 | 0.0% | -11.4% |
| `no_tradeoff_policy` | 228 | 63.6% | 25.9% | 0.0% | 14.9% | 0.567 | -0.9% | 7.5% |
| `no_arbitrage` | 228 | 63.6% | 25.0% | 0.0% | 14.9% | 0.561 | -0.9% | 6.6% |
| `arbitrage_only` | 228 | 63.6% | 21.1% | 0.0% | 14.9% | 0.542 | -0.9% | 2.6% |
| `front_major_boost` | 228 | 64.5% | 25.4% | 0.0% | 15.8% | 0.561 | 0.0% | 7.0% |
| `segment_market` | 228 | 63.6% | 25.9% | 0.0% | 14.9% | 0.566 | -0.9% | 7.5% |
| `guarded_arbitrage` | 228 | 64.5% | 24.6% | 0.0% | 15.8% | 0.558 | 0.0% | 6.1% |
| `prefix_optimizer` | 228 | 63.6% | 26.3% | 0.0% | 15.4% | 0.572 | -0.9% | 7.9% |

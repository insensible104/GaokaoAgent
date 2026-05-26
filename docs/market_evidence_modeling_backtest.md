# Market Evidence Modeling And Backtest

Date: 2026-05-21

This note turns the counselor-style "big data + public information" workflow into explicit, auditable, and backtestable project machinery.

## Problem Anchor

The counselor's practical advantage is not necessarily a large model. It is likely:

```text
public admission tables
+ enrollment plans
+ professional-group structure
+ tuition/campus/pathway labels
+ repeated case experience
+ current publicity awareness
```

GaokaoAgent should turn that experience into:

```text
explicit signals -> evidence cards -> frozen plans -> post-hoc backtest
```

## New Implementation

Code:

- `backend/src/recommendation/market_evidence.py`
- `backend/scripts/audit_market_evidence_2025.py`
- `backend/src/test_market_evidence_smoke.py`

Integrated fields:

- `MajorGroupRow.market_evidence_cards`
- `MajorGroupRow.market_evidence_strength`
- `MajorGroupRow.publicity_heat_score`
- `MajorGroupRow.publicity_rebound_risk`
- same fields preserved in `VolunteerChoice`

The evidence layer is now called inside `score_major_group_arbitrage(...)`, so generated frozen plans preserve the evidence used by the arbitrage model.

The practical goal is to move from:

```text
model says this is high score
```

to:

```text
why others may miss it
+ why this student can take it
+ what can go wrong
+ what evidence supports the claim
```

## EvidenceCard Schema

Each card records one public signal:

```json
{
  "signal_type": "tuition_filter",
  "source_type": "enrollment_plan",
  "value": 0.9,
  "confidence": 0.9,
  "claim": "High tuition can filter demand.",
  "source": "structured_public_fields",
  "cutoff_date": "",
  "usable_for_prediction": true
}
```

Current structured signal families:

- `tuition_filter`
- `campus_discount`
- `cold_major_discount`
- `group_restructure`
- `historical_anchor_overdeterrence`
- `quota_pressure`

Decision-grade card families are now attached after personalized arbitrage
scoring:

- `opportunity_thesis`: summarizes the main leak mechanism and final
  arbitrage score.
- `student_fit`: explains why this student's family profile can absorb the
  required sacrifice.
- `downside_guard`: records tail-assignment, rebound, and blacklist risks.

These cards are intentionally generated after `row.apply_arbitrage_result(...)`
so their claims reflect the final row-level arbitrage score rather than an
uninitialized intermediate value.

Report integration:

- Fallback reports now append the three decision-card claims to each
  recommendation line when available.
- Structured LLM reports receive the same cards in the `matrix_summary`
  recommendation payload.
- The report prompt instructs the model to use decision cards as the primary
  explanation spine instead of inventing generic reasons.
- The critic rejects a report when key-prefix choices have decision cards but
  the report omits their opportunity thesis, student fit, and downside guard.

External signal families are supported but not yet populated in the 73-case run:

- `publicity_heat`
- `sentiment_shock_discount`

This is where LLM/search collectors should later plug in public live-stream, short-video, official-news, forum, and counselor-content evidence.

## 2025 Evidence-Aware Frozen Run

Generated:

```text
logs/frozen_plans_2025_market_evidence_morecases.jsonl
```

Settings:

- requested profiles: 80
- valid records: 73
- target candidates per profile: 240
- max choices: 10
- minimum probability: 0.03
- actual outcomes used only post-hoc

Backtest:

```text
success_rate: 64.4%
sliding_rate: 35.6%
selected_major_hit_rate: 47.9%
preferred_major_hit_rate: 13.7%
blacklist_hit_rate: 0.0%
tail_assignment_rate: 26.0%
average_first_hit_index: 2.02
average_assigned_major_utility: 0.468
```

Ablation:

| Variant | Success | Preferred Major | Tail Assignment | Avg Utility |
| --- | ---: | ---: | ---: | ---: |
| full | 64.4% | 13.7% | 26.0% | 0.468 |
| no_tradeoff_policy | 63.0% | 24.7% | 28.8% | 0.516 |
| no_arbitrage | 63.0% | 24.7% | 28.8% | 0.509 |
| arbitrage_only | 64.4% | 21.9% | 37.0% | 0.482 |
| front_major_boost | 64.4% | 28.8% | 30.1% | 0.514 |

## Market Evidence Audit

Audit output:

```text
logs/market_evidence_2025_morecases_audit.json
```

Candidate-level coverage:

```text
candidate rows with actual labels: 1,077
missing candidate outcomes: 246
```

Evidence card counts:

```text
quota_pressure: 319
tuition_filter: 299
group_restructure: 257
historical_anchor_overdeterrence: 227
```

Candidate-level AUC versus group admission:

```text
admission_prob: 0.712
market_discount_score: 0.487
arbitrage_score: 0.608
front_major_arbitrage_score: 0.650
publicity_rebound_risk: 0.422
```

First-hit-level AUC versus preferred-major hit:

```text
arbitrage_score: 0.497
front_major_arbitrage_score: 0.714
market_evidence_strength: 0.365
publicity_rebound_risk: 0.342
```

## Interpretation

The evidence layer makes the counselor-style experience explicit, but the current structured evidence cards are not enough by themselves.

What is already useful:

- Evidence cards make discount reasons auditable.
- Frozen plans now preserve the evidence basis.
- `front_major_arbitrage_score` is the best current signal for preferred-major hit after first-hit admission.

What is not yet useful:

- `market_discount_score` alone does not predict group admission.
- `publicity_rebound_risk` is weak because there is no real external publicity data yet.
- `market_evidence_strength` measures coverage, not correctness.

The current conclusion should be:

```text
Structured public fields can explain why a group may be discounted,
but external market data is needed to model whether that discount will persist or rebound this year.
```

## Next Step

Add an external evidence collector that writes `EvidenceCard` records for:

```text
publicity_heat
sentiment_shock_discount
official_policy_change
major_value_evidence
employment_value_evidence
```

The LLM should not directly decide recommendations. It should produce evidence cards with source, claim, confidence, and cutoff date. The quant model then consumes those cards.

## Segment-Demand Consumer

The evidence layer now feeds a small market simulation layer:

- `backend/src/recommendation/market_simulation.py`
- `backend/src/test_market_simulation_smoke.py`

Instead of treating a professional group as universally good or bad, the new
layer asks which student/family segments can absorb the visible sacrifice:

```text
tuition / campus / pathway / cold major / region / adjustment risk
```

It outputs:

- `segment_demand_score`: how many plausible segments may want this group
- `low_attention_signal`: whether the opportunity is still hidden after publicity
- `segment_rebound_risk`: whether visible demand and publicity may erase the leak
- `best_fit_archetypes`: which family types can rationally take the trade
- `segment_demand_breakdown`: per-archetype fit scores

This makes the LLM/search collector's role clearer:

```text
collector finds public evidence
-> EvidenceCard records source and claim
-> market simulation estimates demand/rebound
-> ablation tests whether the signal improves 2025 outcomes
```

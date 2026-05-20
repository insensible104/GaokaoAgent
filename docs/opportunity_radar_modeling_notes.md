# Opportunity Radar Modeling Notes

Date: 2026-05-20

This note summarizes the core idea behind the four volunteer-planning screenshots and translates it into GaokaoAgent's mathematical modeling language. The screenshots are treated as strategy examples, not as audited statistical evidence.

## Problem Anchor

The modeling goal is not to prove that a major is absolutely good or bad. The goal is to avoid missing high-value professional-group opportunities caused by market mispricing.

In Gaokao volunteer planning, an opportunity appears when:

```text
true academic / career / preference value remains high
but applicant-side competition is temporarily lower than that value would imply
```

So the project should not only estimate admission probability. It should also estimate whether a school-major group is overpriced, fairly priced, or underpriced relative to comparable alternatives.

## What The Four Images Say

| Image | Case Mechanism | Modeling Name | What The System Should Learn |
| --- | --- | --- | --- |
| 1 | The same or similar major is split into different professional groups, causing large cutoff-rank differences. | `group_partition_mispricing` | The item must be `school + major_group`, not just school or major. Group composition changes can dominate school-level value. |
| 2 | High-value majors at Shanghai University of Finance and Economics / Wuhan University were admitted at much easier ranks than earlier historical anchors suggested. | `historical_line_overdeterrence` | Historical high cutoffs can scare away applicants when current grouping, quota, or market attention changes. |
| 3 | Renmin University law was listed separately. Higher-score applicants saw previous high cutoffs and did not fill it, creating a leak opportunity. | `standalone_major_anchor_discount` | A strong standalone major may be under-filled when applicants over-anchor on old, non-comparable historical lines. |
| 4 | Sichuan University electrical engineering was affected by a public incident and later rebound dynamics. | `sentiment_shock_discount` | School-level public opinion can create temporary discount and rebound risk. Sentiment is a market signal, not a pure quality signal. |

The common structure is:

```text
structural change or narrative shock
-> historical cutoff becomes less comparable
-> applicants misread risk / value
-> competition deviates from true value
-> opportunity or trap appears
```

## Opportunity Types

### 1. Group Partition Mispricing

This happens when similar majors are placed into different professional groups and the market prices the groups unevenly.

Signals:

- same school has multiple groups containing adjacent major clusters
- group-level cutoff rank differs more than peer/major value explains
- one group has acceptable tail majors but is avoided because of group label or historical memory
- group code changed or group composition changed from previous years

Risk:

- the cheap group may contain unacceptable tail majors
- historical group labels may not be comparable
- opportunity can disappear after applicants notice the split

### 2. Historical Line Overdeterrence

This happens when applicants over-anchor on an old high cutoff and skip a current opportunity.

Signals:

- old corresponding major/major-class cutoff was very high
- current year has new grouping, changed quota, changed major list, or standalone listing
- peer schools/majors imply the current group is valuable
- current predicted competition is easier than value peers

Risk:

- if many applicants rediscover the same signal, cutoff can rebound sharply

### 3. Standalone Major Anchor Discount

This is the corrected interpretation of the Renmin University law example. The mechanism is not that the major is weak. The mechanism is:

```text
strong major is listed separately
-> applicants compare it to old high historical lines
-> many high-score applicants self-filter out
-> effective competition is lower than expected
-> lower-rank applicant can hit a high-value major
```

Signals:

- professional group contains one or very few majors
- the major has strong reputation or strong career value
- historical corresponding cutoff is high
- new group has weak comparability to old data
- current opportunity is primarily from applicant psychology, not quality decline

Risk:

- the major can rebound to its true price once market attention returns

### 4. Sentiment Shock Discount

This happens when a school or major is temporarily discounted because of public opinion, controversy, or negative short-term narrative.

Signals:

- school/major public sentiment has a recent negative shock
- cutoff rank worsened more than peer schools/majors
- underlying major quality did not obviously deteriorate
- later year may show rebound

Risk:

- the discount may reflect real institutional risk, not just temporary sentiment
- rebound risk is high if the shock is already absorbed by the market

## Mathematical Modeling

Use a two-part model:

1. Admission and assignment model: can the user get in, and what major might they get?
2. Market mispricing model: is this professional group cheaper or more expensive than its true peer-adjusted value?

### Core Variables

For each candidate professional group `i`:

```text
p_i        = admission probability
u_i        = user-specific major utility
s_i        = school/platform utility
c_i        = city utility
t_i        = tail-assignment risk
b_i        = blacklist risk
q_i        = quota stability score
v_i        = variance opportunity score
h_i        = historical-anchor overdeterrence score
g_i        = group partition / restructuring score
m_i        = peer-adjusted market mispricing score
e_i        = evidence strength
r_i        = rebound risk
```

The existing project already has parts of this:

| Variable | Current Code Base |
| --- | --- |
| `p_i` | `admission_prob`, `StrategyTag`, 2025 backtest |
| `u_i` | `major_utility_mean`, `major_utility_min`, `major_utility_dispersion` |
| `t_i` | `tail_assignment_risk`, `bundle_type`, `adjustment_advice` |
| `q_i` | `quota_stability_score` |
| `v_i` | `variance_opportunity_score` |
| `crowding` | `tradeoff_policy._crowding_risk`, `market_behavior_notes` |

Missing pieces:

```text
market_mispricing_score
historical_anchor_overdeterrence
standalone_major_anchor_discount
group_restructure_score
sentiment_shock_discount
rebound_risk
evidence_strength
opportunity_type
```

### Peer-Adjusted Value

Estimate a peer value score:

```text
Value_i =
  w_school * s_i
  + w_major * u_i
  + w_city * c_i
  + w_outcome * career_value_i
```

Then estimate market difficulty. Because smaller rank means harder admission, convert rank into a monotone difficulty score:

```text
Difficulty_i = -z(log(predicted_cutoff_rank_i))
```

Higher `Difficulty_i` means harder to enter.

A professional group is potentially underpriced when value is high but difficulty is not correspondingly high:

```text
MarketMispricing_i = Value_i - ExpectedDifficultyFromPeers_i
```

In implementation, use a peer model:

```text
ExpectedDifficultyFromPeers_i =
  f(school_tier, city_tier, major_cluster, quota, subject_group, batch)
```

Then:

```text
underpriced_i = Value_i - ActualOrPredictedDifficulty_i
```

Positive residual means the group looks cheaper than comparable groups.

### Opportunity Score

The candidate opportunity score should not be a replacement for admission probability. It is a separate signal used for recall and portfolio construction.

```text
OpportunityScore_i =
  0.25 * market_mispricing_i
  + 0.18 * group_restructure_score_i
  + 0.16 * historical_anchor_overdeterrence_i
  + 0.12 * quota_expansion_score_i
  + 0.10 * variance_opportunity_score_i
  + 0.10 * sentiment_shock_discount_i
  + 0.09 * standalone_major_anchor_discount_i
  - 0.22 * tail_assignment_risk_i
  - 0.18 * blacklist_risk_i
  - 0.12 * rebound_risk_i
  - 0.10 * evidence_uncertainty_i
```

The weights are initial priors, not final truth. They should be tuned by 2025 backtest and ablation.

### Final Recommendation Score

Final ranking should combine probability, user utility, and opportunity:

```text
FinalScore_i =
  alpha * p_i
  + beta  * UserFit_i
  + gamma * OpportunityScore_i
  + delta * SafetyScore_i
  - lambda * RiskPenalty_i
```

But the more important design is not the formula. It is the routing:

```text
high p_i + high safety                 -> safe_anchor_pool
medium p_i + high user fit             -> target_core_pool
lower p_i + high opportunity score     -> rush_opportunity_pool
high opportunity + high tail risk      -> explain_only_or_manual_review
high value + high rebound risk         -> volatile_rush_pool
```

This avoids the current failure mode where a risky but genuinely valuable opportunity is simply penalized away.

## Portfolio Rule

The volunteer table should not be a single global top-k sort. It should be a constrained portfolio:

```text
VolunteerPlan =
  top rush_opportunities
  + target_core choices
  + safe anchors
  + backup anchors
```

Suggested constraints:

```text
at least K safe anchors
at most M high-rebound opportunities
no first-hit critical prefix with blacklist risk
no opportunity row without explicit evidence
no high-tail-risk row unless user accepts adjustment risk
```

For each high-opportunity row, report:

```text
opportunity_type
why_market_may_underprice_it
what_could_go_wrong
whether_it_is_a_true_opportunity_or_a_trap
evidence_strength
```

## How This Explains The Latest Backtest

The latest 2025 backtest showed:

```text
full policy: preferred-major hit = 21.7%, avg utility = 0.493
no_tradeoff_policy: preferred-major hit = 47.8%, avg utility = 0.620
```

This is useful negative evidence. It suggests that the current full tradeoff policy may over-penalize preference-heavy or opportunity-heavy groups after coverage improved to 81.5%.

The modeling implication:

```text
Do not directly subtract risk from value.
First classify whether risk is avoid-risk, explainable opportunity risk, or rebound risk.
Then route candidates into the right portfolio bucket.
```

In other words, the next improvement should not simply lower `tail_risk_penalty_weight`. It should add an opportunity-aware exception:

```text
if opportunity_score is high
and blacklist risk is low
and evidence_strength is high
then keep the group in rush_opportunity_pool
even if tail_assignment_risk is medium
```

## Proposed Data Schema

Add an opportunity block to each `MajorGroupRow` or a separate `OpportunitySignal` object:

```json
{
  "opportunity_score": 0.74,
  "opportunity_type": [
    "standalone_major_anchor_discount",
    "historical_line_overdeterrence"
  ],
  "market_mispricing_score": 0.68,
  "group_restructure_score": 0.82,
  "historical_anchor_overdeterrence": 0.76,
  "sentiment_shock_discount": 0.10,
  "rebound_risk": 0.44,
  "evidence_strength": 0.71,
  "opportunity_explanation": "Strong standalone major; old cutoff is a weak comparator after group restructuring; current peer-adjusted difficulty looks lower than value."
}
```

## Implementation Plan

### P0: Documentation And Labels

Create rule-based labels for the four opportunity types:

```text
group_partition_mispricing
historical_line_overdeterrence
standalone_major_anchor_discount
sentiment_shock_discount
```

### P1: Feature Builder

Add:

```text
recommendation/opportunity_radar.py
```

Core function:

```python
score_opportunity(row, profile, peer_context, history_context) -> OpportunitySignal
```

### P2: Rerank Integration

Modify `tradeoff_policy` so opportunity signals route candidates into pools instead of being swallowed by penalties.

### P3: Report And Critic

The report should explicitly say:

```text
This row is not merely "risky".
It is a high-value opportunity because [mechanism].
The main failure mode is [risk].
```

The critic should reject:

```text
high opportunity score without evidence
high opportunity row with hidden blacklist risk
standalone-major opportunity that is actually a non-comparable fake match
sentiment discount treated as quality decline without evidence
```

### P4: Evaluation

Use 2025 backtest to compare:

```text
full_current
no_tradeoff_policy
full_plus_opportunity_radar
opportunity_only_rush_pool
safe_first
probability_only
```

Metrics:

```text
success_rate
preferred_major_hit_rate
selected_major_hit_rate
tail_assignment_rate
blacklist_hit_rate
average_assigned_major_utility
opportunity_recall_at_first_hit
missed_opportunity_count
```

## Interview Narrative

The clean way to explain this:

> I realized that volunteer planning is not only an admission-probability problem. Some of the best opportunities come from market mispricing: professional-group restructuring, historical cutoff anchoring, standalone major listing, quota changes, and public-sentiment shocks. So I model each school-major group as both a risk object and a market-priced asset. Admission probability tells us whether the student can enter; opportunity score tells us whether the group is underpriced relative to comparable value. The final volunteer plan is a portfolio of safe anchors, target cores, and explainable rush opportunities, with critic checks for tail-assignment and blacklist risk.

One-line version:

> The system should not only ask "can the student get in"; it should ask "is this professional group being mispriced by the market, and is the risk acceptable enough to place it in the portfolio?"

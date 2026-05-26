# Arbitrage Reverse Inference Model

Date: 2026-05-20

This note consolidates the recent strategy discussion into an implementation-oriented model design for GaokaoAgent. The goal is to turn "low-rank students entering higher-tier schools or even front majors" from anecdotal cases into auditable, backtestable signals.

## Problem Anchor

Volunteer planning is not "what score maps to what university." It is a second selection process after the exam.

The exam score measures problem-solving performance under a standardized test. Volunteer planning adds a separate market mechanism: information quality, risk tolerance, family resources, acceptable sacrifices, professional-group structure, and applicant psychology.

The project goal is:

```text
Find personalized arbitrage opportunities where a student can exchange acceptable sacrifices
for a materially better admission outcome than same-rank conventional choices.
```

The opportunity is personalized. A group is not a leak for everyone. It becomes a leak only when:

```text
market discount exists
and the student's tolerance/profile can absorb the discount source
and the final assignment remains acceptable.
```

## Case Patterns We Have Discussed

| Case | Opportunity Type | Hidden Exchange |
| --- | --- | --- |
| Dalian University of Technology Panjin joint program | `brand_discount_front_major_arbitrage` | Accept joint-program / campus / tuition / niche-major labels to enter a higher brand and hit a front major. |
| Central Academy of Fine Arts art management | `symbolic_capital_opportunity` | Use family resources and tolerance for nonstandard career paths to buy industry-top identity, face value, and social capital. |
| Liaocheng University / old public undergraduate example | `public_floor_lift_opportunity` | Sacrifice major preference and sometimes region to move from private/weak options to old public本科. |
| Beijing Sport University joint program | `tuition_campus_brand_discount` | Accept high tuition, Hainan campus, restrictions, and cold majors to access a stronger brand. |
| "二本线上一本 / 一本线上双一流" | `relative_tier_lift` | Prestige is rank-band relative, not absolute. A good opportunity is above the student's counterfactual tier. |

## Sacrifice Vector

Arbitrage needs a price. The student gives up something that most applicants are unwilling or unable to give up.

```text
SacrificeVector_i =
[
  region_sacrifice,
  major_sacrifice,
  tuition_sacrifice,
  campus_sacrifice,
  pathway_sacrifice,
  adjustment_sacrifice,
  employment_uncertainty_sacrifice
]
```

The student has a matching tolerance vector:

```text
ToleranceVector_s =
[
  region_tolerance,
  major_tolerance,
  tuition_tolerance,
  campus_tolerance,
  pathway_tolerance,
  adjustment_tolerance,
  employment_uncertainty_tolerance
]
```

The sacrifice is acceptable only when:

```text
SacrificeCost(s, i) =
  sum_k sacrifice_i,k * (1 - tolerance_s,k) * weight_s,k
```

is low enough relative to the lift.

Typical mappings:

- Rich family + brand/face need -> can absorb tuition and nonstandard pathway sacrifice.
- Major-flexible student -> can absorb cold-major and adjustment sacrifice.
- Region-flexible student -> can absorb remote city or non-main-campus sacrifice.
- Employment-ROI family -> cannot absorb high tuition or weak career certainty unless the employment path is clear.

## Counterfactual Baseline

Every opportunity must be measured against what the same student would normally get.

```text
CounterfactualBaseline(s) =
  expected school tier
  expected public/private status
  expected major quality
  expected city tier
  expected cost type
```

Then:

```text
RelativeLift(s, i) =
  school_tier_lift
  + public_private_lift
  + industry_prestige_lift
  + city_resource_lift
  + brand_face_lift
  + cost_saving_lift
```

"名校" is therefore relative:

- top rank: 清北 / 华五 / 人大 front-major opportunities
- high rank: stronger 985 / 211 cold-major opportunities
- middle rank: 双一流 / old一本 / strong provincial university opportunities
- low rank: public本科 / old本科 opportunities
-本科 boundary: avoiding private high-fee or专科 fallback

## Two-Stage Admission And Assignment

The Dalian case shows that we cannot stop at "can enter the group." We need to model:

1. Can the student enter the professional group?
2. After entering, can the student be assigned to the best or acceptable major?

For group `g`, student rank `r`, and major `m`:

```text
P(final success)
= P(group admitted | r, g)
  * P(assigned acceptable major | admitted, r, g, m choices)
```

For a front major:

```text
P(front major hit)
= P(group admitted)
  * P(number of admitted higher-priority applicants choosing front major < quota_front)
```

Because we do not observe all applicants' preference lists, estimate this through proxies:

- historical major-level min ranks
- current group composition
- quota by major
- new major / old major status
- tuition and campus labels
- major popularity cluster
- whether the top-looking major is actually niche or hard to understand
- whether high-rank applicants are deterred by old high cutoffs
- whether the group is being widely promoted this year

## Front-Major Arbitrage

Some cases are stronger than "low rank entered a better school." They are:

```text
low-rank student entered a discounted group and still hit one of the best majors.
```

This needs a separate score:

```text
FrontMajorArbitrageScore(s, g) =
  P(group admitted)
  * P(front major hit | group admitted)
  * FrontMajorValue(s, g)
  * RelativeLift(s, g)
  - SacrificeCost(s, g)
  - TailAssignmentRisk(s, g)
  - ReboundRisk(g)
```

Useful positive signals:

- group contains one high-value but misunderstood/niche front major
- group-level label is discounted by tuition, campus, cooperation, region, or cold companion majors
- high-score applicants are likely scared away by historical front-major rank
- the student ranks high enough within the new lower-demand entrant pool
- front major quota is not tiny relative to expected demand
- group has acceptable tail majors if front-major hit fails

Useful negative signals:

- front major quota is extremely small
- front major is obvious and heavily publicized
- group discount source disappeared this year
- major assignment rules make front major unlikely unless the student is near the top of admitted entrants
- unacceptable tail majors require obeying adjustment

## Reverse Inference From 2025 Labels

Use 2025 actual outcomes as labels, but only features available before 2025 admission as predictors.

For each historical-like candidate case:

```json
{
  "student_rank": 18888,
  "candidate_group": "...",
  "pre_2025_features": {
    "historical_group_min_rank": "...",
    "historical_major_min_ranks": "...",
    "quota": "...",
    "tuition": "...",
    "campus_label": "...",
    "major_mix": "...",
    "new_major_ratio": "...",
    "school_tier": "...",
    "major_popularity": "...",
    "restriction_count": "..."
  },
  "labels": {
    "group_admitted": true,
    "assigned_major": "...",
    "assigned_major_utility": 0.0,
    "front_major_hit": true,
    "tail_assignment": false
  }
}
```

Then learn or calibrate:

```text
P(group_admitted)
P(front_major_hit | group_admitted)
P(tail_assignment | group_admitted)
RelativeLift
ReboundRisk
```

Start with transparent scoring and logistic calibration before complex ML:

```text
logit(P(front_major_hit)) =
  beta0
  + beta1 * entrant_pool_discount
  + beta2 * front_major_quota_share
  + beta3 * historical_anchor_overdeterrence
  + beta4 * niche_major_understanding_gap
  - beta5 * front_major_obvious_heat
  - beta6 * rebound_risk
```

## Implementation Plan

Add these backend components outside Agent Harness:

1. `CounterfactualBaseline`
   - Estimate same-rank normal outcome tier.
   - Output baseline school tier, public/private type, major quality, city, and cost.

2. `StudentValueModel`
   - Convert student/family profile into value weights and tolerance vector.
   - Explicitly model brand/face, employment ROI, public-school preference, cost sensitivity, major strictness, city flexibility, and adjustment tolerance.

3. `OpportunityRadar`
   - Detect discount sources: cold major, tuition filter, campus discount, region sacrifice, new major, group restructure, historical anchor overdeterrence, low attention, sentiment shock.

4. `AssignmentOpportunityModel`
   - Estimate not only group admission, but also front-major hit and tail-major risk.
   - Use major quota share, major-level historical ranks, major popularity, group mix, and current discount features.

5. `ArbitrageScorer`
   - Combine relative lift, opportunity gap, sacrifice fit, assignment probability, and rebound risk.

6. `PortfolioPlanner`
   - Place opportunities into separate pools:
     - `front_major_arbitrage_pool`
     - `relative_tier_lift_pool`
     - `symbolic_capital_pool`
     - `public_floor_lift_pool`
     - `employment_roi_pool`
     - `safe_anchor_pool`

7. `Backtest/Ablation`
   - Evaluate whether the new modules improve:
     - tier lift vs counterfactual baseline
     - selected/front-major hit rate
     - tail-assignment rate
     - blacklist hit rate
     - wasted score rate
     - assigned major utility

## How This Connects To Existing Code

Existing pieces:

- `admission_prob`: group-level feasibility
- `major_utility_mean/min/dispersion`: student-major fit
- `tail_assignment_risk`: downside of obeying adjustment
- `quota_stability_score`: stability
- `variance_opportunity_score`: high-variance opportunity proxy
- `crowding_risk`: simple market competition proxy
- `first_hit_prob`: which volunteer rows actually matter
- 2025 backtest and ablation: real outcome evaluation

Missing pieces to implement:

- counterfactual same-rank baseline
- student tolerance vector
- explicit sacrifice vector
- relative tier lift
- front-major assignment probability
- rebound risk from publicity / repeated case exposure
- opportunity-type routing pools

## Core Claim

The system should not claim:

```text
Low scores can always enter famous schools.
```

It should claim:

```text
Some higher-tier outcomes are discounted by sacrifices that most applicants cannot accept.
If a specific student can accept those sacrifices and the assignment risk is controlled,
the system can identify personalized arbitrage opportunities and place them safely in a volunteer portfolio.
```


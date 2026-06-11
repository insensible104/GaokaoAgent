# Strategy Coverage and Plan-Change Explanation Design

## Goal

Make the online Guangdong recommendation path produce a defensible rush/target/safe slate without manufacturing weak candidates, and explain how current-year plan evidence changes the recommendation.

## Evidence From the Current System

- `GaokaoQuantEngine.search_major_groups` sorts by historical minimum rank and truncates with `head(target_count)`. This systematically over-samples harder schools and removes later target/safe candidates.
- `game_agent` applies one global Pareto filter before the runtime mix selector. A strategy bucket can therefore be under-covered before the selector gets a chance to satisfy the requested mix.
- The runtime policy exposes a desired mix but does not expose source-pool counts, deficits, or the reason a deficit was filled from another bucket.
- Plan-change events and research evidence are attached to rows, but the student view does not receive a concise before/after recommendation explanation.

## Chosen Approach

Use candidate coverage diagnostics plus constrained recovery. Do not change the probability model or relabel rows merely to satisfy a quota.

1. **Stratified search truncation**
   - Split the historical candidate window by rank difference before truncation.
   - Reserve capacity for harder, near-rank, and safer candidates.
   - Fill unused capacity by preference-aware priority.
   - Preserve deterministic ordering and deduplicate by school and major-group key.

2. **Strategy-aware Pareto retention**
   - Run Pareto retention independently inside rush, target, and safe buckets.
   - Retain at least the desired count plus a small reserve when enough candidates exist.
   - Never promote a row to another strategy label solely to fill a quota.

3. **Coverage report and constrained recovery**
   - Record counts at `classified`, `post_pareto`, and `selected` stages.
   - Record desired counts, deficits, and fallback selections.
   - Fill deficits from remaining rows by quality score, but report the mismatch prominently.
   - Mark a plan as `coverage_sufficient=false` when a required bucket cannot meet its minimum.

4. **Plan-change explanation**
   - For each selected row, summarize current plan changes as `before -> after`, source boundary, direction, and whether the change affected ranking.
   - Deterministic official/local plan diffs may affect ranking.
   - Reference-only research signals may explain uncertainty but may not override official plan fields.
   - Contradictory evidence is retained as a review item instead of being silently averaged.

## Data Contract

Add a `coverage_report` under `GameMatrix.optimization_summary`:

```json
{
  "desired": {"rush": 9, "target": 15, "safe": 6},
  "classified": {"rush": 40, "target": 28, "safe": 35},
  "post_pareto": {"rush": 18, "target": 20, "safe": 12},
  "selected": {"rush": 9, "target": 15, "safe": 6},
  "deficits": {},
  "coverage_sufficient": true,
  "actions": ["target: retained 20 candidates before runtime selection"]
}
```

Selected rows expose a compact `plan_change_explanation` containing change types, evidence lines, ranking impact, and review status.

## Quality Gates

- Search truncation must preserve all three rank-side buckets when each exists in the source data.
- Strategy-aware Pareto must not reduce a bucket below its requested count when enough valid rows exist.
- No strategy label may be rewritten to make the mix look balanced.
- Coverage deficits must be visible in API output and the student view.
- Official data has priority over reference-only research evidence.
- Existing frozen/backtest artifacts remain read-only; runtime changes require new representative-profile checks before external quality claims.

## Verification

- Unit tests for stratified search truncation and strategy-aware Pareto retention.
- Runtime policy tests for desired/available/selected deficits.
- Representative profiles across physics/history and multiple ranks.
- API/browser check that the student can see actual mix, target mix, deficit explanation, and plan-change reason.
- Existing recommendation, probability-boundary, decision-trace, report, build, and lint checks remain green.

## Scope Boundary

This iteration does not retrain probability or RL models, claim calibration, or fabricate 2026 official data. It improves candidate coverage, selection transparency, and evidence conflict handling around the existing models.

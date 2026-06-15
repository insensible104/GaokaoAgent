# Competitive Differentiation Score

Date: 2026-06-15

## Claim

Before the official 2026 admission plan arrives, PathFinder should not pretend it has plan-change alpha. It should quantify whether a case is differentiated from generic AI/report workflows through evidence coverage, external challenge, delivery trace, preference fidelity, official data boundaries, and plan-change readiness.

## Evidence Added

- `frontend/src/lib/competitiveDifferentiationScore.ts` defines `competitive_differentiation_score_v1`.
- The score uses six weighted dimensions:
  - evidence coverage: 20
  - external plan challenge: 15
  - delivery trace: 20
  - preference fidelity: 15
  - official data boundary: 15
  - plan-change alpha: 15
- `plan_change_alpha` is blocked unless official plan-change evidence is attached and applied to ranking.
- `frontend/src/components/CompetitiveDifferentiationPanel.tsx` surfaces the score in the result workflow after the external plan comparator.
- Behavior tests prove weak cases cannot claim competitive advantage, while strong cases can reach flagship status only with official plan-change evidence and clean external audit.

## Product Boundary

This is a benchmark-readiness score. It does not claim that Qianwen, Tencent, or any external product is wrong. It only says whether PathFinder has enough auditable evidence to claim a stronger delivery workflow for this case.

## Next Iteration

When the 2026 official plan arrives, replace plan-change readiness with real plan-change opportunity scoring: quota deltas, group splits/merges, selection requirement changes, comparable-history reliability, opportunity score, and trap risk.

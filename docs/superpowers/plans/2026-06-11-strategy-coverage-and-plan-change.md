# Strategy Coverage and Plan-Change Explanation Implementation Plan

**Goal:** Preserve qualified rush/target/safe candidates through online search and selection, expose coverage deficits honestly, and explain plan-change evidence for selected rows.

**Boundary:** Coverage improvements do not establish improved admission quality or calibration.

## Task 1: Stratified Candidate Search

- [x] Add a failing coverage test for harder, near-rank, and safer candidates.
- [x] Implement deterministic 30/40/30 stratified truncation with remainder fill.
- [x] Replace rank-sorted `head(target_count)` and run focused regressions.

## Task 2: Strategy-Aware Pareto Retention

- [x] Add failing tests for per-strategy capacity retention.
- [x] Implement per-bucket Pareto ordering and coverage reporting.
- [x] Integrate retention before runtime selection.
- [x] Record desired, classified, post-Pareto, selected, deficits, and actions.

## Task 3: Student-Facing Coverage Explanation

- [x] Add frontend static coverage requirements.
- [x] Render target versus actual mix and honest deficit actions.
- [x] Run frontend smoke, build, and lint checks.

## Task 4: Plan-Change Explanation and Conflict Boundary

- [x] Add tests for official before/after changes and contradictory references.
- [x] Implement source-tiered explanations and ranking-impact boundaries.
- [x] Attach explanations after deterministic and research evidence stages.
- [x] Render only evidence-bearing plan-change explanations.
- [x] Run backend and frontend focused checks.

## Task 5: Representative-Profile Evaluation

- [x] Add aggregate runtime-mix audit tests.
- [x] Record candidate supply, selected mix, deficits, latency, and data status.
- [x] Run four physics/history representative API cases.
- [x] Write `logs/runtime_mix_audit_2026-06-11.json`.
- [x] Compare with frozen-plan generation coverage without making a quality claim.

## Task 6: Release Verification

- [x] Run all focused backend recommendation tests.
- [x] Run frontend smoke tests, build, and lint.
- [x] Verify one explicit-profile API/browser workflow.
- [x] Verify profile values, data vintage, mix coverage, trace, and plan changes.
- [x] Run `git diff --check` and inspect the scoped diff.

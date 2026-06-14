# Subject-Aware Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the collapsed global admission-probability calibration with a subject-aware, cross-validated beta calibration while preserving honest strategy labels and full volunteer-plan delivery.

**Architecture:** Keep calibration offline-fitted and runtime-light. The artifact stores a global beta model plus history/physics models blended toward the global model; runtime selects by normalized subject group and falls back globally. Coverage recovery may fill unused plan slots from remaining real candidates, but it must preserve each candidate's original strategy tag and expose the deficit.

**Tech Stack:** Python 3.11, Pydantic, scikit-learn for offline fitting, pytest-style smoke tests, React static contract tests.

---

### Task 1: Subject-Aware Probability Artifact

**Files:**
- Modify: `backend/src/recommendation/probability_calibration.py`
- Modify: `backend/data/probability_calibration_2025.json`
- Test: `backend/src/test_probability_calibration_runtime_smoke.py`

- [ ] Add failing tests proving history and physics use different calibrated probabilities, unknown subjects use the global model, and outputs stay in `[0, 1]`.
- [ ] Run `python -m pytest src/test_probability_calibration_runtime_smoke.py -q` from `backend` and confirm the new tests fail because segmented beta artifacts are unsupported.
- [ ] Add backward-compatible beta model fields and subject normalization to the calibration component.
- [ ] Fit the 2025 artifact from `logs/quant_calibration_2025_200plus_rows.jsonl` using grouped five-fold validation and a fixed shrinkage prior of 250 rows.
- [ ] Re-run the focused tests and confirm they pass.

### Task 2: Runtime Subject Routing

**Files:**
- Modify: `backend/src/agents/game_agent.py`
- Test: `backend/src/test_game_agent_probability_calibration_smoke.py`

- [ ] Add a failing test proving online calibration passes the user's subject group into the artifact selector and reports `historical_beta_subject` metadata.
- [ ] Run the focused test and confirm it fails on the current subject-agnostic API.
- [ ] Route `profile.subject_group` through `_calibrate_online_probability` without changing raw probability, Z-score strategy classification, or evidence year.
- [ ] Re-run the focused tests and confirm they pass.

### Task 3: Honest Coverage Recovery

**Files:**
- Modify: `backend/src/recommendation/strategy_coverage.py`
- Modify: `backend/src/agents/game_agent.py`
- Test: `backend/src/test_strategy_coverage_smoke.py`

- [ ] Add failing tests proving under-supplied target buckets retain their deficit and that remaining real rush/safe rows may fill plan capacity without relabeling.
- [ ] Run the focused tests and confirm the recovery helper is missing.
- [ ] Add deterministic capacity filling after strategy selection, preserving tags and recording `capacity_fill` separately from strategy coverage.
- [ ] Re-run tests and verify the history 70k runtime case returns the configured total count while still reporting the target deficit.

### Task 4: Evidence and Regression Gates

**Files:**
- Modify: `backend/src/evaluation/runtime_mix_audit.py`
- Test: `backend/src/test_runtime_mix_audit_smoke.py`
- Create: `logs/subject_calibration_2025_audit.json`

- [ ] Record grouped five-fold Brier, log loss, ECE, AUC, high-score spread, and per-subject metrics for global isotonic versus subject beta.
- [ ] Require all five folds to beat the global isotonic Brier baseline before the artifact is considered eligible.
- [ ] Run focused backend tests, the broader recommendation regression suite, and frontend static/build checks.
- [ ] Run the four-case runtime audit and browser verification; confirm calibrated ranges differ by subject and no technical errors leak into student copy.

### Task 5: Completion Review

**Files:**
- Review all modified files and generated audit artifacts.

- [ ] Run `git diff --check` and inspect the scoped diff.
- [ ] Confirm claims are bounded to 2025 Guangdong retrospective evidence and do not imply 2026 outcome quality.
- [ ] Update the active plan with measured results and remaining risks.

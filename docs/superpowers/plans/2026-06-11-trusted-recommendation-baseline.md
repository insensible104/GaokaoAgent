# Trusted Recommendation Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the default Guangdong recommendation path refuse fabricated critical inputs, disclose its data vintage, and avoid presenting correlated volunteer outcomes as precise independent probabilities.

**Architecture:** Keep the existing supervisor, quant engine, recommendation rows, and report pipeline. Add small deterministic policy helpers at the profile and plan boundaries, expose their status through existing response models, and make the frontend render the resulting trust notices. No new agent or data platform is introduced.

**Tech Stack:** Python, Pydantic, LangGraph, FastAPI, React, TypeScript, existing smoke-test style.

---

### Task 1: Block Fabricated Critical Inputs

**Files:**
- Modify: `backend/src/agents/profiling_agent.py`
- Test: `backend/src/test_profiling_critical_inputs_smoke.py`

- [x] **Step 1: Write failing tests** asserting that missing score and rank remain missing and produce a structured blocked result instead of synthetic defaults.
- [x] **Step 2: Run** `python backend/src/test_profiling_critical_inputs_smoke.py` and verify failure against current inference behavior.
- [x] **Step 3: Implement** a deterministic critical-input gate reused by `profiling_agent_node` before quant recommendation.
- [x] **Step 4: Re-run** the smoke test and relevant profiling/API tests.

### Task 2: Publish Data-Vintage Boundaries

**Files:**
- Create: `backend/src/recommendation/data_vintage.py`
- Modify: `backend/src/models/game_matrix.py`
- Modify: `backend/src/agents/game_agent.py`
- Modify: `backend/src/agents/report_agent.py`
- Test: `backend/src/test_data_vintage_smoke.py`

- [x] **Step 1: Write failing tests** for detecting the latest historical, enrollment-plan, and rank-table years from `backend/data`.
- [x] **Step 2: Run** the new smoke test and verify the metadata is absent.
- [x] **Step 3: Implement** `RecommendationDataVintage` and attach it to `GameMatrix` and report warnings.
- [x] **Step 4: Re-run** data-vintage, volunteer-plan, report, and API schema smoke tests.

### Task 3: Remove Independent-Probability Overclaim

**Files:**
- Modify: `backend/src/models/game_matrix.py`
- Modify: `backend/src/recommendation/major_choice_planner.py`
- Modify: `backend/src/agents/report_agent.py`
- Test: `backend/src/test_volunteer_plan_probability_boundary_smoke.py`

- [x] **Step 1: Write failing tests** requiring plan-level probability status to be marked heuristic and bounded by an explicit uncertainty interval.
- [x] **Step 2: Run** the test and verify current precise `1 - product(1-p)` output fails the requirement.
- [x] **Step 3: Implement** conservative display bounds while retaining first-hit weights for ordering diagnostics.
- [x] **Step 4: Re-run** volunteer-plan, quant scorecard, and report evidence smoke tests.

### Task 4: Surface Trust Status in the Student View

**Files:**
- Modify: `frontend/src/components/GameMatrixView.tsx`
- Modify: `frontend/src/components/GameMatrixView.quantEvidence.test.mjs`

- [x] **Step 1: Extend the static smoke** to require data vintage, heuristic probability labeling, and uncertainty-bound rendering.
- [x] **Step 2: Run** the smoke and verify it fails.
- [x] **Step 3: Implement** compact trust notices in the recommendation evidence section.
- [x] **Step 4: Run** the smoke, `npm run build`, and `npm run lint`.

### Task 5: Release Verification

**Files:**
- Verify only; do not alter unrelated agency files.

- [x] **Step 1: Run** focused backend smoke tests for profiling, data vintage, volunteer plans, quant scorecards, reports, and API status.
- [x] **Step 2: Run** frontend evidence smoke, build, and lint.
- [x] **Step 3: Inspect** `git diff --check`, `git status --short`, and the scoped diff.
- [x] **Step 4: Record** remaining known limitations: 2026 enrollment data absent, no cross-session memory, and no field-level source-conflict resolver yet.

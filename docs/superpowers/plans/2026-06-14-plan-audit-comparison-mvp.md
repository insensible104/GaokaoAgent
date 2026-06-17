# Plan Audit And Comparison MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first three-day differentiation MVP: a plan-audit summary and A/B plan-comparison layer that positions PathFinder as a volunteer-plan risk auditor rather than another broad Gaokao chatbot.

**Architecture:** Reuse the existing `VolunteerPlan` statistics and `plan_quality_audit` checks. Add thin product-facing backend modules for audit summaries and plan comparison, attach the audit summary to `GameMatrix`, then surface a lightweight audit workbench in the existing recommendation result view without introducing a new endpoint.

**Tech Stack:** Python, Pydantic models, pytest smoke tests, React, TypeScript, static frontend smoke tests.

---

### Task 1: Product-Facing Plan Audit

**Files:**
- Create: `backend/src/evaluation/plan_audit.py`
- Test: `backend/src/test_plan_audit_and_comparison_smoke.py`

- [x] **Step 1: Write failing test** requiring `build_plan_audit_summary` to expose protocol version, status, key prefix, coverage, data boundary, and student-facing items.
- [x] **Step 2: Run focused test** and verify failure because `evaluation.plan_audit` is missing.
- [x] **Step 3: Implement minimal module** by reusing `audit_plan_quality`, `VolunteerPlan.calculate_statistics()`, coverage report, and data vintage.
- [x] **Step 4: Re-run focused test** and verify it passes.

### Task 2: A/B Plan Comparison

**Files:**
- Create: `backend/src/evaluation/plan_comparison.py`
- Test: `backend/src/test_plan_audit_and_comparison_smoke.py`

- [x] **Step 1: Write failing test** requiring `compare_volunteer_plans` to prefer a safer lower-tail-risk plan over a risky rush-heavy plan.
- [x] **Step 2: Run focused test** and verify failure because `evaluation.plan_comparison` is missing.
- [x] **Step 3: Implement deterministic comparison** using expected admission probability, first-hit utility, tail risk, safe-anchor coverage, shadowing, and blacklist violations.
- [x] **Step 4: Re-run focused test** and verify it passes.

### Task 3: Frontend Audit Workbench

**Files:**
- Modify: `frontend/src/components/GameMatrixView.tsx`
- Modify: `frontend/src/components/GameMatrixView.quantEvidence.test.mjs`

- [x] **Step 1: Extend static smoke test** to require `"志愿表审计工作台"`, `"方案对比"`, `auditItems`, `plan_audit_summary`, `comparisonSignals`, `keyPrefixAudit`, and `shadowedAudit`.
- [x] **Step 2: Run static smoke test** and verify failure because the UI tokens are absent.
- [x] **Step 3: Implement audit workbench** from backend `plan_audit_summary`, existing `volunteer_plan`, `coverage_report`, `capacity_fill`, and `data_vintage` data.
- [x] **Step 4: Re-run static smoke test** and verify it passes.

### Task 4: Repository Hygiene

**Files:**
- Modify: `.gitignore`

- [x] **Step 1: Add `.codex_tmp*` and `tmp/` ignore rules** so local temporary scripts and generated files are not accidentally staged.

### Task 5: Verification And Publish

**Files:**
- Commit and push only the intended changes.

- [x] **Step 1: Run backend focused tests.**
- [x] **Step 2: Run frontend smoke tests, lint, and build.**
- [x] **Step 3: Use browser verification for the updated frontend.**
- [x] **Step 4: Commit and push the branch to GitHub.**

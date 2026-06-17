# Student Career Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional 12/30-question RIASEC profiling, self-reported MBTI, and career values to the trusted recommendation pipeline.

**Architecture:** A focused backend assessment module validates and scores answer maps. The public analyze request carries raw assessment input, profiling merges measured results into `UserProfile`, and major utility consumes only RIASEC affinity. A separate frontend component owns the selectable questionnaire and sends raw answers through the existing structured profile contract.

**Tech Stack:** FastAPI, Pydantic, Python, React 19, TypeScript, Vite, Node smoke tests, pytest.

---

### Task 1: Canonical Assessment Scoring

**Files:**
- Create: `backend/src/recommendation/student_profile_assessment.py`
- Create: `backend/src/test_student_profile_assessment_smoke.py`

- [ ] Write failing tests for quick/complete completeness, score normalization, top-code ordering, MBTI normalization, and career-value limits.
- [ ] Run `backend/.venv/Scripts/python.exe -m pytest -q src/test_student_profile_assessment_smoke.py` and confirm missing-module failures.
- [ ] Implement `CareerAssessmentInput`, `CareerAssessmentResult`, and `score_career_assessment` with six RIASEC dimensions and `[1,5]` validation.
- [ ] Re-run the focused tests and confirm all pass.

### Task 2: Structured Profile Integration

**Files:**
- Modify: `backend/src/main.py`
- Modify: `backend/src/models/user_profile.py`
- Modify: `backend/src/agents/profiling_agent.py`
- Modify: `backend/src/test_backend_api_status_smoke.py`
- Modify: `backend/src/test_profiling_critical_inputs_smoke.py`

- [ ] Write failing tests proving raw assessment input reaches the explicit profile and measured results override inferred personality fields.
- [ ] Run the two focused tests and verify expected failures.
- [ ] Extend the request/profile models, score the assessment during explicit-profile construction, and mark provenance.
- [ ] Re-run focused tests and preserve text-only client compatibility.

### Task 3: RIASEC-Aware Major Utility

**Files:**
- Modify: `backend/src/recommendation/major_taxonomy.py`
- Modify: `backend/src/recommendation/major_utility.py`
- Create: `backend/src/test_career_profile_major_utility_smoke.py`

- [ ] Write failing tests for aligned/misaligned majors, MBTI invariance, no-assessment neutrality, and blacklist dominance.
- [ ] Run the focused test and confirm failures come from missing affinity behavior.
- [ ] Add category-to-RIASEC weights and a capped affinity bonus with explanation reasons.
- [ ] Re-run the focused test and relevant recommendation tests.

### Task 4: Selectable Questionnaire UI

**Files:**
- Create: `frontend/src/components/StudentCareerProfile.tsx`
- Create: `frontend/src/components/StudentCareerProfile.test.mjs`
- Modify: `frontend/src/components/GaokaoAgentForm.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] Write source-contract tests for three depth modes, 12/30 question sets, five-point answers, optional MBTI, career values, and structured payload wiring.
- [ ] Run the Node test and confirm it fails before the component exists.
- [ ] Implement the separate profile section and require all questions only when a test mode is selected.
- [ ] Re-run Node tests and `npm run build`.

### Task 5: Student-Visible Profile Evidence

**Files:**
- Modify: `frontend/src/components/GameMatrixView.tsx`
- Modify: `frontend/src/components/GameMatrixView.quantEvidence.test.mjs`

- [ ] Write failing assertions for RIASEC, MBTI boundary copy, career values, and measured provenance.
- [ ] Render the compact profile evidence beside explicit recommendation constraints.
- [ ] Verify desktop and 390px mobile layout without horizontal overflow.

### Task 6: End-to-End Verification

**Files:**
- Create: `logs/career_profile_fidelity_audit_2026-06-12.json`

- [ ] Run backend focused and broad tests.
- [ ] Run all frontend source-contract tests and production build.
- [ ] Compare the same student with aligned and non-aligned RIASEC profiles; record candidate/utility changes and confirm admission probability inputs are unchanged.
- [ ] Submit quick and complete modes in the browser and verify evidence, console errors, and responsive layout.

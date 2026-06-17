# PathFinder Conversation Handoff — 2026-06-14

## 1. Product North Star

PathFinder is not trying to beat Qwen by becoming a broader general-purpose Gaokao chatbot. The intended differentiation is:

- Guangdong New Gaokao recommendation quality first.
- A decision-grade quantitative chain rather than fluent but weakly grounded conversation.
- Explicit student constraints, recommendation evidence, uncertainty disclosure, and plan-change explanations.
- Student-first product judgment informed by the founder's own New Gaokao experience.
- Rich profile fields only when they improve recommendation fidelity or explanation quality.

Qwen's advantages remain full-cycle conversation, richer profile collection, brand distribution, and polished product breadth. PathFinder's defensible direction is narrower but deeper: show why a plan changes, what evidence supports it, what can go wrong, and which student constraints are treated as hard boundaries.

## 2. Git and Workspace State

- Repository: `C:\PathFinder`
- Branch: `codex/trusted-recommendation-baseline`
- HEAD: `f540c20 docs: define student career profile design`
- Compared with `origin/main`: 2 commits ahead, 0 behind at handoff time.
- The active goal service currently reports no active goal.
- The working tree is heavily dirty. Most core implementation from this iteration is not committed.
- Do not run `git reset --hard`, `git checkout --`, broad restore commands, or blind pull/rebase operations.
- Treat all existing modifications and untracked files as intentional work until reviewed.
- The local server is not running at handoff time.

Recent committed documents:

- `e5588ca Document strategy coverage recovery design`
- `f540c20 docs: define student career profile design`

## 3. Implemented Recommendation and Trust Chain

### Critical input and provenance

- Missing score/rank are no longer fabricated for formal quantitative recommendation.
- Structured `delivery_profile` fields override LLM/text inference.
- Field-level provenance distinguishes `user_explicit`, `measured_assessment`, and `inferred` values.
- LLM initialization failure can fall back to structured input rather than losing the request.

### Data and probability boundaries

- Recommendation responses expose data vintage and incomplete-data limitations.
- Plan probability is shown as a bounded heuristic range instead of an over-precise independent-event calculation.
- Subject-aware 2025 beta calibration is wired for physics/history with global fallback.
- Calibration evidence is retrospective 2025 Guangdong evidence only; it does not establish 2026 outcome quality.

### Candidate coverage and plan logic

- Candidate search uses stratified rush/target/safe retention rather than rank-only truncation.
- Strategy-aware Pareto retention preserves qualified candidates by bucket.
- Capacity recovery can fill remaining slots without relabeling strategy tags.
- Coverage deficits remain visible instead of being hidden by forced relabeling.
- Key-prefix and shadowed-choice signals explain which volunteer rows materially affect the plan.

### Evidence and change explanations

- Student results expose recommendation evidence, major risks, data boundaries, coverage, and plan-change explanations.
- Official changes and reference claims are separated by source tier.
- Research/reference claims do not alter ranking unless the deterministic evidence boundary allows it.
- Internal delivery review and agency command-center work exists in the dirty tree; preserve it when continuing.

## 4. Student Career Profile Feature

Implemented selectable depth:

- `skip`
- `quick`: 12 RIASEC questions
- `complete`: 30 RIASEC questions

Behavioral boundaries:

- RIASEC is measured and may influence major utility as a small soft signal.
- Current implementation applies `(career_fit - 0.5) * 0.20`, so the maximum adjustment is stricter than the design cap: approximately `[-0.10, +0.10]`.
- Explicit preferred majors carry larger weight.
- Major blacklists remain absolute and cannot be rescued by career fit.
- MBTI is optional self-report and must never change admission probability, major utility, or hard filters.
- Career values are explicit profile context, limited to three, and currently used for display/explanation rather than admission probability.
- Untaken assessments do not fabricate neutral Holland scores.

Key files:

- `backend/src/recommendation/student_profile_assessment.py`
- `backend/src/recommendation/major_taxonomy.py`
- `backend/src/recommendation/major_utility.py`
- `backend/src/models/user_profile.py`
- `backend/src/agents/profiling_agent.py`
- `backend/src/main.py`
- `frontend/src/components/StudentCareerProfile.tsx`
- `frontend/src/lib/careerAssessment.ts`
- `frontend/src/components/GaokaoAgentForm.tsx`
- `frontend/src/components/GameMatrixView.tsx`

Design and implementation documents:

- `docs/superpowers/specs/2026-06-12-student-career-profile-design.md`
- `docs/superpowers/plans/2026-06-12-student-career-profile.md`

## 5. Measured Evidence

### Preference fidelity

Artifact: `logs/preference_fidelity_audit_2026-06-12.json`

- Same score/rank/subject with swapped city, major, and blacklist changed 26 of 30 recommendation rows.
- Blacklist exposure remained zero in both paired cases.
- Structured profile and field provenance were preserved.
- This proves preference sensitivity and hard-constraint fidelity, not improved admission outcomes.

### Subject-aware 2025 calibration

Artifact: `logs/subject_calibration_2025_audit.json`

- 228 frozen profiles and 2,037 matched choices.
- Grouped five-fold validation by `case_id`.
- Brier improved from `0.221404` global isotonic to `0.176223` subject beta.
- All five folds improved Brier.
- AUC improved from `0.615577` to `0.795243`.
- ECE became worse globally (`0.005227` to `0.051508`) because the old aggregate metric benefited from opposing subject biases cancelling out.
- Claim boundary: retrospective 2025 calibration only.

### Runtime strategy coverage

Artifact: `logs/runtime_mix_audit_2026-06-12.json`

- 4 representative runtime cases.
- Coverage sufficient in 3/4 cases.
- Physics cases were 2/2 sufficient; history was 1/2.
- The history rank-70k case had rush deficit 1 and target deficit 12, while capacity filling still produced the requested 45 rows.
- Average response time was 14.33 seconds.
- All cases reported incomplete current-year data.
- This measures candidate supply and composition, not recommendation quality.

### Career profile verification

- Backend focused tests: 12 passed.
- Import-boundary tests: 5 passed when run in an isolated process.
- Frontend smoke tests and production build passed.
- Browser checks verified 12/30 question modes, answer reset, incomplete-assessment blocking, three-value limit, 390px no horizontal overflow, and no console errors.
- Browser screenshot capture timed out; DOM, interaction, dimensions, and console checks succeeded.

## 6. Known Risks and Incomplete Work

### P0

- The core implementation is uncommitted and mixed across many files. Review and create coherent commits before risky Git operations.
- `logs/career_profile_fidelity_audit_2026-06-12.json` was planned but has not been created.
- Run a paired RIASEC audit proving aligned/misaligned career profiles change major utility while admission-probability inputs and outputs remain unchanged.
- Re-run at least one complete structured-profile API flow after starting the server.

### P1

- Full pytest currently reports 182 passed and 5 failed when import-boundary tests run after modules have already been loaded. The same 5 tests pass in isolation. This is an order-dependent test-design issue, not evidence of a production import regression.
- 2026 enrollment-plan/current-year data remains incomplete; student copy must keep disclosing this.
- Runtime coverage is weak for some lower-ranked history profiles.
- No cross-session student memory exists yet.
- Field-level source-conflict resolution is provenance-aware but not a complete interactive correction workflow.

### Product discipline

- Do not spend the remaining launch window adding decorative personality fields.
- Do not let MBTI become recommendation logic.
- Do not claim calibration means guaranteed admission or improved 2026 outcomes.
- Continue prioritizing recommendation fidelity, hard constraints, plan robustness, and student-visible evidence.

## 7. Recommended Next Actions

1. Read this handoff and run `git status --short` before editing.
2. Inspect scoped diffs for the recommendation baseline, calibration, coverage, and career-profile changes.
3. Create the missing career-profile fidelity audit with a fixed student and controlled RIASEC swap.
4. Verify admission probability is invariant to RIASEC/MBTI while major utility responds only to RIASEC.
5. Start the backend and run one browser/API path with explicit city, preferred major, blacklist, risk tolerance, and quick assessment.
6. Commit the current implementation in coherent feature groups without discarding unrelated work.
7. Return to the one-week release checklist: accurate recommendation, visible evidence, failure boundaries, and a usable student workflow.

## 8. Useful Commands

Backend focused verification:

```powershell
C:\PathFinder\backend\.venv\Scripts\python.exe -m pytest -q `
  src/test_student_profile_assessment_smoke.py `
  src/test_career_profile_major_utility_smoke.py `
  src/test_backend_api_status_smoke.py::test_query_request_scores_raw_career_assessment_into_profile_payload `
  src/test_profiling_critical_inputs_smoke.py::test_measured_career_profile_overrides_inferred_personality_fields `
  src/test_user_profile_null_defaults_smoke.py::test_user_profile_does_not_fabricate_untaken_holland_scores
```

Import-boundary verification must currently run separately:

```powershell
C:\PathFinder\backend\.venv\Scripts\python.exe -m pytest -q src/test_import_boundaries_smoke.py
```

Frontend verification:

```powershell
cd C:\PathFinder\frontend
node src\components\StudentCareerProfile.test.mjs
node src\components\GameMatrixView.quantEvidence.test.mjs
node src\components\GaokaoAgentForm.trustCopy.test.mjs
node src\components\MobileOverflow.test.mjs
npm run lint
npm run build
```

Start local application:

```powershell
Start-Process -FilePath 'C:\PathFinder\backend\.venv\Scripts\python.exe' `
  -ArgumentList '-m','uvicorn','main:app','--host','127.0.0.1','--port','8000' `
  -WorkingDirectory 'C:\PathFinder\backend\src' `
  -WindowStyle Hidden
```

Then open `http://127.0.0.1:8000/app/`.

## 9. Suggested New-Conversation Opening Prompt

> 请先阅读 `C:\PathFinder\docs\handoffs\2026-06-14-pathfinder-handoff.md`，再检查当前分支和 dirty worktree。不要重置或覆盖现有改动。继续围绕“核心推荐与量化链路”迭代，先完成 career profile fidelity audit，证明 RIASEC 只影响专业效用、MBTI 不影响推荐、录取概率保持不变；然后根据审计结果修正并完成一次端到端验证。每次使用科研相关 skill 校准结论边界。

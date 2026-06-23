# Evidence Autopilot Real Case v0 Handoff

Date: 2026-06-24

## What Changed

- Added one Real Case v0 source log for the SCUT intelligent-manufacturing opportunity hypothesis.
- Added one reviewed public-evidence fixture with `captured_candidate` cards.
- Added a fixture-backed provider that emits provider results only from captured cards with URL and excerpt.
- Added `real_case_fixture` API state so the UI can distinguish reviewed fixture evidence from demo snapshot and backend fallback.
- Routed captured evidence through Evidence Autopilot, Opportunity Radar, and the report output.

## What This Proves

The system can carry one reviewed public evidence fixture through the opportunity-research loop.

## What This Does Not Prove

- It does not prove admission probability.
- It does not prove graduate-school or employment outcomes.
- It does not prove improved 2026 admission results.
- It does not validate live web or PDF retrieval.
- It does not validate WeChat, Boss, or other operator evidence.

## Verification Commands

```powershell
node frontend/src/components/EvidenceAutopilotRealCaseProvider.test.mjs
node frontend/src/components/EvidenceAutopilotApi.test.mjs
node frontend/src/components/EvidenceAutopilotResultNormalizer.test.mjs
node frontend/src/components/DeepOpportunityRealCase.test.mjs
node frontend/src/components/PathFinderDeepOpportunityReport.test.mjs
node frontend/src/PublicLaunchReadiness.test.mjs

Set-Location frontend
npm run lint
npm run build
Set-Location ..

Set-Location backend
.\.venv\Scripts\python.exe -m pytest src/test_evidence_autopilot_api_smoke.py src/test_backend_api_status_smoke.py -q
Set-Location ..

git diff --check
```

## Latest Verification Result

- Node smoke tests passed.
- Frontend lint passed with 0 errors and 3 existing Fast Refresh warnings.
- Frontend build passed.
- Backend smoke tests passed: 12 passed, 1 existing Pydantic deprecation warning.
- `git diff --check` passed.

## Remaining Work

- Replace fixture-only public evidence with a live official-source provider.
- Add durable operator capture workflow for semi-closed sources.
- Connect quant positioning and 2025 backtest signals to case selection.
- Run outcome validation before making any effectiveness claim.

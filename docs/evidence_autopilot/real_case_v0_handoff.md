# Evidence Autopilot Real Case v0 Handoff

Date: 2026-06-24

## What Changed

- Added one Real Case v0 source log for the SCUT intelligent-manufacturing opportunity hypothesis.
- Added one reviewed public-evidence fixture with `captured_candidate` cards.
- Added a fixture-backed provider that emits provider results only from captured cards with URL and excerpt.
- Added `real_case_fixture` API state so the UI can distinguish reviewed fixture evidence from demo snapshot and backend fallback.
- Routed captured evidence through Evidence Autopilot, Opportunity Radar, and the report output.
- Added an opt-in backend official-source provider contract, with SCUT plan/charter evidence, historical admission score evidence, and school-source major-profile evidence as the first implementations.
- Added a backend `evidenceCoverage` summary so the API exposes captured tasks, missing P0 gates, operator/manual-review tasks, and counselor-review blockers.
- Updated the frontend Evidence Autopilot API adapter to preserve and validate backend `evidenceCoverage` instead of treating incomplete backend responses as connected evidence.
- Added backend `reviewedEvidenceCards` input so compliant human-captured job-market, WeChat, or manual-review evidence can close P0 gates only when it includes task match, URL/review ID, excerpt, capture time, confidence, and review action.
- Added `POST /api/evidence-autopilot/reviewed-evidence` and a JSONL reviewed-evidence ledger. The endpoint generates a `reviewId`, appends an audit record, and converts missing source URLs into `operator-review://<reviewId>` source IDs for downstream Evidence Autopilot use.
- Added case-scoped reviewed-evidence ledger readback. When a research request supplies `caseId` and `enableReviewedEvidenceLedger`, Evidence Autopilot loads matching reviewed cards from the ledger and merges them into the same coverage gate.
- Updated the frontend Evidence Autopilot API adapter so callers can pass `caseId` and `enableReviewedEvidenceLedger` into backend research requests without changing the school/major context model.
- Added `GET /api/evidence-autopilot/reviewed-evidence/{case_id}` to list reviewed-evidence ledger records for one case without mixing records from other cases.

## What This Proves

The system can carry one reviewed public evidence fixture through the opportunity-research loop. The backend can also run an opt-in official-source provider registry, isolate provider failures, capture SCUT public official plan/charter evidence, one public official score-history card, and three school-source major-profile cards when `enableOfficialSourceProvider` is explicitly enabled. The API now reports whether remaining P0 evidence gaps still block counselor review.

## What This Does Not Prove

- It does not prove admission probability.
- It does not prove graduate-school or employment outcomes.
- It does not prove improved 2026 admission results.
- It does not validate generalized live web or PDF retrieval beyond the narrow SCUT score-history provider.
- It does not validate WeChat, Boss, or other operator evidence.
- It does not make a case counselor-ready while `evidenceCoverage.missingP0TaskIds` remains non-empty.
- It does not accept incomplete operator notes as evidence; cards without source URL/review ID and excerpt remain missing evidence.
- It does not yet provide a full reviewer workflow with authentication, screenshots, redaction, or case-level evidence browsing.

## Verification Commands

```powershell
node frontend/src/components/EvidenceAutopilotRealCaseProvider.test.mjs
node frontend/src/components/EvidenceAutopilotApi.test.mjs
node frontend/src/components/EvidenceAutopilotResultNormalizer.test.mjs
node frontend/src/components/DeepOpportunityRealCase.test.mjs
node frontend/src/components/PathFinderDeepOpportunityReport.test.mjs
node frontend/src/PublicLaunchReadiness.test.mjs

Set-Location backend
.\.venv\Scripts\python.exe -m pytest src/test_official_source_provider_smoke.py -q
Set-Location ..

Set-Location frontend
npm run lint
npm run build
Set-Location ..

Set-Location backend
.\.venv\Scripts\python.exe -m pytest src/test_reviewed_evidence_store_smoke.py src/test_evidence_autopilot_coverage_smoke.py src/test_official_source_provider_smoke.py src/test_evidence_autopilot_api_smoke.py src/test_backend_api_status_smoke.py -q
Set-Location ..

git diff --check
```

## Latest Verification Result

- Node smoke tests passed.
- Frontend lint passed with 0 errors and 3 existing Fast Refresh warnings.
- Frontend build passed.
- Backend smoke tests passed: 12 passed, 1 existing Pydantic deprecation warning.
- Official-source provider smoke test passed: 3 passed, 1 existing Pydantic deprecation warning.
- Manual live SCUT provider check captured `rank-history-band` with highest 644, lowest 629, average 631.9.
- Manual live SCUT provider check captured `official-plan-charter` from the 2026 charter and admissions-plan page.
- Manual live SCUT provider check captured `faculty-research-direction`, `undergrad-access`, and `graduate-progression` from WUSIE school pages.
- Provider registry smoke test passed: provider cards and warnings merge without fabricating captured evidence.
- Evidence coverage smoke test passed: `evidenceCoverage` is exposed by both the builder and FastAPI endpoint, and missing P0 tasks keep counselor review blocked.
- Frontend API adapter smoke test passed: backend `evidenceCoverage` is preserved in API state, and responses without coverage fall back to the demo snapshot boundary.
- Reviewed-evidence smoke test passed: accepted reviewed cards can close operator/manual P0 gates, while incomplete reviewed cards are rejected and keep P0 blocked.
- Reviewed-evidence ledger smoke test passed: API and store generate `reviewId`, write JSONL, and create `operator-review://...` source IDs when a card has no public URL.
- Ledger readback smoke test passed: only cards matching the requested `caseId` are merged back into Evidence Autopilot coverage.
- Frontend API adapter smoke test passed: `caseId` and `enableReviewedEvidenceLedger` are included only when explicitly requested.
- Reviewed-evidence listing smoke test passed: store and API return only records matching the requested `caseId`.
- Backend focused smoke tests passed: 23 passed, 1 existing Pydantic deprecation warning.
- `git diff --check` passed.

## Remaining Work

- Add more official-source providers behind the existing provider registry, starting with final 2026 provincial professional-group tables, province-side plan data, and external outcome validation sources.
- Add durable operator capture workflow for semi-closed sources.
- Connect the reviewed-evidence listing to frontend/delivery views, screenshot attachments, and reviewer identity controls.
- Connect quant positioning and 2025 backtest signals to case selection.
- Run outcome validation before making any effectiveness claim.

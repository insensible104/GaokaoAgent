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
- Added a frontend API adapter for the reviewed-evidence listing endpoint, with response validation before records can be used by future delivery views.
- Added a report-level reviewed-evidence audit trail for the Deep Opportunity report page. It surfaces case-scoped review IDs, source IDs/URLs, and `reviewAction` notes from captured Real Case v0 evidence instead of leaving the ledger only in backend/API state.
- Added a report payload contract for live reviewed-evidence records. When `PathFinderReportPayload.evidenceAutopilot.reviewedEvidenceRecords` is supplied, the Deep Opportunity report uses those case-scoped ledger records before falling back to the Real Case v0 fixture trail.
- Wired the A4 report preview entry to attempt case-scoped reviewed-evidence ledger loading when a case id is available from the delivery manifest or game matrix. Ledger failures keep the report preview available and carry an explicit `ledger_unavailable` boundary in the payload.
- Added a case evidence browser view model for reviewed-evidence records. It filters records by `caseId`, groups them by evidence task, separates ready-for-report captured cards from incomplete operator notes, flags missing P0 tasks, and marks counter-evidence hits for reviewer escalation.
- Added a compact reviewed-evidence case browser panel. It reuses the case browser view model and gives reviewers one summary of captured records, ready-for-report records, pending capture, missing P0 gates, and counter-evidence escalation before report use.
- Wired the compact reviewed-evidence panel into the internal delivery review preview. After a delivery preview returns a case id, the UI attempts case-scoped ledger readback and shows the reviewed evidence gate before the next-action and artifact preview sections.

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
- The report preview can attempt case-scoped ledger loading, but there is still no full case evidence browser, screenshot attachment store, redaction workflow, or reviewer permission model.
- The case evidence browser now has a compact reviewer surface inside internal delivery review, but it is not a full evidence-management workflow, screenshot attachment store, redaction workflow, or reviewer permission system.

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
- Frontend reviewed-evidence listing adapter smoke test passed: case-scoped records are fetched and malformed record lists are rejected.
- Backend focused smoke tests passed: 23 passed, 1 existing Pydantic deprecation warning.
- Report reviewed-evidence audit trail smoke test passed: Deep Opportunity report now exposes case-scoped audit trail labels, generated review IDs, `operator-review://` fallback source IDs, and review actions.
- Report payload behavior test passed: live `reviewedEvidenceRecords` are converted into case-scoped audit trail rows, while incomplete operator-review placeholders are excluded.
- Report preview wiring smoke test passed: App resolves a reviewed-evidence case id, calls the listing adapter, and persists `evidenceAutopilot.reviewedEvidenceRecords` into the preview payload.
- Reviewed-evidence case browser test passed: case records are grouped by task, incomplete operator notes stay pending, missing P0 tasks are listed, and counter-evidence hits force review.
- Reviewed-evidence case browser panel test passed: the reviewer summary marks blocked, needs-review, and ready states from missing P0 tasks, pending capture, and counter-evidence.
- Internal delivery reviewed-evidence wiring test passed: delivery preview wiring imports the panel, fetches case-scoped ledger records, and builds a delivery-derived evidence collection plan for the reviewer surface.
- `git diff --check` passed.

## Remaining Work

- Add more official-source providers behind the existing provider registry, starting with final 2026 provincial professional-group tables, province-side plan data, and external outcome validation sources.
- Add durable operator capture workflow for semi-closed sources.
- Add screenshot attachments, redaction handling, and reviewer identity controls to the internal reviewed-evidence workflow.
- Connect quant positioning and 2025 backtest signals to case selection.
- Run outcome validation before making any effectiveness claim.

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
- Expanded the compact panel record rows to show audit fields: `sourceId`, `reviewer`, and `reviewAction`, so the reviewer can trace why a record is usable or still needs capture.
- Added review-control gates for operator-review evidence. Cards using `operator-review://...` now need at least one attachment, a non-pending redaction status, and a structured reviewer identity before they can close a P0 Evidence Autopilot gate.
- Updated the frontend reviewed-evidence listing contract and panel so `attachments`, `redactionStatus`, and `reviewerIdentity` are preserved and shown to internal reviewers.
- Added `POST /api/evidence-autopilot/reviewed-evidence/attachments` and a local reviewed-evidence attachment store. The endpoint decodes base64 screenshot/PDF/image payloads, writes the binary file, writes a JSON metadata sidecar with case/task/reviewer IDs and SHA-256, and returns a `ReviewedEvidenceAttachment` that can be attached to an operator-review card.
- Added a frontend typed adapter for the attachment upload endpoint. It posts the operator-captured attachment payload, validates the returned `ReviewedEvidenceAttachment`, byte size, SHA-256, and metadata path, and gives future capture UI a stable API seam without adding a new screen.
- Added frontend helpers to compose and submit operator-reviewed evidence cards. The helper refuses missing reviewer identity, missing attachments, and pending redaction before posting to the reviewed-evidence ledger endpoint.
- Added backend attachment existence validation before operator-reviewed evidence can enter the ledger or close an Evidence Autopilot P0 gate. A fake `storageRef` string without a corresponding stored file is rejected.
- Tightened backend attachment audit validation. Operator-reviewed evidence now requires the stored binary, a JSON metadata sidecar, matching `attachmentId` / `storageRef` / `kind` / `capturedAt` / `redactionStatus`, and a sidecar SHA-256 that matches the stored file before the card can enter the ledger or close an Evidence Autopilot P0 gate.
- Added readback-time attachment audit to the case-scoped reviewed-evidence listing endpoint. Delivery/review callers now receive an `attachmentAudit` summary per record, so attachments that were deleted or tampered after ledger submission are flagged before report use.
- Updated the reviewed-evidence case browser model to treat invalid attachment audits as `needs_capture` rather than `ready_for_report`, and surfaced the audit status in the compact internal reviewer panel.
- Added a redaction checklist contract for operator-reviewed attachments. Attachments marked `redacted` now require checklist confirmation that student personal info, private contact info, account identifiers, and third-party personal info were handled, plus reviewer confirmation, before upload succeeds.
- Preserved the redaction checklist through the backend attachment metadata sidecar, returned `ReviewedEvidenceAttachment`, and frontend upload adapter so later capture UI can reuse the same audited path.
- Added a typed frontend capture workflow helper for operator-reviewed evidence. It runs the same path future UI should use: upload reviewed attachment, build the gated operator-reviewed card, and submit the card to the reviewed-evidence ledger.
- Added an operator evidence capture worklist model and a compact internal delivery summary. Missing or invalid operator/manual evidence tasks are now listed with blocking status, recapture reason, required attachment kinds, and the `captureAndSubmitOperatorReviewedEvidence` workflow that future capture UI must use.
- Added an operator capture delivery gate. P0 operator capture gaps now block client-facing bundle download even if the internal delivery preview is otherwise available.
- Added an operator capture packet model. The packet turns each open operator/manual evidence task into a capture brief, search prompts, required output fields, attachment upload template, redaction checklist, rejection rules, and a `captureAndSubmitOperatorReviewedEvidence` submission template.
- Added a packet fill helper. A reviewer-filled packet item now becomes a typed `captureAndSubmitOperatorReviewedEvidence` input only after source title, excerpt, capture time, attachment content, reviewer identity, and complete redaction checklist are present.
- Added an operator capture roundtrip helper. It runs the filled packet input through attachment upload, reviewed-evidence ledger submission, case-scoped readback, worklist recomputation, and delivery gate recomputation.
- Added a backend TestClient roundtrip smoke. It verifies real attachment storage, reviewed-evidence ledger append, case-scoped readback attachment audit, Evidence Autopilot ledger merge, and coverage-gate behavior for both valid and tampered operator evidence.
- Added a Real Case v0 reviewed-evidence adapter. It converts only completed fixture cards with public URL and excerpt into case-scoped reviewed-evidence submissions, maps descriptive fixture claims to canonical Evidence Autopilot claim ids, and filters incomplete operator notes.
- Extended the backend roundtrip smoke with the Real Case v0 `undergrad-access` public source. The smoke submits that source-log evidence to the reviewed ledger and verifies that Evidence Autopilot coverage accepts `undergrad-access` when ledger readback is enabled.

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
- It does not yet provide a full reviewer workflow with authentication, redaction UI, or permission enforcement.
- The report preview can attempt case-scoped ledger loading, but there is still no full redaction workflow or reviewer permission model.
- The case evidence browser now has a compact reviewer surface inside internal delivery review, and operator-review cards are gated by attachment/redaction/identity metadata, redaction checklist confirmation, and sidecar/hash validation at submission and readback. Binary attachment storage and a typed upload-to-ledger workflow now exist, but there is still no frontend capture/redaction UI, authentication, or permission enforcement system.
- The operator capture worklist, packet, fill helper, frontend roundtrip helper, backend roundtrip smoke, Real Case reviewed-evidence adapter, and delivery gate organize missing or invalid capture tasks for internal reviewers. They do not collect evidence, bypass platform limits, visually verify redaction, authenticate reviewers, or prove admission/employment outcomes.

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
- Reviewed-evidence case browser panel test passed: the reviewer summary marks blocked, needs-review, and ready states from missing P0 tasks, pending capture, and counter-evidence, and the panel keeps source ID, reviewer, and review action visible.
- Internal delivery reviewed-evidence wiring test passed: delivery preview wiring imports the panel, fetches case-scoped ledger records, and builds a delivery-derived evidence collection plan for the reviewer surface.
- Operator-review control gate test passed: reviewed cards without attachments, redaction status, and reviewer identity no longer close P0 gates.
- Reviewed-evidence store test passed: attachment, redaction, and reviewer identity metadata are persisted in the JSONL ledger.
- Reviewed-evidence attachment store test passed: binary attachment bytes and JSON metadata sidecars are persisted, and the upload endpoint returns a reusable `storageRef`, `attachmentId`, byte size, and SHA-256.
- Frontend Evidence Autopilot API adapter test passed: attachment upload requests post to the backend endpoint and reject malformed upload responses.
- Frontend reviewed-evidence submit adapter test passed: uploaded attachments can be composed into an operator-reviewed card and posted to the ledger endpoint, while missing reviewer identity is rejected before submission.
- Attachment existence gate test passed: fake operator-review `storageRef` values are rejected before ledger append and cannot close P0 gates through request-scoped `reviewedEvidenceCards`.
- Attachment metadata audit gate test passed: operator-review attachment submissions are rejected when the metadata sidecar is missing or when the sidecar SHA-256 does not match the stored binary.
- Reviewed-evidence listing test passed: case-scoped ledger readback returns per-record `attachmentAudit` and flags tampered stored files before report use.
- Reviewed-evidence case browser test passed: invalid attachment audit records are treated as pending capture and keep P0 tasks out of `ready_for_report`.
- Redaction checklist gate test passed: `redacted` attachment uploads without checklist confirmation are rejected, while complete checklists are persisted in attachment metadata and returned to the frontend.
- Frontend capture workflow test passed: one helper uploads a reviewed attachment, composes the gated operator card, and submits it to the ledger through existing API contracts.
- Operator evidence capture worklist test passed: missing or invalid operator evidence tasks are converted into blocking/non-blocking work items that point to the existing capture workflow, and P0 gaps produce a client-delivery blocking gate.
- Operator evidence capture packet test passed: open operator/manual evidence tasks are converted into capture briefs, search prompts, redaction/rejection rules, attachment templates, ledger submission templates, and typed filled capture inputs when required reviewer/evidence fields are present.
- Operator evidence capture roundtrip test passed: a filled packet input can call upload, ledger submission, case readback, worklist recomputation, and gate recomputation; a valid readback clears the P0 operator capture gate.
- Backend operator evidence capture roundtrip smoke passed: FastAPI TestClient writes the attachment store and ledger, readback returns valid attachment audit, research coverage accepts the operator task, and tampered attachment readback blocks coverage again.
- Real Case reviewed-evidence adapter test passed: completed source-log fixture cards become reviewed-evidence submissions with canonical claim ids, while incomplete operator notes are filtered out.
- Backend Real Case ledger merge smoke passed: the `undergrad-access` public fixture source can be submitted to the reviewed ledger and then accepted by Evidence Autopilot coverage when case-scoped ledger readback is enabled.
- Internal delivery reviewed-evidence wiring test passed: the internal review surface now imports the operator capture worklist and gate, exposes the required capture workflow when case-scoped evidence is incomplete, and blocks client-facing download when P0 operator evidence remains open.
- `git diff --check` passed.

## Remaining Work

- Add more official-source providers behind the existing provider registry, starting with final 2026 provincial professional-group tables, province-side plan data, and external outcome validation sources.
- Add durable operator capture workflow for semi-closed sources.
- Add frontend capture/redaction UI and reviewer authentication/permission enforcement around the attachment and metadata contracts.
- Connect quant positioning and 2025 backtest signals to case selection.
- Run outcome validation before making any effectiveness claim.

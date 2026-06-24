# PathFinder Top Gaokao Opportunity System Analysis

Date: 2026-06-24

## Thesis

The core product is now fixed:

```text
quant positioning
  -> Evidence Autopilot
  -> Opportunity Radar
  -> Deep Opportunity Card
  -> deliverable Chinese report
```

The project should be judged by whether this loop can produce a better auditable opportunity judgment than a generic AI chat answer. More pages, more agents, and more report styling are secondary unless they make this loop more true.

## What Is Already Useful

### January to April agent and recommendation work

The early agent work is not wasted. It should be treated as a research-planning and critique engine, not as the front-stage product.

Useful parts:

- candidate profiling and routing
- two-stage school/major-group/major assignment thinking
- Monte Carlo and risk calibration concepts
- Prompt RL, TTS, and GRPO as future policy-improvement infrastructure
- deep research and critic agents as evidence-task and counter-evidence planners
- FastAPI route/productization groundwork

Current role:

```text
agents generate better questions and checks
evidence decides what can be claimed
```

The agent layer should not make unsupported conclusions visible to families or counselors.

### May quant and outcome work

The May work is one of the strongest assets because it moved the project from recommendation generation toward validation:

- 2025 outcome inventory
- backtest reports
- opportunity radar notes
- enrollment diff analysis
- quant arbitrage and plan-change signals

This should become the quant-positioning layer that decides where Evidence Autopilot should spend attention.

### June delivery and evidence work

The June work made the system presentable and closer to delivery:

- DeepSeek provider support
- QuantLab and evidence-to-quant concepts
- delivery readiness and report package workflows
- public demos and GitHub Pages
- career/job evidence surfaces
- Deep Opportunity Card
- Evidence Autopilot provider contract, normalizer, snapshot provider, backend bridge, API adapter, and report integration

This is enough infrastructure to stop broad expansion and start one real case.

## Current Implementation Maturity

### Implemented

- Evidence Autopilot can generate tasks.
- Provider result shape is typed.
- Operator-only channels are separated from verified evidence.
- Normalizer can mark verified, weak, missing, and counter-hit evidence.
- Frontend API adapter rejects malformed backend evidence cards.
- Only `captured_candidate` cards can become provider results.
- Backend can generate candidate-specific research tasks and placeholders.
- Backend now returns an `evidenceCoverage` gate summary with captured task IDs, missing P0 task IDs, operator/manual-review tasks, review blockers, and counselor-review readiness.
- Frontend API state now preserves and validates backend `evidenceCoverage`, so a malformed or incomplete backend response falls back to the demo boundary instead of appearing connected.
- Backend accepts request-scoped `reviewedEvidenceCards` so compliant human-captured operator evidence can enter the same coverage gate without pretending that an uncollected task is verified.
- Backend now has a JSONL reviewed-evidence ledger endpoint that generates `reviewId` values and creates `operator-review://...` source IDs for cards without public URLs.
- Evidence Autopilot can now load reviewed-evidence ledger cards by `caseId` and merge only matching cards back into coverage.
- Frontend API adapter can now opt into case-scoped ledger readback by sending `caseId` and `enableReviewedEvidenceLedger`.
- Backend can now list reviewed-evidence ledger records for one case through a read-only case-scoped endpoint.
- Frontend API adapter can now fetch and validate case-scoped reviewed-evidence ledger records.
- Report template can show Evidence Autopilot / Opportunity Radar content.
- Report template now carries a reviewed-evidence audit trail into the Deep Opportunity page, including case-scoped review IDs, source IDs/URLs, and `reviewAction` notes from captured Real Case v0 evidence.
- Report payload can now accept live `reviewedEvidenceRecords` and convert captured case-scoped ledger records into the same audit trail before falling back to fixture evidence.
- A4 report preview now attempts to load case-scoped reviewed-evidence records when a case id is available from delivery manifests or the game matrix, then persists those records into the preview payload.
- Reviewed evidence now has a case browser view model that groups records by task, keeps incomplete operator notes pending, exposes missing P0 tasks, and escalates captured counter-evidence.
- Reviewed evidence now has a compact case browser panel that summarizes captured records, ready-for-report records, pending capture, missing P0 gates, and counter-evidence escalation for reviewer signoff.
- Internal delivery review now attempts case-scoped reviewed-evidence ledger readback after a delivery preview is generated and renders the compact reviewer panel before next-action and artifact preview sections.
- The compact reviewed-evidence panel now shows record-level source ID, reviewer, and review action so internal reviewers can audit evidence provenance without opening the raw JSONL ledger.
- Operator-review evidence now has attachment/redaction/identity gates. A card using `operator-review://...` must carry at least one attachment, a non-pending redaction status, and a structured reviewer identity before it can close a P0 evidence gate.
- Backend now has a local reviewed-evidence attachment store and upload endpoint. It persists binary screenshot/PDF/image payloads, emits `ReviewedEvidenceAttachment` metadata, and writes SHA-256 sidecars for audit.
- Backend now rejects fake operator-review attachment references. A `storageRef` must resolve to an existing file in the configured attachment store before the reviewed card can enter the ledger or close an Evidence Autopilot P0 gate.
- Backend now validates reviewed-evidence attachment sidecars before accepting operator evidence. The stored binary, JSON metadata sidecar, submitted `ReviewedEvidenceAttachment` fields, and recorded SHA-256 must agree before an attachment can support ledger submission or P0 closure.
- Backend reviewed-evidence listing now revalidates attachments at readback time and returns per-record `attachmentAudit`, so stale, deleted, or tampered attachments are visible before delivery review or report use.
- Frontend now has a typed attachment upload adapter that posts operator-captured attachment payloads and rejects malformed backend upload responses before they can be used by capture UI.
- Frontend now has typed helpers to compose uploaded attachments into an operator-reviewed card and submit that card to the reviewed-evidence ledger endpoint, with pre-submit checks for reviewer identity, attachment presence, and completed redaction status.
- Frontend case browser now treats invalid attachment audit records as `needs_capture`, keeping affected P0 tasks out of `ready_for_report` until the operator evidence is repaired.

### Partially implemented

- Backend-to-frontend bridge exists, but backend does not execute public web/PDF retrieval.
- Snapshot provider stabilizes demo output, but it is not live evidence.
- Report integration exists and the preview entry can attempt case-scoped ledger fetches. The case browser model and compact reviewer panel are wired into internal delivery review, and operator-review cards now require attachment/redaction/identity metadata plus sidecar/hash validation at submission and readback to close P0 gates. The remaining production gaps are capture/redaction UI, authentication, permission enforcement, and a polished capture workflow.
- Agent research logic exists historically, but it is not yet fully reused as a disciplined evidence planner.

### Not implemented yet

- Real provider retrieval for official public sources.
- Fully durable captured-evidence workflow for one real case.
- Operator workflow for semi-closed evidence capture with capture/redaction UI, reviewer identity enforcement, and screenshots wired into card submission.
- A verified real opportunity case that flows into card and report.
- Outcome validation proving improved 2026 admission results.

## Main Risk

The main risk is not technical inability. It is scope drift.

The project has enough components to keep expanding forever:

- more agent roles
- more report sections
- more public demos
- more career simulations
- more delivery gates
- more quantitative experiments

Most of those are useful later. Right now they are harmful if they delay the first real evidence-to-opportunity case.

## Research Taste Calibration

A top-tier opportunity system should be conservative about claims and aggressive about evidence.

Good taste:

- show the exact source and excerpt
- separate opportunity hypothesis from recommendation
- look for disconfirming evidence
- expose evidence gaps instead of hiding them
- distinguish demo/snapshot from captured evidence
- connect short-term admission, mid-term progression, and long-term career logic

Bad taste:

- claiming certainty from a polished report
- treating agent consensus as proof
- treating synthetic or snapshot evidence as real evidence
- adding dashboards before one real case works
- optimizing prompts before ground truth and evaluation scope are clear

## Next Iteration Slice

The next slice should be Real Case v0:

1. Select one concrete province, rank/score band, school, and major.
2. Capture at least five public evidence cards with URL, excerpt, time, source type, confidence, and review action.
3. Add a fixture-backed provider or backend response path that emits `captured_candidate`.
4. Run the existing normalizer and Opportunity Radar.
5. Render the case in Deep Opportunity Card and the Chinese report.
6. Keep WeChat/Boss as operator tasks unless manually captured evidence is provided.

This is the first milestone where PathFinder can credibly say:

```text
Here is one opportunity hypothesis, here is the evidence, here is what would disprove it, and here is the counselor-review boundary.
```

## Decision

Continue with Real Case v0 before any new UI redesign, multi-case platform, live semi-closed scraping, or additional agent spectacle.

The agent work remains a backend research capability. The product value is the auditable opportunity judgment.

## 2026-06-24 Real Case v0 Status Update

Real Case v0 is now implemented as a fixture-backed, auditable slice:

- Source log: `docs/evidence_autopilot/real_case_v0_source_log.md`
- Fixture: `data/evidence_autopilot/real_case_v0.json`
- Provider: `frontend/src/lib/evidenceAutopilotRealCaseProvider.ts`
- API state: `real_case_fixture`
- Opportunity Radar smoke test: `frontend/src/components/DeepOpportunityRealCase.test.mjs`
- Report integration: `PathFinderReportTemplate.tsx`
- Handoff: `docs/evidence_autopilot/real_case_v0_handoff.md`

This changes the maturity assessment: the system now has one real reviewed public-evidence case flowing through Evidence Autopilot, Opportunity Radar, and the report. It is still fixture-backed, so the next bottleneck is live official-source retrieval and durable capture provenance, not another UI layer.

### 2026-06-24 Live Official-Source Provider Slice

The first narrow live provider now exists on the backend:

- Module: `backend/src/official_source_provider.py`
- Test: `backend/src/test_official_source_provider_smoke.py`
- API contract: `enableOfficialSourceProvider` opt-in on `EvidenceAutopilotResearchRequest`
- Captured cards: `official-plan-charter`, `rank-history-band`, `faculty-research-direction`, `undergrad-access`, `graduate-progression`
- Current scope: SCUT 2026 admissions-plan/charter boundary, the 2025 Guangdong physics ordinary-batch historical score row for `工科试验班(智能装备与先进制造)`, and WUSIE school pages for curriculum/faculty, undergraduate platform access, and school-described progression paths

This is intentionally not a general crawler. It proves that official SCUT and school pages can be parsed into `captured_candidate` cards with URL, excerpt, capture time, confidence, and review action. It also establishes a provider registry that can merge cards and warnings without letting a failed provider fabricate evidence or break task generation. It still does not prove 2026 admission probability, final Guangdong professional-group placement, graduate-school outcomes, employment outcomes, or generalized source coverage.

### 2026-06-24 Evidence Coverage Gate

The backend API now exposes `evidenceCoverage` on every Evidence Autopilot response:

- `capturedTaskIds`: tasks backed by a captured card with URL and excerpt
- `missingP0TaskIds`: P0 evidence gates that still block counselor review
- `operatorTaskIds`: WeChat, job-market, and manual-review tasks that require compliant human capture
- `readyForCounselorReview`: false until P0 gaps are closed
- `reviewBlockers`: machine-readable reasons the case is not yet deliverable

This is a product-control improvement, not an outcome claim. It helps PathFinder stop expanding the case when the immediate blocker is simply missing P0 evidence.

The frontend adapter now carries this summary through `EvidenceAutopilotApiState`. No new UI surface was added in this slice; the point is to stabilize the contract first.

### 2026-06-24 Reviewed Evidence Injection

The backend request contract now accepts `reviewedEvidenceCards` for human-captured evidence from semi-closed or manual-review channels. A reviewed card only closes a task when it matches an existing task and includes a source URL or review ID, excerpt, capture date, confidence, and review action. Incomplete notes are rejected and keep the P0 gate blocked.

This gives the system a compliant path for Boss, WeChat, and counter-evidence work without scraping or fabricating evidence. The next slice added a JSONL ledger and generated review IDs, but reviewer identity controls, screenshots, redaction, and case-level browsing remain future work.

### 2026-06-24 Reviewed Evidence Ledger

The backend now exposes `POST /api/evidence-autopilot/reviewed-evidence`. It appends one reviewed evidence card to a JSONL ledger, generates a `reviewId`, and returns a normalized card. If the submitted operator card has no public source URL, the endpoint assigns `operator-review://<reviewId>` so downstream Evidence Autopilot can reference an auditable source ID instead of an empty field.

This moves operator evidence from ephemeral request payloads toward an audit trail. It is still not a complete evidence-management system: attachment storage exists, but there is no reviewer permission model, redaction workflow, or polished capture UI.

### 2026-06-24 Case-Scoped Ledger Readback

Evidence Autopilot research requests can now opt into reviewed-evidence ledger readback with `caseId` and `enableReviewedEvidenceLedger`. The backend loads matching JSONL records, merges only those reviewed cards into the current evidence cards, and updates `evidenceCoverage` accordingly. Records from other cases are ignored.

This closes the first persistence loop: operator evidence can be submitted, assigned a review ID, stored, and later reused in the same case's research run. The remaining gap is case-level evidence management: listing prior records, attaching screenshots, reviewer permissioning, and showing these records in the delivery UI.

The frontend adapter now exposes this backend capability as explicit request options rather than embedding case state into the core school/major context. That keeps the target context stable while allowing case-scoped evidence reuse when the caller has a real case ID.

### 2026-06-24 Case-Level Ledger Listing

The backend now exposes `GET /api/evidence-autopilot/reviewed-evidence/{case_id}`. It returns full reviewed-evidence ledger records for one case, including review ID, reviewer, target label, recorded time, and the normalized evidence card. Records from other cases are filtered out.

This makes the ledger inspectable enough for future delivery review and report attachment. It is still backend-only; the product still needs a redaction workflow and reviewer permission controls.

The frontend API adapter now has a typed fetch path for this listing endpoint. This is still not a UI feature; it is the contract needed before delivery pages can safely render reviewed operator evidence.

### 2026-06-24 Reviewed Evidence Report Payload

The report template now accepts `PathFinderReportPayload.evidenceAutopilot.reviewedEvidenceRecords`. Captured ledger records are converted into report audit trail rows with `reviewId`, `caseId`, task ID, source ID/URL, confidence, capture time, and `reviewAction`. Incomplete operator-review placeholders remain excluded from the report trail.

This closes the next handoff gap between the case-scoped listing endpoint and the Chinese deliverable report. It is still not a full delivery UI: the report route does not fetch records by case ID on its own, and there is still no redaction workflow or reviewer permission model.

### 2026-06-24 Reviewed Evidence Report Preview Wiring

The A4 report preview entry now resolves a reviewed-evidence case id from the latest delivery manifest first, then from `game_matrix.case_id`, `game_matrix.caseId`, `game_matrix.id`, or matching volunteer-plan fields. If a case id is present, it calls the typed reviewed-evidence listing adapter and writes `evidenceAutopilot.reviewedEvidenceRecords` into `pathfinder-report-preview` session storage.

This moves the ledger from "available to a future report caller" to "attempted by the actual report preview entry." The fallback remains conservative: if the ledger is unavailable, the preview still opens with `status: ledger_unavailable` and does not pretend reviewed operator evidence was captured.

### 2026-06-24 Reviewed Evidence Case Browser Model

The frontend now has a reviewed-evidence case browser model. It accepts case-scoped ledger records plus an optional evidence collection plan, filters records to the requested case, groups them by task, and marks each task as `ready_for_report`, `needs_capture`, or `missing`. Captured counter-evidence forces reviewer attention, incomplete operator notes remain pending, and missing P0 task ids stay visible.

This is the first reviewer-workflow data layer. It does not yet render a full browsing surface, collect screenshots, redact personal data, or enforce reviewer permissions.

### 2026-06-24 Reviewed Evidence Reviewer Panel

The frontend now has a compact reviewed-evidence case browser panel. It reuses the case browser view model and converts case-scoped ledger state into reviewer-facing delivery signals: captured count, ready-for-report count, pending capture count, missing P0 count, blocked/needs-review/ready tone, and the next action before report use.

This improves the product loop because the reviewer can see why a case is not deliverable before the family-facing report is treated as final. The panel also exposes source ID, reviewer, and review action for the first records in each task group. It is still deliberately narrow: it does not yet provide redaction UI, reviewer identity enforcement, or permission enforcement.

### 2026-06-24 Internal Delivery Reviewed-Evidence Gate

Internal delivery review now uses the reviewed-evidence panel as a pre-report gate. After the backend delivery preview returns a case id, the frontend attempts `GET /api/evidence-autopilot/reviewed-evidence/{case_id}`, builds a delivery-derived evidence collection plan, and renders the case-scoped evidence state before next actions and artifact download controls.

This moves reviewed evidence from a standalone model into the delivery workflow. The boundary remains important: ledger readback failure is shown as an internal warning and does not fabricate evidence, while missing P0 evidence and counter-evidence remain reviewer-facing blockers rather than family-facing claims.

### 2026-06-24 Operator-Review Control Gate

Operator-review evidence now carries an explicit control contract: attachments, redaction status, and reviewer identity. Backend merge logic rejects `operator-review://...` reviewed cards from P0 closure unless they include at least one attachment, a redacted or not-required redaction status, a structured reviewer identity, and an attachment `storageRef` that resolves to a real stored file with matching sidecar metadata and SHA-256.

This is a quality-bar change. It prevents semi-closed evidence from becoming report-ready merely because someone typed an excerpt. The next slice added backend attachment storage, but the system still needs redaction UI, reviewer authentication, and permission enforcement before this is a complete production evidence-management workflow.

### 2026-06-24 Reviewed Evidence Attachment Store

The backend now exposes `POST /api/evidence-autopilot/reviewed-evidence/attachments`. It accepts a base64 screenshot/PDF/image payload, persists the binary attachment under a case-scoped `reviewed-evidence/<caseId>/...` storage reference, writes a JSON sidecar with case ID, task ID, reviewer ID, content type, byte size, SHA-256, capture time, and redaction status, and returns a `ReviewedEvidenceAttachment` object suitable for operator-review cards. Ledger submission and P0 merge gates now revalidate that sidecar against the submitted attachment fields and the stored file hash.

This turns attachment evidence from a hand-written string into an auditable local asset. It still does not solve who is allowed to upload, whether the screenshot has been redacted correctly, or how reviewers attach the returned `storageRef` from a UI.

The frontend API adapter now exposes this endpoint as `uploadReviewedEvidenceAttachment`. It also exposes `buildOperatorReviewedEvidenceCard` and `submitReviewedEvidenceCard`, so future capture UI can use one typed path for: upload attachment, compose a gated operator card, and submit it to the reviewed-evidence ledger.

This is still a contract slice, not a complete workflow. There is no capture screen, redaction UI, reviewer authentication, or permission enforcement yet.

### 2026-06-24 Readback-Time Attachment Audit

The case-scoped reviewed-evidence listing endpoint now attaches an `attachmentAudit` summary to each record. It revalidates the stored binary, metadata sidecar, submitted attachment fields, and SHA-256 when the ledger is read, not only when evidence is submitted. If an attachment is deleted or tampered after ledger append, delivery review receives `status: invalid` with per-attachment findings.

The frontend reviewed-evidence case browser now consumes this audit signal. Invalid attachment audit records stay visible for traceability, but they are downgraded to `needs_capture` and cannot count toward `ready_for_report` or close a P0 reviewer gate.

This is a delivery-readiness improvement, not an outcome claim. It still does not implement reviewer authentication, permission enforcement, or a redaction UI.

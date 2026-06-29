# PathFinder Real Case v0 Design

Date: 2026-06-24

## Purpose

PathFinder / GaokaoAgent should converge into a top-tier Gaokao opportunity research system, not a generic admissions chatbot and not a visible multi-agent debate UI. The next shippable milestone is one real auditable opportunity case.

Real Case v0 proves that the system can turn a candidate profile and one target school-major into a counselor-reviewable evidence trail:

```text
candidate profile + target school/major
  -> quant positioning context
  -> Evidence Autopilot tasks
  -> captured public evidence cards
  -> Opportunity Radar gates
  -> Deep Opportunity Card
  -> Chinese report section
```

This milestone does not claim improved 2026 admission outcomes. It only proves that the system can produce a traceable opportunity hypothesis with source evidence and explicit boundaries.

## Current Baseline

The current codebase already has the main skeleton:

- Evidence task generation and opportunity run builder in `frontend/src/lib/evidenceAutopilot.ts`.
- Typed provider request/result contract in `frontend/src/lib/evidenceAutopilotProvider.ts`.
- Provider result normalization in `frontend/src/lib/evidenceAutopilotResultNormalizer.ts`.
- Snapshot provider for stable demo behavior in `frontend/src/lib/evidenceAutopilotSnapshotProvider.ts`.
- Frontend API adapter and fallback states in `frontend/src/lib/evidenceAutopilotApi.ts`.
- Backend task/query bridge at `POST /api/evidence-autopilot/research`.
- Report integration in `frontend/src/components/PathFinderReportTemplate.tsx`.

The missing piece is not another UI surface. The missing piece is a real captured evidence fixture that can pass through the existing contract without being confused with demo snapshot data.

## Scope

Real Case v0 uses one selected opportunity case. It should be narrow enough to finish and strict enough to be useful.

The case must include:

- province
- target year
- candidate score or rank band
- target school
- target major or major group
- short rationale for why this is an opportunity hypothesis

The evidence set must include at least five captured cards:

- official admissions rule or enrollment plan
- historical admission rank or score evidence
- school/faculty/major training evidence
- graduate progression, employment, civil-service, or career-path evidence
- counter-evidence or an explicit evidence gap

Each captured card must include:

- `taskId`
- `claim`
- `status: "captured_candidate"`
- `sourceTitle`
- `sourceUrl`
- `sourceType`
- `excerpt`
- `capturedAt`
- `confidence`
- `reviewAction`

Any card without source URL, excerpt, capture time, and confidence remains `requires_capture` or `operator_review`. It must not enter Opportunity Radar as support.

## Non-Goals

- Do not add a new public UI redesign.
- Do not build uncontrolled scraping for WeChat, Boss, or other semi-closed platforms.
- Do not claim admission certainty, graduate-school certainty, employment certainty, or improved 2026 outcomes.
- Do not make the visible product a multi-agent chat or debate surface.
- Do not rename the product to an internal quality slogan.
- Do not treat snapshot/demo evidence as live verified evidence.

## Evidence Model

The first implementation should create a fixture-backed captured evidence source before adding a live provider.

Recommended path:

```text
data/evidence_autopilot/real_case_v0.json
```

The fixture should hold this shape:

```json
{
  "caseId": "string",
  "candidate": {
    "province": "string",
    "targetYear": "number",
    "score": "number | null",
    "rank": "number | null",
    "subjectTrack": "string"
  },
  "target": {
    "schoolName": "string",
    "majorName": "string"
  },
  "opportunityHypothesis": "string",
  "evidenceCards": []
}
```

The schema above is not evidence. A committed Real Case v0 fixture must contain one concrete case before it can feed Opportunity Radar.

## Data Flow

1. Backend returns Evidence Autopilot tasks and placeholders for the selected case.
2. Fixture provider loads captured evidence cards for matching `taskId` values.
3. Frontend API adapter accepts only cards with `status: "captured_candidate"`.
4. Normalizer converts captured provider results into `DeepEvidenceResult`.
5. Opportunity Radar calculates P0 gate, counter-evidence state, score, and horizon signals.
6. Deep Opportunity Card and report show source excerpts and claim boundaries.

The system should expose whether a run is:

- `demo_snapshot`
- `backend_connected`
- `backend_failed_snapshot_fallback`
- `real_case_fixture`

The final state name can differ if the implementation has a better local pattern, but the user-facing boundary must distinguish real captured fixture evidence from demo snapshot evidence.

## Agent Role

The January to April agent work remains valuable, but it should be used behind the evidence loop:

- planning agent: turns case context into research tasks
- evidence agent: prepares source-specific capture instructions
- critic agent: searches for disconfirming evidence and hard boundaries
- report agent: drafts counselor-reviewable language from accepted evidence
- audit agent: checks whether every claim has source, excerpt, date, confidence, and review action

Agents should not be the product surface for Real Case v0.

## Acceptance Criteria

Real Case v0 is complete only when all of these are true:

- One concrete case fixture exists with no schema placeholders in active evidence fields.
- At least five captured evidence cards have real URLs and excerpts.
- At least one card is counter-evidence or an explicit evidence gap.
- `captured_candidate` cards flow through the existing normalizer.
- Placeholder cards do not enter Opportunity Radar as support.
- Deep Opportunity Card or report shows source excerpts from the real case fixture.
- Claim boundary states that the case is an auditable opportunity hypothesis, not an admission or employment promise.
- Tests cover fixture loading, adapter status handling, normalization, and report visibility.

## Verification

Minimum verification commands:

```powershell
node frontend/src/components/EvidenceAutopilotApi.test.mjs
node frontend/src/components/EvidenceAutopilotResultNormalizer.test.mjs
node frontend/src/components/PathFinderDeepOpportunityReport.test.mjs
python backend/src/test_evidence_autopilot_api_smoke.py
```

If implementation touches frontend build or routing:

```powershell
Set-Location frontend
npm run lint
npm run build
Set-Location ..
```

## Stop Rule

Stop after one real case works end to end. Do not expand to multiple provinces, live scraping, WeChat/Boss automation, new dashboards, or a generalized case-management system until this first case can withstand evidence review.

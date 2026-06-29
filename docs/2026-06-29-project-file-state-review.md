# PathFinder Project File State Review

Date: 2026-06-29
Branch: `codex/evidence-attachment-audit`
HEAD: `6fca6ff feat: attach counselor decision to delivery preview`

## Executive Summary

The repository is not broken, but it has two different work modes mixed together:

1. The committed product mainline is relatively coherent: PathFinder Alpha Loop, Evidence Autopilot, Real Case v0, reviewed evidence, internal delivery preview, and client-delivery gates.
2. The current working tree contains a large untracked research batch from 2026-06-28: `analysis_inputs/`, `analysis_outputs/`, and 80 new `scripts/build_*` or `scripts/run_*` files. This is the main source of perceived disorder.

Research taste calibration: treat the untracked 2026-06-28 batch as internal opportunity discovery evidence only. It should not be merged into the product story as proof of recommendation quality, and it should not become family-facing advice. Its own outputs repeatedly mark `familyAllowed=0`, `deliveryAllowed=0`, `internal_only`, or similar boundaries.

## Git State

Observed state:

- Current branch: `codex/evidence-attachment-audit`
- Last commit: `6fca6ff feat: attach counselor decision to delivery preview`
- No tracked modifications.
- No staged changes.
- Tracked files: 579
- Untracked files: 617
- Ignored files: 77,330, mostly `.venv`, backend caches, frontend dependencies/build artifacts, logs, and temp outputs.

Untracked file distribution:

| Area | Count | Status |
| --- | ---: | --- |
| `analysis_outputs/` | 505 | 2026-06-28 research outputs, not yet curated |
| `scripts/` | 80 | new pipeline scripts, not yet integrated |
| `analysis_inputs/` | 30 | seed/manual source inputs for the new pipeline |
| `AGENTS.md` | 1 | local instruction file, currently untracked |
| `docs/` | 1 | `2026-06-23-pathfinder-alpha-continuation.md`, currently untracked |

Important branch note: `main` is separate and is ahead of `origin/main` by 40 commits in this checkout. The active branch is not `main`.

## Directory Status

| Directory | Role | Current judgment |
| --- | --- | --- |
| `frontend/` | React/Vite app, Evidence Autopilot UI, report preview, delivery review | Active product code. Main recent work is Real Case v0 and internal delivery review. |
| `backend/` | FastAPI, recommendation/evaluation engines, evidence APIs, official source provider | Active product and research backend. Includes current evidence ledger and attachment-gate work. |
| `docs/` | project history, plans, reports, handoffs | Important but overloaded. Needs a current-state index. |
| `data/` | core admissions data and Real Case fixture | Small and central. Should stay curated. |
| `logs/` | historical experiment/backtest outputs | Large historical evidence. Mostly ignored; should not drive new claims without audit. |
| `archive/` | old records | Keep as historical reconstruction material. |
| `tmp/`, `output/` | screenshots/logs/previews | Temporary or visual verification residue. Not product state. |
| `analysis_inputs/` | untracked seeds and source exports for 2026-06-28 pipeline | Research batch inputs. Needs manifest before commit. |
| `analysis_outputs/` | untracked generated opportunity/audit outputs | Research batch outputs. Needs curation or archive. |
| `scripts/` | mixed committed deploy scripts plus untracked pipeline generators | Too crowded now. New scripts need grouping by pipeline. |

## Committed Product Mainline

The current supported product story is:

`candidate profile -> Evidence Autopilot -> Opportunity Radar -> Deep Opportunity Card -> deliverable Chinese report`

This is consistent with `README.md` and the continuation plan. The strongest differentiation is not a generic chatbot; it is auditable opportunity discovery.

Current implemented pieces include:

- Evidence Autopilot task generation and typed provider shape.
- Evidence coverage gates with missing P0 tasks, operator/manual review tasks, review blockers, and counselor-review readiness.
- Case-scoped reviewed-evidence ledger readback.
- Attachment/redaction/reviewer-identity gates for operator evidence.
- Real Case v0 fixture-backed reviewed public evidence flow.
- Internal reviewer handoff, internal report brief, internal delivery preview, counselor decision artifacts.
- Client-facing artifacts are deliberately empty while gates remain blocked.

Current product boundary:

- This proves workflow mechanics, audit continuity, and internal handoff behavior.
- It does not prove admission probability, employment outcomes, real 2026 outcome improvement, source freshness across providers, or production readiness.
- `allow_internal_report_draft` is not client delivery permission.
- `client_delivery.allowed=false` remains the correct boundary until evidence and counselor gates are satisfied.

## Recent Mainline Files

High-signal active files:

- `frontend/src/lib/evidenceAutopilotRealCaseCounselorReviewDecision.ts`
- `frontend/src/components/InternalDeliveryReview.tsx`
- `frontend/src/lib/evidenceAutopilotRealCaseOperatorClosureDeliveryPreview.ts`
- `frontend/src/lib/evidenceAutopilotRealCaseReviewerHandoff*.ts`
- `frontend/src/lib/operatorEvidenceCapture*.ts`
- `frontend/src/lib/reviewedEvidenceCaseBrowser.ts`
- `frontend/src/lib/evidenceAutopilotApi.ts`
- `backend/src/evidence_autopilot_api.py`
- `backend/src/reviewed_evidence_store.py`
- `backend/src/reviewed_evidence_attachment_store.py`
- `backend/src/official_source_provider.py`
- `docs/evidence_autopilot/real_case_v0_handoff.md`
- `data/evidence_autopilot/real_case_v0.json`

The latest verification recorded in `docs/evidence_autopilot/real_case_v0_handoff.md` says frontend, backend, ledger, attachment, redaction, Real Case, and internal delivery smoke tests passed. I did not rerun the whole suite in this review; this document is a file-state audit, not a fresh test certification.

## 2026-06-28 Untracked Research Batch

This batch appears to be a large "special-control / elite opportunity discovery" pipeline. It contains:

- `analysis_outputs/special_control_opportunity_pipeline/pipeline_run_report.md`
- `analysis_outputs/special_control_opportunity_pipeline/pipeline_run.json`
- many per-step status markdown files
- `analysis_outputs/yearly_group_change_ledger/`
- many `analysis_outputs/elite_*` folders
- seed/source files in `analysis_inputs/`
- 80 new generation scripts in `scripts/`

What it seems to accomplish:

- Reconstructs yearly professional-group changes.
- Builds opportunity cards and decision boards.
- Screens 985/211, double-first-class, local strong-school, and blind-spot candidates.
- Produces evidence worklists, family-question gates, manual-verification cards, external counterevidence tasks, blocker-resolution boards, and internal sprint boards.

What it does not yet support:

- It does not support family-facing advice.
- It does not prove actual admission outcome improvement.
- It does not replace Evidence Autopilot's reviewed-evidence gates.
- It does not belong in the main product narrative until its scripts, inputs, and outputs are reproducible and indexed.

The batch is valuable, but currently it is a research run, not product code.

## Research Taste Calibration

Good current taste:

- The project repeatedly blocks family-facing delivery when evidence is incomplete.
- The real-case line separates public source proof, operator evidence, counselor review, and client delivery.
- The 2026-06-28 batch often records `familyAllowed=0` or `deliveryAllowed=0`, which is the correct conservative posture.

Bad drift to avoid:

- Treating a polished markdown report as proof.
- Treating internal opportunity ranking as recommendation truth.
- Adding another dashboard before one real case becomes fully reviewed and deliverable.
- Letting 80 one-off scripts become the new architecture by accident.
- Claiming 2026 admissions improvement without real outcome validation.

Current research standard:

Every opportunity claim must answer:

- What is the claim?
- Which source supports it?
- What exact excerpt supports it?
- What would disprove it?
- Is it admission, progression, career, civil-service, or family-fit evidence?
- Is it ready for counselor review, or is it still an evidence gap?

If it cannot answer these, it is an evidence gap, not a recommendation.

## File Organization Problem

The main disorder is not in `frontend/` or `backend/`. The disorder is that exploratory research outputs are sitting at top-level as if they are active product assets.

Problems:

- `scripts/` now mixes deploy scripts, stable product utilities, and many one-off research generators.
- `analysis_outputs/` is not indexed by `00_REPORTS_INDEX.md` or a run manifest.
- `analysis_inputs/` contains manual/external seeds without a root-level explanation.
- The latest untracked batch is larger than the tracked repo by file count.
- Some older docs still mention mojibake or have old claim boundaries; current Real Case fixture/source-log has guards, but historical docs remain noisy.

## Recommended Classification

Use this classification going forward:

| Class | Meaning | Examples | Action |
| --- | --- | --- | --- |
| Product mainline | code that powers the runnable app or backend contract | `frontend/src/lib/evidenceAutopilot*`, `backend/src/evidence_autopilot_api.py` | keep tested and committed |
| Research run | generated exploration with inputs, outputs, scripts, and report | `analysis_outputs/special_control_opportunity_pipeline/` | add manifest, then archive or commit as one run |
| Evidence fixture | small curated data used by tests/demo | `data/evidence_autopilot/real_case_v0.json` | keep small and reviewed |
| Historical record | old docs/logs that explain project evolution | `docs/reports_archive/`, `logs/` | keep but do not cite as current proof without audit |
| Temporary artifact | screenshots, preview outputs, scratch files | `tmp/`, `output/` | ignore or periodically clean after handoff |

## Suggested Cleanup Plan

1. Create a run manifest for the 2026-06-28 batch.
   - Name: `docs/research_runs/2026-06-28-special-control-opportunity-pipeline.md`
   - Include command order, input files, output folders, and claim boundary.

2. Move or group the 80 new scripts.
   - Prefer `scripts/research_runs/2026_06_28_special_control/`.
   - Keep a small stable wrapper only if this should become repeatable tooling.

3. Decide what to track.
   - Track compact reports, status files, seed templates, and scripts needed to reproduce.
   - Do not track every large intermediate unless it is required evidence.
   - Keep raw generated bulk under `analysis_outputs/` ignored or archived if it is not needed for review.

4. Update `00_REPORTS_INDEX.md`.
   - Add a short "2026-06-28 opportunity discovery research run" entry.
   - Mark it internal-only.

5. Resume product work only through one narrow gate.
   - The next product-quality slice should be one real candidate/opportunity case moving from the research run into Evidence Autopilot reviewed evidence.
   - Do not broaden to a multi-case platform until that case passes source, counterevidence, family-fit, and counselor gates.

## Current Answer To "What State Are We In?"

PathFinder is currently a strong but overgrown research-product hybrid.

The committed codebase has a defensible direction: an auditable Gaokao opportunity system with internal delivery gates. The untracked 2026-06-28 batch shows a lot of useful opportunity-mining work, but it is not yet governed as a reproducible research run and should not be treated as client-ready output.

The right next move is not more feature creation. It is consolidation:

- freeze the current mainline,
- register the 2026-06-28 batch as an internal research run,
- pick one candidate from that batch,
- push that one case through Evidence Autopilot and counselor gates,
- only then decide which scripts and outputs deserve to become permanent project assets.

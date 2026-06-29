# 2026-06-28 Special-Control Opportunity Pipeline Manifest

Date registered: 2026-06-30
Run date: 2026-06-28
Status: internal research run only

## Purpose

This manifest registers the large local opportunity-mining batch generated on 2026-06-28. The raw batch is useful for retrospective research, but it is not committed as product code and it is not family-facing advice.

The batch should be used for one narrow next step:

```text
select one retrospective candidate -> build one clean case dossier -> run Evidence Autopilot gates -> audit against 2026 outcomes when available
```

## Scope

The run explored special-control and elite-opportunity candidates through yearly professional-group changes, evidence gaps, family hard-stop questions, manual verification gates, and external counterevidence checks.

Local raw inputs and outputs:

- `analysis_inputs/`
- `analysis_outputs/`
- `analysis_outputs/special_control_opportunity_pipeline/pipeline_run_report.md`
- `analysis_outputs/special_control_opportunity_pipeline/pipeline_run.json`
- one-off generator scripts under `scripts/build_*.py`, `scripts/run_special_control_*.py`, and related local scratch scripts

These raw artifacts remain local and are ignored by git unless a later review explicitly promotes selected files.

## Why The Raw Batch Is Not Uploaded

The raw batch contains hundreds of generated files and many one-off scripts. Uploading all of it would make the repository look more complete while making the research state less clear.

The correct research boundary is:

- keep the raw run local;
- commit this manifest and the post-season summary;
- promote only curated case dossiers or audited result summaries later.

## Observed Pipeline Shape

The run produced multiple internal boards and audits, including:

- yearly professional-group change ledger;
- special-control opportunity cards;
- elite / 985 / 211 rechecks;
- top-20 and top-50 comprehensive audits;
- external counterevidence worklists;
- family-fit and hard-question gates;
- manual verification cards;
- blocker-resolution boards;
- blind-spot intake and next-attack boards.

The pipeline repeatedly recorded internal-only boundaries such as `familyAllowed=0`, `deliveryAllowed=0`, `internal_only`, and `not family-facing`.

## Evidence Boundary

This run does not prove:

- final 2026 admission recommendation quality;
- admission probability accuracy;
- employment, graduate progression, or civil-service outcomes;
- counselor-approved deliverability;
- family-facing readiness;
- generalized live official-source retrieval.

This run can support:

- opportunity hypothesis generation;
- retrospective candidate selection;
- evidence-gap discovery;
- family-constraint question design;
- counterevidence checklist design;
- one-case audit preparation.

## Candidate Selection Rule For Next Work

Pick one candidate only. The selected candidate must have:

- a visible opportunity mechanism, such as group restructuring, low-heat professional package, code change, or overlooked strong-school window;
- current official 2026 plan or charter evidence;
- a 2025 historical rank or major-line anchor;
- at least one plausible counterevidence path;
- explicit family hard-stop questions;
- a path into Evidence Autopilot reviewed-evidence gates.

Do not select a candidate just because it has the highest score. Select the candidate that can be audited cleanly.

## Next Required Artifact

Create one case dossier:

```text
docs/case_studies/2026-retro-case-001.md
```

Required sections:

- candidate identity and claim;
- opportunity mechanism;
- official source evidence;
- rank / major anchor;
- counterevidence;
- family-fit hard questions;
- counselor decision;
- blocked gates;
- expected retrospective audit once 2026 actual admission outcomes are available.

## Claim Boundary For Any Future Summary

Allowed wording:

```text
This run generated internal opportunity hypotheses and evidence worklists for post-season review.
```

Forbidden wording:

```text
This run produced family-facing recommendations.
This run proves improved 2026 admissions outcomes.
This run is counselor-approved.
```

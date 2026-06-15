# External Plan Comparator Design

Date: 2026-06-15

## Goal

Build a lightweight external-plan audit layer for PathFinder so a counselor can paste a Qianwen, parent, or human-written volunteer plan and compare its structure against the current PathFinder plan.

This iteration deliberately excludes new official-data ingestion. It must not claim that the external plan is correct or incorrect.

## Product Position

Qianwen Gaokao can generate broad answers quickly. PathFinder should differentiate by turning any external answer into an auditable decision artifact:

- Which school-major-group rows overlap with the current plan.
- Which external rows are not represented in PathFinder's structure.
- Whether rush/target/safe tags are missing or imbalanced.
- Which rows need manual review before a real application decision.

The product value is not another generated list. It is a repeatable review protocol.

## Evidence Boundary

The audit protocol is intentionally conservative:

- It does not judge whether the external plan is right or wrong.
- It does not use incomplete 2026 official data to create new conclusions.
- It only provides structure checks and review actions.
- Formal recommendation readiness remains controlled by the existing data vintage and plan audit gates.

## MVP Scope

Frontend-only:

- Add a pure parser and audit helper.
- Add an external plan comparison panel to `GameMatrixView`.
- Show parsed row count, matched row count, overlap rate, strategy mix, unmatched rows, and review actions.
- Keep the helper independent from React so it can later move behind an API or report export step.

Out of scope:

- Official-data refresh.
- LLM-based semantic matching.
- Auto-merging an external plan into the volunteer list.
- Report-template layout changes.

## Follow-Up Slots

- Add a saved comparison artifact to the internal delivery review console.
- Export external-plan audit results into the report package.
- Add stricter matching once official 2026 enrollment and admission data are complete.
- Add a side-by-side A/B table if users repeatedly compare two full volunteer lists.

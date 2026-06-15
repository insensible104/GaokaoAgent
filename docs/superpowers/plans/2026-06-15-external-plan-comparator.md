# External Plan Comparator Plan

Date: 2026-06-15

## Claim Map

| Claim | Evidence Required | Implementation |
| --- | --- | --- |
| External plans can be reviewed without official-data refresh. | The tool only parses pasted rows and compares them with current plan structure. | `externalPlanAudit.ts` exposes parser and audit summary with explicit claim boundary. |
| PathFinder can differentiate from generic Qianwen-style generation. | The UI converts an outside answer into unmatched rows and concrete review actions. | `ExternalPlanComparator.tsx` renders metrics, strategy mix, unmatched entries, and findings. |
| The feature is safe to ship as an internal audit aid. | It avoids correctness claims and formal recommendation language. | UI copy states the PathFinder audit scope and non-official-data boundary. |

## Implementation Steps

1. Add a smoke test that requires parser, audit protocol, UI labels, and GameMatrix integration.
2. Add `parseExternalPlanText` and `auditExternalPlan` as pure functions.
3. Add `ExternalPlanComparator` for paste input, metrics, unmatched entries, and review actions.
4. Render the comparator after the existing volunteer-plan audit workbench.
5. Run targeted tests, lint, build, and a local browser smoke check.
6. Stage only this comparator iteration and leave unrelated report-template edits unstaged.

## Verification

- `node src\components\ExternalPlanComparator.test.mjs`
- `node src\components\GameMatrixView.quantEvidence.test.mjs`
- `npm run lint`
- `npm run build`
- Browser smoke on the built or dev frontend route.

## Known Limits

- Matching is syntactic and conservative.
- Missing group codes fall back to school-level matching only when the external line lacks a group.
- The feature does not replace manual review, official enrollment-plan refresh, or final application validation.

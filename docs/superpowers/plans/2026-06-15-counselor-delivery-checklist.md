# Counselor Delivery Checklist Plan

Date: 2026-06-15

## Claim Map

| Claim | Why It Matters | Evidence |
| --- | --- | --- |
| PathFinder can behave like a delivery system, not just a generator. | Families and counselors need actionability, not another chat answer. | The checklist turns existing evidence into blocked/review/ready items. |
| The feature remains safe without official-data refresh. | 2026 official data is incomplete. | The helper only organizes existing signals and keeps a conservative claim boundary. |
| External Qianwen or teacher plans can become audit inputs. | Users will compare plans anyway. | The checklist includes an external-comparison item that points to the external plan auditor. |

## Implementation Steps

1. Add a smoke test requiring the checklist helper, protocol tokens, UI labels, and GameMatrix integration.
2. Implement `buildCounselorDeliveryChecklist` as a pure helper.
3. Implement `CounselorDeliveryChecklist` as a presentational component.
4. Render it after the existing internal plan audit workbench.
5. Update GameMatrix smoke coverage.
6. Run targeted tests, lint, build, and browser smoke.
7. Stage only this iteration and leave unrelated report-template edits unstaged.

## Verification

- `node src\components\CounselorDeliveryChecklist.test.mjs`
- `node src\components\GameMatrixView.quantEvidence.test.mjs`
- Existing frontend smoke tests
- `npm run lint`
- `npm run build`
- Local preview smoke

## Follow-Up

- Persist counselor checklist decisions as a delivery review record.
- Mirror the checklist into internal delivery review.
- Add handoff export when the report template work is stable.
- Track whether external plan comparison was completed from the comparator state.

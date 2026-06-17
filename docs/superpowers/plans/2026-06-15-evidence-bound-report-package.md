# Evidence-Bound Report Package

Date: 2026-06-15

## Claim

The report template can keep the polished sample-report visual direction, but formal payload rendering must be evidence-bound. A real analyzed payload must not leak sample-only claims such as fixed 985/A+ counts, example-student labels, or default cities and majors.

## Implementation

- Export `buildReportPayload` so behavior tests can inspect the report data contract.
- Add `PathFinderReportTemplate.behavior.test.mjs`.
- Keep sample-mode defaults only when no `gameMatrix` exists.
- For real payloads, build profile, strategy, focus, rows, evidence, risks, and data boundary from `gameMatrix`, `deliveryProfile`, `plan_audit_summary`, and `deliveryReadiness`.
- Preserve the existing visual template work without resetting the dirty report layout.

## Verification Contract

The behavior test asserts:

- real rows come from `gameMatrix`
- row evidence comes from `quant_evidence`
- profile text comes from `deliveryProfile`
- strategy mix comes from `total_rush / total_target / total_safe`
- sample-only strings such as `示例29`, fixed 985/A+ counts, and default city lists do not appear in formal payload fields

## Remaining Boundary

This does not make the report a signed final filing document. It remains a delivery package that must disclose official-data limits and requires final human review before application submission.

# GaokaoAgent Iteration Log

This log records product-facing and engineering-facing improvements that are easy to miss from terse commit titles. Use it with `git log` when reviewing whether each iteration moved GaokaoAgent closer to the goal:

> Make high-quality Gaokao volunteer planning more equal, auditable, and affordable, while approaching the rigor of top counseling agencies and creators.

## Logging Standard

Each future iteration should record:

| Field | Meaning |
| --- | --- |
| Goal | The user/business problem this iteration addresses. |
| Commits | Git commits included in the iteration. |
| What Changed | Concrete implementation changes. |
| Why It Matters | Product, delivery, risk, or quant value. |
| Validation | Commands/tests/builds actually run. |
| Remaining Risk | What is still not proven or still manual. |

## 2026-06-12: Portfolio-Level Client Delivery Readiness

### Goal

Make batch service review reflect whether cases are actually safe to send to families, not just whether individual audit modules produced artifacts.

### Commits

| Commit | Title |
| --- | --- |
| this commit | Track client delivery readiness in portfolio audits |

### What Changed

- Extended delivery portfolio audits with client-delivery readiness metrics:
  - `client_delivery_allowed_rate`
  - `client_delivery_blocked_rate`
  - `client_delivery_status_counts`
  - top repeated client-delivery blocked reasons
- Made portfolio aggregation prefer explicit `client_delivery` manifest gates when present.
- Added conservative fallback behavior for older manifests that do not yet include `client_delivery`.
- Added Markdown reporting for client delivery gate counts and repeated blocked reasons.
- Fed client-delivery allowed rate into the overall self-improvement audit so low client-ready share becomes prioritized product work.
- Updated smoke coverage to assert both explicit client-delivery gates and legacy-manifest fallback behavior.

### Why It Matters

Single-case gates prevent one bad handoff. Batch metrics show whether the service process is improving across paid cases. For real counseling operations, this matters more than a beautiful single report: if many cases remain blocked from client delivery, the product still has workflow, intake, plan-quality, or report-quality problems.

This moves the project closer to an internal operations dashboard where a counselor can answer:

- How many cases can be safely sent to families now?
- How many are still internal-only?
- Which repeated blocked reasons should become the next product or process fix?

### Validation

| Command | Result |
| --- | --- |
| `uv run python -m pytest src/test_delivery_portfolio_smoke.py src/test_delivery_bundle_smoke.py src/test_improvement_audit_smoke.py` | 4 passed |
| `uv run ruff check src/evaluation/delivery_portfolio.py src/test_delivery_portfolio_smoke.py` | not run: `ruff` is not installed in the backend environment |

### Remaining Risk

- Portfolio audit still depends on exported delivery manifests being collected into a batch.
- The dashboard/UI does not yet visualize these portfolio metrics directly.
- The current gate is deterministic; final counselor review remains required before paid delivery.

## 2026-06-11: Client-Safe Delivery Export Split

### Goal

Reduce operational risk in paid-case handoff by separating internal audit materials from client-facing confirmation materials.

### Commits

| Commit | Title |
| --- | --- |
| this commit | Split client-facing and internal delivery exports |
| this commit | Add manifest-driven artifact audience tags |
| this commit | Gate client package download by delivery status |

### What Changed

- Added a separate frontend download action for a client-facing confirmation package.
- Limited the client package to:
  - `expectation_packet`
  - `final_report`
- Kept the full internal preflight package as a separate download that includes audits, gates, and internal review artifacts.
- Preserved the previous complete internal export for counselor review and case archiving.
- Added backend artifact audience tags:
  - `client_confirmation`
  - `internal_review`
- Updated the frontend client package filter to prefer manifest `audience` metadata while keeping id-based fallback compatibility.
- Added a backend `client_delivery` gate so client package download is allowed only when the case is `ready_to_deliver` or `pending_signoff`.
- Disabled frontend client-package download and showed the backend blocked reason when the bundle still needs revision.

### Why It Matters

The internal delivery workbench now supports two distinct handoff modes:

1. Internal review package: counselor-facing, includes audit findings and failed gates.
2. Client confirmation package: family-facing, focuses on expectation confirmation and final recommendation text.

This reduces the chance of sending internal diagnostic language to families while still preserving a complete review trail for the counselor.

### Validation

| Command | Result |
| --- | --- |
| `npm run build` in `frontend/` | passed |
| `npm run lint` in `frontend/` | 0 errors, 2 existing Fast Refresh warnings |

### Remaining Risk

- The client package is still Markdown, not a signed PDF/DOCX with signature fields.
- The split and download permission are now manifest-driven, but the project still needs a signed PDF/DOCX export path before polished paid delivery.

## 2026-06-07: One-Click Delivery Bundle Export

### Goal

Close the immediate operational gap in the internal delivery workbench: after a case passes or partially passes pre-delivery review, the counselor should be able to export a complete review packet for manual checking, archiving, or client-delivery preparation.

### Commits

| Commit | Title |
| --- | --- |
| this commit | Return and download complete delivery preview bundle |

### What Changed

- Returned `delivery_bundle.md` from `/api/delivery/preview` as the `delivery_bundle` artifact.
- Added API smoke assertions that the delivery bundle index is returned and contains `服务交付包`.
- Added a frontend "下载完整预检包" action to the internal delivery review workbench.
- Combined all returned Markdown artifacts into one downloadable Markdown file named `<case_id>-delivery-preview.md`.

### Why It Matters

The previous workbench made delivery issues visible but still required manual copying across multiple previews. This iteration makes the workflow closer to how an internal counseling desk actually works:

1. Generate recommendation.
2. Run internal delivery preflight.
3. Inspect gates and next actions.
4. Download a single review packet.
5. Use that packet for human review, family confirmation, or case archive.

This reduces operational friction and makes it easier to prove what was explained before handoff.

### Validation

| Command | Result |
| --- | --- |
| `uv run python -m pytest src/test_backend_api_status_smoke.py src/test_delivery_bundle_smoke.py` | 7 passed |
| `npm run build` in `frontend/` | passed |
| `npm run lint` in `frontend/` | 0 errors, 2 existing Fast Refresh warnings |

### Remaining Risk

- The export is Markdown, not a signed PDF or DOCX package.
- It still depends on the counselor using the download before final communication.
- The frontend does not yet support separate "client-facing" versus "internal-only" artifact filtering.

## 2026-06-05: Structured Delivery Review Workbench

### Goal

Move the project from "can generate a recommendation report" toward "can support real internal case delivery." The immediate business problem is reducing disputes caused by unclear constraints, unclear risk boundaries, and weak pre-delivery quality control.

### Commits

| Commit | Title |
| --- | --- |
| `c599b74` | Add internal delivery review workbench |
| `25dbe25` | Feed volunteer plans into delivery preview |

### What Changed

- Added a FastAPI internal delivery endpoint: `POST /api/delivery/preview`.
- Added a frontend internal workbench: `frontend/src/components/InternalDeliveryReview.tsx`.
- Preserved structured intake fields from the frontend form:
  - score, rank, subject group
  - preferred cities
  - preferred majors
  - blacklisted majors
  - risk tolerance
  - subject scores
- Connected delivery preview to existing deterministic delivery artifacts:
  - intake readiness audit
  - expectation packet
  - volunteer-plan quality audit
  - report quality audit
  - delivery gates
  - next actions
- Extended `/api/delivery/preview` to accept an optional structured `VolunteerPlan`.
- Made the frontend pass `game_matrix.volunteer_plan` when available.
- Added a frontend fallback that synthesizes a `VolunteerPlan` from `major_group_rows` when the backend does not return a plan.
- Preserved key plan-quality fields in the synthesized plan:
  - choice order
  - school and major-group code
  - rush/target/safe tag
  - admission probability
  - adjustment advice
  - tail-assignment risk
  - major choices
  - blacklist risk
  - quant evidence
- Added API smoke coverage so delivery preview with a structured plan no longer silently regresses to `plan_quality_status=not_provided`.

### Why It Matters

Before this iteration, the project had strong offline delivery-audit modules, but the user-facing workflow still stopped at "generate report." That created a product gap: a counselor could not easily inspect whether a generated case was ready to show a family.

This iteration makes the UI support an internal service workflow:

1. Collect a case.
2. Generate analysis.
3. Inspect game matrix and report.
4. Run delivery preview.
5. See blocked gates and next actions.
6. Review expectation and disclaimer artifacts before handing anything to a client.

This directly addresses the 2025 service pain point: families may impose hard constraints such as "only in province" and later judge recommendations poorly unless the constraints, tradeoffs, and non-guarantee boundaries were confirmed before delivery.

### Validation

Latest verified commands during this iteration:

| Command | Result |
| --- | --- |
| `uv run python -m pytest src/test_backend_api_status_smoke.py src/test_delivery_bundle_smoke.py` | 7 passed |
| `uv run python scripts/gaokao_agent.py smoke --fail-fast` | 43 smoke tests passed |
| `npm run build` in `frontend/` | passed |
| `npm run lint` in `frontend/` | 0 errors, 2 existing Fast Refresh warnings |
| `curl http://127.0.0.1:8000/api/status` | backend status returned successfully |
| `curl -I http://127.0.0.1:5173/app/` | frontend returned 200 |

Known lint warnings:

- `frontend/src/components/ui/badge.tsx`: Fast Refresh warning because the file exports both component and variant helper.
- `frontend/src/components/ui/button.tsx`: Fast Refresh warning for the same pattern.

These warnings predate the delivery-workbench iteration and do not block production build.

### Remaining Risk

- The fallback frontend `VolunteerPlan` synthesis is an audit bridge, not a replacement for a backend-generated final plan. The preferred path remains returning canonical `game_matrix.volunteer_plan` from the backend.
- The internal workbench still needs real case walkthroughs to find operational friction.
- The current frontend can preview Markdown artifacts, but it does not yet provide one-click export of a complete signed delivery bundle.
- The current delivery gates are deterministic checks. They do not replace human review for official招生章程, fee, campus, medical restriction, and final考试院 data confirmation.

## 2026-06-04: Self-Improving Quant and Evidence Loop

### Goal

Move from isolated recommendation logic toward a repeatable improvement loop: evidence collection, quant evaluation, failure mining, claim control, and next-action planning.

### Commits

| Commit | Title |
| --- | --- |
| `8b76c44` | Add next iteration plan |
| `78cbf14` | Wire research evidence into experiment suite |
| `c658c8b` | Fold research evidence into improvement audit |
| `0fa121b` | Add research evidence audit |
| `e7c39bf` | Add claim readiness portfolio |
| `bb9c10f` | Add claim readiness gate |
| `19e5f2e` | Track benchmark coverage repair impact |
| `fc27c5a` | Add benchmark coverage repair plan |
| `dc01729` | Add benchmark coverage audit |
| `7b237ab` | Add QuantLab experiment leaderboard |

### What Changed

- Added or extended the research evidence audit path.
- Wired research evidence into the experiment suite.
- Folded evidence quality into the improvement audit.
- Added claim-readiness gates and claim-readiness portfolio checks.
- Added benchmark coverage audit and repair planning.
- Added QuantLab leaderboard visibility.
- Added a next-iteration planner that consumes audit outputs and produces prioritized work.

### Why It Matters

This iteration makes the project less dependent on ad hoc judgment. Instead of "the model feels better," the project now has a loop:

1. Run experiments.
2. Audit evidence.
3. Audit claims.
4. Check benchmark coverage.
5. Mine failures.
6. Produce prioritized next actions.

That is the right direction for a product whose core promise is fairness and rigor rather than personality-driven counseling.

### Validation

The standard smoke suite was run repeatedly during this phase, with the latest full smoke state reported as:

- `uv run python scripts/gaokao_agent.py smoke --fail-fast`
- Result: 43 smoke tests passed.

### Remaining Risk

- A good improvement loop does not automatically mean the recommendations are already agency-grade.
- Benchmark coverage still needs more real edge cases from actual user consultations.
- Research evidence improves explanation and demand-side interpretation, but social/creator content must remain blocked from direct prediction ingestion.

## 2026-06-03: Research Evidence, Market Signals, and Delivery Governance

### Goal

Strengthen the parts that distinguish a professional planning workflow from a generic AI report: source-aware research, market/demand interpretation, delivery gates, and expectation control.

### Representative Commits

| Commit | Title |
| --- | --- |
| `a6e2a52` | Add source-aware deep research evidence |
| `4558545` | Convert research evidence into quant signals |
| `3a67020` | Feed research evidence into game scoring |
| `5b8c636` | Refresh game evidence after deep research |
| `d855e6d` | Block quant promotion on critical slice regressions |
| `6f8ae2f` | Add QuantLab failure mining |
| `baddc42` | Turn failure mining into improvement actions |
| `aeb7693` | Add failure replay queue |
| `1c7c139` | Add volunteer plan quality audit |
| `4c917fc` | Gate delivery bundles on plan quality |
| `8a0d643` | Include delivery gates in improvement audit |
| `74918e5` | Add delivery portfolio audit |
| `554b71c` | Include delivery portfolio in improvement audit |

### What Changed

- Added source-aware evidence cards for deep research.
- Converted approved research evidence into controlled quant signals.
- Fed research evidence into game scoring.
- Added failure mining and replay queue.
- Added volunteer-plan quality audit.
- Added delivery bundle gates.
- Included delivery and portfolio audits in the improvement audit.
- Blocked quant promotion when critical slice regressions appear.

### Why It Matters

Top counseling workflows are not just rankings. They combine:

- hard data
- preference discovery
- market behavior interpretation
- risk explanation
- plan structure checks
- customer expectation management
- final human review

This phase added the backbone for those checks, especially the distinction between "useful research signal" and "unsafe prediction input."

### Validation

The individual smoke tests for these modules were added and included in the full smoke suite:

- research evidence audit
- plan quality audit
- delivery bundle audit
- delivery portfolio audit
- failure mining
- replay queue
- improvement audit

### Remaining Risk

- Search evidence quality still depends on source collection and manual verification.
- WeChat and creator-platform discovery remain difficult to automate reliably. The safer near-term path is manual link capture plus evidence-card normalization.
- Delivery quality still depends on whether real counselors use the pre-delivery gates before talking to families.

## Push Documentation Gap Found

The commit history was readable enough to show technical direction, but not enough to support enterprise-style review:

- Commit titles usually described the engineering action, not the business reason.
- Validation results were recorded in conversation but not in Git.
- Multi-commit iterations lacked a single written summary.

This document is the correction. Future significant pushes should update this log in the same commit or in a follow-up documentation commit.

## Suggested Future Commit Body Template

```text
<short imperative title>

Why:
- Business or product problem.
- Risk being reduced or metric being improved.

What:
- Main implementation changes.
- Important files or interfaces.

Validation:
- Exact commands run and results.

Remaining risk:
- What is not proven.
- What still requires manual review.
```

# Delivery Review Record Design

Date: 2026-06-15

## Goal

Add a lightweight delivery review record so PathFinder behaves less like a one-shot generator and more like a trustworthy delivery workspace.

The immediate product claim: after the counselor sees the delivery checklist, they can copy a versioned review snapshot that records current status, blockers, review items, next action, and evidence boundary.

## Why This Slice

Persistence and CRM integration will matter later, but they are heavier than the current product needs. A copyable review record gives the team an immediate operating artifact:

- hand off a plan between advisors
- paste into Feishu, CRM, or a family follow-up note
- preserve the current review state before official data refresh
- make external Qianwen or teacher-plan comparisons part of the review record

## Evidence Boundary

The review record is not a new recommendation engine. It reuses the counselor delivery checklist and must state:

- it saves the current evidence snapshot
- it does not generate new admission conclusions
- it does not replace signed confirmation
- it does not override official-data readiness gates

## Interface

Add `buildDeliveryReviewRecord` in `frontend/src/lib/deliveryReviewRecord.ts`.

The helper returns:

- `delivery_review_record_v1`
- version stamp
- status
- lead action
- blocked items
- review items
- ready items
- metric counts
- copyable Markdown text
- claim boundary

Add `DeliveryReviewRecord` to `GameMatrixView` after `CounselorDeliveryChecklist` and before `ExternalPlanComparator`.

## Non-Goals

- No backend persistence.
- No user authentication.
- No report-template changes.
- No official-data refresh.
- No automatic sign-off.

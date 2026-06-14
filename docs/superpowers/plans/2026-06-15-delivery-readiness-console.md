# Delivery Readiness Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a delivery readiness console that turns the current recommendation into an operational handoff checklist and mirrors the same readiness summary into the A4 report preview.

**Architecture:** Add `frontend/src/lib/deliveryReadiness.ts` as the shared decision helper. Add `DeliveryReadinessConsole.tsx` for result-page presentation. Update `App.tsx` to pass readiness into the report preview payload and update `PathFinderReportTemplate.tsx` to render the same readiness gates.

**Tech Stack:** React, TypeScript, lucide-react icons, static Node smoke tests, Vite build.

---

### Task 1: Shared Readiness Helper

**Files:**
- Create: `frontend/src/lib/deliveryReadiness.ts`
- Test: `frontend/src/components/DeliveryReadinessConsole.test.mjs`

- [x] **Step 1: Write failing static smoke test** requiring `buildDeliveryReadinessSummary`, gate ids `data_boundary`, `plan_structure`, `evidence_pack`, `report_package`, `human_review`, and conservative claim-boundary copy.
- [x] **Step 2: Run smoke test** with `node src\components\DeliveryReadinessConsole.test.mjs`; expect failure because the helper and component are missing.
- [x] **Step 3: Implement `buildDeliveryReadinessSummary`** using existing `game_matrix.plan_audit_summary`, `data_vintage`, `volunteer_plan`, report text, and profile fields.
- [x] **Step 4: Re-run smoke test** and confirm the helper contract tokens are present.

### Task 2: Result Page Console

**Files:**
- Create: `frontend/src/components/DeliveryReadinessConsole.tsx`
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/components/DeliveryReadinessConsole.test.mjs`

- [x] **Step 1: Extend smoke test** requiring `DeliveryReadinessConsole`, `交付准备度`, `正式交付前必须复核`, `不是录取承诺`, and `打开 A4 报告预览`.
- [x] **Step 2: Run smoke test** and verify failure before implementation.
- [x] **Step 3: Implement console component** with five gate rows, overall status, and an A4 report preview action.
- [x] **Step 4: Replace the existing report-preview banner in `App.tsx`** with `DeliveryReadinessConsole`.
- [x] **Step 5: Re-run smoke test** and confirm it passes.

### Task 3: A4 Report Synchronization

**Files:**
- Modify: `frontend/src/components/PathFinderReportTemplate.tsx`
- Modify: `frontend/src/components/PathFinderReportTemplate.test.mjs`
- Modify: `frontend/src/App.tsx`

- [x] **Step 1: Extend report smoke test** requiring `DeliveryReadiness`, `deliveryReadiness`, `交付准备度`, and `正式交付前必须复核`.
- [x] **Step 2: Run report smoke test** and verify failure before implementation.
- [x] **Step 3: Add `deliveryReadiness` to `PathFinderReportPayload`** and compute it in `openReportTemplatePreview`.
- [x] **Step 4: Render a compact readiness section in the A4 report.**
- [x] **Step 5: Re-run report smoke test** and confirm it passes.

### Task 4: Verification And Publish

**Files:**
- Commit and push only the intended changes.

- [x] **Step 1: Run frontend smoke tests.**
- [x] **Step 2: Run `npm run lint` and `npm run build`.**
- [x] **Step 3: Browser-check `/app/report-template-preview` and the result-page route if reachable.**
- [x] **Step 4: Run `git diff --check`.**
- [ ] **Step 5: Commit and push to `codex/trusted-recommendation-baseline`.**

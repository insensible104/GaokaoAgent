# Public Demo And Report Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the public app entry, two public demos, and generated report into one evidence-workbench and research-report visual system.

**Architecture:** Keep the existing React/Vite/Tailwind stack and data contracts. Add a static redesign contract test, then change presentation components only: `App.tsx`, `ExternalPlanAuditDemoPanel.tsx`, `AdmissionsOpportunityDemoCasePanel.tsx`, and `PathFinderReportTemplate.tsx`.

**Tech Stack:** React 19, Vite, Tailwind classes, static Node smoke tests.

---

### Task 1: Redesign Contract Test

**Files:**
- Create: `frontend/src/components/PublicDemoAndReportRedesign.test.mjs`
- Modify: none

- [ ] **Step 1: Write failing test** requiring new design tokens and no mojibake.
- [ ] **Step 2: Run `node frontend/src/components/PublicDemoAndReportRedesign.test.mjs` and verify it fails before implementation.**

### Task 2: Public App Shell

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Replace gradient landing shell with evidence-workbench shell.**
- [ ] **Step 2: Keep existing routes and form behavior intact.**

### Task 3: Public Demo Workstations

**Files:**
- Modify: `frontend/src/components/ExternalPlanAuditDemoPanel.tsx`
- Modify: `frontend/src/components/AdmissionsOpportunityDemoCasePanel.tsx`

- [ ] **Step 1: Reframe each public demo as a three-zone workbench.**
- [ ] **Step 2: Preserve existing child components and all public static demo data.**

### Task 4: Research Report Template

**Files:**
- Modify: `frontend/src/components/PathFinderReportTemplate.tsx`
- Modify if needed: `frontend/src/components/PathFinderReportTemplate.test.mjs`

- [ ] **Step 1: Replace old brochure skin with research-report design tokens.**
- [ ] **Step 2: Rename visible report framing around opportunity radar, trend analysis, risk ledger, evidence ledger, and delivery boundary.**
- [ ] **Step 3: Preserve `EvidenceLedger`, `RiskLedger`, `buildReportPayload`, real-payload safeguards, and report preview route.**

### Task 5: Verification

**Files:**
- No new files unless verification reveals a focused fix.

- [ ] **Step 1: Run focused Node smoke tests for redesign and report template.**
- [ ] **Step 2: Run `npm run build` in `frontend`.**
- [ ] **Step 3: Run browser verification for `/app`, `/app/admissions-opportunity-demo`, `/app/external-plan-audit-demo`, and `/app/report-template-preview`.**

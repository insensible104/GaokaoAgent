# PathFinder Post-Score Season Project Summary

Date: 2026-06-29

## Bottom Line

PathFinder should no longer be treated as a 2026 live delivery product. Scores are already out, the decision window is compressed, and the current system is not validated enough to responsibly support real family-facing advice this year.

This is not a reason to discard the project. It is a reason to change its operating mode:

```text
2026 emergency delivery attempt -> post-season research/product asset -> 2027-ready evidence system
```

## What The Project Actually Became

PathFinder started as a Gaokao recommendation and agent system, but its strongest current form is more specific:

```text
An evidence-governed opportunity discovery system for Gaokao volunteer planning.
```

The valuable part is not "AI recommends schools." The valuable part is:

- finding non-obvious school-major-group opportunities,
- explaining the mechanism behind the opportunity,
- collecting official and counter-evidence,
- forcing family-fit and counselor-review gates,
- blocking delivery when evidence is incomplete.

The core loop remains:

```text
quant positioning -> Evidence Autopilot -> Opportunity Radar -> Deep Opportunity Card -> Chinese report / internal review
```

## What Worked

The project produced real reusable assets:

- A runnable frontend/backend research prototype.
- Structured recommendation, risk-control, and report-generation foundations.
- 2025 admissions/outcome data and backtest-oriented artifacts.
- Evidence Autopilot contracts, provider/result normalization, reviewed-evidence ledger, attachment/redaction gates, and internal delivery review.
- Real Case v0: a fixture-backed auditable slice that proves the workflow can preserve evidence boundaries.
- A large 2026-06-28 opportunity-mining batch that shows how to search for special-control, elite, local-strong-school, and blind-spot opportunities.

The best design decision was conservative gating. The system repeatedly says "internal only" instead of pretending a partially supported opportunity is ready for a parent.

## What Did Not Work

The project did not converge in time for the live 2026 admissions cycle.

Main reasons:

- Scope expanded faster than one real deliverable could be hardened.
- Too many subsystems accumulated: RL, graph agents, quant scoring, report UI, delivery gates, evidence search, opportunity mining, family-fit routing.
- The Evidence Autopilot path became strong internally but not production-ready for live source retrieval, reviewer auth, redaction UI, and counselor signoff.
- The 2026-06-28 opportunity batch is promising but uncurated: many scripts and outputs exist, but they are not yet a reproducible, indexed research run.
- There is still no outcome validation proving improved real admissions decisions.

The failure mode is not "nothing works." The failure mode is "too much works partially, and the parts were not narrowed early enough into one deliverable."

## 2026 Claim Boundary

For this year, the correct claim is:

```text
PathFinder can support internal research, retrospective analysis, and opportunity hypothesis generation.
It should not be used as final 2026 family-facing admission advice.
```

Do not claim:

- admission probability accuracy for 2026,
- improved real admission outcomes,
- production readiness,
- counselor-approved final recommendation,
- employment or progression outcome certainty,
- family-facing deliverability from the current internal reports.

Safe claims:

- The system has a coherent evidence-gated product direction.
- It has reusable product and research infrastructure.
- It can generate internal opportunity hypotheses and evidence worklists.
- It can expose why a case is blocked instead of hiding uncertainty.

## What To Keep

Keep as core assets:

- `frontend/src/lib/evidenceAutopilot*`
- `frontend/src/lib/opportunityDiscoveryEngine.ts`
- `frontend/src/lib/planChangeOpportunityLedger.ts`
- `frontend/src/lib/planChangeDiffEngine.ts`
- `frontend/src/lib/evidenceTriangulationReport.ts`
- `frontend/src/lib/publicOpinionTrendAnalyzer.ts`
- `backend/src/evidence_autopilot_api.py`
- `backend/src/official_source_provider.py`
- `backend/src/reviewed_evidence_store.py`
- `backend/src/reviewed_evidence_attachment_store.py`
- `data/evidence_autopilot/real_case_v0.json`
- `docs/evidence_autopilot/real_case_v0_handoff.md`
- the 2026-06-28 research batch, but only after it is indexed as an internal research run.

## What To Freeze

Freeze for now:

- new UI/dashboard expansion,
- broad multi-case delivery claims,
- additional agent spectacle,
- RL/GRPO delivery claims,
- client-facing report wording,
- more opportunity-mining scripts before the existing 80 scripts are organized.

## What To Archive Or Downgrade

Archive or treat as historical:

- one-off preview screenshots,
- old temporary output,
- stale public-demo positioning,
- old prompt/RL claims that are not connected to current evidence gates,
- generated bulk outputs that cannot be traced to commands, inputs, and claim boundaries.

## Recommended 2027-Oriented Path

The next phase should be small and evidence-first:

1. Register the 2026-06-28 opportunity pipeline as a research run.
2. Pick one candidate opportunity from the batch.
3. Build a clean case packet with official source, historical rank anchor, group/major mapping, counter-evidence, family-fit hard questions, and counselor decision.
4. Push that case through Evidence Autopilot's reviewed-evidence and delivery gates.
5. Run a retrospective audit against 2026 actual admission outcomes once outcome data is available.
6. Only after that, build the 2027-facing workflow.

## Strategic Judgment

PathFinder missed the 2026 live-use window. That should stop the emergency product push.

But as a long-term asset, it still has a clear shape: it can become a serious, evidence-governed admissions research and counseling workflow if it is consolidated around one proof-grade case at a time.

The next correct posture is patience and reduction:

```text
fewer features,
fewer scripts,
one reproducible run,
one reviewed case,
one honest retrospective result.
```
